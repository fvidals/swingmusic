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

    @classmethod
    def search_all_image_candidates(cls, artist_name: str) -> dict[str, Any]:
        """
        Aggregates image candidates from all available providers (Deezer, Spotify, etc.)
        """
        deezer_results = cls.search_deezer(artist_name)
        spotify_results = cls.search_spotify(artist_name)
        musicbrainz_results = cls.search_musicbrainz(artist_name)

        all_images = []
        for r in spotify_results:
            all_images.append(r)
        for r in deezer_results:
            all_images.append(r)

        return {
            "query": artist_name,
            "images": all_images,
            "musicbrainz": musicbrainz_results,
            "spotify_configured": bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET),
        }
