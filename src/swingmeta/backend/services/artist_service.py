import json
import logging
from typing import Any, Dict, List, Optional

from config import settings
from database import swing_db, user_db
from services.hash_utils import create_hash

log = logging.getLogger(__name__)


class ArtistService:
    @staticmethod
    def get_all_artists() -> List[Dict[str, Any]]:
        """
        Extracts and aggregates all artists from swingmusic.db track table,
        joined with metadata from userdata.db.
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
                try:
                    artists_data = json.loads(row["artists"]) if row["artists"] else []
                except Exception:
                    artists_data = []

                try:
                    album_artists_data = json.loads(row["albumartists"]) if row["albumartists"] else []
                except Exception:
                    album_artists_data = []

                combined_artists = []
                for a in artists_data:
                    if isinstance(a, dict) and "name" in a:
                        combined_artists.append(a)
                for a in album_artists_data:
                    if isinstance(a, dict) and "name" in a:
                        if not any(ca.get("artisthash") == a.get("artisthash") for ca in combined_artists):
                            combined_artists.append(a)

                albumhash = row["albumhash"] or ""
                duration = row["duration"] or 0

                for a in combined_artists:
                    name = a.get("name", "").strip()
                    if not name:
                        continue
                    ahash = a.get("artisthash") or create_hash(name, decode=True)

                    if ahash not in artist_map:
                        artist_map[ahash] = {
                            "artisthash": ahash,
                            "name": name,
                            "album_hashes": set(),
                            "track_count": 0,
                            "duration": 0,
                            "genres": set(),
                        }

                    entry = artist_map[ahash]
                    entry["track_count"] += 1
                    entry["duration"] += duration
                    if albumhash:
                        entry["album_hashes"].add(albumhash)

        # 2. Query userdata.db for bio, color, and extra info
        meta_map: Dict[str, Dict[str, Any]] = {}
        if settings.userdata_db_path.exists():
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
                    log.warning(f"Erro ao ler artistdata do userdata.db: {e}")

        # 3. Build final artist list with image check
        result = []
        for ahash, data in artist_map.items():
            img_filename = f"{ahash}.webp"
            has_image = (
                (settings.artist_images_lg / img_filename).exists()
                or (settings.artist_images_md / img_filename).exists()
                or (settings.artist_images_sm / img_filename).exists()
            )

            meta = meta_map.get(ahash, {})
            colors = []
            if meta.get("color"):
                try:
                    colors = json.loads(meta["color"]) if isinstance(meta["color"], str) else meta["color"]
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
                "image": f"/api/images/artist/medium/{img_filename}" if has_image else None,
                "image_lg": f"/api/images/artist/large/{img_filename}" if has_image else None,
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

        if settings.swingmusic_db_path.exists():
            with swing_db() as conn:
                cursor = conn.execute("""
                    SELECT id, title, artists, albumartists, album, albumhash, duration,
                           track, disc, date, genres, bitrate, filepath
                    FROM track
                    WHERE artists LIKE ? OR albumartists LIKE ?;
                """, (f"%{artisthash}%", f"%{artisthash}%"))

                for row in cursor.fetchall():
                    t_data = dict(row)
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
        Updates bio, info, and extra metadata for an artist in userdata.db.
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
