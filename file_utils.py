import re
import unicodedata
from pathlib import PurePath


def sanitize_filename(filename: str) -> str:
    normalized_name = unicodedata.normalize("NFKC", filename).replace("\\", "/")
    basename = PurePath(normalized_name).name
    stem, separator, suffix = basename.rpartition(".")

    if not separator:
        stem = basename
        suffix = ""

    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("._-")
    safe_stem = safe_stem or "uploaded"
    safe_suffix = ".pdf" if suffix.lower() == "pdf" else ".pdf"

    return f"{safe_stem}{safe_suffix}"
