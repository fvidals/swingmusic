import io
import json
import logging
from pathlib import Path
from typing import Any, Tuple

from PIL import Image

from config import settings
from database import user_db

log = logging.getLogger(__name__)

# Attempt to import optional colorgram and blurhash
try:
    import colorgram
except ImportError:
    colorgram = None

try:
    import blurhash
except ImportError:
    blurhash = None


def extract_dominant_colors(image_path: Path, count: int = 2) -> list[str]:
    """
    Extracts the dominant RGB colors from an image.
    Returns list of 'rgb(r, g, b)'.
    """
    if not image_path.exists():
        return []

    if colorgram is not None:
        try:
            colors = sorted(colorgram.extract(str(image_path), count), key=lambda c: c.hsl.h)
            return [f"rgb({c.rgb.r}, {c.rgb.g}, {c.rgb.b})" for c in colors]
        except Exception as e:
            log.warning(f"Error extracting colorgram colors: {e}")

    # Fallback to PIL palette / average color
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB").resize((50, 50))
            pixels = list(img.getdata())
            avg_r = sum(p[0] for p in pixels) // len(pixels)
            avg_g = sum(p[1] for p in pixels) // len(pixels)
            avg_b = sum(p[2] for p in pixels) // len(pixels)
            return [f"rgb({avg_r}, {avg_g}, {avg_b})"]
    except Exception as e:
        log.warning(f"Fallback color extraction failed: {e}")
        return []


def calculate_blurhash(image_path: Path) -> str | None:
    """
    Calculates blurhash for the given image.
    """
    if not image_path.exists() or blurhash is None:
        return None

    try:
        with Image.open(image_path) as img:
            img_copy = img.convert("RGB")
            img_copy.thumbnail((100, 100))
            return blurhash.encode(img_copy, x_components=4, y_components=4)
    except Exception as e:
        log.warning(f"Error computing blurhash: {e}")
        return None


class ImageService:
    @staticmethod
    def process_and_save_artist_image(image_bytes: bytes, artisthash: str) -> dict[str, Any]:
        """
        Receives raw image bytes, crops to square if needed, resizes into:
        - large: 500x500
        - medium: 256x256
        - small: 128x128
        and saves as {artisthash}.webp.
        Also calculates dominant colors and updates userdata.db.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Formato de imagem inválido: {e}")

        # Convert to RGB (handles RGBA / P / CMYK)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            # Create white or transparent background
            bg = Image.new("RGBA", img.size, (255, 255, 255, 0))
            bg.paste(img, (0, 0), img.convert("RGBA"))
            img = bg
        else:
            img = img.convert("RGB")

        # Crop to center square if aspect ratio is not 1:1
        width, height = img.size
        if width != height:
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            top = (height - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim
            img = img.crop((left, top, right, bottom))

        filename = f"{artisthash}.webp"
        lg_path = settings.artist_images_lg / filename
        md_path = settings.artist_images_md / filename
        sm_path = settings.artist_images_sm / filename

        # Large (max 500x500 or original if smaller)
        lg_size = min(500, img.width)
        img_lg = img.resize((lg_size, lg_size), Image.Resampling.LANCZOS)
        img_lg.save(lg_path, format="webp", quality=90)

        # Medium (256x256)
        img_md = img.resize((256, 256), Image.Resampling.LANCZOS)
        img_md.save(md_path, format="webp", quality=85)

        # Small (128x128)
        img_sm = img.resize((128, 128), Image.Resampling.LANCZOS)
        img_sm.save(sm_path, format="webp", quality=80)

        # Extract colors and blurhash from small image
        colors = extract_dominant_colors(sm_path, count=2)
        bhash = calculate_blurhash(sm_path)
        color_json = json.dumps(colors) if colors else json.dumps(["rgb(30, 30, 30)"])

        # Update userdata.db artistdata
        itemhash = f"artist{artisthash}"
        with user_db() as conn:
            # Check if row exists
            row = conn.execute(
                "SELECT id, extra FROM artistdata WHERE itemhash = ?;",
                (itemhash,),
            ).fetchone()

            if row:
                extra_data = json.loads(row["extra"]) if row["extra"] else {}
                if bhash:
                    extra_data["blurhash"] = bhash
                conn.execute(
                    """
                    UPDATE artistdata
                    SET color = ?, extra = ?
                    WHERE itemhash = ?;
                    """,
                    (color_json, json.dumps(extra_data), itemhash),
                )
            else:
                extra_data = {"blurhash": bhash} if bhash else {}
                conn.execute(
                    """
                    INSERT INTO artistdata (itemhash, itemtype, color, bio, info, extra)
                    VALUES (?, 'artist', ?, NULL, NULL, ?);
                    """,
                    (itemhash, color_json, json.dumps(extra_data)),
                )
            conn.commit()

        return {
            "success": True,
            "artisthash": artisthash,
            "colors": colors,
            "blurhash": bhash,
            "images": {
                "large": f"/api/images/artist/large/{filename}",
                "medium": f"/api/images/artist/medium/{filename}",
                "small": f"/api/images/artist/small/{filename}",
            },
        }

    @staticmethod
    def delete_artist_image(artisthash: str) -> bool:
        """
        Removes custom artist image files and resets colors in database.
        """
        filename = f"{artisthash}.webp"
        for folder in [
            settings.artist_images_lg,
            settings.artist_images_md,
            settings.artist_images_sm,
        ]:
            file_path = folder / filename
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    log.error(f"Erro ao remover {file_path}: {e}")

        # Reset in database
        itemhash = f"artist{artisthash}"
        with user_db() as conn:
            conn.execute(
                "UPDATE artistdata SET color = NULL WHERE itemhash = ?;",
                (itemhash,),
            )
            conn.commit()

        return True

    @staticmethod
    def get_artist_image_path(size: str, filename: str) -> Path | None:
        """
        Returns Path to the artist image if it exists.
        """
        if size == "small":
            p = settings.artist_images_sm / filename
        elif size == "medium":
            p = settings.artist_images_md / filename
        else:
            p = settings.artist_images_lg / filename

        if p.exists():
            return p
        return None
