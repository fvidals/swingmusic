import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4, MP4Tags
from mutagen.oggvorbis import OggVorbis

from config import settings
from database import swing_db
from services.hash_utils import create_hash

log = logging.getLogger(__name__)


class TagService:
    @staticmethod
    def read_audio_tags(filepath: str) -> Dict[str, Any]:
        """
        Reads metadata tags directly from the audio file using Mutagen.
        """
        p = Path(filepath)
        if not p.is_absolute() and settings.MUSIC_DIR.exists():
            p = settings.MUSIC_DIR / filepath

        if not p.exists():
            return {"error": f"Arquivo não encontrado: {filepath}"}

        tags: Dict[str, Any] = {
            "filepath": str(p),
            "filename": p.name,
            "format": p.suffix.lower().replace(".", ""),
            "title": "",
            "artist": "",
            "album": "",
            "albumartist": "",
            "year": "",
            "tracknumber": "",
            "discnumber": "",
            "genre": "",
        }

        try:
            audio = mutagen.File(p, easy=True)
            if audio is not None:
                tags["title"] = audio.get("title", [""])[0] if audio.get("title") else ""
                tags["artist"] = audio.get("artist", [""])[0] if audio.get("artist") else ""
                tags["album"] = audio.get("album", [""])[0] if audio.get("album") else ""
                tags["albumartist"] = audio.get("albumartist", [""])[0] if audio.get("albumartist") else ""
                tags["year"] = audio.get("date", [""])[0] if audio.get("date") else ""
                tags["tracknumber"] = audio.get("tracknumber", [""])[0] if audio.get("tracknumber") else ""
                tags["discnumber"] = audio.get("discnumber", [""])[0] if audio.get("discnumber") else ""
                tags["genre"] = audio.get("genre", [""])[0] if audio.get("genre") else ""
        except Exception as e:
            log.warning(f"Erro ao ler tags com mutagen de {p}: {e}")

        return tags

    @staticmethod
    def update_audio_tags(filepath: str, new_tags: Dict[str, Any]) -> Dict[str, Any]:
        """
        Writes updated tags directly to the audio file and updates swingmusic.db.
        """
        p = Path(filepath)
        if not p.is_absolute() and settings.MUSIC_DIR.exists():
            p = settings.MUSIC_DIR / filepath

        if not p.exists():
            return {"success": False, "error": f"Arquivo não encontrado: {filepath}"}

        try:
            # 1. Update file tags via Mutagen
            audio = mutagen.File(p, easy=True)
            if audio is None:
                # Try format specific
                ext = p.suffix.lower()
                if ext == ".mp3":
                    try:
                        audio = EasyID3(p)
                    except Exception:
                        audio = mutagen.File(p)
                        audio.add_tags()
                        audio = EasyID3(p)
                elif ext == ".flac":
                    audio = FLAC(p)
                elif ext in (".m4a", ".mp4"):
                    audio = MP4(p)
                elif ext in (".ogg", ".oga"):
                    audio = OggVorbis(p)

            if audio is not None:
                if "title" in new_tags and new_tags["title"] is not None:
                    audio["title"] = str(new_tags["title"])
                if "artist" in new_tags and new_tags["artist"] is not None:
                    audio["artist"] = str(new_tags["artist"])
                if "album" in new_tags and new_tags["album"] is not None:
                    audio["album"] = str(new_tags["album"])
                if "albumartist" in new_tags and new_tags["albumartist"] is not None:
                    audio["albumartist"] = str(new_tags["albumartist"])
                if "year" in new_tags and new_tags["year"] is not None:
                    audio["date"] = str(new_tags["year"])
                if "tracknumber" in new_tags and new_tags["tracknumber"] is not None:
                    audio["tracknumber"] = str(new_tags["tracknumber"])
                if "genre" in new_tags and new_tags["genre"] is not None:
                    audio["genre"] = str(new_tags["genre"])

                audio.save()

            # 2. Update swingmusic.db track row if exists
            if settings.swingmusic_db_path.exists():
                with swing_db() as conn:
                    # Construct artist JSON objects and hashes
                    title = new_tags.get("title")
                    artist_str = new_tags.get("artist")
                    album_str = new_tags.get("album")
                    albumartist_str = new_tags.get("albumartist") or artist_str

                    artists_list = []
                    if artist_str:
                        for a in artist_str.split(","):
                            aname = a.strip()
                            if aname:
                                artists_list.append({
                                    "name": aname,
                                    "artisthash": create_hash(aname, decode=True),
                                    "image": f"{create_hash(aname, decode=True)}.webp",
                                })

                    albumartists_list = []
                    if albumartist_str:
                        for a in albumartist_str.split(","):
                            aname = a.strip()
                            if aname:
                                albumartists_list.append({
                                    "name": aname,
                                    "artisthash": create_hash(aname, decode=True),
                                    "image": f"{create_hash(aname, decode=True)}.webp",
                                })

                    albumhash = create_hash(album_str, decode=True) if album_str else ""
                    last_mod = os.path.getmtime(p)

                    update_fields = ["last_mod = ?"]
                    params = [last_mod]

                    if title is not None:
                        update_fields.append("title = ?")
                        params.append(title)
                    if album_str is not None:
                        update_fields.append("album = ?")
                        params.append(album_str)
                        update_fields.append("albumhash = ?")
                        params.append(albumhash)
                    if artists_list:
                        update_fields.append("artists = ?")
                        params.append(json.dumps(artists_list))
                    if albumartists_list:
                        update_fields.append("albumartists = ?")
                        params.append(json.dumps(albumartists_list))
                    if "year" in new_tags and new_tags["year"]:
                        try:
                            year_int = int(str(new_tags["year"])[:4])
                            update_fields.append("date = ?")
                            params.append(year_int)
                        except Exception:
                            pass

                    params.append(str(filepath))
                    query = f"UPDATE track SET {', '.join(update_fields)} WHERE filepath = ?;"
                    conn.execute(query, params)
                    conn.commit()

            return {"success": True, "filepath": str(filepath)}

        except Exception as e:
            log.error(f"Erro ao salvar tags para {filepath}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @classmethod
    def batch_update_tags(cls, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Applies batch tag updates to multiple files.
        """
        results = []
        success_count = 0
        for item in updates:
            fpath = item.get("filepath")
            tags = item.get("tags", {})
            if fpath and tags:
                res = cls.update_audio_tags(fpath, tags)
                results.append(res)
                if res.get("success"):
                    success_count += 1

        return {
            "total": len(updates),
            "success_count": success_count,
            "results": results,
        }
