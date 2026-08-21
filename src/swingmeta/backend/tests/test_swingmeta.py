import base64
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

# Setup sys.path for test imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from database import get_db_connection
from services.hash_utils import create_hash
from services.image_service import ImageService
from services.online_search import OnlineSearchService
from services.tag_service import TagService
from app import create_app


class TestSwingMeta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp())
        settings.CONFIG_DIR = cls.temp_dir
        settings.MUSIC_DIR = cls.temp_dir / "music"
        settings.MUSIC_DIR.mkdir(parents=True, exist_ok=True)

        # Setup mock databases
        cls.swing_db_path = settings.swingmusic_db_path
        cls.user_db_path = settings.userdata_db_path

        # Create mock swingmusic.db
        with get_db_connection(cls.swing_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS track (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    album VARCHAR,
                    albumartists VARCHAR,
                    albumhash VARCHAR,
                    artists VARCHAR,
                    bitrate INTEGER,
                    copyright VARCHAR,
                    date INTEGER,
                    disc INTEGER,
                    duration INTEGER,
                    filepath VARCHAR UNIQUE,
                    folder VARCHAR,
                    genres VARCHAR,
                    last_mod REAL,
                    title VARCHAR,
                    track INTEGER,
                    trackhash VARCHAR,
                    lastplayed INTEGER DEFAULT 0,
                    playcount INTEGER DEFAULT 0,
                    playduration INTEGER DEFAULT 0,
                    extra JSON
                );
            """)

            # Insert sample tracks
            queen_artists = json.dumps([{"name": "Queen", "artisthash": create_hash("Queen", decode=True)}])
            conn.execute("""
                INSERT OR IGNORE INTO track (album, albumartists, albumhash, artists, bitrate, disc, duration, filepath, folder, title, track, trackhash, last_mod, date, lastplayed, playcount, playduration)
                VALUES ('A Night at the Opera', ?, 'albumhash123', ?, 320000, 1, 354, '/music/bohemian.mp3', '/music', 'Bohemian Rhapsody', 1, 'trackhash123', 1700000000, 1975, 0, 0, 0);
            """, (queen_artists, queen_artists))
            conn.commit()

        # Create mock userdata.db
        with get_db_connection(cls.user_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artistdata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    itemhash VARCHAR UNIQUE,
                    itemtype VARCHAR,
                    color VARCHAR,
                    bio VARCHAR,
                    info JSON,
                    extra JSON
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR UNIQUE,
                    image VARCHAR,
                    password VARCHAR,
                    roles JSON,
                    extra JSON
                );
            """)
            conn.execute("""
                INSERT OR IGNORE INTO user (id, username, image, password, roles, extra)
                VALUES (1, 'admin', NULL, 'hashedpass', '["admin"]', '{"firstname": "Administrador", "email": "admin@local"}');
            """)
            conn.commit()

        cls.app = create_app()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_hash_generation(self):
        """Test that hash generation works identically to SwingMusic"""
        h1 = create_hash("Queen")
        h2 = create_hash("queen")
        h3 = create_hash(" Queen ")
        self.assertEqual(h1, h2)
        self.assertEqual(h1, h3)
        self.assertTrue(len(h1) > 0)

    def test_02_image_processing_and_webp(self):
        """Test image resizing, WebP conversion, and color extraction"""
        img = Image.new("RGB", (600, 600), color=(34, 197, 94))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        queen_hash = create_hash("Queen")
        result = ImageService.process_and_save_artist_image(raw_bytes, queen_hash)

        self.assertTrue(result["success"])
        self.assertTrue((settings.artist_images_lg / f"{queen_hash}.webp").exists())
        self.assertTrue((settings.artist_images_md / f"{queen_hash}.webp").exists())
        self.assertTrue((settings.artist_images_sm / f"{queen_hash}.webp").exists())

    def test_03_online_search_deezer(self):
        """Test searching Deezer API (zero-config)"""
        results = OnlineSearchService.search_deezer("Daft Punk")
        self.assertIsInstance(results, list)
        if len(results) > 0:
            self.assertEqual(results[0]["provider"], "Deezer")
            self.assertTrue("image_url" in results[0])

    def test_04_system_status_api(self):
        """Test /api/system/status endpoint"""
        res = self.client.get("/api/system/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "online")
        self.assertTrue(data["mounts"]["swingmusic_db_exists"])
        self.assertEqual(data["stats"]["track_count"], 1)

    def test_05_artists_api(self):
        """Test /api/artists list and detail endpoints"""
        res = self.client.get("/api/artists")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["artists"][0]["name"], "Queen")
        self.assertTrue(data["artists"][0]["has_image"])

        # Test artist detail
        queen_hash = data["artists"][0]["artisthash"]
        res_detail = self.client.get(f"/api/artists/{queen_hash}")
        self.assertEqual(res_detail.status_code, 200)
        detail_data = res_detail.get_json()
        self.assertEqual(detail_data["name"], "Queen")
        self.assertEqual(len(detail_data["tracks"]), 1)

    def test_06_artist_bio_update(self):
        """Test updating artist biography in userdata.db"""
        queen_hash = create_hash("Queen")
        res = self.client.put(f"/api/artists/{queen_hash}/metadata", json={
            "bio": "Queen é uma lendária banda britânica de rock fundada em Londres em 1970."
        })
        self.assertEqual(res.status_code, 200)

        # Check detail again
        res_detail = self.client.get(f"/api/artists/{queen_hash}")
        detail_data = res_detail.get_json()
        self.assertEqual(detail_data["bio"], "Queen é uma lendária banda britânica de rock fundada em Londres em 1970.")
        self.assertTrue(detail_data["has_bio"])

    def test_07_m3u_playlists(self):
        """Test M3U scanning, path resolving, and playlist creation in SwingMusic"""
        with get_db_connection(self.user_db_path) as conn:
            conn.execute("DELETE FROM playlist WHERE name = 'Rock Classics';")
            conn.commit()

        playlists_dir = settings.MUSIC_DIR / "Playlists"
        playlists_dir.mkdir(parents=True, exist_ok=True)
        m3u_file = playlists_dir / "Rock Classics.m3u"
        m3u_file.write_text("""#EXTM3U
#EXTINF:354,Queen - Bohemian Rhapsody
../bohemian.mp3
#EXTINF:200,Musica Desconhecida
../desconhecida.mp3
""", encoding="utf-8")

        # Test listing playlists
        res = self.client.get("/api/playlists")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["playlists"][0]["name"], "Rock Classics")
        self.assertEqual(data["playlists"][0]["total_tracks"], 2)
        self.assertEqual(data["playlists"][0]["matched_tracks"], 1)
        self.assertEqual(data["playlists"][0]["match_rate"], 50.0)
        self.assertFalse(data["playlists"][0]["is_created_in_swing"])

        # Test detail endpoint
        res_detail = self.client.get(f"/api/playlists/detail?path={m3u_file}")
        self.assertEqual(res_detail.status_code, 200)
        detail = res_detail.get_json()
        self.assertEqual(len(detail["tracks"]), 2)
        self.assertTrue(detail["tracks"][0]["matched"])
        self.assertTrue(len(detail["tracks"][0]["trackhash"]) > 0)
        self.assertFalse(detail["tracks"][1]["matched"])

        # Test creating playlist in SwingMusic
        res_create = self.client.post("/api/playlists/create", json={
            "filepath": str(m3u_file),
            "name": "Rock Classics",
        })
        self.assertEqual(res_create.status_code, 200)
        create_data = res_create.get_json()
        self.assertTrue(create_data["success"])
        self.assertEqual(create_data["imported_tracks"], 1)

        # Verify it now shows as created
        res2 = self.client.get("/api/playlists")
        self.assertTrue(res2.get_json()["playlists"][0]["is_created_in_swing"])

    def test_08_swingmusic_customization(self):
        """Test listing users, uploading user avatar, and updating assets"""
        # 1. Test listing users
        res = self.client.get("/api/swingmusic/users")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["users"][0]["username"], "admin")
        self.assertTrue(data["users"][0]["is_admin"])

        # 2. Test uploading user avatar
        img = Image.new("RGB", (300, 300), color=(59, 130, 246))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()
        b64_str = "data:image/png;base64," + base64.b64encode(raw_bytes).decode("utf-8")

        res_avatar = self.client.post("/api/swingmusic/users/1/avatar", json={
            "image_base64": b64_str
        })
        self.assertEqual(res_avatar.status_code, 200)
        avatar_data = res_avatar.get_json()
        self.assertTrue(avatar_data["success"])
        self.assertTrue(avatar_data["avatar_url"].startswith("/api/images/user/"))

        # 3. Test listing fallback assets
        res_assets = self.client.get("/api/swingmusic/assets")
        self.assertEqual(res_assets.status_code, 200)
        assets_data = res_assets.get_json()
        self.assertEqual(assets_data["total"], 4)

        # 4. Test client info
        res_client = self.client.get("/api/swingmusic/client")
        self.assertEqual(res_client.status_code, 200)

    def test_09_batch_cover_and_url(self):
        """Test batch cover endpoint with base64/URL and track IDs"""
        img = Image.new("RGB", (400, 400), color=(236, 72, 153))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64_str = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

        res = self.client.post("/api/tracks/batch-cover", json={
            "track_ids": [1],
            "image_base64": b64_str,
            "embed_audio": False,
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_tracks"], 1)
        self.assertEqual(data["updated_albums"], 1)
        self.assertTrue((settings.thumb_images_lg / "albumhash123.webp").exists())

    def test_10_client_patch(self):
        """Test applying and removing client custom avatar patch"""
        client_dir = settings.CONFIG_DIR / "client"
        client_dir.mkdir(parents=True, exist_ok=True)
        index_file = client_dir / "index.html"
        index_file.write_text("<!DOCTYPE html><html><head></head><body><div id='app'></div></body></html>", encoding="utf-8")

        # 1. Check initial info
        res_info = self.client.get("/api/swingmusic/client")
        self.assertEqual(res_info.status_code, 200)
        self.assertFalse(res_info.get_json()["is_patched"])

        # 2. Apply patch
        res_patch = self.client.post("/api/swingmusic/client/patch")
        self.assertEqual(res_patch.status_code, 200)
        self.assertTrue(res_patch.get_json()["success"])
        self.assertTrue(res_patch.get_json()["is_patched"])

        # Verify file content
        content = index_file.read_text(encoding="utf-8")
        self.assertIn("swingmeta-avatar-patch", content)

        # 3. Remove patch
        res_unpatch = self.client.delete("/api/swingmusic/client/patch")
        self.assertEqual(res_unpatch.status_code, 200)
        self.assertFalse(res_unpatch.get_json()["is_patched"])
        content_unpatched = index_file.read_text(encoding="utf-8")
        self.assertNotIn("swingmeta-avatar-patch", content_unpatched)

    def test_11_backup_and_restore(self):
        """Test backup summary, ZIP generation/download and restore"""
        import zipfile

        # 1. Summary
        res_sum = self.client.get("/api/system/backup/summary")
        self.assertEqual(res_sum.status_code, 200)
        sum_data = res_sum.get_json()
        self.assertTrue(sum_data["exists"])
        self.assertTrue(sum_data["total_files"] > 0)
        self.assertTrue(sum_data["total_size_bytes"] > 0)

        # 2. Download ZIP
        res_dl = self.client.get("/api/system/backup/download")
        self.assertEqual(res_dl.status_code, 200)
        self.assertEqual(res_dl.mimetype, "application/zip")
        zip_bytes = res_dl.data
        self.assertTrue(len(zip_bytes) > 0)

        buf = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buf, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("swingmeta_manifest.json", namelist)
            self.assertTrue(any("swingmusic.db" in n for n in namelist))

        # 3. Restore
        data = {
            "file": (io.BytesIO(zip_bytes), "test_backup.zip")
        }
        res_res = self.client.post("/api/system/backup/restore", data=data, content_type="multipart/form-data")
        self.assertEqual(res_res.status_code, 200)
        res_data = res_res.get_json()
        self.assertTrue(res_data["success"])
        self.assertTrue(res_data["restored_files"] > 0)


if __name__ == "__main__":
    unittest.main()


