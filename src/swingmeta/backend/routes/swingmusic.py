import base64
import logging
from flask import Blueprint, abort, jsonify, request, send_from_directory

from config import settings
from services.swing_custom_service import SwingCustomService

log = logging.getLogger(__name__)
swingmusic_bp = Blueprint("swingmusic", __name__, url_prefix="/api/swingmusic")


@swingmusic_bp.route("/users", methods=["GET"])
def list_users():
    """
    Lists all users registered in SwingMusic.
    """
    users = SwingCustomService.get_all_users()
    return jsonify({
        "total": len(users),
        "users": users,
    })


from services.image_service import ImageService


@swingmusic_bp.route("/users/<int:user_id>/avatar", methods=["POST"])
def upload_user_avatar(user_id: int):
    """
    Uploads a new avatar image for a user (file, image_url, or image_base64).
    """
    file_obj = request.files.get("file") or request.files.get("image")
    image_url = None
    image_base64 = None

    if request.is_json:
        data = request.get_json() or {}
        image_url = data.get("image_url")
        image_base64 = data.get("image_base64")
    else:
        image_url = request.form.get("image_url")
        image_base64 = request.form.get("image_base64")

    image_bytes, err = ImageService.resolve_image_bytes(
        file_obj=file_obj,
        image_url=image_url,
        image_base64=image_base64,
    )
    if err or not image_bytes:
        return jsonify({"error": err or "Nenhum arquivo ou URL de imagem fornecida"}), 400

    result = SwingCustomService.update_user_avatar(user_id, image_bytes)
    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)



@swingmusic_bp.route("/users/<int:user_id>/avatar", methods=["DELETE"])
def delete_user_avatar(user_id: int):
    """
    Removes custom avatar for a user.
    """
    SwingCustomService.delete_user_avatar(user_id)
    return jsonify({"success": True})


@swingmusic_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    """
    Updates user info (username, roles, extra).
    """
    data = request.get_json() or {}
    username = data.get("username")
    roles = data.get("roles")
    extra = data.get("extra")

    result = SwingCustomService.update_user_profile(user_id, username, roles, extra)
    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)


@swingmusic_bp.route("/assets", methods=["GET"])
def list_assets():
    """
    Lists default fallback images in SwingMusic assets folder.
    """
    assets = SwingCustomService.get_fallback_assets()
    return jsonify({
        "total": len(assets),
        "assets": assets,
    })


@swingmusic_bp.route("/assets/<name>", methods=["GET"])
def serve_asset(name: str):
    """
    Serves a fallback asset image.
    """
    assets_dir = SwingCustomService.get_assets_dir()
    file_path = assets_dir / name
    if not file_path.exists():
        abort(404)

    return send_from_directory(str(assets_dir), name, max_age=3600)


@swingmusic_bp.route("/assets/<name>", methods=["POST"])
def upload_asset(name: str):
    """
    Replaces a default fallback asset in SwingMusic.
    """
    file_bytes = None

    if "file" in request.files:
        file_bytes = request.files["file"].read()
    elif request.is_json:
        data = request.get_json()
        b64_data = data.get("file_base64", "")
        if b64_data:
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            try:
                file_bytes = base64.b64decode(b64_data)
            except Exception as e:
                return jsonify({"error": f"Base64 inválido: {e}"}), 400

    if not file_bytes:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    result = SwingCustomService.update_fallback_asset(name, file_bytes)
    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)


@swingmusic_bp.route("/client", methods=["GET"])
def get_client_info():
    """
    Returns information about the extracted webclient directory.
    """
    info = SwingCustomService.get_client_info()
    return jsonify(info)


@swingmusic_bp.route("/client/patch", methods=["POST"])
def patch_client():
    """
    Applies the custom avatar patch to SwingMusic's client/index.html.
    """
    result = SwingCustomService.patch_client()
    if not result.get("success"):
        return jsonify(result), 400
    return jsonify(result)


@swingmusic_bp.route("/client/patch", methods=["DELETE"])
def unpatch_client():
    """
    Removes the custom avatar patch from SwingMusic's client/index.html.
    """
    result = SwingCustomService.unpatch_client()
    if not result.get("success"):
        return jsonify(result), 400
    return jsonify(result)

