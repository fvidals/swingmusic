import logging
from flask import Blueprint, jsonify, request

from config import settings
from database import user_db
from services.playlist_service import PlaylistService

log = logging.getLogger(__name__)
playlists_bp = Blueprint("playlists", __name__, url_prefix="/api/playlists")


@playlists_bp.route("", methods=["GET"])
def get_playlists():
    """
    Scans for .m3u playlists in MUSIC_DIR and returns their matching status in SwingMusic.
    """
    playlists = PlaylistService.list_all_m3u_playlists()
    return jsonify({
        "total": len(playlists),
        "playlists": playlists,
    })


@playlists_bp.route("/detail", methods=["GET"])
def get_playlist_detail():
    """
    Returns full track-by-track match analysis for a specific M3U file.
    """
    filepath = request.args.get("path", "").strip()
    if not filepath:
        return jsonify({"error": "Caminho do arquivo M3U não fornecido"}), 400

    detail = PlaylistService.get_m3u_detail(filepath)
    if not detail:
        return jsonify({"error": "Arquivo M3U não encontrado"}), 404

    return jsonify(detail)


@playlists_bp.route("/create", methods=["POST"])
def create_playlist():
    """
    Creates or updates a playlist in SwingMusic using matched trackhashes from an M3U file.
    """
    data = request.get_json() or {}
    m3u_path = data.get("filepath", "").strip()
    custom_name = data.get("name", "").strip()

    if not m3u_path:
        return jsonify({"error": "Caminho do arquivo M3U não fornecido"}), 400

    result = PlaylistService.create_or_sync_playlist(m3u_path, custom_name)
    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)


@playlists_bp.route("/<int:playlist_id>", methods=["DELETE"])
def delete_swing_playlist(playlist_id: int):
    """
    Removes a playlist from SwingMusic's database.
    """
    with user_db() as conn:
        conn.execute("DELETE FROM playlist WHERE id = ?;", (playlist_id,))
        conn.commit()
    return jsonify({"success": True})
