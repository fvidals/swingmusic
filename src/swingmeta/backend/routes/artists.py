import logging
import requests
from flask import Blueprint, jsonify, request

from services.artist_service import ArtistService
from services.image_service import ImageService
from services.online_search import OnlineSearchService

log = logging.getLogger(__name__)
artists_bp = Blueprint("artists", __name__, url_prefix="/api/artists")


@artists_bp.route("", methods=["GET"])
def get_artists():
    """
    List artists with filtering, search, and pagination.
    """
    search = request.args.get("q", "").strip().lower()
    filter_by = request.args.get("filter", "all")  # all, missing_image, has_image, missing_bio
    sort_by = request.args.get("sort", "name")  # name, track_count, album_count
    sort_order = request.args.get("order", "asc")  # asc, desc
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 40))

    all_artists = ArtistService.get_all_artists()

    # Search filter
    if search:
        all_artists = [a for a in all_artists if search in a["name"].lower()]

    # Status filter
    if filter_by == "missing_image":
        all_artists = [a for a in all_artists if not a["has_image"]]
    elif filter_by == "has_image":
        all_artists = [a for a in all_artists if a["has_image"]]
    elif filter_by == "missing_bio":
        all_artists = [a for a in all_artists if not a["has_bio"]]

    # Sorting
    reverse = sort_order.lower() == "desc"
    if sort_by in ("track_count", "album_count", "duration"):
        all_artists.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
    else:
        all_artists.sort(key=lambda x: x["name"].lower(), reverse=reverse)

    total = len(all_artists)
    start = (page - 1) * limit
    end = start + limit
    paginated = all_artists[start:end]

    return jsonify({
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
        "artists": paginated,
    })


@artists_bp.route("/<artisthash>", methods=["GET"])
def get_artist(artisthash: str):
    """
    Get detailed information about an artist.
    """
    artist = ArtistService.get_artist_by_hash(artisthash)
    if not artist:
        return jsonify({"error": "Artista não encontrado"}), 404
    return jsonify(artist)


@artists_bp.route("/<artisthash>/image", methods=["POST"])
def upload_artist_image(artisthash: str):
    """
    Upload a new image for the artist (via multipart form-data or JSON with image_url).
    """
    image_bytes = None

    # Check for direct file upload
    if "file" in request.files:
        file = request.files["file"]
        if file.filename:
            image_bytes = file.read()

    # Check for image_url in JSON body
    if image_bytes is None and request.is_json:
        data = request.get_json() or {}
        img_url = data.get("image_url")
        if img_url:
            try:
                res = requests.get(img_url, timeout=15, headers={"User-Agent": "SwingMeta/1.0"})
                if res.status_code == 200:
                    image_bytes = res.content
                else:
                    return jsonify({"error": f"Falha ao baixar imagem: HTTP {res.status_code}"}), 400
            except Exception as e:
                return jsonify({"error": f"Erro ao acessar URL da imagem: {e}"}), 400

    if not image_bytes:
        return jsonify({"error": "Nenhum arquivo ou URL de imagem fornecida"}), 400

    try:
        result = ImageService.process_and_save_artist_image(image_bytes, artisthash)
        return jsonify(result)
    except Exception as e:
        log.error(f"Erro ao processar imagem de {artisthash}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@artists_bp.route("/<artisthash>/image", methods=["DELETE"])
def delete_artist_image(artisthash: str):
    """
    Deletes the artist's custom image files.
    """
    success = ImageService.delete_artist_image(artisthash)
    return jsonify({"success": success})


@artists_bp.route("/<artisthash>/search-online", methods=["GET", "POST"])
def search_online(artisthash: str):
    """
    Searches Deezer, iTunes, MusicBrainz, and Spotify for photos and bio info.
    """
    name = request.args.get("name")
    if not name:
        artist = ArtistService.get_artist_by_hash(artisthash)
        if artist:
            name = artist.get("name")

    if not name:
        return jsonify({"error": "Nome do artista não informado"}), 400

    results = OnlineSearchService.search_all_image_candidates(name)
    return jsonify(results)


@artists_bp.route("/<artisthash>/metadata", methods=["PUT"])
def update_metadata(artisthash: str):
    """
    Updates the artist's biography and extra metadata in userdata.db.
    """
    data = request.get_json() or {}
    bio = data.get("bio")
    info = data.get("info")
    extra = data.get("extra")

    success = ArtistService.update_artist_metadata(
        artisthash=artisthash,
        bio=bio,
        info=info,
        extra=extra,
    )
    return jsonify({"success": success})
