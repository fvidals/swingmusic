import json
import os
import pathlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    # Port to run swingmeta
    PORT: int = int(os.environ.get("SWINGMETA_PORT", os.environ.get("PORT", "1971")))
    HOST: str = os.environ.get("SWINGMETA_HOST", os.environ.get("HOST", "0.0.0.0"))

    # Config Directory for SwingMusic (where swingmusic.db, userdata.db, images/ reside)
    CONFIG_DIR: Path = Path(
        os.environ.get(
            "SWING_CONFIG_DIR",
            os.environ.get("SWINGMUSIC_CONFIG_DIR", "/config"),
        )
    ).resolve()

    # Music Directory for audio files (where mp3, flac, etc. are stored)
    MUSIC_DIR: Path = Path(
        os.environ.get(
            "SWING_MUSIC_DIR",
            os.environ.get("SWINGMUSIC_MUSIC_DIR", "/music"),
        )
    ).resolve()

    # Spotify API credentials (optional)
    SPOTIFY_CLIENT_ID: str = os.environ.get("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.environ.get("SPOTIFY_CLIENT_SECRET", "")

    # Static build folder for Vue 3 frontend
    CLIENT_DIR: Path = (
        Path(__file__).parent.parent / "frontend" / "dist"
    ).resolve()

    # Fixed, read/write directory owned by SwingMeta that mirrors artist photos
    # in full quality for any third-party media server to mount read-only
    # (e.g. Navidrome's ArtistImageFolder). No configuration needed.
    SHARED_ARTIST_ART_DIR: Path = Path("/shared/artist-art")

    @property
    def resolved_config_dir(self) -> Path:
        """
        Determines the actual config dir.
        If /config exists or SWING_CONFIG_DIR was specified, use that.
        Otherwise falls back to ~/.swingmusic or ~/.config/swingmusic or subfolder swingmusic.
        """
        # 1. Custom or explicit CONFIG_DIR
        if self.CONFIG_DIR != Path("/config") and self.CONFIG_DIR.exists():
            if (self.CONFIG_DIR / "swingmusic" / "swingmusic.db").exists():
                return self.CONFIG_DIR / "swingmusic"
            return self.CONFIG_DIR

        # 2. Standard /config mount
        if self.CONFIG_DIR.exists():
            if (self.CONFIG_DIR / "swingmusic.db").exists():
                return self.CONFIG_DIR
            if (self.CONFIG_DIR / "swingmusic" / "swingmusic.db").exists():
                return self.CONFIG_DIR / "swingmusic"
            if (self.CONFIG_DIR / ".swingmusic" / "swingmusic.db").exists():
                return self.CONFIG_DIR / ".swingmusic"
            if (self.CONFIG_DIR / "images").exists() or (self.CONFIG_DIR / "userdata.db").exists():
                return self.CONFIG_DIR

        # 3. Check user home
        home = Path.home().resolve()
        for candidate in [
            home / ".swingmusic",
            home / "swingmusic",
            home / ".config" / "swingmusic",
        ]:
            if candidate.exists():
                return candidate

        return self.CONFIG_DIR

    @property
    def swingmusic_db_path(self) -> Path:
        return self.resolved_config_dir / "swingmusic.db"

    @property
    def userdata_db_path(self) -> Path:
        return self.resolved_config_dir / "userdata.db"

    @property
    def images_dir(self) -> Path:
        return self.resolved_config_dir / "images"

    @property
    def artist_images_lg(self) -> Path:
        p = self.images_dir / "artists" / "large"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def artist_images_md(self) -> Path:
        p = self.images_dir / "artists" / "medium"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def artist_images_sm(self) -> Path:
        p = self.images_dir / "artists" / "small"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def thumbnails_dir(self) -> Path:
        return self.images_dir / "thumbnails"

    @property
    def thumb_images_orig(self) -> Path:
        p = self.images_dir / "thumbnails" / "original"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def thumb_images_lg(self) -> Path:
        p = self.images_dir / "thumbnails" / "large"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def thumb_images_md(self) -> Path:
        p = self.images_dir / "thumbnails" / "medium"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def thumb_images_sm(self) -> Path:
        p = self.images_dir / "thumbnails" / "small"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def thumb_images_xsm(self) -> Path:
        p = self.images_dir / "thumbnails" / "xsmall"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def playlist_images_dir(self) -> Path:
        p = self.images_dir / "playlists"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def shared_artist_art_dir(self) -> Path:
        self.SHARED_ARTIST_ART_DIR.mkdir(parents=True, exist_ok=True)
        return self.SHARED_ARTIST_ART_DIR

    @property
    def swingmeta_settings_file(self) -> Path:
        return self.resolved_config_dir / "swingmeta.json"

    def get_custom_settings(self) -> dict:
        p = self.swingmeta_settings_file
        defaults = {
            "embed_audio_tags": False,  # Feature toggle: Disabled by default
            "spotify_client_id": self.SPOTIFY_CLIENT_ID,
            "spotify_client_secret": self.SPOTIFY_CLIENT_SECRET,
        }
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                defaults.update(data)
            except Exception:
                pass
        return defaults

    def update_custom_settings(self, new_settings: dict) -> dict:
        current = self.get_custom_settings()
        current.update(new_settings)
        try:
            self.resolved_config_dir.mkdir(parents=True, exist_ok=True)
            self.swingmeta_settings_file.write_text(json.dumps(current, indent=2), encoding="utf-8")
        except Exception:
            pass
        if "spotify_client_id" in current:
            self.SPOTIFY_CLIENT_ID = current["spotify_client_id"]
        if "spotify_client_secret" in current:
            self.SPOTIFY_CLIENT_SECRET = current["spotify_client_secret"]
        return current


settings = Settings()

