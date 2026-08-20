import logging
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import settings
from database import ensure_database_tables
from routes.artists import artists_bp
from routes.images import images_bp
from routes.playlists import playlists_bp
from routes.swingmusic import swingmusic_bp
from routes.system import system_bp
from routes.tracks import tracks_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("swingmeta")


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Ensure required tables exist
    ensure_database_tables()

    # Register Blueprints
    app.register_blueprint(artists_bp)
    app.register_blueprint(tracks_bp)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(swingmusic_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(system_bp)

    # Serve Vue frontend build if present
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        # Don't intercept API routes
        if path.startswith("api/"):
            return jsonify({"error": "Endpoint not found"}), 404

        client_dir = settings.CLIENT_DIR
        if client_dir.exists():
            target_file = client_dir / path
            if path and target_file.exists() and not target_file.is_dir():
                return send_from_directory(str(client_dir), path)
            index_path = client_dir / "index.html"
            if index_path.exists():
                return send_from_directory(str(client_dir), "index.html")

        return jsonify({
            "message": "SwingMeta Backend está ativo!",
            "docs": "Frontend não encontrado em " + str(client_dir),
            "status_api": "/api/system/status",
            "artists_api": "/api/artists",
        })

    return app


app = create_app()

if __name__ == "__main__":
    log.info(f"Iniciando SwingMeta na porta {settings.PORT}...")
    log.info(f"Diretório de Configuração: {settings.resolved_config_dir}")
    log.info(f"Diretório de Músicas: {settings.MUSIC_DIR}")
    app.run(host=settings.HOST, port=settings.PORT, debug=True)
