import os
from flask import Blueprint, jsonify, request

from config import settings
from database import swing_db, user_db
from services.online_search import OnlineSearchService, _spotify_token

system_bp = Blueprint("system", __name__, url_prefix="/api/system")


@system_bp.route("/status", methods=["GET"])
def get_system_status():
    """
    Returns the status of volume mounts, databases, and general statistics.
    """
    swing_db_ok = settings.swingmusic_db_path.exists()
    user_db_ok = settings.userdata_db_path.exists()
    images_ok = settings.images_dir.exists()
    music_ok = settings.MUSIC_DIR.exists()

    track_count = 0
    if swing_db_ok:
        try:
            with swing_db() as conn:
                row = conn.execute("SELECT COUNT(*) as count FROM track;").fetchone()
                if row:
                    track_count = row["count"]
        except Exception:
            pass

    artist_image_count = 0
    if settings.artist_images_lg.exists():
        try:
            artist_image_count = len(list(settings.artist_images_lg.glob("*.webp")))
        except Exception:
            pass

    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "paths": {
            "config_dir": str(settings.resolved_config_dir),
            "swingmusic_db": str(settings.swingmusic_db_path),
            "userdata_db": str(settings.userdata_db_path),
            "images_dir": str(settings.images_dir),
            "music_dir": str(settings.MUSIC_DIR),
        },
        "mounts": {
            "swingmusic_db_exists": swing_db_ok,
            "userdata_db_exists": user_db_ok,
            "images_dir_exists": images_ok,
            "music_dir_exists": music_ok,
        },
        "stats": {
            "track_count": track_count,
            "artist_image_count": artist_image_count,
        },
        "spotify": {
            "configured": bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET),
            "client_id": settings.SPOTIFY_CLIENT_ID[:6] + "..." if settings.SPOTIFY_CLIENT_ID else "",
        },
    })


@system_bp.route("/spotify-config", methods=["POST"])
def update_spotify_config():
    """
    Updates Spotify API credentials in runtime.
    """
    global _spotify_token
    data = request.get_json() or {}
    client_id = data.get("client_id", "").strip()
    client_secret = data.get("client_secret", "").strip()

    settings.SPOTIFY_CLIENT_ID = client_id
    settings.SPOTIFY_CLIENT_SECRET = client_secret
    _spotify_token = None

    # Test credentials
    token = OnlineSearchService.get_spotify_token()
    if client_id and not token:
        return jsonify({
            "success": False,
            "error": "Falha na autenticação com Spotify. Verifique seu Client ID e Client Secret.",
        }), 400

    return jsonify({
        "success": True,
        "configured": bool(token),
        "message": "Credenciais do Spotify atualizadas com sucesso!",
    })
