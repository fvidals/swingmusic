import datetime
import io
import json
import logging
import os
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import settings

logger = logging.getLogger(__name__)


class BackupService:
    @staticmethod
    def _is_ignored_file(filename: str) -> bool:
        if filename in {"__pycache__", ".pytest_cache", ".DS_Store", "Thumbs.db"}:
            return True
        if filename.endswith((".tmp", ".lock", ".bak", ".db-wal", ".db-shm", ".db-journal", "-shm", "-wal", "-journal")):
            return True
        if filename.startswith(".") and filename != ".device-id":
            return True
        return False

    @staticmethod
    def _checkpoint_sqlite(db_path: Path):
        """Forces SQLite to flush WAL and checkpoint to the main db file."""
        if not db_path.exists():
            return
        try:
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()
        except Exception as e:
            logger.warning(f"Could not checkpoint {db_path}: {e}")

    @classmethod
    def get_backup_summary(cls) -> Dict[str, Any]:
        """
        Calculates size, file count, and details of the SwingMusic config directory.
        """
        config_dir = settings.resolved_config_dir
        if not config_dir.exists():
            return {
                "exists": False,
                "config_dir": str(config_dir),
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "total_files": 0,
                "database_count": 0,
                "image_count": 0,
                "databases": [],
                "images_size_bytes": 0,
            }

        total_size = 0
        total_files = 0
        image_count = 0
        images_size = 0
        databases = []

        # Checkpoint known databases
        cls._checkpoint_sqlite(settings.swingmusic_db_path)
        cls._checkpoint_sqlite(settings.userdata_db_path)

        for root, dirs, files in os.walk(config_dir):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not cls._is_ignored_file(d) and not d.startswith(".git")]

            for file in files:
                if cls._is_ignored_file(file):
                    continue

                fp = Path(root) / file
                try:
                    size = fp.stat().st_size
                    total_size += size
                    total_files += 1

                    rel_path = fp.relative_to(config_dir).as_posix()

                    if file.endswith(".db"):
                        databases.append({
                            "name": file,
                            "relative_path": rel_path,
                            "size_bytes": size,
                            "size_mb": round(size / (1024 * 1024), 2),
                        })

                    if "images" in rel_path.split("/") or file.endswith((".webp", ".jpg", ".jpeg", ".png", ".svg")):
                        image_count += 1
                        images_size += size

                except Exception:
                    continue

        return {
            "exists": True,
            "config_dir": str(config_dir),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_files": total_files,
            "database_count": len(databases),
            "image_count": image_count,
            "images_size_bytes": images_size,
            "images_size_mb": round(images_size / (1024 * 1024), 2),
            "databases": databases,
        }

    @classmethod
    def create_backup_zip(cls) -> Tuple[io.BytesIO, str]:
        """
        Creates a compressed .zip archive of the entire config directory.
        Returns (BytesIO, filename).
        """
        config_dir = settings.resolved_config_dir
        if not config_dir.exists():
            raise FileNotFoundError(f"Config directory {config_dir} does not exist")

        # Checkpoint databases
        cls._checkpoint_sqlite(settings.swingmusic_db_path)
        cls._checkpoint_sqlite(settings.userdata_db_path)

        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        zip_filename = f"swingmusic-backup-{timestamp_str}.zip"

        buf = io.BytesIO()
        file_count = 0
        total_uncompressed = 0

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
            for root, dirs, files in os.walk(config_dir):
                dirs[:] = [d for d in dirs if not cls._is_ignored_file(d) and not d.startswith(".git")]

                for file in files:
                    if cls._is_ignored_file(file):
                        continue

                    fp = Path(root) / file
                    try:
                        rel_path = fp.relative_to(config_dir).as_posix()
                        zip_file.write(fp, arcname=rel_path)
                        total_uncompressed += fp.stat().st_size
                        file_count += 1
                    except Exception as e:
                        logger.warning(f"Could not add {fp} to backup: {e}")

            # Add manifest metadata
            manifest = {
                "backup_date": datetime.datetime.now().isoformat(),
                "generator": "SwingMeta",
                "version": "1.0",
                "source_config_dir": str(config_dir),
                "total_files": file_count,
                "total_uncompressed_bytes": total_uncompressed,
            }
            zip_file.writestr("swingmeta_manifest.json", json.dumps(manifest, indent=2))

        buf.seek(0)
        return buf, zip_filename

    @classmethod
    def restore_backup_zip(cls, zip_data: bytes) -> Dict[str, Any]:
        """
        Restores a backup .zip archive into the SwingMusic config directory.
        Creates a safety snapshot before overwriting.
        """
        config_dir = settings.resolved_config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        if not zip_data:
            return {"success": False, "error": "Arquivo de backup vazio ou inválido"}

        buf = io.BytesIO(zip_data)
        if not zipfile.is_zipfile(buf):
            return {"success": False, "error": "O arquivo enviado não é um arquivo .ZIP válido"}

        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zip_file:
            namelist = zip_file.namelist()

            # Security check: prevent Zip Slip path traversal
            for name in namelist:
                if name.startswith("/") or ".." in name or "\\" in name:
                    return {"success": False, "error": f"Arquivo corrompido ou inseguro no ZIP: {name}"}

            # Verify it contains at least some configuration or database
            has_db_or_config = any(
                n.endswith(".db") or n.endswith(".json") or "images/" in n or "client/" in n or n == "swingmeta_manifest.json"
                for n in namelist
            )
            if not has_db_or_config:
                return {"success": False, "error": "O arquivo ZIP não parece ser um backup válido do SwingMusic"}

            # Create safety snapshot of current config if files exist
            safety_dir = None
            if any(config_dir.iterdir()):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_dir = config_dir.parent / f"swingmusic_config_backup_{timestamp}.bak"
                try:
                    shutil.copytree(config_dir, safety_dir, dirs_exist_ok=True)
                except Exception as e:
                    logger.warning(f"Could not create safety snapshot: {e}")

            # Extract archive
            restored_count = 0
            for member in zip_file.infolist():
                if member.filename.endswith("/") or member.filename == "swingmeta_manifest.json":
                    continue
                if cls._is_ignored_file(Path(member.filename).name):
                    continue

                target_file = config_dir / member.filename
                target_file.parent.mkdir(parents=True, exist_ok=True)

                try:
                    with zip_file.open(member) as source, open(target_file, "wb") as target:
                        shutil.copyfileobj(source, target)
                        restored_count += 1
                except Exception as e:
                    logger.warning(f"Could not restore {member.filename}: {e}")

        return {
            "success": True,
            "message": f"Backup restaurado com sucesso ({restored_count} arquivos)!",
            "restored_files": restored_count,
            "safety_snapshot": str(safety_dir) if safety_dir else None,
        }
