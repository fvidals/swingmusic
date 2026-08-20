import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import settings
from database import swing_db, user_db

log = logging.getLogger(__name__)


class PlaylistService:
    @staticmethod
    def find_m3u_files() -> List[Path]:
        """
        Finds all .m3u and .m3u8 files in the MUSIC_DIR.
        Prioritizes the 'Playlists' subdirectory if it exists.
        """
        music_dir = settings.MUSIC_DIR
        if not music_dir.exists():
            return []

        m3u_files = []

        # Check in Playlists directory first
        playlists_dir = music_dir / "Playlists"
        if playlists_dir.exists() and playlists_dir.is_dir():
            for p in playlists_dir.glob("*.m3u*"):
                if p.is_file():
                    m3u_files.append(p)

        # Also search recursively in music_dir
        for p in music_dir.rglob("*.m3u*"):
            if p.is_file() and p not in m3u_files:
                m3u_files.append(p)

        return sorted(m3u_files, key=lambda x: x.name.lower())

    @staticmethod
    def parse_m3u_lines(content: str, base_dir: Path) -> List[Dict[str, Any]]:
        """
        Parses the lines of an M3U file, extracting #EXTINF titles and target file paths.
        """
        items = []
        current_title = ""
        current_duration = 0

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("#EXTINF:"):
                # Format: #EXTINF:248,Ls Jack - Carla
                try:
                    meta = line[8:].split(",", 1)
                    current_duration = int(meta[0].strip()) if meta[0].strip().lstrip("-").isdigit() else 0
                    current_title = meta[1].strip() if len(meta) > 1 else ""
                except Exception:
                    current_title = line[8:].strip()
            elif not line.startswith("#"):
                # Audio file path (relative to M3U location or absolute)
                raw_path = line.replace("\\", "/")
                
                # Resolve path
                if os.path.isabs(raw_path):
                    resolved_path = Path(raw_path)
                else:
                    resolved_path = (base_dir / raw_path).resolve()

                items.append({
                    "raw_path": line,
                    "resolved_path": str(resolved_path),
                    "filename": Path(raw_path).name,
                    "title": current_title or Path(raw_path).stem,
                    "duration": current_duration,
                })
                current_title = ""
                current_duration = 0

        return items

    @classmethod
    def match_tracks_in_db(cls, parsed_items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Matches parsed M3U items against tracks in swingmusic.db.
        Returns the annotated track list and the list of matched trackhashes.
        """
        if not settings.swingmusic_db_path.exists():
            return parsed_items, []

        matched_hashes = []
        annotated_items = []

        with swing_db() as conn:
            for item in parsed_items:
                resolved_p = item["resolved_path"]
                filename = item["filename"]
                raw_p = item["raw_path"]

                # 1. Try exact filepath match
                row = conn.execute(
                    "SELECT id, title, artists, album, trackhash, filepath, duration FROM track WHERE filepath = ?;",
                    (resolved_p,),
                ).fetchone()

                # 2. Try normalized path match
                if not row:
                    norm_path = os.path.normpath(resolved_p)
                    row = conn.execute(
                        "SELECT id, title, artists, album, trackhash, filepath, duration FROM track WHERE filepath = ?;",
                        (norm_path,),
                    ).fetchone()

                # 3. Try filename substring or suffix match
                if not row and filename:
                    row = conn.execute(
                        "SELECT id, title, artists, album, trackhash, filepath, duration FROM track WHERE filepath LIKE ? LIMIT 1;",
                        (f"%{filename}",),
                    ).fetchone()

                if row:
                    track_data = dict(row)
                    try:
                        artists = json.loads(track_data["artists"]) if track_data["artists"] else []
                        artist_names = ", ".join(a.get("name", "") for a in artists if isinstance(a, dict))
                    except Exception:
                        artist_names = ""

                    thash = track_data.get("trackhash")
                    if thash:
                        matched_hashes.append(thash)

                    annotated_items.append({
                        **item,
                        "matched": True,
                        "track_id": track_data.get("id"),
                        "trackhash": thash,
                        "db_title": track_data.get("title"),
                        "db_artists": artist_names,
                        "db_album": track_data.get("album"),
                        "db_filepath": track_data.get("filepath"),
                        "db_duration": track_data.get("duration"),
                    })
                else:
                    annotated_items.append({
                        **item,
                        "matched": False,
                        "track_id": None,
                        "trackhash": None,
                    })

        return annotated_items, matched_hashes

    @classmethod
    def get_existing_swing_playlists(cls) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves all playlists currently registered in SwingMusic's userdata.db.
        """
        if not settings.userdata_db_path.exists():
            return {}

        playlists = {}
        with user_db() as conn:
            try:
                cursor = conn.execute("""
                    SELECT id, name, last_updated, image, trackhashes, settings
                    FROM playlist;
                """)
                for row in cursor.fetchall():
                    name = row["name"]
                    try:
                        hashes = json.loads(row["trackhashes"]) if row["trackhashes"] else []
                    except Exception:
                        hashes = []
                    playlists[name] = {
                        "id": row["id"],
                        "name": name,
                        "last_updated": row["last_updated"],
                        "track_count": len(hashes),
                        "trackhashes": hashes,
                    }
            except Exception as e:
                log.warning(f"Erro ao ler playlists do userdata.db: {e}")

        return playlists

    @classmethod
    def list_all_m3u_playlists(cls) -> List[Dict[str, Any]]:
        """
        Scans for all M3U files, parses them, matches them with tracks in swingmusic.db,
        and determines if they already exist as a playlist in SwingMusic.
        """
        m3u_files = cls.find_m3u_files()
        existing_playlists = cls.get_existing_swing_playlists()

        result = []
        for file_path in m3u_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                log.warning(f"Erro ao ler arquivo M3U {file_path}: {e}")
                continue

            parsed = cls.parse_m3u_lines(content, file_path.parent)
            annotated, matched_hashes = cls.match_tracks_in_db(parsed)

            playlist_name = file_path.stem
            is_created = playlist_name in existing_playlists

            result.append({
                "name": playlist_name,
                "filename": file_path.name,
                "filepath": str(file_path),
                "relative_path": str(file_path.relative_to(settings.MUSIC_DIR)) if str(file_path).startswith(str(settings.MUSIC_DIR)) else file_path.name,
                "total_tracks": len(parsed),
                "matched_tracks": len(matched_hashes),
                "match_rate": round((len(matched_hashes) / len(parsed) * 100), 1) if parsed else 0,
                "is_created_in_swing": is_created,
                "swing_playlist": existing_playlists.get(playlist_name),
            })

        return result

    @classmethod
    def get_m3u_detail(cls, m3u_path: str) -> Optional[Dict[str, Any]]:
        """
        Returns full detailed track breakdown for a specific M3U file.
        """
        p = Path(m3u_path)
        if not p.is_absolute() and settings.MUSIC_DIR.exists():
            p = settings.MUSIC_DIR / m3u_path

        if not p.exists():
            return None

        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return {"error": str(e)}

        parsed = cls.parse_m3u_lines(content, p.parent)
        annotated, matched_hashes = cls.match_tracks_in_db(parsed)
        existing = cls.get_existing_swing_playlists().get(p.stem)

        return {
            "name": p.stem,
            "filename": p.name,
            "filepath": str(p),
            "total_tracks": len(parsed),
            "matched_count": len(matched_hashes),
            "tracks": annotated,
            "is_created": existing is not None,
            "swing_playlist": existing,
        }

    @classmethod
    def create_or_sync_playlist(
        cls,
        m3u_path: str,
        custom_name: Optional[str] = None,
        userid: int = 1,
    ) -> Dict[str, Any]:
        """
        Creates or updates a playlist in SwingMusic's userdata.db using matched trackhashes from an M3U file.
        """
        p = Path(m3u_path)
        if not p.is_absolute() and settings.MUSIC_DIR.exists():
            p = settings.MUSIC_DIR / m3u_path

        if not p.exists():
            return {"success": False, "error": f"Arquivo M3U não encontrado: {m3u_path}"}

        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return {"success": False, "error": f"Erro ao ler M3U: {e}"}

        parsed = cls.parse_m3u_lines(content, p.parent)
        annotated, matched_hashes = cls.match_tracks_in_db(parsed)

        if not matched_hashes:
            return {
                "success": False,
                "error": "Nenhuma música deste arquivo M3U foi encontrada na biblioteca do SwingMusic.",
            }

        playlist_name = custom_name.strip() if custom_name else p.stem
        now = int(time.time())
        trackhashes_json = json.dumps(matched_hashes)
        settings_json = json.dumps({"has_image": False, "similar_artists": []})

        with user_db() as conn:
            # Check if playlist already exists by name
            existing = conn.execute(
                "SELECT id FROM playlist WHERE name = ?;",
                (playlist_name,),
            ).fetchone()

            if existing:
                playlist_id = existing["id"]
                conn.execute("""
                    UPDATE playlist
                    SET last_updated = ?, trackhashes = ?
                    WHERE id = ?;
                """, (now, trackhashes_json, playlist_id))
                action = "updated"
            else:
                cursor = conn.execute("""
                    INSERT INTO playlist (name, last_updated, image, userid, settings, trackhashes, extra)
                    VALUES (?, ?, NULL, ?, ?, ?, ?);
                """, (playlist_name, now, userid, settings_json, trackhashes_json, json.dumps({})))
                playlist_id = cursor.lastrowid
                action = "created"

            conn.commit()

        return {
            "success": True,
            "action": action,
            "playlist_id": playlist_id,
            "name": playlist_name,
            "total_tracks": len(parsed),
            "imported_tracks": len(matched_hashes),
        }
