"""Domain matching utility for detecting tracked domains in URLs."""
from urllib.parse import urlparse


def normalize_domain(url: str) -> str:
    """Normalize URL to bare domain: lowercase, strip www., strip trailing /."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return url.lower().strip("/")


def match_domain(url: str, targets: list[str]) -> bool:
    """Return True if the URL's domain matches any of the target domains."""
    host = normalize_domain(url)
    for target in targets:
        t = target.lower().strip()
        if t.startswith("www."):
            t = t[4:]
        if host == t or host.endswith("." + t):
            return True
    return False


def extract_domain(url: str) -> str:
    """Return the bare domain from a URL."""
    return normalize_domain(url)
