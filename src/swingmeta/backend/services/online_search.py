import base64
import logging
import urllib.parse
from typing import Any, List, Optional

import requests

from config import settings

log = logging.getLogger(__name__)

# Cache for Spotify access token
_spotify_token: Optional[str] = None


class OnlineSearchService:
    @staticmethod
    def search_deezer(artist_name: str) -> List[dict[str, Any]]:
        """
        Searches Deezer for artist images and basic info without any API key.
        """
        results = []
        try:
            query = urllib.parse.quote(artist_name)
            url = f"https://api.deezer.com/search/artist?q={query}&limit=6"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json().get("data", [])
                for item in data:
                    img_url = item.get("picture_xl") or item.get("picture_big") or item.get("picture_medium")
                    if img_url:
                        results.append({
                            "provider": "Deezer",
                            "name": item.get("name"),
                            "image_url": img_url,
                            "thumbnail_url": item.get("picture_medium") or img_url,
                            "nb_fan": item.get("nb_fan", 0),
                            "nb_album": item.get("nb_album", 0),
                            "link": item.get("link", ""),
                        })
        except Exception as e:
            log.warning(f"Erro na busca Deezer para '{artist_name}': {e}")

        return results

    @staticmethod
    def search_itunes(artist_name: str) -> List[dict[str, Any]]:
        """
        Searches iTunes / Apple Music search API (zero config) for artists and album arts.
        """
        results = []
        try:
            query = urllib.parse.quote(artist_name)
            url = f"https://itunes.apple.com/search?term={query}&entity=musicArtist&limit=4"
            headers = {"User-Agent": "SwingMeta/1.0"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json().get("results", [])
                for item in data:
                    name = item.get("artistName", "")
                    genre = item.get("primaryGenreName", "")
                    link = item.get("artistLinkUrl", "")
                    # iTunes artist entity doesn't always have a direct artist portrait in musicArtist,
                    # but provides valid metadata and genre.
                    if link:
                        results.append({
                            "provider": "iTunes",
                            "name": name,
                            "genre": genre,
                            "link": link,
                        })
        except Exception as e:
            log.warning(f"Erro na busca iTunes para '{artist_name}': {e}")

        return results

    @staticmethod
    def search_musicbrainz(artist_name: str) -> List[dict[str, Any]]:
        """
        Searches MusicBrainz for artist biography, aliases, country, and links (zero config).
        """
        results = []
        try:
            query = urllib.parse.quote(f'artist:"{artist_name}"')
            url = f"https://musicbrainz.org/ws/2/artist/?query={query}&fmt=json&limit=3"
            headers = {"User-Agent": "SwingMeta/1.0.0 (https://github.com/swingmx/swingmusic)"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json().get("artists", [])
                for item in data:
                    results.append({
                        "provider": "MusicBrainz",
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "disambiguation": item.get("disambiguation", ""),
                        "country": item.get("country", ""),
                        "type": item.get("type", ""),
                        "lifespan": item.get("life-span", {}),
                        "tags": [t.get("name") for t in item.get("tags", [])[:5]],
                    })
        except Exception as e:
            log.warning(f"Erro na busca MusicBrainz para '{artist_name}': {e}")

        return results

    @staticmethod
    def get_spotify_token() -> Optional[str]:
        """
        Obtains or caches a Spotify OAuth2 Client Credentials access token.
        """
        global _spotify_token
        if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
            return None

        if _spotify_token:
            return _spotify_token

        try:
            auth_str = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            url = "https://accounts.spotify.com/api/token"
            headers = {
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            res = requests.post(url, data={"grant_type": "client_credentials"}, headers=headers, timeout=10)
            if res.status_code == 200:
                _spotify_token = res.json().get("access_token")
                return _spotify_token
        except Exception as e:
            log.warning(f"Erro ao autenticar no Spotify: {e}")

        return None

    @staticmethod
    def search_spotify(artist_name: str) -> List[dict[str, Any]]:
        """
        Searches Spotify for artist portraits, followers, popularity, and genres.
        Requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.
        """
        token = OnlineSearchService.get_spotify_token()
        if not token:
            return []

        results = []
        try:
            query = urllib.parse.quote(artist_name)
            url = f"https://api.spotify.com/v1/search?q={query}&type=artist&limit=5"
            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                artists = res.json().get("artists", {}).get("items", [])
                for item in artists:
                    images = item.get("images", [])
                    img_url = images[0]["url"] if images else None
                    thumb_url = images[-1]["url"] if images else None
                    if img_url:
                        results.append({
                            "provider": "Spotify",
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "image_url": img_url,
                            "thumbnail_url": thumb_url or img_url,
                            "genres": item.get("genres", []),
                            "popularity": item.get("popularity", 0),
                            "followers": item.get("followers", {}).get("total", 0),
                            "link": item.get("external_urls", {}).get("spotify", ""),
                        })
        except Exception as e:
            log.warning(f"Erro na busca Spotify para '{artist_name}': {e}")

        return results

        return {
            "query": artist_name,
            "images": all_images,
            "musicbrainz": musicbrainz_results,
            "spotify_configured": bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET),
        }

    @staticmethod
    def search_deezer_albums(album_name: str, artist_name: str = "") -> List[dict[str, Any]]:
        """
        Searches Deezer for album covers.
        """
        results = []
        try:
            q = f"{artist_name} {album_name}".strip() if artist_name else album_name.strip()
            query = urllib.parse.quote(q)
            url = f"https://api.deezer.com/search/album?q={query}&limit=8"
            headers = {"User-Agent": "SwingMeta/1.0"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json().get("data", [])
                for item in data:
                    img_url = item.get("cover_xl") or item.get("cover_big") or item.get("cover_medium")
                    if img_url:
                        results.append({
                            "provider": "Deezer",
                            "album": item.get("title"),
                            "artist": item.get("artist", {}).get("name", ""),
                            "image_url": img_url,
                            "thumbnail_url": item.get("cover_medium") or img_url,
                            "nb_tracks": item.get("nb_tracks", 0),
                            "link": item.get("link", ""),
                        })
        except Exception as e:
            log.warning(f"Erro na busca Deezer Album para '{album_name}': {e}")
        return results

    @staticmethod
    def search_itunes_albums(album_name: str, artist_name: str = "") -> List[dict[str, Any]]:
        """
        Searches iTunes / Apple Music for high-resolution album covers.
        """
        results = []
        try:
            q = f"{artist_name} {album_name}".strip() if artist_name else album_name.strip()
            query = urllib.parse.quote(q)
            url = f"https://itunes.apple.com/search?term={query}&entity=album&limit=8"
            headers = {"User-Agent": "SwingMeta/1.0"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json().get("results", [])
                for item in data:
                    raw_art = item.get("artworkUrl100", "")
                    if raw_art:
                        # Replace 100x100 with 1000x1000 for high resolution artwork
                        hi_res = raw_art.replace("100x100bb.jpg", "1000x1000bb.jpg").replace("100x100bb.png", "1000x1000bb.png")
                        results.append({
                            "provider": "Apple Music",
                            "album": item.get("collectionName", ""),
                            "artist": item.get("artistName", ""),
                            "image_url": hi_res,
                            "thumbnail_url": raw_art,
                            "track_count": item.get("trackCount", 0),
                            "year": item.get("releaseDate", "")[:4] if item.get("releaseDate") else "",
                            "genre": item.get("primaryGenreName", ""),
                        })
        except Exception as e:
            log.warning(f"Erro na busca iTunes Album para '{album_name}': {e}")
        return results

    @classmethod
    def search_spotify_albums(cls, album_name: str, artist_name: str = "") -> List[dict[str, Any]]:
        """
        Searches Spotify for album covers if credentials are set.
        """
        token = cls.get_spotify_token()
        if not token:
            return []

        results = []
        try:
            q = f"{artist_name} {album_name}".strip() if artist_name else album_name.strip()
            query = urllib.parse.quote(q)
            url = f"https://api.spotify.com/v1/search?q={query}&type=album&limit=6"
            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                albums = res.json().get("albums", {}).get("items", [])
                for item in albums:
                    images = item.get("images", [])
                    img_url = images[0]["url"] if images else None
                    thumb_url = images[-1]["url"] if images else None
                    artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
                    if img_url:
                        results.append({
                            "provider": "Spotify",
                            "id": item.get("id"),
                            "album": item.get("name"),
                            "artist": artists,
                            "image_url": img_url,
                            "thumbnail_url": thumb_url or img_url,
                            "total_tracks": item.get("total_tracks", 0),
                            "release_date": item.get("release_date", ""),
                            "link": item.get("external_urls", {}).get("spotify", ""),
                        })
        except Exception as e:
            log.warning(f"Erro na busca Spotify Album para '{album_name}': {e}")
        return results

    @classmethod
    def search_all_album_covers(cls, album_name: str, artist_name: str = "") -> dict[str, Any]:
        """
        Aggregates album cover candidates from all providers.
        """
        deezer = cls.search_deezer_albums(album_name, artist_name)
        itunes = cls.search_itunes_albums(album_name, artist_name)
        spotify = cls.search_spotify_albums(album_name, artist_name)

        all_covers = []
        all_covers.extend(spotify)
        all_covers.extend(itunes)
        all_covers.extend(deezer)

        return {
            "query": f"{artist_name} - {album_name}".strip(" -"),
            "covers": all_covers,
            "spotify_configured": bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET),
        }

