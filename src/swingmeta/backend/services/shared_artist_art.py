import io
import logging
import re
from typing import Any, Dict, List, Optional

from PIL import Image

from config import settings

log = logging.getLogger(__name__)

_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


class SharedArtistArtService:
    """
    Maintains a flat, SwingMeta-owned directory of full-quality artist photos
    named `{ArtistName}.jpg`, for any third-party media server to mount
    read-only and consume as its own artist image source (e.g. Navidrome's
    ArtistImageFolder, which matches files by artist name or MusicBrainz ID).
    Always writes to the fixed path settings.shared_artist_art_dir
    (/shared/artist-art); mount that path as a volume to actually share it.
    """

    @staticmethod
    def _filename_for(artist_name: str) -> str:
        safe_name = _INVALID_FILENAME_CHARS.sub("_", artist_name).strip()
        return f"{safe_name}.jpg"

    @classmethod
    def save(cls, artist_name: str, image_bytes: bytes) -> Optional[str]:
        """
        Saves the given image bytes as a full-quality JPEG named after the
        artist, without downscaling, so the shared folder always holds the
        best quality available at upload time. Returns the saved filename,
        or None on failure.
        """
        target_dir = settings.shared_artist_art_dir
        if not artist_name:
            return None

        try:
            img = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            log.warning(f"Não foi possível decodificar imagem para espelhar '{artist_name}': {e}")
            return None

        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            bg.paste(img, (0, 0), img.convert("RGBA"))
            img = bg.convert("RGB")
        else:
            img = img.convert("RGB")

        # Center square crop, preserving the original resolution (no resize).
        width, height = img.size
        if width != height:
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            top = (height - min_dim) // 2
            img = img.crop((left, top, left + min_dim, top + min_dim))

        filename = cls._filename_for(artist_name)
        try:
            img.save(target_dir / filename, format="jpeg", quality=95)
        except Exception as e:
            log.error(f"Erro ao salvar arte compartilhada de '{artist_name}': {e}")
            return None

        return filename

    @classmethod
    def export_existing_artists(cls, artists: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk-exports the artist photos already stored by SwingMusic (the
        500x500 WebP in artist_images_lg, the best quality currently
        retained for those) into the shared directory as JPEG. Used by the
        "export existing art" action for artists uploaded before this
        feature existed.
        """
        exported = 0
        skipped = 0
        failed = 0

        for artist in artists:
            if not artist.get("has_image"):
                skipped += 1
                continue

            src_path = settings.artist_images_lg / f"{artist['artisthash']}.webp"
            if not src_path.exists():
                skipped += 1
                continue

            try:
                image_bytes = src_path.read_bytes()
            except Exception as e:
                log.warning(f"Erro ao ler '{src_path}': {e}")
                failed += 1
                continue

            if cls.save(artist["name"], image_bytes):
                exported += 1
            else:
                failed += 1

        return {
            "success": True,
            "exported": exported,
            "skipped": skipped,
            "failed": failed,
            "total": len(artists),
        }

    @classmethod
    def delete(cls, artist_name: str) -> None:
        if not artist_name:
            return

        file_path = settings.shared_artist_art_dir / cls._filename_for(artist_name)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                log.error(f"Erro ao remover arte compartilhada de '{artist_name}': {e}")
