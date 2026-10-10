import ipaddress
import re
from pathlib import Path

from PySide6.QtCore import QUrl

AUDIO_EXTENSIONS = ("mp3", "wav", "flac", "ogg", "m4a", "aac", "opus")
VIDEO_EXTENSIONS = ("mp4", "mkv", "webm", "mov", "avi", "m4v")

STREAM_SCHEMES = ("http", "https", "rtsp", "rtmp", "mms", "udp")


def format_time(ms: int) -> str:
    total_seconds = max(0, ms) // 1000
    hours, rest = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def file_dialog_filter() -> str:
    audio = " ".join(f"*.{ext}" for ext in AUDIO_EXTENSIONS)
    video = " ".join(f"*.{ext}" for ext in VIDEO_EXTENSIONS)
    return (
        f"Media files ({audio} {video});;"
        f"Audio ({audio});;"
        f"Video ({video});;"
        "All files (*)"
    )


_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+([a-z]{2,63}|xn--[a-z0-9-]{1,59})$"
)


def _is_valid_host(host: str) -> bool:
    if host == "localhost" or _DOMAIN_RE.match(host):
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def parse_stream_url(text: str) -> tuple[QUrl | None, str]:
    text = text.strip()
    if not text or text.lower() in ("http://", "https://"):
        return None, "Enter a link."
    if any(ch.isspace() for ch in text):
        return None, "The link must not contain spaces."

    if "://" not in text:
        text = "https://" + text

    url = QUrl(text, QUrl.ParsingMode.StrictMode)
    if not url.isValid():
        return None, "The link contains invalid characters."

    scheme = url.scheme().lower()
    if scheme not in STREAM_SCHEMES:
        allowed = ", ".join(STREAM_SCHEMES)
        return None, f"Protocol \"{scheme}\" is not supported. Allowed: {allowed}."

    host = url.host(QUrl.ComponentFormattingOption.FullyEncoded).lower()
    if not host:
        return None, "The link has no server address."
    if not _is_valid_host(host):
        return None, f"\"{_pretty_host(url)}\" does not look like a server address (e.g. example.com)."
    return url, ""


def _pretty_host(url: QUrl) -> str:
    ace = url.host(QUrl.ComponentFormattingOption.FullyEncoded).encode()
    return QUrl.fromAce(ace, QUrl.AceProcessingOption.IgnoreIDNWhitelist)


def to_qurl(source: str) -> QUrl:
    url = QUrl(source.strip())
    if url.scheme().lower() in STREAM_SCHEMES or url.isLocalFile():
        return url
    return QUrl.fromLocalFile(str(Path(source).expanduser().resolve()))


def describe_source(url: QUrl) -> str:
    if url.isLocalFile():
        suffix = Path(url.toLocalFile()).suffix.lstrip(".").upper() or "file"
        return f"Local file · {suffix}"
    return f"Stream · {_pretty_host(url) or url.scheme()}"


def display_name(url: QUrl) -> str:
    if url.isLocalFile():
        return Path(url.toLocalFile()).stem
    return url.fileName() or _pretty_host(url) or url.toDisplayString()
