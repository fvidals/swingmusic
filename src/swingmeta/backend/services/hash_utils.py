import json
import re
from typing import Any, List, Tuple
from unidecode import unidecode
import xxhash

KEYWORDS = [
    "explicit", "360 audio", "anniversary", "diamond", "centennial", "gold", "platinum",
    "silver", "ultimate", "expanded", "extended", "deluxe", "super deluxe", "complete",
    "legacy", "special", "collector", "archive", "acoustic", "instrumental", "double disc",
    "double disk", "unplugged", "summer", "winter", "spring", "fall", "bonus", "bonus track",
    "original", " og ", "og ", "international", "uk version", "us version", "pa version",
    "limited", "mono", "stereo", "hi-res", "re-mix", "re-recorded", "rerecorded", "reissue",
    "remaster"
]
KEYWORD_PATTERN = re.compile(
    r"\s*[\(\[][^\)\]]*?(?:" + "|".join(re.escape(k) for k in KEYWORDS) + r")[^\)\]]*?[\)\]]$",
    re.IGNORECASE,
)


def clean_album_title(album: str) -> str:
    """
    Extracts the base album title without edition/version bracketed info.
    """
    if not album:
        return ""
    match = KEYWORD_PATTERN.search(album)
    if match:
        return album[:match.start()].strip()
    return album


def remove_prod(title: str) -> str:
    """
    Removes producer credits (e.g. prod. by) from song title.
    """
    if "prod." not in title.lower():
        return title
    if re.search(r"[()\[\]]", title):
        regex = r"\s?(\(|\[)prod\..*?(\)|\])\s?"
    else:
        regex = r"\s?\bprod\.\s*\S+"
    return re.sub(regex, "", title, flags=re.IGNORECASE).strip()


def clean_title(title: str) -> str:
    """
    Removes remaster tags from song title.
    """
    if "remaster" not in title.lower():
        return title
    rem_1 = re.sub(r"\s*[\\[(][^)\]]*remaster[^)\]]*[)\]]\s*", "", title, flags=re.IGNORECASE).strip()
    rem_2 = re.sub(r"\s-\s*[^-]*\bremaster[^-]*\s*", "", title, flags=re.IGNORECASE).strip()
    return rem_1 if len(rem_2) > len(rem_1) else rem_2


def parse_feat(title: str) -> Tuple[List[str], str]:
    """
    Extracts featured artists and base title.
    """
    regex = r"\((?:feat|ft|featuring|with)\.?\s+(.+?)\)"
    sqr_regex = r"\[(?:feat|ft|featuring|with)\.?\s+(.+?)\]"
    match = re.search(regex, title, re.IGNORECASE)
    if not match:
        match = re.search(sqr_regex, title, re.IGNORECASE)
        regex = sqr_regex
    if not match:
        return [], title
    artists_str = match.group(1)
    parts = re.split(r"[;/]+", artists_str)
    feat_artists = [p.strip() for p in parts if p.strip()]
    new_title = re.sub(regex, "", title, flags=re.IGNORECASE).strip()
    return feat_artists, new_title


def extract_artist_names(raw_artists: Any) -> List[str]:
    """
    Parses artist names from string (with separators / and ;) or JSON array.
    """
    if not raw_artists:
        return []
    if isinstance(raw_artists, list):
        return [a.get("name", "") if isinstance(a, dict) else str(a) for a in raw_artists if a]
    if isinstance(raw_artists, str):
        if raw_artists.startswith("["):
            try:
                arr = json.loads(raw_artists)
                return [a.get("name", "") if isinstance(a, dict) else str(a) for a in arr if a]
            except Exception:
                pass
        parts = re.split(r"[;/]+", raw_artists)
        return [p.strip() for p in parts if p.strip()]
    return [str(raw_artists)]


def create_hash(*args: str, decode: bool = False) -> str:
    """
    Creates a case-insensitive, non-alphanumeric chars ignoring hash
    from the given arguments (identical algorithm to SwingMusic).
    """

    def remove_non_alnum(token: str) -> str:
        token = token.lower().strip().replace(" ", "")
        t = "".join(t for t in token if t.isalnum())
        if t == "":
            return token
        return t

    str_ = "".join(remove_non_alnum(t) for t in args)

    if decode:
        str_ = unidecode(str_)

    return xxhash.xxh3_64(str_.encode("utf-8")).hexdigest()


def compute_runtime_trackhash(title: str, album: str, raw_artists: Any) -> str:
    """
    Computes the exact runtime trackhash that SwingMusic's TrackStore uses in memory.
    """
    if not title:
        return ""
    artists = extract_artist_names(raw_artists)
    feat_artists, clean_t = parse_feat(title)
    clean_t = remove_prod(clean_t)
    clean_t = clean_title(clean_t)
    for fa in feat_artists:
        if fa not in artists:
            artists.append(fa)
    clean_a = clean_album_title(album or "")
    return create_hash(clean_t, clean_a, *artists, decode=False)
