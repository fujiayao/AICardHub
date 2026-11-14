from urllib.parse import unquote, urlsplit


def safe_url(value: str) -> str:
    if not value:
        return value
    if any(ord(c) < 32 for c in value) or "\\" in value:
        raise ValueError("invalid URL")
    parsed = urlsplit(value)
    if value.startswith("/files/") and not parsed.netloc and not parsed.scheme:
        decoded = unquote(parsed.path)
        if any(part in (".", "..") for part in decoded.split("/")) or "\\" in decoded:
            raise ValueError("unsafe file URL")
        return value
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("only http/https and /files/ URLs are allowed")
    return value
