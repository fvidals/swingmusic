import os
from flask import Blueprint, abort, send_from_directory

from config import settings

images_bp = Blueprint("images", __name__, url_prefix="/api/images")


@images_bp.route("/artist/<size>/<filename>", methods=["GET"])
@images_bp.route("/artist/<filename>", methods=["GET"])
def serve_artist_image(filename: str, size: str = "large"):
    """
    Serves artist image in requested size (small, medium, large).
    """
    if size == "small":
        folder = settings.artist_images_sm
    elif size == "medium":
        folder = settings.artist_images_md
    else:
        folder = settings.artist_images_lg

    file_path = folder / filename
    if not file_path.exists():
        abort(404)

    return send_from_directory(str(folder), filename, max_age=86400)


@images_bp.route("/thumbnail/<size>/<filename>", methods=["GET"])
@images_bp.route("/thumbnail/<filename>", methods=["GET"])
def serve_thumbnail(filename: str, size: str = "medium"):
    """
    Serves album cover / track thumbnail image.
    """
    folder = settings.thumbnails_dir / size
    if not folder.exists():
        folder = settings.thumbnails_dir / "medium"

    file_path = folder / filename
    if not file_path.exists():
        abort(404)

    return send_from_directory(str(folder), filename, max_age=86400)


@images_bp.route("/user/<filename>", methods=["GET"])
def serve_user_image(filename: str):
    """
    Serves custom user avatar image.
    """
    folder = settings.images_dir / "users"
    file_path = folder / filename
    if not file_path.exists():
        abort(404)

    return send_from_directory(str(folder), filename, max_age=3600)

