import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional

from config import settings
from database import swing_db, user_db
from services.hash_utils import create_hash

log = logging.getLogger(__name__)

KNOWN_PLACEHOLDER_MD5 = {
    # Deezer / SwingMusic default placeholder silhouettes
    "49a5d317ed0eedc6c1d7cdbc42d2fd22",  # 500x500 large
    "44ea537d85bf5c966c584b044d562e72",  # 500x500 large alt
    "0a016037a46f675271501143faf70722",  # medium
    "727257d93c7c1ddfe12ba3258cd2c86b",  # medium alt
    "8e83759394785b36ebe584df29e01e77",  # small
    "0b0793c22075523df33113a3fee28c65",  # small alt
    "e38dc6041923df57beecbf4bebb32b91",  # swingmusic assets/artist.webp
}


def is_valid_artist_image(artisthash: str) -> tuple[bool, int]:
    """
    Checks if an artist has a REAL custom photo (not a generic placeholder/silhouette).
    Returns (has_real_image, mtime_timestamp).
    """
    img_filename = f"{artisthash}.webp"
    for folder in (settings.artist_images_lg, settings.artist_images_md, settings.artist_images_sm):
        p = folder / img_filename
        if p.exists():
            try:
                data = p.read_bytes()
                if len(data) == 0:
                    continue
                h = hashlib.md5(data).hexdigest()
                if h in KNOWN_PLACEHOLDER_MD5:
                    return False, 0
                mtime = int(p.stat().st_mtime)
                return True, mtime
            except Exception:
                pass
    return False, 0


def extract_artists_from_raw(raw: Any) -> List[Dict[str, str]]:
    """
    Extracts artist names and calculates their artisthash from various representations:
    - Plain string: "The Offspring", "CPM 22 / Charlie Brown Jr.", "Artist 1, Artist 2", "Artist 1; Artist 2"
    - JSON list of dicts: [{"name": "Queen", "artisthash": "..."}]
    - JSON list of strings: ["Queen", "David Bowie"]
    """
    if not raw:
        return []

    # 1. If already a list
    if isinstance(raw, list):
        items = []
        for item in raw:
            if isinstance(item, dict) and "name" in item:
                name = str(item["name"]).strip()
                if name:
                    ahash = item.get("artisthash") or create_hash(name, decode=True)
                    items.append({"name": name, "artisthash": ahash})
            elif isinstance(item, str) and item.strip():
                name = item.strip()
                items.append({"name": name, "artisthash": create_hash(name, decode=True)})
        return items

    # 2. If string
    if isinstance(raw, str):
        raw_str = raw.strip()
        if not raw_str:
            return []

        # Check if JSON string
        if (raw_str.startswith("[") and raw_str.endswith("]")) or (raw_str.startswith("{") and raw_str.endswith("}")):
            try:
                parsed = json.loads(raw_str)
                if isinstance(parsed, (list, dict)):
                    return extract_artists_from_raw(parsed)
            except Exception:
                pass

        # Split plain string by common music separators (, / ; & feat. ft.)
        # Protects AC/DC from being split
        parts = re.split(r'[,;&]|\bfeat\.?\b|\bft\.?\b|(?<!AC)\/(?!DC)', raw_str, flags=re.IGNORECASE)
        items = []
        for p in parts:
            name = p.strip()
            if name:
                items.append({"name": name, "artisthash": create_hash(name, decode=True)})
        return items

    return []


class ArtistService:
    @staticmethod
    def get_all_artists() -> List[Dict[str, Any]]:
        """
        Extracts and aggregates all artists from swingmusic.db track table,
        joined with metadata from userdata/swingmusic database.
        """
        if not settings.swingmusic_db_path.exists():
            return []

        artist_map: Dict[str, Dict[str, Any]] = {}

        # 1. Aggregate artists from tracks in swingmusic.db
        with swing_db() as conn:
            cursor = conn.execute("""
                SELECT id, artists, albumartists, album, albumhash, duration, genres, date
                FROM track;
            """)
            for row in cursor.fetchall():
                artists_list = extract_artists_from_raw(row["artists"])
                album_artists_list = extract_artists_from_raw(row["albumartists"])

                combined_artists = []
                seen_in_track = set()
                for a in artists_list + album_artists_list:
                    ahash = a["artisthash"]
                    if ahash not in seen_in_track:
                        seen_in_track.add(ahash)
                        combined_artists.append(a)

                albumhash = row["albumhash"] or ""
                duration = row["duration"] or 0

                for a in combined_artists:
                    name = a["name"].strip()
                    if not name:
                        continue
                    ahash = a["artisthash"]

                    if ahash not in artist_map:
                        artist_map[ahash] = {
                            "artisthash": ahash,
                            "name": name,
                            "album_hashes": set(),
                            "track_count": 0,
                            "duration": 0,
                        }

                    entry = artist_map[ahash]
                    entry["track_count"] += 1
                    entry["duration"] += duration
                    if albumhash:
                        entry["album_hashes"].add(albumhash)

        # 2. Query artistdata table (color, bio, info, extra)
        meta_map: Dict[str, Dict[str, Any]] = {}
        with user_db() as conn:
            try:
                cursor = conn.execute("""
                    SELECT itemhash, color, bio, info, extra
                    FROM artistdata
                    WHERE itemtype = 'artist' OR itemhash LIKE 'artist%';
                """)
                for row in cursor.fetchall():
                    ihash = row["itemhash"]
                    ahash = ihash.replace("artist", "")
                    meta_map[ahash] = {
                        "color": row["color"],
                        "bio": row["bio"],
                        "info": json.loads(row["info"]) if row["info"] else {},
                        "extra": json.loads(row["extra"]) if row["extra"] else {},
                    }
            except Exception as e:
                log.warning(f"Erro ao ler artistdata: {e}")

        # 3. Build final artist list with image check
        result = []
        for ahash, data in artist_map.items():
            img_filename = f"{ahash}.webp"
            has_image, img_mtime = is_valid_artist_image(ahash)

            meta = meta_map.get(ahash, {})
            colors = []
            if meta.get("color"):
                try:
                    colors = json.loads(meta["color"]) if isinstance(meta["color"], str) and meta["color"].startswith("[") else [meta["color"]]
                except Exception:
                    colors = [meta["color"]]

            blurhash_val = meta.get("extra", {}).get("blurhash", "")

            result.append({
                "artisthash": ahash,
                "name": data["name"],
                "album_count": len(data["album_hashes"]),
                "track_count": data["track_count"],
                "duration": data["duration"],
                "has_image": has_image,
                "has_bio": bool(meta.get("bio")),
                "bio": meta.get("bio") or "",
                "colors": colors,
                "blurhash": blurhash_val,
                "info": meta.get("info") or {},
                "extra": meta.get("extra") or {},
                "image": f"/api/images/artist/medium/{img_filename}?t={img_mtime}" if has_image else None,
                "image_lg": f"/api/images/artist/large/{img_filename}?t={img_mtime}" if has_image else None,
            })

        # Sort alphabetically by default
        result.sort(key=lambda x: x["name"].lower())
        return result

    @classmethod
    def get_artist_by_hash(cls, artisthash: str) -> Optional[Dict[str, Any]]:
        """
        Returns full details for a specific artist by artisthash,
        including their albums and track list.
        """
        all_artists = cls.get_all_artists()
        artist = next((a for a in all_artists if a["artisthash"] == artisthash), None)
        if not artist:
            return None

        tracks = []
        album_dict = {}
        target_name = artist["name"].lower()

        if settings.swingmusic_db_path.exists():
            with swing_db() as conn:
                cursor = conn.execute("""
                    SELECT id, title, artists, albumartists, album, albumhash, duration,
                           track, disc, date, genres, bitrate, filepath
                    FROM track;
                """)

                for row in cursor.fetchall():
                    t_data = dict(row)
                    combined = extract_artists_from_raw(t_data.get("artists")) + extract_artists_from_raw(t_data.get("albumartists"))
                    if any(a["artisthash"] == artisthash or a["name"].lower() == target_name for a in combined):
                        tracks.append(t_data)
                        ahash = t_data.get("albumhash")
                        if ahash and ahash not in album_dict:
                            album_dict[ahash] = {
                                "albumhash": ahash,
                                "title": t_data.get("album"),
                                "date": t_data.get("date"),
                                "cover": f"/api/images/thumbnail/medium/{ahash}.webp",
                            }

        artist["tracks"] = tracks
        artist["albums"] = list(album_dict.values())
        return artist

    @staticmethod
    def update_artist_metadata(
        artisthash: str,
        bio: Optional[str] = None,
        info: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Updates bio, info, and extra metadata for an artist in artistdata table.
        """
        itemhash = f"artist{artisthash}"
        with user_db() as conn:
            row = conn.execute(
                "SELECT id, bio, info, extra FROM artistdata WHERE itemhash = ?;",
                (itemhash,),
            ).fetchone()

            if row:
                new_bio = bio if bio is not None else row["bio"]
                new_info = json.dumps(info) if info is not None else row["info"]
                current_extra = json.loads(row["extra"]) if row["extra"] else {}
                if extra is not None:
                    current_extra.update(extra)
                new_extra = json.dumps(current_extra)

                conn.execute("""
                    UPDATE artistdata
                    SET bio = ?, info = ?, extra = ?
                    WHERE itemhash = ?;
                """, (new_bio, new_info, new_extra, itemhash))
            else:
                new_info = json.dumps(info) if info else None
                new_extra = json.dumps(extra) if extra else json.dumps({})
                conn.execute("""
                    INSERT INTO artistdata (itemhash, itemtype, color, bio, info, extra)
                    VALUES (?, 'artist', NULL, ?, ?, ?);
                """, (itemhash, bio, new_info, new_extra))

            conn.commit()

        return True
