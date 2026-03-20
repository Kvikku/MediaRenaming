"""Constants and regex patterns for media name normalization."""

from __future__ import annotations

import re

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts"}

SUBTITLE_EXTENSIONS = {".srt", ".sub", ".idx", ".ass", ".ssa"}

TOKEN_SET = {
    # Source / release type
    "bluray",
    "brrip",
    "bdrip",
    "webrip",
    "webdl",
    "web-dl",
    "web",
    "hdrip",
    "dvdrip",
    "dvdscr",
    "hdtv",
    "pdtv",
    "remux",
    # Streaming service tags
    "amzn",
    "nf",
    "dsnp",
    "atvp",
    "hmax",
    "pcok",
    "hulu",
    "crav",
    "pmtp",
    "iT",
    # Codecs
    "x264",
    "x265",
    "h264",
    "h265",
    "h 264",
    "h 265",
    "hevc",
    "avc",
    "xvid",
    "divx",
    "av1",
    # Audio
    "dts",
    "dtshd",
    "truehd",
    "atmos",
    "aac",
    "ac3",
    "eac3",
    "ddp",
    "dd",
    "ma",
    "flac",
    "lpcm",
    "2ch",
    "6ch",
    "8ch",
    # Video quality
    "hdr",
    "hdr10",
    "hdr10plus",
    "dv",
    "dolbyvision",
    "sdr",
    "10bit",
    "8bit",
    "uhd",
    "imax",
    "3d",
    # Container formats
    "mp4",
    "mkv",
    "avi",
    # Release tags
    "proper",
    "repack",
    "internal",
    "readnfo",
    "remastered",
    "extended",
    "unrated",
    "directors cut",
    "theatrical",
    "complete",
    # Language / multi tags
    "dual",
    "dualaudio",
    "dual-audio",
    "multi",
    "multisubs",
    # Encoder / reenc tags
    "reenc",
    "reencode",
}

NORMALIZED_TOKEN_SET = {re.sub(r"[^a-z0-9]+", "", token.lower()) for token in TOKEN_SET}

RESOLUTION_RE = re.compile(r"^\d{3,4}p$|^\d{1,2}k$")
FRAMERATE_RE = re.compile(r"^\d{2}(?:\.\d{1,3})?fps$")
AUDIO_CHANNEL_RE = re.compile(r"^\d\.\d$")
YEAR_RE = re.compile(r"^(19\d{2}|20\d{2})$")
BRACKET_RE = re.compile(r"\[[^\]]*\]|\{[^\}]*\}|<[^>]*>")
SEPARATOR_RE = re.compile(r"[._]+")
MULTISPACE_RE = re.compile(r"\s+")
TRAILING_GROUP_RE = re.compile(r"\s-\s[\w.]+$")
RELEASE_GROUP_RE = re.compile(r"(?<![SE]\d{2})-[A-Za-z][A-Za-z0-9]*\s*$")
LANGUAGE_TAG_RE = re.compile(
    r"\b(?:ger|eng|fre|fra|spa|ita|por|rus|jpn|kor|chi|zho|hin|ara|tur|pol|dut|nld|swe|nor|dan|fin|cze|ces|hun)"
    r"(?:[-](?:ger|eng|fre|fra|spa|ita|por|rus|jpn|kor|chi|zho|hin|ara|tur|pol|dut|nld|swe|nor|dan|fin|cze|ces|hun))*\b",
    re.IGNORECASE,
)
ORPHAN_PARENS_RE = re.compile(r"\(\s*\)")
METADATA_PARENS_RE = re.compile(r"\([^)]*\d{3,4}p[^)]*\)", re.IGNORECASE)
WEBSITE_RE = re.compile(r"(?:www\.)?[a-zA-Z0-9-]+\.(?:org|com|net|info|to|me|cc|io)\b", re.IGNORECASE)
COMPOUND_TOKEN_RE = re.compile(
    r"\bDDP?\d[\s.]\d\b|\bDD\+\d[\s.]\d\b"
    r"|\bAAC\d[\s.]\d\b"
    r"|\b[HhXx][\s.]?26[45]\b"
    r"|\b10[\s.]?bit\b|\b8[\s.]?bit\b"
    r"|\bHDR10(?:\+|plus)?\b|\bDTS[\s-]?HD\b"
    r"|\b\d[\s.]\d\b",
    re.IGNORECASE,
)
