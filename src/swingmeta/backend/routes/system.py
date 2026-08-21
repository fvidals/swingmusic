import logging
import os
from pathlib import Path
from typing import Any, List
from flask import Blueprint, jsonify, request, send_file

from config import settings
from database import swing_db, user_db
from services.backup_service import BackupService
from services.online_search import OnlineSearchService, _spotify_token

log = logging.getLogger(__name__)
system_bp = Blueprint("system", __name__, url_prefix="/api/system")


def get_discovered_mount_points() -> List[dict[str, Any]]:
    """
    Auto-discovers and validates all volume mount points:
    1. Configured /music
    2. Root prefixes from track table in swingmusic.db (e.g. /downtify, /downloads)
    3. Container mount points from /proc/mounts (if Linux)
    """
    discovered = {}

    # 1. Configured MUSIC_DIR
    music_str = str(settings.MUSIC_DIR)
    discovered[music_str] = {
        "path": music_str,
        "label": "Diretório /music Padrão",
        "source": "config",
        "is_swing_root": False,
    }

    # 2. Configured rootDirs in SwingMusic's settings.json
    swing_settings_path = settings.resolved_config_dir / "settings.json"
    if swing_settings_path.exists():
        try:
            import json
            with open(swing_settings_path, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                root_dirs = sdata.get("rootDirs", [])
                for r in root_dirs:
                    if r and isinstance(r, str):
                        r_clean = r.rstrip("/") if r != "/" else "/"
                        discovered[r_clean] = {
                            "path": r_clean,
                            "label": f"Fonte de Áudio do SwingMusic ({r_clean})",
                            "source": "swingmusic_config",
                            "is_swing_root": True,
                        }
        except Exception as e:
            log.warning(f"Erro ao ler settings.json do SwingMusic: {e}")

    # 3. Extract from track table in database
    if settings.swingmusic_db_path.exists():
        try:
            with swing_db() as conn:
                rows = conn.execute("SELECT DISTINCT folder, filepath FROM track;").fetchall()
                for r in rows:
                    p = r["filepath"] or r["folder"] or ""
                    if p.startswith("/"):
                        parts = p.strip("/").split("/")
                        if parts:
                            top = "/" + parts[0]
                            if top not in discovered:
                                discovered[top] = {
                                    "path": top,
                                    "label": f"Volume de Músicas / Downloads ({top})",
                                    "source": "database",
                                }
                    elif ":" in p:  # Windows style
                        drive = p.split(":")[0] + ":/"
                        if drive not in discovered:
                            discovered[drive] = {
                                "path": drive,
                                "label": f"Unidade ({drive})",
                                "source": "database",
                            }
        except Exception as e:
            log.warning(f"Erro ao extrair pontos de montagem do banco: {e}")

    # 3. Check /proc/mounts in Linux container
    if os.path.exists("/proc/mounts"):
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        target = parts[1]
                        # Exclude system/virtual mounts
                        ignored_prefixes = ("/etc", "/sys", "/proc", "/dev", "/root", "/run", "/var", "/tmp", "/bin", "/lib", "/lib64", "/usr")
                        if target in ignored_prefixes or target.startswith(ignored_prefixes):
                            continue
                        if target != "/" and os.path.isdir(target):
                            if target not in discovered and not target.startswith(str(settings.resolved_config_dir)):
                                discovered[target] = {
                                    "path": target,
                                    "label": f"Volume do Container ({target})",
                                    "source": "container",
                                }
        except Exception:
            pass

    # Evaluate each mount point
    results = []
    for path_str, info in discovered.items():
        p = Path(path_str)
        exists = p.exists()
        writable = os.access(p, os.W_OK) if exists else False

        track_cnt = 0
        if settings.swingmusic_db_path.exists():
            try:
                with swing_db() as conn:
                    row = conn.execute(
                        "SELECT COUNT(*) as c FROM track WHERE filepath LIKE ? OR folder LIKE ?;",
                        (f"{path_str}%", f"{path_str}%"),
                    ).fetchone()
                    if row:
                        track_cnt = row["c"]
            except Exception:
                pass

        results.append({
            "path": path_str,
            "label": info.get("label", path_str),
            "exists": exists,
            "writable": writable,
            "track_count": track_cnt,
            "source": info.get("source", "custom"),
            "is_swing_root": info.get("is_swing_root", False),
        })

    # Sort so that SwingMusic roots & folders with tracks come first
    results.sort(key=lambda x: (x["is_swing_root"], x["track_count"] > 0, x["exists"]), reverse=True)
    return results


@system_bp.route("/status", methods=["GET"])
def get_system_status():
    """
    Returns the status of volume mounts, databases, dynamic music mount points, and general statistics.
    """
    swing_db_ok = settings.swingmusic_db_path.exists()
    user_db_ok = settings.userdata_db_path.exists() or settings.swingmusic_db_path.exists()
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

    mount_points = get_discovered_mount_points()

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
        "mount_points": mount_points,
        "stats": {
            "track_count": track_count,
            "artist_image_count": artist_image_count,
        },
        "settings": settings.get_custom_settings(),
        "spotify": {
            "configured": bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET),
            "client_id": settings.SPOTIFY_CLIENT_ID[:6] + "..." if settings.SPOTIFY_CLIENT_ID else "",
        },
    })


@system_bp.route("/settings", methods=["GET"])
def get_system_settings():
    """
    Returns custom persistent SwingMeta settings (e.g. embed_audio_tags).
    """
    return jsonify(settings.get_custom_settings())


@system_bp.route("/settings", methods=["POST"])
def update_system_settings():
    """
    Updates custom persistent SwingMeta settings.
    """
    data = request.get_json() or {}
    updated = settings.update_custom_settings(data)
    return jsonify({
        "success": True,
        "message": "Configurações salvas com sucesso!",
        "settings": updated,
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

    # Save to persistent swingmeta.json
    settings.update_custom_settings({
        "spotify_client_id": client_id,
        "spotify_client_secret": client_secret,
    })

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


@system_bp.route("/backup/summary", methods=["GET"])
def get_backup_summary():
    """
    Returns summary statistics of the SwingMusic config directory for backup.
    """
    summary = BackupService.get_backup_summary()
    return jsonify(summary)


@system_bp.route("/backup/download", methods=["GET"])
def download_backup():
    """
    Generates and downloads a .zip archive of the SwingMusic configuration.
    """
    try:
        buf, filename = BackupService.create_backup_zip()
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        log.error(f"Erro ao gerar backup ZIP: {e}")
        return jsonify({"success": False, "error": f"Falha ao gerar arquivo de backup: {e}"}), 500


@system_bp.route("/backup/restore", methods=["POST"])
def restore_backup():
    """
    Restores a backup .zip archive into the SwingMusic configuration directory.
    """
    file_bytes = None

    if "file" in request.files:
        file_bytes = request.files["file"].read()
    elif request.is_json:
        import base64
        data = request.get_json()
        b64_str = data.get("file_base64", "")
        if b64_str:
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            try:
                file_bytes = base64.b64decode(b64_str)
            except Exception as e:
                return jsonify({"success": False, "error": f"Base64 inválido: {e}"}), 400

    if not file_bytes:
        return jsonify({"success": False, "error": "Nenhum arquivo de backup (.zip) enviado"}), 400

    result = BackupService.restore_backup_zip(file_bytes)
    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)

