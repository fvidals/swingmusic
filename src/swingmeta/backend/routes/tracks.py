import io
import json
import logging
from flask import Blueprint, jsonify, request
import requests

from config import settings
from database import swing_db
from services.artist_service import ArtistService
from services.image_service import ImageService
from services.online_search import OnlineSearchService
from services.tag_service import TagService

log = logging.getLogger(__name__)
tracks_bp = Blueprint("tracks", __name__, url_prefix="/api/tracks")


def check_album_has_cover(albumhash: str) -> bool:
    """
    Checks if a thumbnail exists for an albumhash in thumbnails folders.
    """
    if not albumhash:
        return False
    filename = f"{albumhash}.webp"
    return (
        (settings.thumb_images_md / filename).exists()
        or (settings.thumb_images_sm / filename).exists()
        or (settings.thumb_images_lg / filename).exists()
        or (settings.thumb_images_orig / filename).exists()
    )


@tracks_bp.route("", methods=["GET"])
def get_tracks():
    """
    List tracks with search, cover filter, and pagination.
    """
    if not settings.swingmusic_db_path.exists():
        return jsonify({
            "total": 0,
            "tracks": [],
            "page": 1,
            "total_pages": 0,
            "counts": {"total": 0, "has_cover": 0, "no_cover": 0},
        })

    search = request.args.get("q", "").strip().lower()
    artist_hash = request.args.get("artisthash", "").strip()
    album_hash = request.args.get("albumhash", "").strip()
    cover_filter = request.args.get("filter", "all").strip().lower()  # all, no_cover, has_cover
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))

    query = "SELECT id, title, artists, albumartists, album, albumhash, duration, track, disc, date, genres, bitrate, filepath, last_mod FROM track WHERE 1=1"
    params = []

    if artist_hash:
        all_artists = ArtistService.get_all_artists()
        target_artist = next((a for a in all_artists if a["artisthash"] == artist_hash), None)
        if target_artist:
            query += " AND (artists LIKE ? OR albumartists LIKE ?)"
            params.extend([f"%{target_artist['name']}%", f"%{target_artist['name']}%"])
        else:
            query += " AND (artists LIKE ? OR albumartists LIKE ?)"
            params.extend([f"%{artist_hash}%", f"%{artist_hash}%"])

    if album_hash:
        query += " AND albumhash = ?"
        params.append(album_hash)

    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(album) LIKE ? OR LOWER(artists) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY album ASC, disc ASC, track ASC;"

    with swing_db() as conn:
        cursor = conn.execute(query, params)
        all_matched_tracks = []
        count_has_cover = 0
        count_no_cover = 0

        for row in cursor.fetchall():
            t = dict(row)
            try:
                t["artists"] = json.loads(t["artists"]) if t["artists"] and t["artists"].startswith("[") else t["artists"]
            except Exception:
                pass
            try:
                t["albumartists"] = json.loads(t["albumartists"]) if t["albumartists"] and t["albumartists"].startswith("[") else t["albumartists"]
            except Exception:
                pass

            ahash = t.get("albumhash") or ""
            has_cover = check_album_has_cover(ahash)
            t["has_cover"] = has_cover
            t["cover_url"] = f"/api/images/thumbnail/medium/{ahash}.webp" if has_cover else None
            t["cover_url_lg"] = f"/api/images/thumbnail/large/{ahash}.webp" if has_cover else None

            if has_cover:
                count_has_cover += 1
            else:
                count_no_cover += 1

            # Apply cover filter
            if cover_filter == "no_cover" and has_cover:
                continue
            if cover_filter == "has_cover" and not has_cover:
                continue

            all_matched_tracks.append(t)

        total_filtered = len(all_matched_tracks)
        total_pages = (total_filtered + limit - 1) // limit if limit > 0 else 1
        offset = (page - 1) * limit
        paginated_tracks = all_matched_tracks[offset : offset + limit]

    return jsonify({
        "total": total_filtered,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "counts": {
            "total": count_has_cover + count_no_cover,
            "has_cover": count_has_cover,
            "no_cover": count_no_cover,
        },
        "tracks": paginated_tracks,
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

    ahash = track.get("albumhash") or ""
    has_cover = check_album_has_cover(ahash)
    track["has_cover"] = has_cover
    track["cover_url"] = f"/api/images/thumbnail/medium/{ahash}.webp" if has_cover else None

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


@tracks_bp.route("/search-covers", methods=["GET"])
def search_covers():
    """
    Searches Deezer, iTunes, and Spotify for high-resolution album covers.
    """
    album = request.args.get("album", "").strip()
    artist = request.args.get("artist", "").strip()
    if not album and not artist:
        return jsonify({"covers": []})

    result = OnlineSearchService.search_all_album_covers(album, artist)
    return jsonify(result)


@tracks_bp.route("/<int:track_id>/cover/upload", methods=["POST"])
def upload_track_cover(track_id: int):
    """
    Upload manual cover for a specific track (and its album).
    """
    if "image" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Arquivo vazio"}), 400

    with swing_db() as conn:
        row = conn.execute("SELECT albumhash, album, filepath FROM track WHERE id = ?;", (track_id,)).fetchone()
        if not row:
            return jsonify({"error": "Faixa não encontrada"}), 404
        albumhash = row["albumhash"]

    if not albumhash:
        return jsonify({"error": "A faixa não possui albumhash associado"}), 400

    image_bytes = file.read()
    try:
        res = ImageService.process_and_save_album_cover(image_bytes, albumhash)
        return jsonify(res)
    except Exception as e:
        log.error(f"Erro ao salvar capa do álbum {albumhash}: {e}")
        return jsonify({"error": str(e)}), 500


@tracks_bp.route("/<int:track_id>/cover/online", methods=["POST"])
def apply_track_online_cover(track_id: int):
    """
    Applies an online cover URL (from Deezer, Spotify, iTunes) to a track's album.
    """
    data = request.get_json() or {}
    image_url = data.get("image_url", "").strip()
    if not image_url:
        return jsonify({"error": "image_url é obrigatório"}), 400

    with swing_db() as conn:
        row = conn.execute("SELECT albumhash, album, filepath FROM track WHERE id = ?;", (track_id,)).fetchone()
        if not row:
            return jsonify({"error": "Faixa não encontrada"}), 404
        albumhash = row["albumhash"]

    if not albumhash:
        return jsonify({"error": "A faixa não possui albumhash associado"}), 400

    try:
        resp = requests.get(image_url, timeout=15, headers={"User-Agent": "SwingMeta/1.0"})
        if resp.status_code != 200:
            return jsonify({"error": f"Falha ao baixar imagem: HTTP {resp.status_code}"}), 400

        res = ImageService.process_and_save_album_cover(resp.content, albumhash)
        return jsonify(res)
    except Exception as e:
        log.error(f"Erro ao aplicar capa online: {e}")
        return jsonify({"error": str(e)}), 500


@tracks_bp.route("/album/<albumhash>/cover/upload", methods=["POST"])
def upload_album_cover(albumhash: str):
    """
    Upload manual cover for an album by albumhash.
    """
    if "image" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Arquivo vazio"}), 400

    image_bytes = file.read()
    try:
        res = ImageService.process_and_save_album_cover(image_bytes, albumhash)
        return jsonify(res)
    except Exception as e:
        log.error(f"Erro ao salvar capa do álbum {albumhash}: {e}")
        return jsonify({"error": str(e)}), 500


@tracks_bp.route("/album/<albumhash>/cover/online", methods=["POST"])
def apply_album_online_cover(albumhash: str):
    """
    Applies an online cover URL to an album by albumhash.
    """
    data = request.get_json() or {}
    image_url = data.get("image_url", "").strip()
    if not image_url:
        return jsonify({"error": "image_url é obrigatório"}), 400

    try:
        resp = requests.get(image_url, timeout=15, headers={"User-Agent": "SwingMeta/1.0"})
        if resp.status_code != 200:
            return jsonify({"error": f"Falha ao baixar imagem: HTTP {resp.status_code}"}), 400

        res = ImageService.process_and_save_album_cover(resp.content, albumhash)
        return jsonify(res)
    except Exception as e:
        log.error(f"Erro ao aplicar capa online: {e}")
        return jsonify({"error": str(e)}), 500
