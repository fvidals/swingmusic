import xxhash
from unidecode import unidecode


def create_hash(*args: str, decode: bool = True) -> str:
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
