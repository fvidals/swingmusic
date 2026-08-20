import json
import logging
from flask import Blueprint, jsonify, request

from config import settings
from database import swing_db
from services.tag_service import TagService

log = logging.getLogger(__name__)
tracks_bp = Blueprint("tracks", __name__, url_prefix="/api/tracks")


@tracks_bp.route("", methods=["GET"])
def get_tracks():
    """
    List tracks with search and pagination.
    """
    if not settings.swingmusic_db_path.exists():
        return jsonify({"total": 0, "tracks": [], "page": 1, "total_pages": 0})

    search = request.args.get("q", "").strip().lower()
    artist_hash = request.args.get("artisthash", "").strip()
    album_hash = request.args.get("albumhash", "").strip()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))

    query = "SELECT id, title, artists, albumartists, album, albumhash, duration, track, disc, date, genres, bitrate, filepath, last_mod FROM track WHERE 1=1"
    params = []

    if artist_hash:
        query += " AND (artists LIKE ? OR albumartists LIKE ?)"
        params.extend([f"%{artist_hash}%", f"%{artist_hash}%"])

    if album_hash:
        query += " AND albumhash = ?"
        params.append(album_hash)

    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(album) LIKE ? OR LOWER(artists) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    with swing_db() as conn:
        # Count total
        count_query = f"SELECT COUNT(*) as total FROM ({query})"
        total = conn.execute(count_query, params).fetchone()["total"]

        # Fetch page
        query += " ORDER BY album ASC, disc ASC, track ASC LIMIT ? OFFSET ?;"
        offset = (page - 1) * limit
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        tracks = []
        for row in cursor.fetchall():
            t = dict(row)
            try:
                t["artists"] = json.loads(t["artists"]) if t["artists"] else []
            except Exception:
                pass
            try:
                t["albumartists"] = json.loads(t["albumartists"]) if t["albumartists"] else []
            except Exception:
                pass
            tracks.append(t)

    return jsonify({
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
        "tracks": tracks,
    })


@tracks_bp.route("/<int:track_id>", methods=["GET"])
def get_track_detail(track_id: int):
    """
    Get detailed track info from database and directly from audio file tags.
    """
    with swing_db() as conn:
        row = conn.execute("SELECT * FROM track WHERE id = ?;", (track_id,)).fetchone()
        if not row:
            return jsonify({"error": "Faixa não encontrada"}), 404
        track = dict(row)

    file_tags = TagService.read_audio_tags(track["filepath"])
    return jsonify({
        "database": track,
        "file_tags": file_tags,
    })


@tracks_bp.route("/<int:track_id>/tags", methods=["PUT"])
def update_track_tags(track_id: int):
    """
    Writes updated tags directly to the audio file and updates SQLite.
    """
    with swing_db() as conn:
        row = conn.execute("SELECT filepath FROM track WHERE id = ?;", (track_id,)).fetchone()
        if not row:
            return jsonify({"error": "Faixa não encontrada"}), 404
        filepath = row["filepath"]

    data = request.get_json() or {}
    result = TagService.update_audio_tags(filepath, data)
    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)


@tracks_bp.route("/batch-tags", methods=["POST"])
def batch_update_tags():
    """
    Batch updates tags across multiple files.
    """
    data = request.get_json() or {}
    updates = data.get("updates", [])
    result = TagService.batch_update_tags(updates)
    return jsonify(result)
