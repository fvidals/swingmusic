import base64
import io
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from config import settings
from database import user_db

log = logging.getLogger(__name__)


class SwingCustomService:
    @staticmethod
    def get_users_images_dir() -> Path:
        """
        Directory where custom user avatars are stored.
        """
        p = settings.images_dir / "users"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def get_assets_dir() -> Path:
        """
        Directory where SwingMusic fallback assets are stored (/config/assets or /config/swingmusic/assets).
        """
        p = settings.resolved_config_dir / "assets"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def get_client_dir() -> Path:
        """
        Directory where SwingMusic extracted webclient resides (/config/client or /config/swingmusic/client).
        """
        return settings.resolved_config_dir / "client"

    @classmethod
    def get_all_users(cls) -> List[Dict[str, Any]]:
        """
        Retrieves all users from database with avatar paths.
        """
        if not settings.userdata_db_path.exists() and not settings.swingmusic_db_path.exists():
            return []

        users = []
        with user_db() as conn:
            try:
                cursor = conn.execute("""
                    SELECT id, username, image, roles, extra
                    FROM user;
                """)
                for row in cursor.fetchall():
                    uid = row["id"]
                    uname = row["username"]
                    img = row["image"] or ""

                    # Parse roles
                    try:
                        roles = json.loads(row["roles"]) if row["roles"] else []
                        if isinstance(roles, str):
                            roles = [roles]
                    except Exception:
                        roles = ["user"]

                    # Parse extra
                    try:
                        extra = json.loads(row["extra"]) if row["extra"] else {}
                    except Exception:
                        extra = {}

                    # Check if avatar file exists on disk
                    user_img_file = cls.get_users_images_dir() / f"user_{uid}.webp"
                    avatar_url = None
                    if img and (img.startswith("http://") or img.startswith("https://") or img.startswith("data:")):
                        avatar_url = img
                    elif user_img_file.exists():
                        mtime = int(user_img_file.stat().st_mtime)
                        avatar_url = f"/api/images/user/user_{uid}.webp?t={mtime}"
                    elif img:
                        custom_file = cls.get_users_images_dir() / img
                        mtime = int(custom_file.stat().st_mtime) if custom_file.exists() else int(time.time())
                        avatar_url = f"/api/images/user/{img}?t={mtime}"

                    users.append({
                        "id": uid,
                        "username": uname,
                        "image": img,
                        "avatar_url": avatar_url,
                        "has_custom_avatar": bool(avatar_url),
                        "roles": roles,
                        "is_admin": "admin" in roles,
                        "is_guest": "guest" in roles or uname == "guest",
                        "firstname": extra.get("firstname", ""),
                        "lastname": extra.get("lastname", ""),
                        "email": extra.get("email", ""),
                        "extra": extra,
                    })
            except Exception as e:
                log.warning(f"Erro ao ler usuários: {e}")

        return users

    @classmethod
    def update_user_avatar(cls, user_id: int, image_bytes: bytes) -> Dict[str, Any]:
        """
        Processes avatar image (crops to 1:1, converts to WebP 256x256),
        saves to images/users/user_{user_id}.webp and updates UserTable.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return {"success": False, "error": f"Arquivo de imagem inválido: {e}"}

        # Convert to RGB / RGBA
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            bg = Image.new("RGBA", img.size, (255, 255, 255, 0))
            bg.paste(img, (0, 0), img.convert("RGBA"))
            img = bg
        else:
            img = img.convert("RGB")

        # Crop to square 1:1
        w, h = img.size
        if w != h:
            min_dim = min(w, h)
            left = (w - min_dim) // 2
            top = (h - min_dim) // 2
            img = img.crop((left, top, left + min_dim, top + min_dim))

        img = img.resize((256, 256), Image.Resampling.LANCZOS)

        # Save file to disk
        filename = f"user_{user_id}.webp"
        save_path = cls.get_users_images_dir() / filename
        img.save(save_path, format="webp", quality=90)
        mtime = int(save_path.stat().st_mtime)

        # Update user in database
        with user_db() as conn:
            conn.execute(
                "UPDATE user SET image = ? WHERE id = ?;",
                (filename, user_id),
            )
            conn.commit()

        return {
            "success": True,
            "user_id": user_id,
            "filename": filename,
            "avatar_url": f"/api/images/user/{filename}?t={mtime}",
        }

    @classmethod
    def delete_user_avatar(cls, user_id: int) -> bool:
        """
        Removes custom avatar for a user and clears image field in userdata.db.
        """
        filename = f"user_{user_id}.webp"
        save_path = cls.get_users_images_dir() / filename
        if save_path.exists():
            try:
                save_path.unlink()
            except Exception:
                pass

        with user_db() as conn:
            conn.execute("UPDATE user SET image = NULL WHERE id = ?;", (user_id,))
            conn.commit()

        return True

    @classmethod
    def update_user_profile(
        cls,
        user_id: int,
        username: Optional[str] = None,
        roles: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Updates profile info for a user.
        """
        with user_db() as conn:
            row = conn.execute("SELECT id, username, roles, extra FROM user WHERE id = ?;", (user_id,)).fetchone()
            if not row:
                return {"success": False, "error": "Usuário não encontrado"}

            new_username = username.strip() if username else row["username"]
            new_roles = json.dumps(roles) if roles is not None else row["roles"]

            current_extra = json.loads(row["extra"]) if row["extra"] else {}
            if extra:
                current_extra.update(extra)
            new_extra = json.dumps(current_extra)

            conn.execute("""
                UPDATE user
                SET username = ?, roles = ?, extra = ?
                WHERE id = ?;
            """, (new_username, new_roles, new_extra, user_id))
            conn.commit()

        return {"success": True, "user_id": user_id}

    @classmethod
    def get_fallback_assets(cls) -> List[Dict[str, Any]]:
        """
        Lists default fallback images in SwingMusic assets folder (artist.webp, default.webp, playlist.svg, album.svg).
        """
        assets_dir = cls.get_assets_dir()
        known_assets = [
            {"name": "artist.webp", "label": "Artista Padrão (Sem foto)", "type": "image/webp"},
            {"name": "default.webp", "label": "Capa de Álbum Padrão", "type": "image/webp"},
            {"name": "playlist.svg", "label": "Ícone de Playlist Padrão", "type": "image/svg+xml"},
            {"name": "album.svg", "label": "Ícone de Álbum Padrão", "type": "image/svg+xml"},
        ]

        result = []
        for a in known_assets:
            file_path = assets_dir / a["name"]
            exists = file_path.exists()
            size = file_path.stat().st_size if exists else 0
            result.append({
                **a,
                "exists": exists,
                "size_bytes": size,
                "url": f"/api/swingmusic/assets/{a['name']}" if exists else None,
                "filepath": str(file_path),
            })

        return result

    @classmethod
    def update_fallback_asset(cls, asset_name: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Replaces a default fallback asset in SwingMusic's assets directory.
        """
        allowed = ["artist.webp", "default.webp", "playlist.svg", "album.svg", "logo-fill.light.ico"]
        if asset_name not in allowed:
            return {"success": False, "error": f"Asset '{asset_name}' não permitido"}

        assets_dir = cls.get_assets_dir()
        target_path = assets_dir / asset_name

        try:
            target_path.write_bytes(file_bytes)
            return {"success": True, "name": asset_name, "filepath": str(target_path)}
        except Exception as e:
            return {"success": False, "error": f"Erro ao gravar asset: {e}"}

    AVATAR_PATCH_SCRIPT = """
    <!-- SwingMeta Custom Avatar Patch -->
    <script id="swingmeta-avatar-patch">
      (function() {
        function applyCustomAvatar() {
          var containers = document.querySelectorAll('.topnav .avatar .img.circular, .avatar .img.circular');
          if (!containers || containers.length === 0) return;

          var host = window.location.hostname || 'localhost';
          var isHttps = window.location.protocol === 'https:';
          var metaUrl = (isHttps ? 'https://' : 'http://') + host + ':1971/api/images/user/user_1.webp';
          var relativeUrl = '/api/images/user/user_1.webp';

          containers.forEach(function(container) {
            if (container.getAttribute('data-swingmeta-patched') === 'true') return;
            container.setAttribute('data-swingmeta-patched', 'true');

            var img = document.createElement('img');
            img.src = metaUrl + '?t=' + Date.now();
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '50%';
            img.style.display = 'block';

            img.onload = function() {
              container.innerHTML = '';
              container.appendChild(img);
            };

            img.onerror = function() {
              if (img.src.indexOf(':1971') !== -1) {
                img.src = relativeUrl + '?t=' + Date.now();
              } else {
                container.removeAttribute('data-swingmeta-patched');
              }
            };
          });
        }

        var observer = new MutationObserver(function() {
          applyCustomAvatar();
        });
        observer.observe(document.documentElement, { childList: true, subtree: true });
        window.addEventListener('DOMContentLoaded', applyCustomAvatar);
        window.addEventListener('load', applyCustomAvatar);
        setInterval(applyCustomAvatar, 2000);
      })();
    </script>"""

    @classmethod
    def get_client_info(cls) -> Dict[str, Any]:
        """
        Inspects SwingMusic webclient folder (/config/client).
        """
        client_dir = cls.get_client_dir()
        index_file = client_dir / "index.html"
        exists = client_dir.exists() and index_file.exists()

        is_patched = False
        if exists:
            try:
                content = index_file.read_text(encoding="utf-8")
                is_patched = "swingmeta-avatar-patch" in content
            except Exception:
                pass

        version = "Desconhecida"
        version_file = client_dir / "version.txt"
        if version_file.exists():
            try:
                version = version_file.read_text().strip()
            except Exception:
                pass

        total_files = 0
        if exists:
            try:
                total_files = len(list(client_dir.rglob("*")))
            except Exception:
                pass

        return {
            "exists": exists,
            "is_patched": is_patched,
            "version": version,
            "path": str(client_dir),
            "total_files": total_files,
        }

    @classmethod
    def patch_client(cls) -> Dict[str, Any]:
        """
        Applies the custom avatar patch to SwingMusic's client/index.html and index.html.gz.
        """
        import gzip
        client_dir = cls.get_client_dir()
        index_file = client_dir / "index.html"
        gz_file = client_dir / "index.html.gz"

        if not index_file.exists():
            return {"success": False, "error": "client/index.html não encontrado na pasta de configuração"}

        content = index_file.read_text(encoding="utf-8")
        if "swingmeta-avatar-patch" in content:
            return {"success": True, "message": "O patch já está aplicado no client!", "is_patched": True}

        if "</body>" in content:
            new_content = content.replace("</body>", f"{cls.AVATAR_PATCH_SCRIPT}\n  </body>")
        else:
            new_content = content + cls.AVATAR_PATCH_SCRIPT

        index_file.write_text(new_content, encoding="utf-8")
        gz_data = gzip.compress(new_content.encode("utf-8"))
        gz_file.write_bytes(gz_data)

        return {"success": True, "message": "Patch de avatar aplicado com sucesso no WebClient do SwingMusic!", "is_patched": True}

    @classmethod
    def unpatch_client(cls) -> Dict[str, Any]:
        """
        Removes the custom avatar patch from SwingMusic's client/index.html and index.html.gz.
        """
        import gzip
        import re
        client_dir = cls.get_client_dir()
        index_file = client_dir / "index.html"
        gz_file = client_dir / "index.html.gz"

        if not index_file.exists():
            return {"success": False, "error": "client/index.html não encontrado"}

        content = index_file.read_text(encoding="utf-8")
        if "swingmeta-avatar-patch" not in content:
            return {"success": True, "message": "O patch não está aplicado.", "is_patched": False}

        pattern = r"\s*<!-- SwingMeta Custom Avatar Patch -->[\s\S]*?</script>"
        new_content = re.sub(pattern, "", content)

        index_file.write_text(new_content, encoding="utf-8")
        if gz_file.exists():
            gz_data = gzip.compress(new_content.encode("utf-8"))
            gz_file.write_bytes(gz_data)

        return {"success": True, "message": "Patch removido com sucesso!", "is_patched": False}
