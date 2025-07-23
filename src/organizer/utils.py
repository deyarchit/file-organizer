import hashlib


def _calculate_md5(file_path: str) -> str:
    """Calculates the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def _calculate_short_sha256(file_path: str, length: int = 12) -> str:
    """
    Calculates a short SHA-256 hash of a file.
    Default length is 12 hex chars (~48 bits), customizable via `length`.
    """
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)
    return sha.hexdigest()[:length]
