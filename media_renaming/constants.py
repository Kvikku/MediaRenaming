"""Constants and regex patterns for media name normalization."""

from __future__ import annotations

import re

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov"}

TOKEN_SET = {
    "bluray",
    "brrip",
    "bdrip",
    "webrip",
    "webdl",
    "web-dl",
    "hdrip",
    "dvdrip",
    "remux",
    "x264",
    "x265",
    "h264",
    "h265",
    "hevc",
    "avc",
    "xvid",
    "divx",
    "dts",
    "dtshd",
    "truehd",
    "atmos",
    "aac",
    "ac3",
    "ddp",
    "dd",
    "ma",
    "hdr",
    "sdr",
    "10bit",
    "8bit",
    "proper",
    "repack",
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
