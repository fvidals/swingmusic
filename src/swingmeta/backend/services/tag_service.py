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
                    if artist_str is not None:
                        update_fields.append("artists = ?")
                        params.append(artist_str)
                    if albumartist_str is not None:
                        update_fields.append("albumartists = ?")
                        params.append(albumartist_str)
                    if "year" in new_tags and new_tags["year"]:
                        try:
                            year_int = int(str(new_tags["year"])[:4])
                            update_fields.append("date = ?")
                            params.append(year_int)
                        except Exception:
                            pass

                    if "genre" in new_tags and new_tags["genre"] is not None:
                        genre_val = str(new_tags["genre"]).strip()
                        update_fields.append("genres = ?")
                        params.append(genre_val)

                    if "tracknumber" in new_tags and new_tags["tracknumber"]:
                        try:
                            t_num = int(str(new_tags["tracknumber"]).split("/")[0].strip())
                            update_fields.append("track = ?")
                            params.append(t_num)
                        except Exception:
                            pass

                    if "discnumber" in new_tags and new_tags["discnumber"]:
                        try:
                            d_num = int(str(new_tags["discnumber"]).split("/")[0].strip())
                            update_fields.append("disc = ?")
                            params.append(d_num)
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

    @staticmethod
    def embed_cover_in_audio_file(filepath: str, image_bytes: bytes) -> bool:
        """
        Embeds cover artwork directly into the physical audio file (MP3 ID3 APIC, FLAC, M4A, etc.).
        """
        p = Path(filepath)
        if not p.is_absolute() and settings.MUSIC_DIR.exists():
            p = settings.MUSIC_DIR / filepath

        if not p.exists():
            return False

        try:
            import io
            from PIL import Image

            # Prepare JPEG image for broad audio player compatibility
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Crop to 1:1 square
            width, height = img.size
            if width != height:
                min_dim = min(width, height)
                left = (width - min_dim) // 2
                top = (height - min_dim) // 2
                img = img.crop((left, top, left + min_dim, top + min_dim))

            # Resize if larger than 1200x1200 for embedded tag performance
            if img.width > 1200:
                img = img.resize((1200, 1200), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            jpeg_data = buf.getvalue()

            ext = p.suffix.lower()
            if ext == ".mp3":
                from mutagen.id3 import ID3, APIC, error
                try:
                    tags = ID3(p)
                except error:
                    tags = ID3()
                tags.delall("APIC")
                tags.add(APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,  # Front cover
                    desc="Cover",
                    data=jpeg_data,
                ))
                tags.save(p, v2_version=3)
                return True

            elif ext == ".flac":
                from mutagen.flac import FLAC, Picture
                audio = FLAC(p)
                pic = Picture()
                pic.type = 3
                pic.mime = "image/jpeg"
                pic.desc = "Cover"
                pic.data = jpeg_data
                audio.clear_pictures()
                audio.add_picture(pic)
                audio.save()
                return True

            elif ext in (".m4a", ".mp4"):
                from mutagen.mp4 import MP4, MP4Cover
                audio = MP4(p)
                audio["covr"] = [MP4Cover(jpeg_data, imageformat=MP4Cover.FORMAT_JPEG)]
                audio.save()
                return True

            elif ext in (".ogg", ".oga"):
                import base64
                from mutagen.flac import Picture
                from mutagen.oggvorbis import OggVorbis
                audio = OggVorbis(p)
                pic = Picture()
                pic.type = 3
                pic.mime = "image/jpeg"
                pic.desc = "Cover"
                pic.data = jpeg_data
                encoded = base64.b64encode(pic.write()).decode("ascii")
                audio["metadata_block_picture"] = [encoded]
                audio.save()
                return True

        except Exception as e:
            log.warning(f"Erro ao embutir capa no arquivo de áudio {filepath}: {e}")
            return False

        return False

    @classmethod
    def embed_cover_for_album(cls, albumhash: str, image_bytes: bytes) -> int:
        """
        Embeds cover artwork into all tracks belonging to the given albumhash in swingmusic.db.
        Returns the number of files successfully updated.
        """
        updated = 0
        if settings.swingmusic_db_path.exists():
            try:
                with swing_db() as conn:
                    rows = conn.execute("SELECT filepath FROM track WHERE albumhash = ?;", (albumhash,)).fetchall()
                    for r in rows:
                        fpath = r["filepath"]
                        if fpath and cls.embed_cover_in_audio_file(fpath, image_bytes):
                            updated += 1
            except Exception as e:
                log.warning(f"Erro ao embutir capa nas faixas do álbum {albumhash}: {e}")
        return updated

    @classmethod
    def embed_cover_for_tracks(cls, track_ids: List[int], image_bytes: bytes, embed_audio: bool = True) -> Dict[str, Any]:
        """
        Embeds cover artwork into the given list of track IDs and updates album thumbnails.
        """
        from services.image_service import ImageService
        if not track_ids:
            return {"success": False, "error": "Nenhuma faixa informada"}

        updated_files = 0
        albumhashes = set()
        
        with swing_db() as conn:
            placeholders = ",".join("?" for _ in track_ids)
            rows = conn.execute(
                f"SELECT id, filepath, albumhash FROM track WHERE id IN ({placeholders});",
                track_ids,
            ).fetchall()

            for r in rows:
                ahash = r["albumhash"]
                if ahash:
                    albumhashes.add(ahash)
                fpath = r["filepath"]
                if embed_audio and fpath:
                    if cls.embed_cover_in_audio_file(fpath, image_bytes):
                        updated_files += 1

        # Process and save album thumbnails for all distinct albumhashes
        updated_albums = 0
        for ahash in albumhashes:
            try:
                ImageService.process_and_save_album_cover(image_bytes, ahash)
                updated_albums += 1
            except Exception as e:
                log.warning(f"Erro ao salvar miniatura do álbum {ahash}: {e}")

        return {
            "success": True,
            "total_tracks": len(rows),
            "updated_files": updated_files,
            "updated_albums": updated_albums,
            "albumhashes": list(albumhashes),
        }


