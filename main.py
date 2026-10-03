#!/usr/bin/env python3
from __future__ import annotations
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ShortnerBypass — Production-Ready Telegram Auto Link Bypass Bot
  Developer & Updates: @ProviderBotz
  Features:
    - Real Colored Inline Buttons (Bot API 9.4+ ButtonStyle: PRIMARY, SUCCESS, DANGER)
    - Telethon Userbot (DZHQ Group Flow + Alex DM Flow)
    - Dynamic Auto-Generated PUBLIC_URL
    - Promo/Ad Links Stripped (Preserving valid t.me destinations)
    - Obsidian Red Telegram Mini App + Flask Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import time
import re
import html
import json
import uuid
import secrets
import logging
import config
import config
import asyncio
import threading
import shutil
import platform
import stat
import subprocess
import base64
import urllib.request
import urllib.parse
from enum import Enum
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional, Dict, Any, List, Tuple, Union, Set, Callable, Sequence

import aiohttp
from flask import Flask, request, jsonify, send_file
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from telethon.errors import (
    FloodWaitError,
    PeerFloodError,
    UserDeactivatedBanError,
    AuthKeyError,
    RPCError
)

# ══════════════════════════════════════════════════════════════
#  ENV LOADER (.env support)
# ══════════════════════════════════════════════════════════════
def load_env(path: str = ".env"):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

load_env()

# ══════════════════════════════════════════════════════════════
#  GLOBAL LOGGING SETUP (Available to all modules immediately)
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ProviderBotz")
logging.getLogger("telethon").setLevel(logging.WARNING)

# ══════════════════════════════════════════════════════════════
#  MANUAL CONFIGURATION / ম্যানুয়াল কনফিগারেশন (সরাসরি কোডে পেস্ট করুন)
# ══════════════════════════════════════════════════════════════
# 🚀 1. MINI APP URL (মিনি অ্যাপ লিংক):
# কোড থেকেই সরাসরি আপনার টেলিগ্রাম মিনি অ্যাপ লিংক বা ওয়েব ডোমেইন পেস্ট করতে পারেন:
# উদাহরণ: "https://t.me/YourBot/app" অথবা "https://your-domain.run.app"
# যদি ফাঁকা ("") থাকে, তবে এটি অটো-ডিটেক্ট বা হোস্টিং এনভায়রনমেন্ট ভ্যারিয়েবল (PUBLIC_URL) ব্যবহার করবে।
MANUAL_MINI_APP_URL: str = "https://codenestauth2.onrender.com/live/u13-linkzov4bot-987d39"  # 👈 PASTE YOUR MINI APP LINK HERE MANUALLY!

# 👥 2. DZHQ GROUP (ডিজেডএইচকিউ গ্রুপ আইডি / ইউজারনেম):
# DZHQ Bot (@DZHQ_BypassBot) মডারদের নিয়মানুযায়ী শুধুমাত্র অনুমোদিত গ্রুপে কাজ করে (DM-এ কাজ করে না)।
# আপনার অনুমোদিত DZHQ গ্রুপের আইডি (যেমন: -1001234567890) বা ইউজারনেম (যেমন: "my_dzhq_group") পেস্ট করুন:
# যদি ফাঁকা থাকে, তবে DZHQ গ্রুপ ছাড়া চলবে না এবং প্রাইভেট DM-এর জন্য Alex DM স্বয়ংক্রিয়ভাবে ব্যবহৃত হবে।
MANUAL_DZHQ_GROUP: Union[int, str, None] = None  # 👈 PASTE DZHQ GROUP ID (-100xxxx) OR USERNAME HERE!

# 🖼️ 3. START MESSAGE IMAGE (স্টার্ট মেসেজের ফটো / ব্যানার লিংক):
# টেলিগ্রাম /start মেসেজের সাথে সুন্দর ব্যানার বা ফটো যুক্ত করার জন্য নিচে ছবির লিংক দিন (URL e.g. Telegraph/Imgur/CDN link):
# ডিফল্ট: র্যান্ডম এনিমে গার্ল আর্ট (v4.0)
MANUAL_START_IMAGE_URL: str = "https://api.aniwallpaper.workers.dev/random?type=girl"  # 👈 PASTE START IMAGE / BANNER URL HERE!

# 👑 4. OWNER ID (বট ওনার আইডি):
MANUAL_OWNER_ID: Union[int, str, None] = 7931847651  # 👈 YOUR TELEGRAM ID HERE (e.g. 7931847651)

# ══════════════════════════════════════════════════════════════
#  SYSTEM CONFIGURATION & CREDENTIALS
# ══════════════════════════════════════════════════════════════
DEVELOPER = "@LazyProvider"
BRAND_NAME = "ProviderBotz"
OFFICIAL_CHANNEL = "https://t.me/ProviderBotz"
FSUB_CHANNEL = os.environ.get("FSUB_CHANNEL", "@ProviderBotz").strip()

# Public Bot Credentials
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8678804822:AAHgbpb6q40Yvjw-SeZVyZicW2BXk-1kS0E").strip()
BOT_USERNAME = os.environ.get("BOT_USERNAME", "TheLinkzoBot").strip().lstrip("@")

# Owner ID Priority: MANUAL_OWNER_ID (in code) -> OWNER_ID (env var)
_raw_owner = MANUAL_OWNER_ID if MANUAL_OWNER_ID is not None and str(MANUAL_OWNER_ID).strip() else os.environ.get("OWNER_ID", "7931847651").strip()
OWNER_ID = int(_raw_owner) if str(_raw_owner).isdigit() else 7931847651

# Start Message Image Priority: MANUAL_START_IMAGE_URL (in code) -> START_IMAGE_URL (env var)
START_IMAGE_URL: str = (MANUAL_START_IMAGE_URL or os.environ.get("START_IMAGE_URL", "")).strip()

bot_api: Optional[Any] = None

# Telethon Userbot Credentials
TELEGRAM_API_ID_RAW = os.environ.get("TELEGRAM_API_ID", "36805393").strip()
TELEGRAM_API_ID = int(TELEGRAM_API_ID_RAW) if TELEGRAM_API_ID_RAW.isdigit() else 36805393
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "cfd5ff24d915c1691d88b0f3b51b96f5").strip()
TELEGRAM_SESSION = os.environ.get("TELEGRAM_SESSION", "1BVtsOIEBu4aGtZ5tO0oVs4oK6qbC997f6X0rLwOP1JQd9jeVtdq-xI49Rpr95rE5b0Wrg0ues8_NaiCZJe-ZJ-tCcYdBmImREowuBCsDjq1zNRbeOIEL0Z0L6-nBdYkoDPsXuuqLv4t27daPhbvwzm8RusQKcjMj5S8p7kuG4J7KzKAaRZiT1uwGA6-3nUP6XU24ZxB_7BsBXkUqJJVYi29CxHdt6_Xo2_UVpXA1amPO3ifuy9MbfC0ikLRfF-KxlXtStgIBSZqHrE1yxLe8BxHN2XAM0EitlNhD_lPPBV7znBNFKHBZjZTl4Ey40lR6-qx0ipRlwYT7LZn6oCxKy0secDH1McM=").strip()

# External Bypass Bots (Supports DZHQ Group & Alex DM)
DZHQ_BOT = os.environ.get("DZHQ_BOT_USERNAME", "@DZHQ_BypassBot").strip()

# DZHQ Group Priority: MANUAL_DZHQ_GROUP (Code) -> DZHQ_GROUP (Environment Variable)
_raw_dzhq_grp = MANUAL_DZHQ_GROUP if MANUAL_DZHQ_GROUP is not None and str(MANUAL_DZHQ_GROUP).strip() else os.environ.get("DZHQ_GROUP", "-1003644908415").strip()
if _raw_dzhq_grp:
    try:
        DZHQ_GROUP: Optional[Union[int, str]] = int(str(_raw_dzhq_grp).strip())
    except ValueError:
        DZHQ_GROUP = str(_raw_dzhq_grp).strip()
else:
    DZHQ_GROUP = None

ALEX_BOT = os.environ.get("ALEX_BOT_USERNAME", "@alexbypassbot").strip()

# Web Server & Port Configuration
PORT = int(os.environ.get("PORT", "5000"))
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ProviderPro").strip()

# Dynamic Public URL Detection & Cloudflare Quick Tunnel
_CURRENT_PUBLIC_URL: Optional[str] = None
_TUNNEL_PROC: Optional[subprocess.Popen] = None
_TUNNEL_LOCK = threading.Lock()

def get_cloudflared_path() -> Optional[str]:
    """Find or download a standalone cloudflared binary for the host OS & architecture."""
    which_cf = shutil.which("cloudflared")
    if which_cf and os.path.exists(which_cf):
        return which_cf

    base_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(base_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    system = platform.system().lower()
    machine = platform.machine().lower()
    bin_name = "cloudflared.exe" if system == "windows" else "cloudflared"

    local_path = os.path.join(bin_dir, bin_name)
    if os.path.exists(local_path) and os.access(local_path, os.X_OK):
        return local_path

    tmp_path = f"/tmp/{bin_name}"
    if os.path.exists(tmp_path) and os.access(tmp_path, os.X_OK):
        return tmp_path

    base_url = "https://github.com/cloudflare/cloudflared/releases/latest/download"
    download_url = None

    if system == "linux":
        if machine in ("x86_64", "amd64"):
            download_url = f"{base_url}/cloudflared-linux-amd64"
        elif machine in ("aarch64", "arm64"):
            download_url = f"{base_url}/cloudflared-linux-arm64"
        elif "arm" in machine:
            download_url = f"{base_url}/cloudflared-linux-arm"
    elif system == "darwin":
        download_url = f"{base_url}/cloudflared-darwin-amd64.tgz"
    elif system == "windows":
        download_url = f"{base_url}/cloudflared-windows-amd64.exe"

    if not download_url:
        return None

    try:
        logger.info(f"🌐 Auto-downloading Cloudflare Quick Tunnel binary for {system}-{machine}...")
        try:
            urllib.request.urlretrieve(download_url, local_path)
            os.chmod(local_path, os.stat(local_path).st_mode | stat.S_IEXEC | stat.S_IRUSR)
            return local_path
        except Exception:
            urllib.request.urlretrieve(download_url, tmp_path)
            os.chmod(tmp_path, os.stat(tmp_path).st_mode | stat.S_IEXEC | stat.S_IRUSR)
            return tmp_path
    except Exception as e:
        logger.warning(f"⚠️ Could not auto-download cloudflared: {e}")
        return None

def start_auto_tunnel(port: int) -> Optional[str]:
    """Start cloudflared tunnel to expose local port to a real public HTTPS URL."""
    global _TUNNEL_PROC, _CURRENT_PUBLIC_URL
    if _CURRENT_PUBLIC_URL and not _CURRENT_PUBLIC_URL.startswith("http://localhost"):
        return _CURRENT_PUBLIC_URL

    cf_bin = get_cloudflared_path()
    if not cf_bin:
        return None

    try:
        cmd = [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{port}"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        _TUNNEL_PROC = proc

        start_time = time.time()
        tunnel_url = None
        while time.time() - start_time < 12:
            line = proc.stderr.readline()
            if not line and proc.poll() is not None:
                break
            m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if m:
                tunnel_url = m.group(0)
                _CURRENT_PUBLIC_URL = tunnel_url
                logger.info(f"🚀 Real Public Cloudflare HTTPS URL generated: {tunnel_url}")
                break

        def _drain():
            while proc.poll() is None:
                try:
                    proc.stderr.readline()
                except Exception:
                    break
        threading.Thread(target=_drain, daemon=True, name="CloudflaredDrain").start()

        return tunnel_url
    except Exception as e:
        logger.warning(f"⚠️ Failed to launch cloudflared tunnel: {e}")
        return None

def get_auto_public_url() -> str:
    """Return the dynamically resolved or manually pasted public URL for the Mini App and webhooks."""
    global _CURRENT_PUBLIC_URL

    # 1. Manual paste in code (Highest priority)
    if MANUAL_MINI_APP_URL and MANUAL_MINI_APP_URL.strip():
        url = MANUAL_MINI_APP_URL.strip().rstrip("/")
        _CURRENT_PUBLIC_URL = url
        return url

    if _CURRENT_PUBLIC_URL and not _CURRENT_PUBLIC_URL.startswith("http://localhost"):
        return _CURRENT_PUBLIC_URL

    # 2. Environment variables for Mini App / Web App
    for env_key in ("MINI_APP_URL", "WEBAPP_URL", "PUBLIC_URL", "APP_URL"):
        env_val = os.environ.get(env_key, "").strip().rstrip("/")
        if env_val and not env_val.startswith("http://localhost"):
            _CURRENT_PUBLIC_URL = env_val
            return _CURRENT_PUBLIC_URL

    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
    if render_url:
        _CURRENT_PUBLIC_URL = render_url
        return _CURRENT_PUBLIC_URL

    railway_url = os.environ.get("RAILWAY_STATIC_URL", "").strip().rstrip("/") or os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip().rstrip("/")
    if railway_url:
        if not railway_url.startswith("http"):
            railway_url = f"https://{railway_url}"
        _CURRENT_PUBLIC_URL = railway_url
        return _CURRENT_PUBLIC_URL

    koyeb_url = os.environ.get("KOYEB_PUBLIC_DOMAIN", "").strip().rstrip("/")
    if koyeb_url:
        if not koyeb_url.startswith("http"):
            koyeb_url = f"https://{koyeb_url}"
        _CURRENT_PUBLIC_URL = koyeb_url
        return _CURRENT_PUBLIC_URL

    # Auto create a real public URL if on localhost or no external domain
    with _TUNNEL_LOCK:
        if not _CURRENT_PUBLIC_URL or _CURRENT_PUBLIC_URL.startswith("http://localhost"):
            tunnel_url = start_auto_tunnel(PORT)
            if tunnel_url:
                _CURRENT_PUBLIC_URL = tunnel_url
                return _CURRENT_PUBLIC_URL

    return f"http://localhost:{PORT}"

# Timeouts
BYPASS_IDLE_TIMEOUT_SEC = float(os.environ.get("BYPASS_IDLE_TIMEOUT_SEC", "30"))
ALEX_DM_TIMEOUT_SEC = float(os.environ.get("ALEX_DM_TIMEOUT_SEC", "75"))
MAX_BYPASS_TIMEOUT_SEC = float(os.environ.get("MAX_BYPASS_TIMEOUT_SEC", "120"))

# Rate Limiting & User Concurrency
RATE_LIMIT_SECONDS = float(os.environ.get("RATE_LIMIT_SECONDS", "3"))
MAX_CONCURRENT_PER_USER = int(os.environ.get("MAX_CONCURRENT_PER_USER", "2"))
TRACE_BOTS = os.environ.get("TRACE_BOTS", "false").lower() in ("true", "1", "yes")

# ══════════════════════════════════════════════════════════════
#  PYROGRAM & BOT API 9.4+ REAL COLORED BUTTON STYLE SYSTEM
# ══════════════════════════════════════════════════════════════
class ButtonStyle(str, Enum):
    """
    Telegram Bot API 9.4+ Native Colored Button Styles:
    - PRIMARY: 🔵 Dark Blue / Accent (bg_primary)
    - SUCCESS: 🟢 Green (bg_success)
    - DANGER:  🔴 Red (bg_danger)
    """
    PRIMARY = "primary"  # 🔵 Dark Blue / Accent
    SUCCESS = "success"  # 🟢 Green
    DANGER = "danger"    # 🔴 Red

class InlineKeyboardButton:
    """Inline Keyboard Button supporting Bot API 9.4+ native colors and Pyrogram syntax."""
    def __init__(
        self,
        text: str,
        url: Optional[str] = None,
        callback_data: Optional[str] = None,
        web_app: Optional[Dict[str, str]] = None,
        style: Optional[Union[ButtonStyle, str]] = None
    ):
        self.text = text
        self.url = url
        self.callback_data = callback_data
        self.web_app = web_app
        if isinstance(style, ButtonStyle):
            self.style = style.value
        else:
            self.style = style

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"text": self.text}
        if self.url:
            d["url"] = self.url
        if self.callback_data:
            d["callback_data"] = self.callback_data
        if self.web_app:
            d["web_app"] = self.web_app
        if self.style:
            d["style"] = self.style
        return d

class InlineKeyboardMarkup:
    """Inline Keyboard Markup containing rows of InlineKeyboardButtons."""
    def __init__(self, inline_keyboard: List[List[InlineKeyboardButton]]):
        self.inline_keyboard = inline_keyboard

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inline_keyboard": [
                [btn.to_dict() if isinstance(btn, InlineKeyboardButton) else btn for btn in row]
                for row in self.inline_keyboard
            ]
        }

# ══════════════════════════════════════════════════════════════
#  MANDATORY SMALL-CAPS UNICODE ALPHABET
#  ᴧ ʙ ᴄ ᴅ є ꜰ ɢ ʜ ι ᴊ ᴋ ʟ ᴍ ɴ σ ᴩ ǫ ʀ ѕ т υ ν ω ᥊ ʏ ᴢ
# ══════════════════════════════════════════════════════════════
SMALL_CAPS_MAP = {
    'a': 'ᴧ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'є', 'f': 'ꜰ',
    'g': 'ɢ', 'h': 'ʜ', 'i': 'ι', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ',
    'm': 'ᴍ', 'n': 'ɴ', 'o': 'σ', 'p': 'ᴩ', 'q': 'ǫ', 'r': 'ʀ',
    's': 'ѕ', 't': 'т', 'u': 'υ', 'v': 'ν', 'w': 'ω', 'x': '᥊',
    'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴧ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'є', 'F': 'ꜰ',
    'G': 'ɢ', 'H': 'ʜ', 'I': 'ι', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ',
    'M': 'ᴍ', 'N': 'ɴ', 'O': 'σ', 'P': 'ᴩ', 'Q': 'ǫ', 'R': 'ʀ',
    'S': 'ѕ', 'T': 'т', 'U': 'υ', 'V': 'ν', 'W': 'ω', 'X': '᥊',
    'Y': 'ʏ', 'Z': 'ᴢ'
}

def to_small_caps(text: str) -> str:
    """Transform string into the mandatory ProviderBotz small-caps font."""
    return "".join(SMALL_CAPS_MAP.get(c, c) for c in text)

def _trace(provider: str, message: str):
    if TRACE_BOTS:
        logger.info(f"[TRACE][{provider}] {message}")

# ══════════════════════════════════════════════════════════════
#  PROMO & JUNK URL FILTERING (ALLOWING LEGITIMATE T.ME DESTINATIONS)
# ══════════════════════════════════════════════════════════════
_PROMO_USERNAMES = {
    "dzhqbypass",
    "dzhq_official",
    "dzhq_bypassbot",
    "alexmodz",
    "alexbypassbot",
    "apkamitrr",
    "nick_bypass_bot"
}

def clean_url(u: str) -> str:
    """Normalize extracted URLs and remove sentence punctuation from edges."""
    if not u:
        return ""
    cleaned = re.sub(r'[\*`\'\"✔️✅]+', '', u).strip()
    return cleaned.rstrip('.,;:!?)>]\'"}').strip()

def normalize_for_comparison(u: str) -> str:
    """Normalize URL for identical comparison (strips scheme and trailing slash)."""
    if not u:
        return ""
    u = clean_url(u).lower()
    u = re.sub(r'^https?://', '', u)
    u = re.sub(r'^www\.', '', u)
    return u.rstrip('/')

def is_same_url(u1: str, u2: str) -> bool:
    """Check if two URLs resolve to the exact same link."""
    n1 = normalize_for_comparison(u1)
    n2 = normalize_for_comparison(u2)
    if not n1 or not n2:
        return False
    return n1 == n2

def is_valid_bypassed_destination(url: str, original_url: str) -> bool:
    """
    Strictly verifies that a candidate URL is a true final bypassed destination.
    Allows ALL legitimate destination domains (including valid t.me posts/files/bots,
    mega.nz, Google Drive, direct links), while strictly filtering out:
    - Identical input links
    - Telegram share action buttons
    - External bypass providers' own promotional ads and channels
    """
    if not url or not url.startswith(("http://", "https://")):
        return False
    if is_same_url(url, original_url):
        return False

    try:
        parsed = urllib.parse.urlsplit(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path.strip("/")

        # 1. Reject Telegram share intent action links
        if "share/url" in url.lower():
            return False

        # 2. Handle Telegram URLs (t.me, telegram.me, telegram.dog)
        if any(tg_host in host for tg_host in ("t.me", "telegram.me", "telegram.dog")):
            segments = [s.lower() for s in path.split("/") if s]
            if segments:
                first_seg = segments[0].lstrip("@")
                # Reject only known external provider promo channels & bots
                if first_seg in _PROMO_USERNAMES:
                    return False
            # Valid Telegram destinations:
            # - t.me/c/... (Private channel/group file)
            # - t.me/ChannelName/123 (Public channel post/file)
            # - t.me/SomeBot?start=xyz (Bot download link)
            # - t.me/+InviteCode (Private invite link)
            return True

        # 3. Reject provider promo websites
        if any(promo in host for promo in ("dzhq", "alexmodz")):
            return False

        return True
    except Exception:
        return False

def extract_valid_urls_from_text(text: str, original_url: str = "") -> List[str]:
    """Extract valid http/https URLs from a block of text, stripping promo links."""
    if not text:
        return []
    raw_urls = re.findall(r'https?://[^\s\n\)\]>"\']+', text)
    result = []
    for r in raw_urls:
        c = clean_url(r)
        if is_valid_bypassed_destination(c, original_url):
            if c not in result:
                result.append(c)
    return result

def extract_query_param_redirect(target_url: str) -> Optional[str]:
    """Unwrap destination URLs hidden in query parameters, including base64 and nested encodings."""
    try:
        parsed = urllib.parse.urlsplit(target_url)
        qs = urllib.parse.parse_qs(parsed.query)
        for key in ('url', 'link', 'dest', 'destination', 'target', 'go', 'to', 'r', 'u', 'redirect', 'out', 'next', 'dl', 'file', 'download'):
            if key in qs:
                for val in qs[key]:
                    val = val.strip()
                    if val.startswith(('http://', 'https://')):
                        if is_valid_bypassed_destination(val, target_url):
                            return val
                    # Try base64 decoding
                    try:
                        pad = '=' * ((4 - len(val) % 4) % 4)
                        b64 = base64.b64decode((val + pad).encode('ascii')).decode('utf-8', errors='ignore').strip()
                        if b64.startswith(('http://', 'https://')):
                            if is_valid_bypassed_destination(b64, target_url):
                                return b64
                    except Exception:
                        pass
    except Exception:
        pass
    return None

async def fast_direct_bypass(target_url: str) -> Optional[str]:
    """
    High-speed direct unshortening and redirect bypass engine:
    1. Query param & Base64 parameter decoding
    2. Multi-hop HTTP redirect following with modern browser headers
    3. HTML meta-refresh & window.location JavaScript redirect extraction
    """
    # 1. Parameter extraction
    param_res = extract_query_param_redirect(target_url)
    if param_res:
        return param_res

    # 2. HTTP redirect follow
    current = target_url
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            for _ in range(8):
                try:
                    async with session.get(current, allow_redirects=False) as resp:
                        loc = resp.headers.get("Location")
                        if loc and resp.status in (301, 302, 303, 307, 308):
                            cand = urllib.parse.urljoin(current, loc)
                            if cand != target_url:
                                current = cand
                                continue

                        if resp.status == 200:
                            text = await resp.text(errors="ignore")
                            # Meta refresh
                            m_meta = re.search(r'<meta[^>]*http-equiv=["\']?refresh["\']?[^>]*content=["\']?[0-9]*;\s*url=([^"\'>]+)', text, re.I)
                            if m_meta:
                                cand = urllib.parse.urljoin(current, m_meta.group(1).strip())
                                if is_valid_bypassed_destination(cand, target_url):
                                    current = cand
                                    continue

                            # JS location
                            m_js = re.search(r'window\.location(?:\.href|\.replace)?\s*=\s*["\'](https?://[^"\']+)["\']', text, re.I)
                            if m_js:
                                cand = m_js.group(1).strip()
                                if is_valid_bypassed_destination(cand, target_url):
                                    current = cand
                                    continue
                        break
                except Exception:
                    break
    except Exception:
        pass

    if current != target_url and is_valid_bypassed_destination(current, target_url):
        return current

    return None

def sanitize_and_validate_outbound_link(url_str: str) -> Optional[str]:
    """
    Strictly validates and formats an outgoing target link before sending to Alex DM or DZHQ.
    Guarantees that:
    1. NEVER sends commands (/start, /help, etc.), plain text, emojis, or chat messages.
    2. Accepts:
       - URLs starting with http:// or https:// (with valid domain name & TLD)
       - Bare domain links like 'example.com/shortner' or 'droplink.co/abc', which are normalized to 'https://example.com/shortner'
    3. Rejects invalid, dangerous, empty, or non-link strings so the Telethon account stays 100% safe.
    """
    if not url_str or not isinstance(url_str, str):
        return None
    raw = url_str.strip()
    if not raw or raw.startswith(('/', '@', '!', '.', '#', '$')):
        return None

    # 1. URLs starting with http:// or https://
    if raw.startswith(('http://', 'https://')):
        m = re.match(r'^https?://([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d+)?(/.*)?$', raw, re.IGNORECASE)
        if m:
            host = m.group(1).lower()
            if not host.startswith(('t.me', 'telegram.me', 'telegram.dog')):
                return raw
        return None

    # 2. Bare domain links (e.g. droplink.co/xyz, example.com/shortner)
    m_bare = re.match(r'^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d+)?(/.*)?$', raw, re.IGNORECASE)
    if m_bare:
        host = m_bare.group(1).lower()
        if not host.startswith(('t.me', 'telegram.me', 'telegram.dog')):
            return f"https://{raw}"

    return None

# ══════════════════════════════════════════════════════════════
#  PARSERS (DZHQ GROUP & ALEX DM)
# ══════════════════════════════════════════════════════════════

# DZHQ Regexes
_RX_IN = re.compile(r'In\s+Link[^:\n]*?:-\s*\*{0,4}\s*(https?://[^\s*\n]+)', re.I)
_RX_GOT = re.compile(r'Got\s+Result[^:\n]*?:-\s*\*{0,4}\s*(https?://[^\s*\n]+)', re.I)
_RX_ERR = re.compile(
    r'invalid\s*link|not\s*support|unsupported|no\s*script|not\s*found|'
    r'error|failed|cannot|wrong|sorry|got\s+error',
    re.I
)
_RX_RATE = re.compile(r'rate\s*limit|flood|wait\s*\d+|try\s*again', re.I)
_RX_INTERMEDIATE = re.compile(
    r'^[\*\s]*bypass(?:ing)?\.{0,6}[\*\s]*$'
    r'|^[\*\s]*processing\.{0,6}[\*\s]*$'
    r'|^[\*\s]*please\s*wait[\*\s]*$'
    r'|^[\*\s]*fetching[\*\s]*$'
    r'|^[\*\s]*checking[\*\s]*$'
    r'|bypassing\.\.\.'
    r'|processing\.\.\.'
    r'|checking link\.\.\.'
    r'|almost done\.\.\.'
    r'|bypass started',
    re.I | re.M
)
_RX_GOT_ERR = re.compile(r'Got\s+Error[^:\n]*?:-\s*[`*\s]*(.*?)\s*[`*]*\s*$', re.I | re.M)
_RX_SEP = re.compile(r'━{3,}.*?✦.*?━{3,}')

def parse_dzhq_message(text: str, entities: list, sent_link: str) -> List[Dict[str, Any]]:
    """Parse DZHQ bot Telegram group response, rejecting promo links."""
    if not text:
        return [{"status": "empty"}]
    stripped = text.strip()

    if _RX_INTERMEDIATE.search(stripped) and len(stripped) < 200:
        return [{"status": "intermediate", "raw": stripped[:80]}]

    if _RX_RATE.search(text):
        return [{"status": "rate_limit", "error": "Rate limited by DZHQ bot"}]

    if _RX_ERR.search(text):
        err_m = _RX_GOT_ERR.search(text)
        clean_err = clean_url(err_m.group(1)) if err_m else stripped[:120]
        return [{"status": "failed", "error": clean_err}]

    ent_urls = []
    if entities:
        for ent in entities:
            off = getattr(ent, 'offset', None)
            lng = getattr(ent, 'length', None)
            url = getattr(ent, 'url', None)
            if not url:
                if isinstance(ent, MessageEntityUrl) and off is not None and lng:
                    url = text[off:off + lng]
                else:
                    continue
            url = clean_url(url)
            if is_valid_bypassed_destination(url, sent_link):
                ent_urls.append((url, url))

    results = []
    blocks = _RX_SEP.split(text)
    blocks = [b.strip() for b in blocks if b.strip()]
    for block in blocks:
        if 'Powered By' in block and 'DZHQBypass' in block and len(block) < 80:
            continue
        r = _parse_dzhq_block(block, ent_urls, sent_link)
        if r:
            results.append(r)

    if not results:
        r = _parse_dzhq_block(text, ent_urls, sent_link)
        if r:
            results.append(r)

    if not results:
        return [{"status": "no_link", "error": "No valid bypassed link found", "raw": text[:300]}]
    return results

def _parse_dzhq_block(block: str, ent_urls: list, sent_link: str) -> Optional[Dict[str, Any]]:
    original = None

    m_in = _RX_IN.search(block)
    if m_in:
        original = clean_url(m_in.group(1))

    # Priority 1: Exact "Got Result :-" link is the ONLY authentic destination
    m_got = _RX_GOT.search(block)
    if m_got:
        u = clean_url(m_got.group(1))
        if is_valid_bypassed_destination(u, sent_link):
            return {
                "status": "ok",
                "original": original or sent_link,
                "bypassed": u,
                "all_bypassed": [u]
            }

    # Priority 2: Fallback only if no Got Result pattern matched
    bypassed = []
    for _, url in ent_urls:
        if is_valid_bypassed_destination(url, sent_link) and url not in bypassed:
            bypassed.append(url)

    if not bypassed:
        for u in extract_valid_urls_from_text(block, sent_link):
            if u not in bypassed:
                bypassed.append(u)

    if not bypassed:
        return None

    return {
        "status": "ok",
        "original": original or sent_link,
        "bypassed": bypassed[0],
        "all_bypassed": bypassed
    }

# ══════════════════════════════════════════════════════════════
#  ALEX BOT PARSER (TELEGRAM DM ONLY)
# ══════════════════════════════════════════════════════════════
_SMALLCAPS_FOLD_MAP = {
    'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ꜰ': 'f', 'ɢ': 'g', 'ʜ': 'h', 'ɪ': 'i', 'ᴊ': 'j',
    'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴩ': 'p', 'ᴘ': 'p', 'q': 'q', 'ǫ': 'q', 'ʀ': 'r',
    'ꜱ': 's', 'ѕ': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'x': 'x', 'ʏ': 'y', 'ᴢ': 'z', 'є': 'e',
    'σ': 'o', 'υ': 'u', 'ν': 'v', 'ω': 'w', '᥊': 'x', 'ι': 'i'
}

def fold_small_caps(s: str) -> str:
    """Fold small-caps Unicode characters into plain ASCII for regex matching."""
    return ''.join(_SMALLCAPS_FOLD_MAP.get(ch, ch) for ch in (s or ''))

_RX_ALEX_BYPASSED = re.compile(r'bypass(?:ed)?\s*link[^:\n]*:?-?\s*\**\s*\n?\s*(https?://\S+)', re.I)
_RX_ALEX_PROGRESS = re.compile(
    r'initialis|initializ|fetching|scanning|bypassing\s*security|cracking|decoding|solving|'
    r'processing|please\s*wait|\d{1,3}\s*%|[▰▱]|checking|working|loading|almost\s*done',
    re.I
)
_RX_ALEX_FAIL = re.compile(
    r'bypass\s*(?:failed|error)|invalid\s*link|not\s*support(?:ed)?|unsupported|'
    r'no\s*script|not\s*found|unable|unable\s+to|cannot|can[\'’]t|'
    r'could\s*not|couldn[\'’]t|not\s*possible|does\s*not\s*support|'
    r'doesn[\'’]t\s*support|failed|error',
    re.I
)

def parse_alex_message(text: str, entities: list, sent_link: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    stripped = text.strip()
    folded = fold_small_caps(stripped)

    if (
        _RX_ALEX_PROGRESS.search(folded)
        and not _RX_ALEX_BYPASSED.search(folded)
        and not _RX_ALEX_FAIL.search(folded)
    ):
        return {"status": "intermediate", "raw": stripped[:100]}

    if _RX_INTERMEDIATE.search(folded) and len(folded) < 140:
        return {"status": "intermediate", "raw": stripped[:100]}

    if _RX_RATE.search(folded):
        return {"status": "rate_limit", "error": "Alex bot rate limited", "raw": stripped[:200]}

    if _RX_ALEX_FAIL.search(folded) and not _RX_ALEX_BYPASSED.search(folded):
        return {"status": "failed", "error": stripped[:200], "raw": stripped[:200]}

    m = _RX_ALEX_BYPASSED.search(folded)
    if m:
        u = clean_url(m.group(1))
        if is_valid_bypassed_destination(u, sent_link):
            return {
                "status": "ok",
                "original": sent_link,
                "bypassed": u,
                "raw": stripped[:200]
            }

    urls_found = []
    if entities:
        for ent in entities:
            off = getattr(ent, 'offset', None)
            lng = getattr(ent, 'length', None)
            url = getattr(ent, 'url', None)
            if not url:
                if isinstance(ent, MessageEntityUrl) and off is not None and lng:
                    url = text[off:off + lng]
                else:
                    continue
            url = clean_url(url)
            if is_valid_bypassed_destination(url, sent_link) and url not in urls_found:
                urls_found.append(url)

    if not urls_found:
        for u in extract_valid_urls_from_text(text, sent_link):
            if u not in urls_found:
                urls_found.append(u)

    if urls_found:
        return {
            "status": "ok",
            "original": sent_link,
            "bypassed": urls_found[0],
            "all": urls_found,
            "raw": stripped[:200]
        }

    return None

# ══════════════════════════════════════════════════════════════
#  RUNTIME STATE & JOB ENGINE
# ══════════════════════════════════════════════════════════════
class JobState:
    WAITING = "WAITING"
    PROCESSING = "PROCESSING"
    RESULT_FOUND = "RESULT_FOUND"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"

def build_owner_log_markup(user_id: Optional[int], target_url: str, final_url: Optional[str] = None) -> Optional[InlineKeyboardMarkup]:
    """Generates direct DM button and quick link buttons for owner audit logs."""
    keyboard = []
    if user_id:
        keyboard.append([
            InlineKeyboardButton(f"👤 Direct DM User ({user_id})", url=f"tg://user?id={user_id}")
        ])
    row = []
    if final_url and final_url.startswith(("http://", "https://")):
        row.append(InlineKeyboardButton("🎯 Bypassed Link", url=final_url))
    if target_url and target_url.startswith(("http://", "https://")):
        row.append(InlineKeyboardButton("🔗 Original Link", url=target_url))
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard) if keyboard else None

class BypassEngine:
    def __init__(self):
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.jobs_lock = threading.Lock()
        self.user_active_jobs: Dict[int, int] = defaultdict(int)
        self.user_last_request: Dict[int, float] = {}
        self.rate_lock = threading.Lock()

        # Telethon Userbot & entity caches
        self.userbot: Optional[TelegramClient] = None
        self.userbot_connected = False
        self.alex_bot_id: Optional[int] = None
        self.dzhq_bot_id: Optional[int] = None
        self.dzhq_group_entity: Any = None

        # FIFO Queue for Alex DM jobs
        self.alex_dm_queue: List[str] = []
        self.alex_queue_lock = threading.Lock()

        # Telethon Anti-Flood, Rate-Limiting & Account Ban Protection
        self.telethon_send_lock: Optional[asyncio.Lock] = None
        self.telethon_last_send_ts: float = 0.0
        self.telethon_floodwait_until: float = 0.0
        self.telethon_min_interval: float = 2.5  # Safe pacing (at least 2.5s between sends) to prevent account bans

        # Statistics
        self.total_bypasses = 0
        self.successful_bypasses = 0
        self.failed_bypasses = 0
        self.start_time = time.time()

    def get_telethon_send_lock(self) -> asyncio.Lock:
        if self.telethon_send_lock is None:
            self.telethon_send_lock = asyncio.Lock()
        return self.telethon_send_lock

    def check_user_rate_limit(self, user_id: int) -> Tuple[bool, str]:
        with self.rate_lock:
            now = time.time()
            last_ts = self.user_last_request.get(user_id, 0)
            if now - last_ts < RATE_LIMIT_SECONDS:
                wait_sec = round(RATE_LIMIT_SECONDS - (now - last_ts), 1)
                return False, f"⏳ Rate limit reached. Please wait {wait_sec}s before sending another link."

            if self.user_active_jobs[user_id] >= MAX_CONCURRENT_PER_USER:
                return False, f"⚠️ You have {self.user_active_jobs[user_id]} active bypass jobs. Please wait for them to finish."

            self.user_last_request[user_id] = now
            self.user_active_jobs[user_id] += 1
            return True, ""

    def release_user_job(self, user_id: int):
        with self.rate_lock:
            if self.user_active_jobs[user_id] > 0:
                self.user_active_jobs[user_id] -= 1

    def create_job(self, url: str, user_id: Optional[int] = None, source: str = "auto", first_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        job_id = secrets.token_hex(8)
        job = {
            "id": job_id,
            "url": url,
            "user_id": user_id,
            "first_name": first_name or "User",
            "state": JobState.WAITING,
            "status_msg": "Initializing...",
            "provider": None,
            "created_at": time.time(),
            "last_activity_ts": time.time(),
            "final_url": None,
            "error": None,
            "event": asyncio.Event(),
            "dzhq_sent_id": None,
            "alex_sent_id": None,
            "source_origin": source
        }
        with self.jobs_lock:
            self.active_jobs[job_id] = job
        return job_id, job

    def cleanup_job(self, job_id: str):
        with self.jobs_lock:
            job = self.active_jobs.pop(job_id, None)

        if job and job.get("user_id"):
            self.release_user_job(job["user_id"])

        with self.alex_queue_lock:
            if job_id in self.alex_dm_queue:
                self.alex_dm_queue.remove(job_id)

    async def log_to_owner(self, text: str, reply_markup: Optional[Union[InlineKeyboardMarkup, Dict[str, Any]]] = None):
        logger.info(f"[OWNER LOG] {text}")
        if bot_api and OWNER_ID:
            try:
                await bot_api.send_message(
                    OWNER_ID,
                    f"🛡 <b>[ProviderBotz Audit v4.0]</b>\n\n{text}",
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            except Exception as e:
                _trace("LOG", f"Failed to deliver log to owner: {e}")

engine = BypassEngine()

async def safe_telethon_send(
    entity: Any,
    message_text: str,
    reply_to: Optional[int] = None,
    enforce_link_safety: bool = True
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Safely sends a message via Telethon Userbot with:
    1. Comprehensive FloodWaitError handling & automatic backoff.
    2. PeerFloodError detection & cooldown.
    3. Strict Link-Safety enforcement (NEVER sends /start, chat commands, or plain text to Alex Bot/DZHQ).
    4. Anti-Flood Human Pacing (minimum 2.5s delay between sends) with asyncio lock.
    Returns: (sent_message_object, error_description)
    """
    if not engine.userbot or not engine.userbot_connected:
        return None, "Telethon Userbot is not connected."

    # 1. Link-Safety Check if target is Alex Bot or external bypasser
    if enforce_link_safety:
        cleaned_link = sanitize_and_validate_outbound_link(message_text)
        if not cleaned_link:
            logger.warning(f"🛡️ [SAFETY SHIELD] Refused to send invalid non-link payload to userbot peer: {repr(message_text[:40])}")
            return None, "Payload was not a valid URL (safety rule: only http/https or domain links permitted)."
        message_text = cleaned_link

    # 2. Check if global FloodWait cooldown is still active
    now = time.time()
    if now < engine.telethon_floodwait_until:
        wait_left = int(engine.telethon_floodwait_until - now)
        if wait_left > 30:
            logger.warning(f"⚠️ [TELETHON FLOODWAIT] Active FloodWait cooldown ({wait_left}s remaining). Skipping request to protect account.")
            return None, f"Telegram FloodWait is active ({wait_left}s remaining). Request postponed to protect userbot."
        else:
            _trace("SAFETY", f"Sleeping {wait_left}s for active FloodWait cooldown...")
            await asyncio.sleep(wait_left + 1)

    send_lock = engine.get_telethon_send_lock()
    async with send_lock:
        # Enforce minimum delay since last send to simulate natural human activity
        time_since_last = time.time() - engine.telethon_last_send_ts
        if time_since_last < engine.telethon_min_interval:
            delay_needed = engine.telethon_min_interval - time_since_last
            _trace("SAFETY", f"Pacing userbot send: sleeping {delay_needed:.2f}s...")
            await asyncio.sleep(delay_needed)

        # Attempt sending with FloodWait protection and retry
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                sent = await engine.userbot.send_message(entity, message_text, reply_to=reply_to)
                engine.telethon_last_send_ts = time.time()
                return sent, None
            except FloodWaitError as e:
                wait_sec = int(getattr(e, 'seconds', 10))
                logger.warning(f"⚠️ [TELETHON FLOODWAIT ERROR] Telegram returned FloodWait: wait {wait_sec}s! Account protection initiated.")
                engine.telethon_floodwait_until = time.time() + wait_sec + 2

                if wait_sec <= 30 and attempt == 0:
                    logger.info(f"⏳ Waiting {wait_sec + 2}s before safe retry...")
                    await asyncio.sleep(wait_sec + 2)
                    continue
                else:
                    return None, f"Telegram FloodWait triggered ({wait_sec}s). Operation aborted to safeguard user account."
            except PeerFloodError as e:
                logger.error(f"⚠️ [TELETHON PEER FLOOD] Telegram flagged peer message rate. Cooldown 120s set to prevent ban: {e}")
                engine.telethon_floodwait_until = time.time() + 120.0
                return None, "Telegram PeerFlood rate-limit detected. Cooldown activated to prevent account restriction."
            except UserDeactivatedBanError as e:
                logger.critical(f"❌ [ACCOUNT BANNED] Telethon user account was deactivated or banned by Telegram: {e}")
                engine.userbot_connected = False
                return None, "Userbot account is banned or deactivated by Telegram."
            except Exception as e:
                err_str = str(e)
                if "FLOOD_WAIT" in err_str.upper():
                    m = re.search(r'FLOOD_WAIT_?(\d+)', err_str, re.I)
                    wait_sec = int(m.group(1)) if m else 15
                    engine.telethon_floodwait_until = time.time() + wait_sec + 2
                    logger.warning(f"⚠️ [FLOOD_WAIT DETECTED] Wait {wait_sec}s recorded.")
                    return None, f"Telegram FloodWait active ({wait_sec}s)."
                logger.error(f"❌ Userbot send_message failed: {e}")
                return None, f"Userbot send error: {e}"

    return None, "Failed to send message after retries."

# ══════════════════════════════════════════════════════════════
#  USERBOT TELEGRAM HANDLERS (DZHQ GROUP/DM + ALEX DM)
# ══════════════════════════════════════════════════════════════
def setup_userbot_handlers(client: TelegramClient):
    """
    DZHQ operates in DZHQ_GROUP (if configured) or via direct DM with DZHQ_BOT.
    Alex operates in private DM.
    """

    # 1. DZHQ Handler — Operates in authorized Telegram group (as restricted by DZHQ modders)
    async def on_dzhq_message(event):
        msg = event.message
        # Telethon Message: use text or message or raw_text safely without raising AttributeError
        text = getattr(msg, 'text', None) or getattr(msg, 'message', None) or getattr(msg, 'raw_text', '') or ""
        if not text:
            return

        sender_id = event.sender_id
        is_dzhq_sender = bool(engine.dzhq_bot_id and sender_id == engine.dzhq_bot_id)
        
        is_group_msg = bool(DZHQ_GROUP and (event.chat_id == DZHQ_GROUP or (engine.dzhq_group_entity and event.chat_id == engine.dzhq_group_entity.id)))
        is_private_msg = bool(event.is_private and (is_dzhq_sender or (engine.dzhq_bot_id and event.chat_id == engine.dzhq_bot_id)))

        if not is_group_msg and not is_private_msg:
            return

        # If in group, verify message came from DZHQ bot or contains DZHQ signature
        if is_group_msg and not is_dzhq_sender:
            sender = await event.get_sender()
            s_username = (getattr(sender, 'username', '') or '').lower()
            if s_username == DZHQ_BOT.lstrip('@').lower() or getattr(sender, 'is_bot', False):
                is_dzhq_sender = True
                if not engine.dzhq_bot_id:
                    engine.dzhq_bot_id = sender_id
            elif not any(k in text for k in ('DZHQBypass', 'Got Result', 'In Link', 'Got Error', 'Bypassing...')):
                return

        rt_obj = getattr(msg, 'reply_to', None)
        reply_to_id = getattr(rt_obj, 'reply_to_msg_id', None) if rt_obj else None

        target_job = None
        with engine.jobs_lock:
            for job in engine.active_jobs.values():
                if job.get("provider") == "dzhq" and job["state"] in (JobState.WAITING, JobState.PROCESSING):
                    # 1. Exact match with the sent /b message
                    if reply_to_id and job.get("dzhq_sent_id") == reply_to_id:
                        target_job = job
                        break
                    # 2. Or reply to previous message in reply chain for this job
                    elif reply_to_id and job.get("dzhq_last_msg_id") == reply_to_id:
                        target_job = job
                        break
                    # 3. Or if original link is mentioned in the text
                    elif job.get("url") and job["url"] in text:
                        target_job = job
                        break
            # 4. If only one active DZHQ job in progress in the group
            if not target_job and is_group_msg:
                active_dzhq = [j for j in engine.active_jobs.values() if j.get("provider") == "dzhq" and j["state"] in (JobState.WAITING, JobState.PROCESSING)]
                if len(active_dzhq) == 1:
                    target_job = active_dzhq[0]

        if not target_job:
            return

        target_job["dzhq_last_msg_id"] = msg.id

        parsed = parse_dzhq_message(text, msg.entities or [], target_job["url"])
        status = parsed[0].get("status") if parsed else "empty"
        _trace("DZHQ", f"Job {target_job['id']} update: status={status}")

        target_job["last_activity_ts"] = time.time()

        if status == "intermediate":
            target_job["state"] = JobState.PROCESSING
            target_job["status_msg"] = "⏳ ᴘʀσᴄєѕѕιɴɢ... (DZHQ bypass)"
            return

        # Auto-click Delete button on DZHQ result message
        buttons = getattr(msg, 'buttons', None)
        if buttons:
            async def _click_delete():
                try:
                    for row in buttons:
                        for btn in row:
                            bt = (getattr(btn, 'text', '') or '').lower()
                            if any(k in bt for k in ('delete', '🗑', '❌')):
                                await btn.click()
                                _trace("DZHQ", "Auto-clicked delete button on result")
                                return
                except Exception as e:
                    _trace("DZHQ", f"Delete button click error: {e}")
            asyncio.create_task(_click_delete())

        if status == "ok" and parsed[0].get("bypassed"):
            bypassed_link = parsed[0]["bypassed"]
            if is_valid_bypassed_destination(bypassed_link, target_job["url"]):
                target_job["final_url"] = bypassed_link
                target_job["provider"] = "dzhq"
                target_job["state"] = JobState.RESULT_FOUND
                target_job["event"].set()
        elif status in ("failed", "rate_limit", "no_link"):
            target_job["error"] = parsed[0].get("error", "DZHQ failed to bypass link")
            target_job["state"] = JobState.FAILED
            target_job["event"].set()

    client.add_event_handler(on_dzhq_message, events.NewMessage())
    client.add_event_handler(on_dzhq_message, events.MessageEdited())

    # 2. Alex DM Handler — STRICTLY IN PRIVATE DM
    async def on_alex_message(event):
        msg = event.message
        # Telethon Message: use text or message or raw_text safely without raising AttributeError
        text = getattr(msg, 'text', None) or getattr(msg, 'message', None) or getattr(msg, 'raw_text', '') or ""
        if not text:
            return

        sender_id = event.sender_id
        if engine.alex_bot_id and sender_id != engine.alex_bot_id:
            return

        with engine.alex_queue_lock:
            if not engine.alex_dm_queue:
                return
            target_job_id = engine.alex_dm_queue[0]

        with engine.jobs_lock:
            target_job = engine.active_jobs.get(target_job_id)

        if not target_job or target_job["state"] not in (JobState.WAITING, JobState.PROCESSING):
            with engine.alex_queue_lock:
                if engine.alex_dm_queue and engine.alex_dm_queue[0] == target_job_id:
                    engine.alex_dm_queue.pop(0)
            return

        incoming_id = getattr(msg, "id", None)
        sent_id = target_job.get("alex_sent_id")
        if sent_id and incoming_id and incoming_id <= sent_id:
            return

        parsed = parse_alex_message(text, msg.entities or [], target_job["url"])
        _trace("ALEX_DM", f"Job {target_job['id']} Alex message received: parsed={parsed}")

        target_job["last_activity_ts"] = time.time()

        if not parsed or parsed.get("status") == "intermediate":
            target_job["state"] = JobState.PROCESSING
            target_job["status_msg"] = "🔄 ʙʏᴘᴀѕѕιɴɢ... (Alex DM solving)"
            return

        if parsed.get("status") == "ok" and parsed.get("bypassed"):
            with engine.alex_queue_lock:
                if engine.alex_dm_queue and engine.alex_dm_queue[0] == target_job_id:
                    engine.alex_dm_queue.pop(0)

            bypassed_link = parsed["bypassed"]
            if is_valid_bypassed_destination(bypassed_link, target_job["url"]):
                target_job["final_url"] = bypassed_link
                target_job["provider"] = "alex_dm"
                target_job["state"] = JobState.RESULT_FOUND
                target_job["event"].set()
        elif parsed.get("status") in ("failed", "rate_limit"):
            with engine.alex_queue_lock:
                if engine.alex_dm_queue and engine.alex_dm_queue[0] == target_job_id:
                    engine.alex_dm_queue.pop(0)

            target_job["error"] = parsed.get("error", "Alex DM bypass failed")
            target_job["state"] = JobState.FAILED
            target_job["event"].set()

    client.add_event_handler(on_alex_message, events.NewMessage(incoming=True, func=lambda e: e.is_private))
    client.add_event_handler(on_alex_message, events.MessageEdited(incoming=True, func=lambda e: e.is_private))

# ══════════════════════════════════════════════════════════════
#  BYPASS WORKFLOW EXECUTOR
# ══════════════════════════════════════════════════════════════
async def execute_bypass_job(job_id: str) -> Dict[str, Any]:
    with engine.jobs_lock:
        job = engine.active_jobs.get(job_id)
    if not job:
        return {"status": False, "message": "Job not found"}

    target_url = job["url"]
    t0 = time.time()

    # Priority 0: Check fast direct redirect / query parameter unshortener
    try:
        fast_res = await fast_direct_bypass(target_url)
        if fast_res and is_valid_bypassed_destination(fast_res, target_url):
            duration_ms = int((time.time() - t0) * 1000)
            engine.total_bypasses += 1
            engine.successful_bypasses += 1
            job["state"] = JobState.RESULT_FOUND
            job["final_url"] = fast_res
            job["provider"] = "direct_resolver"

            user_id_val = job.get("user_id")
            first_name_val = job.get("first_name") or "User"
            first_name_esc = html.escape(str(first_name_val))
            user_mention = f'<a href="tg://user?id={user_id_val}">{first_name_esc}</a> [<code>{user_id_val}</code>]' if user_id_val else f"<code>{first_name_esc}</code>"
            log_entry = (
                f"✅ <b>Bypass Success (Direct Fast v4.0)</b>\n"
                f"• User: {user_mention}\n"
                f"• Provider: <code>DIRECT_FAST</code>\n"
                f"• Time: <code>{duration_ms}ms</code>\n"
                f"• Original: {target_url}\n"
                f"• Destination: {fast_res}"
            )
            asyncio.create_task(engine.log_to_owner(log_entry, reply_markup=build_owner_log_markup(user_id_val, target_url, fast_res)))

            return {
                "status": True,
                "developer": DEVELOPER,
                "response_ms": f"{duration_ms}ms",
                "source": "direct_resolver",
                "url": fast_res,
                "links": {
                    "original": target_url,
                    "bypassed": fast_res
                }
            }
    except Exception as e:
        _trace("DIRECT", f"Pre-check direct bypass exception: {e}")

    if not engine.userbot or not engine.userbot_connected:
        job["state"] = JobState.FAILED
        job["error"] = "Telethon Userbot is offline. Please configure TELEGRAM_SESSION, TELEGRAM_API_ID, and TELEGRAM_API_HASH in your hosting settings (.env)."
        logger.warning(f"⚠️ Bypass job {job_id} aborted: Telethon Userbot is not connected.")
        return {
            "status": False,
            "developer": DEVELOPER,
            "message": job["error"],
            "response_ms": "0ms"
        }

    # Provider Selection & Modder Policy:
    # DZHQ Bot (@DZHQ_BypassBot) only operates in authorized groups (modder restriction, DM is disabled).
    has_dzhq_group = bool(engine.dzhq_group_entity or DZHQ_GROUP)
    is_alex_favored = any(k in target_url.lower() for k in ("urlking", "monteolympus", "alex", "shortx"))

    if not has_dzhq_group:
        # Without an authorized group, DZHQ cannot be used (modders allow only group execution).
        # Fall back directly to Alex DM without wasting timeout on DZHQ.
        _trace("ENGINE", "DZHQ group is not configured (DZHQ bot modders require authorized group). Using Alex DM.")
        primary_provider = "alex_dm"
        fallback_provider = None
    elif is_alex_favored:
        primary_provider = "alex_dm"
        fallback_provider = "dzhq"
    else:
        primary_provider = "dzhq"
        fallback_provider = "alex_dm"

    providers_to_try = [p for p in (primary_provider, fallback_provider) if p]
    last_error_detail = None

    for current_provider in providers_to_try:
        job["provider"] = current_provider
        job["state"] = JobState.PROCESSING
        job["event"].clear()
        job["last_activity_ts"] = time.time()

        _trace("ENGINE", f"Executing job {job_id} on {current_provider}")

        try:
            if current_provider == "dzhq":
                group_target = engine.dzhq_group_entity if engine.dzhq_group_entity else DZHQ_GROUP
                if not group_target:
                    _trace("ENGINE", "Skipping DZHQ: group not configured. DZHQ bot modders require an authorized group.")
                    last_error_detail = "DZHQ bot requires an authorized Telegram group (modder restriction). Set MANUAL_DZHQ_GROUP in bot.py."
                    continue

                clean_target = sanitize_and_validate_outbound_link(target_url)
                if not clean_target:
                    last_error_detail = "Invalid target URL format (only valid web/domain links allowed)."
                    continue

                sent, send_err = await safe_telethon_send(group_target, f"/b {clean_target}", enforce_link_safety=False)
                if not sent or send_err:
                    _trace("ENGINE", f"DZHQ group send failed: {send_err}")
                    last_error_detail = f"Could not send to DZHQ group: {send_err}"
                    continue
                job["dzhq_sent_id"] = sent.id
                _trace("ENGINE", f"Sent /b {clean_target} to DZHQ group (msg id {sent.id})")

            elif current_provider == "alex_dm":
                clean_target = sanitize_and_validate_outbound_link(target_url)
                if not clean_target:
                    last_error_detail = "Invalid target URL format. Alex Bypass Bot strictly accepts links starting with http://, https://, or domain/path."
                    continue

                with engine.alex_queue_lock:
                    engine.alex_dm_queue.append(job_id)

                sent, send_err = await safe_telethon_send(ALEX_BOT, clean_target, enforce_link_safety=True)
                if not sent or send_err:
                    with engine.alex_queue_lock:
                        if engine.alex_dm_queue and engine.alex_dm_queue[0] == job_id:
                            engine.alex_dm_queue.pop(0)
                    _trace("ENGINE", f"Alex DM send failed: {send_err}")
                    last_error_detail = f"Could not send to {ALEX_BOT}: {send_err}"
                    continue
                job["alex_sent_id"] = sent.id
                _trace("ENGINE", f"Sent {clean_target} to {ALEX_BOT} in DM (msg id {sent.id})")

            provider_timeout = ALEX_DM_TIMEOUT_SEC if current_provider == "alex_dm" else BYPASS_IDLE_TIMEOUT_SEC
            while time.time() - t0 < MAX_BYPASS_TIMEOUT_SEC:
                now = time.time()
                if now - job["last_activity_ts"] > provider_timeout:
                    _trace("ENGINE", f"Provider {current_provider} idle timeout ({provider_timeout}s)")
                    last_error_detail = f"Provider {current_provider} timed out after {provider_timeout}s without response"
                    break

                try:
                    await asyncio.wait_for(asyncio.shield(job["event"].wait()), timeout=1.0)
                except asyncio.TimeoutError:
                    pass

                if job["state"] in (JobState.RESULT_FOUND, JobState.FAILED):
                    break

            if job["state"] == JobState.RESULT_FOUND and job.get("final_url"):
                duration_ms = int((time.time() - t0) * 1000)
                engine.total_bypasses += 1
                engine.successful_bypasses += 1

                user_id_val = job.get("user_id")
                first_name_val = job.get("first_name") or "User"
                first_name_esc = html.escape(str(first_name_val))

                if user_id_val:
                    user_mention = f'<a href="tg://user?id={user_id_val}">{first_name_esc}</a> [<code>{user_id_val}</code>]'
                else:
                    user_mention = f"<code>{first_name_esc}</code>"

                log_entry = (
                    f"✅ <b>Bypass Success</b>\n"
                    f"• User: {user_mention}\n"
                    f"• Provider: <code>{current_provider.upper()}</code>\n"
                    f"• Time: <code>{duration_ms}ms</code>\n"
                    f"• Original: {job['url']}\n"
                    f"• Destination: {job['final_url']}"
                )
                asyncio.create_task(engine.log_to_owner(log_entry, reply_markup=build_owner_log_markup(user_id_val, job['url'], job['final_url'])))

                return {
                    "status": True,
                    "developer": DEVELOPER,
                    "response_ms": f"{duration_ms}ms",
                    "source": current_provider,
                    "url": job["final_url"],
                    "links": {
                        "original": job["url"],
                        "bypassed": job["final_url"]
                    }
                }
            elif job["state"] == JobState.FAILED and job.get("error"):
                last_error_detail = job.get("error")

        except Exception as e:
            _trace("ENGINE", f"Provider {current_provider} send error: {e}")
            logger.error(f"❌ Failed to send message to {current_provider}: {e}")
            last_error_detail = f"Could not send message to {current_provider}: {e}"

        _trace("ENGINE", f"Primary {current_provider} did not resolve. Attempting fallback.")

    # Final fallback attempt using direct unshortener / redirect extractor
    try:
        deep_res = await fast_direct_bypass(target_url)
        if deep_res and is_valid_bypassed_destination(deep_res, target_url):
            duration_ms = int((time.time() - t0) * 1000)
            engine.total_bypasses += 1
            engine.successful_bypasses += 1
            job["state"] = JobState.RESULT_FOUND
            job["final_url"] = deep_res
            job["provider"] = "direct_resolver"

            user_id_val = job.get("user_id")
            first_name_val = job.get("first_name") or "User"
            first_name_esc = html.escape(str(first_name_val))
            user_mention = f'<a href="tg://user?id={user_id_val}">{first_name_esc}</a> [<code>{user_id_val}</code>]' if user_id_val else f"<code>{first_name_esc}</code>"
            log_entry = (
                f"✅ <b>Bypass Success (Deep Direct Resolver v4.0)</b>\n"
                f"• User: {user_mention}\n"
                f"• Provider: <code>DIRECT_DEEP</code>\n"
                f"• Time: <code>{duration_ms}ms</code>\n"
                f"• Original: {target_url}\n"
                f"• Destination: {deep_res}"
            )
            asyncio.create_task(engine.log_to_owner(log_entry, reply_markup=build_owner_log_markup(user_id_val, target_url, deep_res)))

            return {
                "status": True,
                "developer": DEVELOPER,
                "response_ms": f"{duration_ms}ms",
                "source": "direct_resolver",
                "url": deep_res,
                "links": {
                    "original": target_url,
                    "bypassed": deep_res
                }
            }
    except Exception:
        pass

    duration_ms = int((time.time() - t0) * 1000)
    engine.total_bypasses += 1
    engine.failed_bypasses += 1
    job["state"] = JobState.FAILED

    clean_err = last_error_detail or "Unable to bypass this link with active providers."
    if "unable to bypass" in clean_err.lower():
        clean_err = "Unable to bypass this link with active providers. The shortener domain is either unsupported, expired, or requires interactive captcha."

    user_id_val = job.get("user_id")
    first_name_val = job.get("first_name") or "User"
    first_name_esc = html.escape(str(first_name_val))

    if user_id_val:
        user_mention = f'<a href="tg://user?id={user_id_val}">{first_name_esc}</a> [<code>{user_id_val}</code>]'
    else:
        user_mention = f"<code>{first_name_esc}</code>"

    fail_log = (
        f"❌ <b>Bypass Failed</b>\n"
        f"• User: {user_mention}\n"
        f"• Original: {job['url']}\n"
        f"• Time: <code>{duration_ms}ms</code>\n"
        f"• Reason: {clean_err}"
    )
    asyncio.create_task(engine.log_to_owner(fail_log, reply_markup=build_owner_log_markup(user_id_val, job['url'], None)))

    return {
        "status": False,
        "developer": DEVELOPER,
        "message": clean_err,
        "response_ms": f"{duration_ms}ms"
    }

# ══════════════════════════════════════════════════════════════
#  CUSTOM REPLY TEXT / QUOTE PATCH (ZERO-ERROR RESILIENT)
# ══════════════════════════════════════════════════════════════
try:
    import pyrogram
    from pyrogram import types, enums
    from pyrogram.types import Message, LinkPreviewOptions, ReplyParameters
except (ImportError, AttributeError, Exception):
    class _ChatTypeDummy:
        PRIVATE = "private"
        GROUP = "group"
        SUPERGROUP = "supergroup"
        CHANNEL = "channel"

    class _EnumsDummy:
        ChatType = _ChatTypeDummy

    enums = _EnumsDummy()

    class LinkPreviewOptions:
        def __init__(self, is_disabled: bool = False, **kwargs):
            self.is_disabled = is_disabled

    class ReplyParameters:
        def __init__(self, message_id: int = None, story_id: int = None, chat_id = None, allow_sending_without_reply: bool = True, **kwargs):
            self.message_id = message_id
            self.story_id = story_id
            self.chat_id = chat_id
            self.allow_sending_without_reply = allow_sending_without_reply

    class _TypesDummy:
        class Message:
            pass

    types = _TypesDummy()

    class Message:
        pass

async def custom_reply_text(
    self: "types.Message",
    text: str,
    quote: bool = None,
    parse_mode=None,
    entities=None,
    disable_web_page_preview: bool = None,
    link_preview_options=None,
    disable_notification: bool = None,
    message_thread_id: int = None,
    reply_to_message_id: int = None,
    reply_to_story_id: int = None,
    reply_to_chat_id=None,
    schedule_date=None,
    protect_content: bool = None,
    reply_markup=None,
    **kwargs
):
    if quote is None:
        quote = getattr(getattr(self, "chat", None), "type", None) != getattr(getattr(enums, "ChatType", None), "PRIVATE", "private")
    if reply_to_message_id is None and reply_to_story_id is None and quote:
        reply_to_message_id = getattr(self, "id", None)

    if link_preview_options is None and disable_web_page_preview is not None:
        link_preview_options = LinkPreviewOptions(is_disabled=disable_web_page_preview)

    reply_parameters = None
    if reply_to_message_id or reply_to_story_id:
        try:
            reply_parameters = ReplyParameters(
                message_id=reply_to_message_id,
                story_id=reply_to_story_id,
                chat_id=reply_to_chat_id,
                allow_sending_without_reply=True
            )
        except TypeError:
            reply_parameters = ReplyParameters(
                message_id=reply_to_message_id,
                story_id=reply_to_story_id,
                chat_id=reply_to_chat_id,
            )

    client = getattr(self, "_client", None)
    if client and hasattr(client, "send_message"):
        return await client.send_message(
            chat_id=self.chat.id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            link_preview_options=link_preview_options,
            disable_notification=disable_notification,
            message_thread_id=message_thread_id,
            reply_parameters=reply_parameters,
            schedule_date=schedule_date,
            protect_content=protect_content,
            reply_markup=reply_markup,
            **kwargs
        )
    return None

Message.reply_text = custom_reply_text
Message.reply = custom_reply_text

def wrap_quote(text: str) -> str:
    """Wraps message text cleanly in Telegram HTML blockquote from start to end ensuring zero entity errors."""
    if not text:
        return ""
    stripped = text.strip()
    if stripped.startswith("<blockquote>") and stripped.endswith("</blockquote>"):
        return stripped
    return f"<blockquote>{stripped}</blockquote>"

# ══════════════════════════════════════════════════════════════
#  TELEGRAM BOT API (REAL COLORED BUTTONS VIA BOT API 9.4+)
# ══════════════════════════════════════════════════════════════
class TelegramBotAPI:
    """
    Direct Telegram Bot API client that natively sends Bot API 9.4+ button styles:
    - style: 'primary' (Dark Blue Accent)
    - style: 'success' (Emerald Green)
    - style: 'danger'  (Red)
    """
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=45))
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def call(self, method: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session = await self.get_session()
        url = f"{self.base_url}/{method}"
        try:
            async with session.post(url, json=data or {}) as resp:
                result = await resp.json()
                # Handle Telegram Bot API 429 Flood Wait gracefully
                if not result.get("ok") and result.get("error_code") == 429:
                    retry_after = result.get("parameters", {}).get("retry_after", 3)
                    logger.warning(f"⚠️ Telegram Flood Wait: sleeping {retry_after}s for {method}")
                    await asyncio.sleep(retry_after + 0.5)
                    async with session.post(url, json=data or {}) as retry_resp:
                        return await retry_resp.json()
                return result
        except Exception as e:
            _trace("BOT_API", f"Error calling {method}: {e}")
            return {"ok": False, "description": str(e)}

    async def get_me(self) -> Dict[str, Any]:
        return await self.call("getMe")

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: str,
        caption: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        reply_to_message_id: Optional[int] = None,
        parse_mode: str = "HTML",
        quote: bool = True
    ) -> Dict[str, Any]:
        """Send a photo with caption and native colored buttons."""
        cap_text = wrap_quote(caption) if (quote and parse_mode == "HTML" and caption) else (caption or "")
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": cap_text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup.to_dict()
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
            payload["reply_parameters"] = {
                "message_id": reply_to_message_id,
                "allow_sending_without_reply": True
            }
        res = await self.call("sendPhoto", payload)
        if not res.get("ok"):
            err_desc = res.get("description", "")
            # Fallback if reply message not found
            if "reply" in err_desc.lower() and ("reply_parameters" in payload or "reply_to_message_id" in payload):
                no_reply_payload = dict(payload)
                no_reply_payload.pop("reply_parameters", None)
                no_reply_payload.pop("reply_to_message_id", None)
                res = await self.call("sendPhoto", no_reply_payload)
            # Fallback if reply_markup styles not accepted
            elif "reply_markup" in payload:
                fallback_payload = dict(payload)
                fallback_payload["reply_markup"] = self._strip_styles(payload["reply_markup"])
                res = await self.call("sendPhoto", fallback_payload)
        return res

    async def edit_message_caption(
        self,
        chat_id: Union[int, str],
        message_id: int,
        caption: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "HTML",
        quote: bool = True
    ) -> Dict[str, Any]:
        """Edit caption of an existing photo/media message."""
        cap_text = wrap_quote(caption) if (quote and parse_mode == "HTML" and caption) else caption
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": cap_text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup.to_dict()
        res = await self.call("editMessageCaption", payload)
        if not res.get("ok"):
            err_desc = res.get("description", "")
            if "reply_markup" in payload:
                fallback_payload = dict(payload)
                fallback_payload["reply_markup"] = self._strip_styles(payload["reply_markup"])
                res = await self.call("editMessageCaption", fallback_payload)
        return res

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        reply_to_message_id: Optional[int] = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False,
        link_preview_options: Optional[Dict[str, Any]] = None,
        quote: bool = True
    ) -> Dict[str, Any]:
        msg_text = wrap_quote(text) if (quote and parse_mode == "HTML" and text) else text
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": msg_text,
            "parse_mode": parse_mode
        }
        if disable_web_page_preview:
            payload["disable_web_page_preview"] = True
            payload["link_preview_options"] = {"is_disabled": True}
        elif link_preview_options:
            payload["link_preview_options"] = link_preview_options
        if reply_markup:
            payload["reply_markup"] = reply_markup.to_dict()
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
            payload["reply_parameters"] = {
                "message_id": reply_to_message_id,
                "allow_sending_without_reply": True
            }
        res = await self.call("sendMessage", payload)
        if not res.get("ok"):
            err_desc = res.get("description", "")
            # 1. Fallback if quote or HTML entity parsing error occurs
            if "can't parse entities" in err_desc or "entity" in err_desc.lower():
                clean_payload = dict(payload)
                clean_payload["text"] = text.replace("<blockquote>", "").replace("</blockquote>", "")
                res = await self.call("sendMessage", clean_payload)
            # 2. Fallback if replied message not found
            elif "reply" in err_desc.lower() and ("reply_parameters" in payload or "reply_to_message_id" in payload):
                no_reply_payload = dict(payload)
                no_reply_payload.pop("reply_parameters", None)
                no_reply_payload.pop("reply_to_message_id", None)
                res = await self.call("sendMessage", no_reply_payload)
            # 3. Fallback if server does not accept style field on buttons
            elif "reply_markup" in payload:
                fallback_payload = dict(payload)
                fallback_payload["reply_markup"] = self._strip_styles(payload["reply_markup"])
                res = await self.call("sendMessage", fallback_payload)
        return res

    async def edit_message_text(
        self,
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False,
        link_preview_options: Optional[Dict[str, Any]] = None,
        quote: bool = True
    ) -> Dict[str, Any]:
        msg_text = wrap_quote(text) if (quote and parse_mode == "HTML" and text) else text
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": msg_text,
            "parse_mode": parse_mode
        }
        if disable_web_page_preview:
            payload["disable_web_page_preview"] = True
            payload["link_preview_options"] = {"is_disabled": True}
        elif link_preview_options:
            payload["link_preview_options"] = link_preview_options
        if reply_markup:
            payload["reply_markup"] = reply_markup.to_dict()
        res = await self.call("editMessageText", payload)
        if not res.get("ok"):
            err_desc = res.get("description", "")
            if "can't parse entities" in err_desc or "entity" in err_desc.lower():
                clean_payload = dict(payload)
                clean_payload["text"] = text.replace("<blockquote>", "").replace("</blockquote>", "")
                res = await self.call("editMessageText", clean_payload)
            elif "reply_markup" in payload:
                fallback_payload = dict(payload)
                fallback_payload["reply_markup"] = self._strip_styles(payload["reply_markup"])
                res = await self.call("editMessageText", fallback_payload)
        return res

    @staticmethod
    def _strip_styles(markup_dict: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(markup_dict, dict) or "inline_keyboard" not in markup_dict:
            return markup_dict
        new_keyboard = []
        for row in markup_dict.get("inline_keyboard", []):
            new_row = []
            for btn in row:
                if isinstance(btn, dict):
                    new_row.append({k: v for k, v in btn.items() if k != "style"})
                else:
                    new_row.append(btn)
            new_keyboard.append(new_row)
        return {"inline_keyboard": new_keyboard}

    async def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None, show_alert: bool = False) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        if show_alert:
            payload["show_alert"] = True
        return await self.call("answerCallbackQuery", payload)

    async def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> Dict[str, Any]:
        return await self.call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def delete_message(self, chat_id: Union[int, str], message_id: int) -> Dict[str, Any]:
        return await self.call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

bot_api: Optional[TelegramBotAPI] = None

def schedule_auto_delete(chat_id: int, message_id: int, delay_seconds: int = 120):
    """Automatically deletes a message after 2 minutes (120 seconds) completely silently without any warning."""
    async def _deleter():
        try:
            await asyncio.sleep(delay_seconds)
            if bot_api:
                await bot_api.delete_message(chat_id, message_id)
        except Exception:
            pass
    asyncio.create_task(_deleter())

# ══════════════════════════════════════════════════════════════
#  USER DATABASE & PERSISTENCE (FOR OWNER BROADCASTING)
# ══════════════════════════════════════════════════════════════
USER_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
_USERS_SET: set[int] = set()
_USERS_LOCK = threading.Lock()

def load_registered_users():
    """Load persistent list of bot users from disk."""
    global _USERS_SET
    with _USERS_LOCK:
        if os.path.exists(USER_DB_FILE):
            try:
                with open(USER_DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        _USERS_SET = set(int(x) for x in data if str(x).lstrip("-").isdigit())
            except Exception as e:
                logger.warning(f"Could not load users.json: {e}")
        if OWNER_ID:
            _USERS_SET.add(OWNER_ID)

def register_user(user_id: int):
    """Record an active user ID for broadcasts."""
    if not user_id or user_id <= 0:
        return
    with _USERS_LOCK:
        if user_id not in _USERS_SET:
            _USERS_SET.add(user_id)
            try:
                with open(USER_DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(_USERS_SET), f)
            except Exception as e:
                logger.warning(f"Could not save users.json: {e}")

def get_registered_users() -> List[int]:
    """Return all active users."""
    with _USERS_LOCK:
        return list(_USERS_SET)

# ══════════════════════════════════════════════════════════════
#  REAL COLORED BUTTON BUILDERS (PRIMARY, SUCCESS, DANGER)
# ══════════════════════════════════════════════════════════════
def get_start_buttons(user_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    Start screen buttons with REAL native Bot API 9.4 colored styles:
    - Mini App (Success / Green) - includes ?owner=true ONLY for the verified owner ID!
    - Help (Danger / Red) | About (Primary / Blue)
    """
    public_url = get_auto_public_url()
    buttons = []

    # If user is owner, append owner authorization flag so gear icon (⚙️) appears in Mini App
    is_owner = bool(user_id and OWNER_ID and user_id == OWNER_ID)
    app_url = public_url
    if app_url and not app_url.startswith("http://localhost"):
        sep = "&" if "?" in app_url else "?"
        if is_owner:
            app_url = f"{app_url}{sep}owner=true&uid={user_id}"
        elif user_id:
            app_url = f"{app_url}{sep}uid={user_id}"

    # Mini App Button (always present with start message)
    is_tme_link = bool(public_url and ("t.me/" in public_url or "telegram.me/" in public_url))
    if public_url and public_url.startswith("https://") and not is_tme_link:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 σᴩєɴ ᴍιɴι ᴧᴩᴩ 🚀",
                web_app={"url": app_url},
                style=ButtonStyle.SUCCESS
            )
        ])
    else:
        target_url = app_url if (app_url and not app_url.startswith("http://localhost")) else "https://t.me"
        buttons.append([
            InlineKeyboardButton(
                text="🚀 σᴩєɴ ᴍιɴι ᴧᴩᴩ 🚀",
                url=target_url,
                style=ButtonStyle.SUCCESS
            )
        ])

    # DANGER & PRIMARY ROW: ⛑️ Help (Red) | 👻 About (Blue)
    buttons.append([
        InlineKeyboardButton(
            text="⛑️ ʜєʟᴩ",
            callback_data="cmd_help",
            style=ButtonStyle.DANGER
        ),
        InlineKeyboardButton(
            text="ᴧʙσυт 👻",
            callback_data="cmd_about",
            style=ButtonStyle.PRIMARY
        )
    ])

    return InlineKeyboardMarkup(buttons)

# Retry cache for safe 64-byte Telegram callback_data
_RETRY_CACHE: Dict[str, str] = {}

def get_retry_callback_data(job_url: str) -> str:
    token = secrets.token_hex(6)
    _RETRY_CACHE[token] = job_url
    if len(_RETRY_CACHE) > 500:
        for k in list(_RETRY_CACHE.keys())[:100]:
            _RETRY_CACHE.pop(k, None)
    return f"retry:{token}"

def get_result_buttons(final_url: str, job_url: str) -> InlineKeyboardMarkup:
    """
    Final Result buttons with REAL native Bot API 9.4 colored styles:
    - SUCCESS: 🟢 Open Link (Green)
    - PRIMARY: 🔵 Copy Link via Mini App (Blue)
    - SUCCESS/PRIMARY: 🟣 ProviderBotz Channel (Alternating Accent)
    - PRIMARY/DANGER:  🔵 Retry (Blue) | 🔴 Close (Red)
    """
    public_url = get_auto_public_url()
    retry_cb = get_retry_callback_data(job_url)
    buttons = [
        # SUCCESS BUTTON: 🟢 Open Link
        [
            InlineKeyboardButton(
                text="🔗 ᴏᴩєɴ ʟιɴᴋ",
                url=final_url,
                style=ButtonStyle.SUCCESS
            )
        ]
    ]

    has_mini_app = bool(public_url and not public_url.startswith("http://localhost"))
    is_tme_link = bool(public_url and ("t.me/" in public_url or "telegram.me/" in public_url))
    if has_mini_app and not is_tme_link and public_url.startswith("https://"):
        # PRIMARY BUTTON: 🔵 Copy Link (Auto-copy in Mini App)
        mini_app_copy_url = f"{public_url}/?copy={urllib.parse.quote(final_url)}"
        buttons.append([
            InlineKeyboardButton(
                text="📋 ᴄσᴩʏ ʟιɴᴋ",
                web_app={"url": mini_app_copy_url},
                style=ButtonStyle.PRIMARY
            )
        ])

    # VIBRANT PROVIDERBOTZ TELEGRAM CHANNEL BUTTON (Distinct Color)
    buttons.append([
        InlineKeyboardButton(
            text="📢 ᴩʀσᴠιᴅєʀʙσтᴢ",
            url=OFFICIAL_CHANNEL,
            style=ButtonStyle.SUCCESS if has_mini_app else ButtonStyle.PRIMARY
        )
    ])

    # DISTINCT COLOR ROW: 🔵 Retry (Primary) | 🔴 Close (Danger)
    buttons.append([
        InlineKeyboardButton(
            text="🔄 ʀєтʀʏ ʙʏᴩᴧѕѕ",
            callback_data=retry_cb,
            style=ButtonStyle.PRIMARY
        ),
        InlineKeyboardButton(
            text="❌ ᴄʟσѕє",
            callback_data="cmd_close",
            style=ButtonStyle.DANGER
        )
    ])

    return InlineKeyboardMarkup(buttons)

def get_failed_buttons(job_url: str) -> InlineKeyboardMarkup:
    """Failure buttons with distinct, vibrant colors."""
    retry_cb = get_retry_callback_data(job_url)
    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 ʀєтʀʏ ʙʏᴩᴧѕѕ",
                callback_data=retry_cb,
                style=ButtonStyle.PRIMARY
            )
        ],
        [
            InlineKeyboardButton(
                text="⛑️ ʜєʟᴩ",
                callback_data="cmd_help",
                style=ButtonStyle.DANGER
            ),
            InlineKeyboardButton(
                text="👻 ᴧʙσυт",
                callback_data="cmd_about",
                style=ButtonStyle.SUCCESS
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 ʜσᴍє",
                callback_data="cmd_home",
                style=ButtonStyle.PRIMARY
            )
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_help_buttons() -> InlineKeyboardMarkup:
    """Help screen buttons with all 3 distinct native colors: Blue, Green, Red."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="📢 ᴩʀσᴠιᴅєʀʙσтᴢ ᴄʜᴧɴɴєʟ",
                url=OFFICIAL_CHANNEL,
                style=ButtonStyle.PRIMARY
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 ʜσᴍє",
                callback_data="cmd_home",
                style=ButtonStyle.SUCCESS
            ),
            InlineKeyboardButton(
                text="👻 ᴧʙσυт",
                callback_data="cmd_about",
                style=ButtonStyle.DANGER
            )
        ]
    ])

def get_about_buttons() -> InlineKeyboardMarkup:
    """About screen buttons with all 3 distinct native colors: Blue, Green, Red."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="📢 ᴩʀσᴠιᴅєʀʙσтᴢ ᴄʜᴧɴɴєʟ",
                url=OFFICIAL_CHANNEL,
                style=ButtonStyle.PRIMARY
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 ʜσᴍє",
                callback_data="cmd_home",
                style=ButtonStyle.SUCCESS
            ),
            InlineKeyboardButton(
                text="⛑️ ʜєʟᴩ",
                callback_data="cmd_help",
                style=ButtonStyle.DANGER
            )
        ]
    ])

def get_fsub_buttons() -> InlineKeyboardMarkup:
    """Force subscribe channel buttons with distinct styles."""
    chnl_url = f"https://t.me/{FSUB_CHANNEL.lstrip('@')}" if FSUB_CHANNEL else OFFICIAL_CHANNEL
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="📢 ᴊσιɴ ᴏꜰꜰιᴄιᴧʟ ᴄʜᴧɴɴєʟ",
                url=chnl_url,
                style=ButtonStyle.PRIMARY
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 ᴊσιɴєᴅ / ʀєтʀʏ",
                callback_data="cmd_fsub_check",
                style=ButtonStyle.SUCCESS
            )
        ]
    ])

def extract_input_url(data: Union[Dict[str, Any], str]) -> Optional[str]:
    """Extract any target URL from a Telegram message dict or string (handles plain text, caption, and entities)."""
    if isinstance(data, dict):
        text = (data.get("text") or data.get("caption") or "").strip()
        entities = data.get("entities") or data.get("caption_entities") or []
        for ent in entities:
            if ent.get("type") == "text_link" and ent.get("url"):
                u = clean_url(ent["url"])
                if is_valid_bypassed_destination(u, ""):
                    return u
            elif ent.get("type") == "url":
                offset = ent.get("offset", 0)
                length = ent.get("length", 0)
                if text and offset is not None and length:
                    u = clean_url(text[offset:offset + length])
                    if u and not u.startswith(('/start', '/help', '/about')):
                        return u
    else:
        text = str(data or "").strip()

    if not text:
        return None

    if text.startswith("/bypass"):
        text = text[len("/bypass"):].strip()

    # 1. Match full http/https URLs
    m = re.search(r'https?://[^\s\n\)\]>"\']+', text)
    if m:
        return clean_url(m.group(0))

    # 2. Match bare domain/path (e.g. droplink.co/abc, gplinks.co/xyz)
    m_bare = re.search(r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?', text)
    if m_bare:
        candidate = m_bare.group(0)
        if not candidate.startswith(('@', '/')) and '.' in candidate and not candidate.startswith(('t.me/', 'telegram.me/')):
            return "https://" + clean_url(candidate)
    return None

# ══════════════════════════════════════════════════════════════
#  TELEGRAM BOT WORKER & LONG POLLING (ALEX BYPASS BOT STYLE)
# ══════════════════════════════════════════════════════════════
# Anti-flood & rate limit cooldown tracking
_USER_MSG_TIMESTAMPS: Dict[int, float] = {}
_USER_WARN_COOLDOWN: Dict[int, float] = {}

async def process_user_link(chat_id: int, user_id: int, target_url: str, reply_msg_id: Optional[int] = None, first_name: Optional[str] = None):
    """
    Automatically bypasses links with dynamic animated progress frames
    and displays the final clean result formatted like @alexbypassbot (no raw JSON, no internal source leaked).
    """
    allowed, rate_msg = engine.check_user_rate_limit(user_id)
    if not allowed:
        now_ts = time.time()
        last_warn = _USER_WARN_COOLDOWN.get(user_id, 0)
        if now_ts - last_warn > 8.0:
            _USER_WARN_COOLDOWN[user_id] = now_ts
            await bot_api.send_message(chat_id, rate_msg, reply_to_message_id=reply_msg_id)
        return

    job_id, _ = engine.create_job(target_url, user_id=user_id, source="telegram", first_name=first_name)

    # Initial Animation Frame (10%)
    initial_frame = (
        f"🔄 <b>{to_small_caps('bypassing link...')}</b> [▰▱▱▱▱▱▱▱▱▱] 10%\n"
        f"🔍 <i>{to_small_caps('fetching link data...')}</i>"
    )
    initial_msg = await bot_api.send_message(
        chat_id,
        initial_frame,
        reply_to_message_id=reply_msg_id
    )
    status_msg_id = initial_msg.get("result", {}).get("message_id")

    stop_updater = asyncio.Event()

    async def _status_ticker():
        # Fast, responsive animation frames like AlexBypassBot
        frames = [
            (
                f"🔄 <b>{to_small_caps('bypassing link...')}</b> [▰▰▰▱▱▱▱▱▱▱] 35%\n"
                f"🔓 <i>{to_small_caps('bypassing security & captcha...')}</i>"
            ),
            (
                f"🔄 <b>{to_small_caps('bypassing link...')}</b> [▰▰▰▰▰▱▱▱▱▱] 60%\n"
                f"⚙️ <i>{to_small_caps('decoding shortlink tokens...')}</i>"
            ),
            (
                f"🔄 <b>{to_small_caps('bypassing link...')}</b> [▰▰▰▰▰▰▰▱▱▱] 80%\n"
                f"📡 <i>{to_small_caps('solving destination redirect...')}</i>"
            ),
            (
                f"🔄 <b>{to_small_caps('bypassing link...')}</b> [▰▰▰▰▰▰▰▰▰▱] 95%\n"
                f"✨ <i>{to_small_caps('verifying clean destination...')}</i>"
            )
        ]
        idx = 0
        while not stop_updater.is_set():
            await asyncio.sleep(1.2)
            if stop_updater.is_set():
                break
            if status_msg_id:
                try:
                    await bot_api.edit_message_text(chat_id, status_msg_id, frames[idx])
                except Exception:
                    pass
            idx = (idx + 1) % len(frames)

    ticker_task = asyncio.create_task(_status_ticker())

    try:
        result = await execute_bypass_job(job_id)
    finally:
        stop_updater.set()
        ticker_task.cancel()
        engine.cleanup_job(job_id)

    # Output formatted PROPERLY like AlexBypassBot message:
    # No raw JSON! No internal source name shown! Stylized fonts, no copycode on link, preview off, auto delete in 2 minutes!
    if result.get("status") is True and result.get("url"):
        final_url = result["url"]
        duration_ms = int(result.get("response_ms", "1000ms").replace("ms", ""))
        duration_formatted = f"{duration_ms / 1000:.1f}s" if duration_ms >= 1000 else f"{duration_ms}ms"

        res_text = (
            f"⚡ <b>{to_small_caps('Link Bypassed Successfully!')}</b>\n\n"
            f"🔗 <b>{to_small_caps('Original Link')}:</b>\n"
            f"{html.escape(target_url)}\n\n"
            f"🎯 <b>{to_small_caps('Bypassed Link')}:</b>\n"
            f"{html.escape(final_url)}\n\n"
            f"⏱ <b>{to_small_caps('Time Taken')}:</b> <code>{duration_formatted}</code>\n\n"
            f"👆 <i>{to_small_caps('Tap the bypassed link above to copy immediately!')}</i>"
        )
        reply_markup = get_result_buttons(final_url, target_url)
        sent_res = None
        if status_msg_id:
            try:
                sent_res = await bot_api.edit_message_text(
                    chat_id,
                    status_msg_id,
                    res_text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            except Exception:
                sent_res = await bot_api.send_message(
                    chat_id,
                    res_text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
        else:
            sent_res = await bot_api.send_message(
                chat_id,
                res_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

        # Auto delete in 2 minutes (120 seconds) as requested - completely silent, without warning
        final_msg_id = status_msg_id or (sent_res.get("result", {}).get("message_id") if isinstance(sent_res, dict) else None)
        if final_msg_id:
            schedule_auto_delete(chat_id, final_msg_id, 120)
        if reply_msg_id:
            schedule_auto_delete(chat_id, reply_msg_id, 120)
    else:
        err_msg = result.get("message") or "The link could not be bypassed or expired."
        is_userbot_offline = not engine.userbot_connected or "userbot is offline" in err_msg.lower() or "userbot is not connected" in err_msg.lower()

        if is_userbot_offline:
            err_text = (
                f"❌ <b>{to_small_caps('Bypass Failed!')}</b>\n\n"
                f"⚠️ <b>{to_small_caps('Telethon Userbot Offline')}</b>\n"
                f"<i>{to_small_caps('The bot cannot send links to bypass engines because Telethon Userbot is not connected.')}</i>\n\n"
                f"🔧 <b>{to_small_caps('How to Fix (Bot Owner)')}:</b>\n"
                f"• <i>{to_small_caps('Please set TELEGRAM_SESSION, TELEGRAM_API_ID, and TELEGRAM_API_HASH in your hosting environment (.env).')}</i>\n"
                f"• <i>{to_small_caps('Send /stats to check live Userbot & provider status.')}</i>\n\n"
                f"🔗 <b>{to_small_caps('Original Link')}:</b>\n"
                f"{html.escape(target_url)}"
            )
        else:
            err_text = (
                f"❌ <b>{to_small_caps('Bypass Failed!')}</b>\n\n"
                f"⚠️ <i>{to_small_caps(err_msg)}</i>\n\n"
                f"🔗 <b>{to_small_caps('Original Link')}:</b>\n"
                f"{html.escape(target_url)}\n\n"
                f"• <i>{to_small_caps('Please check if the link is active and valid.')}</i>\n"
                f"• <i>{to_small_caps('Tap Retry below to try bypassing again.')}</i>"
            )
        reply_markup = get_failed_buttons(target_url)
        if status_msg_id:
            try:
                await bot_api.edit_message_text(chat_id, status_msg_id, err_text, reply_markup=reply_markup, disable_web_page_preview=True)
            except Exception:
                await bot_api.send_message(chat_id, err_text, reply_markup=reply_markup, disable_web_page_preview=True)
        else:
            await bot_api.send_message(chat_id, err_text, reply_markup=reply_markup, disable_web_page_preview=True)

async def check_user_fsub(user_id: int) -> bool:
    """Check if user has joined the official channel @ProviderBotz."""
    if not FSUB_CHANNEL or not bot_api:
        return True
    try:
        res = await bot_api.get_chat_member(FSUB_CHANNEL, user_id)
        if res.get("ok"):
            status = res.get("result", {}).get("status", "")
            return status in ("creator", "administrator", "member", "restricted")
        return True
    except Exception as e:
        _trace("FSUB", f"Chat member check exception: {e} (allowing user)")
        return True

async def run_bot_polling():
    """Continuous async long-polling loop for the public bot."""
    global bot_api
    if not BOT_TOKEN:
        logger.warning("⚠️ BOT_TOKEN is missing. Public bot polling will not run.")
        return

    bot_api = TelegramBotAPI(BOT_TOKEN)
    me = await bot_api.get_me()
    if not me.get("ok"):
        logger.error(f"❌ Failed to connect to Telegram Bot API with BOT_TOKEN: {me.get('description')}")
        return

    global BOT_USERNAME
    bot_info = me.get("result", {})
    BOT_USERNAME = bot_info.get("username", BOT_USERNAME)
    logger.info(f"✅ Public Bot API online: @{BOT_USERNAME} (Bot API 9.4 Colored Buttons Enabled)")

    offset = 0
    while True:
        try:
            updates = await bot_api.call("getUpdates", {"offset": offset, "timeout": 25})
            if not updates.get("ok"):
                await asyncio.sleep(2)
                continue

            for u in updates.get("result", []):
                offset = max(offset, u["update_id"] + 1)

                # 1. Handle Messages
                if "message" in u:
                    msg = u["message"]
                    chat_id = msg.get("chat", {}).get("id")
                    user = msg.get("from", {})
                    user_id = user.get("id")
                    text = (msg.get("text") or msg.get("caption") or "").strip()
                    first_name = html.escape(user.get("first_name", "Friend") or "Friend")

                    if not text or not chat_id:
                        continue

                    # Record user for broadcast system
                    if user_id:
                        register_user(user_id)

                    # Anti-spam rate limiting: prevent bot from getting blocked by Telegram flood
                    now_ts = time.time()
                    last_msg_ts = _USER_MSG_TIMESTAMPS.get(user_id, 0)
                    if now_ts - last_msg_ts < 1.2:
                        warn_ts = _USER_WARN_COOLDOWN.get(user_id, 0)
                        if now_ts - warn_ts > 10.0:
                            _USER_WARN_COOLDOWN[user_id] = now_ts
                            await bot_api.send_message(
                                chat_id,
                                f"⚠️ <b>{to_small_caps('slow down!')}</b>\n<i>{to_small_caps('please wait a moment between messages to avoid flooding.')}</i>",
                                reply_to_message_id=msg.get("message_id")
                            )
                        continue
                    _USER_MSG_TIMESTAMPS[user_id] = now_ts

                    # Force Subscription check for private chat users
                    if chat_id > 0 and user_id:
                        is_member = await check_user_fsub(user_id)
                        if not is_member:
                            fsub_msg = (
                                f"⚠️ <b>{to_small_caps('access denied!')}</b>\n\n"
                                f"Hello {first_name} 🌹\n"
                                f"To use this bot, you must first join our official updates channel.\n\n"
                                f"📢 <b>{to_small_caps('channel')}:</b> {FSUB_CHANNEL}\n\n"
                                f"<i>Tap Join Channel below, then tap 'Joined / Retry'!</i>"
                            )
                            await bot_api.send_message(chat_id, fsub_msg, reply_markup=get_fsub_buttons(), reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)
                            continue

                    if text == "/start":
                        start_text = (
                            f"{to_small_caps('welcome')} {first_name} 🌹\n\n"
                            f"{to_small_caps('this is the fastest and powerful auto link bypass bot ∆')}\n\n"
                            f"⚡ <b>{to_small_caps('providerbotz engine')}</b>\n"
                            f"{to_small_caps('send any supported shortener link below to bypass instantly.')}\n\n"
                            f"📢 <b>{to_small_caps('official updates')}:</b> @ProviderBotz"
                        )
                        start_markup = get_start_buttons(user_id=user_id)
                        sent = False
                        if START_IMAGE_URL:
                            try:
                                photo_res = await bot_api.send_photo(
                                    chat_id,
                                    photo=START_IMAGE_URL,
                                    caption=start_text,
                                    reply_markup=start_markup,
                                    reply_to_message_id=msg.get("message_id")
                                )
                                if photo_res.get("ok"):
                                    sent = True
                            except Exception as e:
                                logger.warning(f"Could not send start photo: {e}")
                        if not sent:
                            await bot_api.send_message(chat_id, start_text, reply_markup=start_markup, reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)

                    elif text == "/help":
                        help_text = (
                            f"📖 <b>{to_small_caps('help guide')}</b>\n\n"
                            f"1. <b>{to_small_caps('send a link')}</b>: Simply paste any supported shortlink.\n"
                            f"2. <b>{to_small_caps('automatic processing')}</b>: The bot resolves the link through automatic processing.\n"
                            f"3. <b>{to_small_caps('clean result')}</b>: Only the pure final destination URL is returned.\n"
                            f"4. <b>{to_small_caps('copy link')}</b>: Tap on the link to copy instantly.\n\n"
                            f"🛡 <i>{to_small_caps('powered by')} {DEVELOPER}</i>"
                        )
                        await bot_api.send_message(chat_id, help_text, reply_markup=get_help_buttons(), reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)

                    elif text == "/about":
                        about_text = (
                            f"ℹ️ <b>{to_small_caps('about')} ShortnerBypass</b>\n\n"
                            f"• <b>{to_small_caps('developer')}</b>: {DEVELOPER}\n"
                            f"• <b>{to_small_caps('engines')}</b>: ProviderBotz V3.0.0\n"
                            f"• <b>{to_small_caps('speed')}</b>: High-Speed Async Telethon Userbot\n"
                            f"• <b>{to_small_caps('mini app')}</b>: Obsidian Red Glassmorphism Dashboard\n\n"
                            f"🚀 <i>{to_small_caps('crafted for speed and reliability')}</i>"
                        )
                        await bot_api.send_message(chat_id, about_text, reply_markup=get_about_buttons(), reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)

                    elif text.startswith(("/broadcast", "/bc")):
                        is_owner = bool(OWNER_ID and user_id == OWNER_ID)
                        if not is_owner:
                            denied_msg = (
                                f"⛔ <b>{to_small_caps('access denied!')}</b>\n\n"
                                f"<i>{to_small_caps('this command is strictly restricted to the bot owner.')}</i>"
                            )
                            await bot_api.send_message(chat_id, denied_msg, reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)
                            continue

                        # Extract broadcast content
                        reply_to = msg.get("reply_to_message")
                        bc_text = ""
                        if reply_to:
                            bc_text = (reply_to.get("text") or reply_to.get("caption") or "").strip()
                        if not bc_text:
                            parts = text.split(None, 1)
                            if len(parts) > 1:
                                bc_text = parts[1].strip()

                        if not bc_text:
                            help_bc = (
                                f"📢 <b>{to_small_caps('owner broadcast system')}</b>\n\n"
                                f"• <b>{to_small_caps('usage')} 1:</b> <code>/broadcast &lt;message&gt;</code>\n"
                                f"• <b>{to_small_caps('usage')} 2:</b> <i>{to_small_caps('reply to any message with')}</i> <code>/broadcast</code>\n\n"
                                f"👥 <b>{to_small_caps('registered users')}:</b> <code>{len(get_registered_users())}</code>"
                            )
                            await bot_api.send_message(chat_id, help_bc, reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)
                            continue

                        targets = get_registered_users()
                        if not targets:
                            targets = [chat_id]

                        status_init = await bot_api.send_message(
                            chat_id,
                            f"🚀 <b>{to_small_caps('broadcasting to')} {len(targets)} {to_small_caps('users...')}</b>",
                            disable_web_page_preview=True
                        )
                        s_msg_id = status_init.get("result", {}).get("message_id") if isinstance(status_init, dict) else None

                        async def _run_broadcast_task(broadcast_content: str, uids: List[int], notify_chat: int, stat_id: Optional[int]):
                            t0_bc = time.time()
                            ok_count = 0
                            fail_count = 0
                            bc_payload = (
                                f"📢 <b>{to_small_caps('official announcement')}</b>\n\n"
                                f"{broadcast_content}\n\n"
                                f"🛡 <i>{to_small_caps('powered by')} {DEVELOPER}</i>"
                            )
                            for target_uid in uids:
                                try:
                                    resp = await bot_api.send_message(target_uid, bc_payload, disable_web_page_preview=True)
                                    if resp and resp.get("ok"):
                                        ok_count += 1
                                    else:
                                        fail_count += 1
                                except Exception:
                                    fail_count += 1
                                await asyncio.sleep(0.05)

                            dur = round(time.time() - t0_bc, 2)
                            report_text = (
                                f"✅ <b>{to_small_caps('broadcast completed successfully!')}</b>\n\n"
                                f"• 👥 <b>{to_small_caps('total targets')}:</b> <code>{len(uids)}</code>\n"
                                f"• 🚀 <b>{to_small_caps('delivered')}:</b> <code>{ok_count}</code>\n"
                                f"• ❌ <b>{to_small_caps('failed / blocked')}:</b> <code>{fail_count}</code>\n"
                                f"• ⏱ <b>{to_small_caps('time elapsed')}:</b> <code>{dur}s</code>\n\n"
                                f"⚡ <i>{to_small_caps('providerbotz broadcast core')}</i>"
                            )
                            if stat_id:
                                try:
                                    await bot_api.edit_message_text(notify_chat, stat_id, report_text, disable_web_page_preview=True)
                                    return
                                except Exception:
                                    pass
                            await bot_api.send_message(notify_chat, report_text, disable_web_page_preview=True)

                        asyncio.create_task(_run_broadcast_task(bc_text, targets, chat_id, s_msg_id))

                    elif text in ("/stats", "/users"):
                        is_owner = bool(not OWNER_ID or user_id == OWNER_ID)
                        if is_owner:
                            dzhq_mode = f"Group ({DZHQ_GROUP})" if DZHQ_GROUP else "Not Set (Required by DZHQ modders)"
                            mini_app_status = f"{get_auto_public_url()} (Manual in code)" if MANUAL_MINI_APP_URL else f"{get_auto_public_url()} (Auto)"
                            stats_text = (
                                f"📊 <b>{to_small_caps('bot statistics & status')}</b>\n\n"
                                f"• 🤖 <b>{to_small_caps('userbot status')}:</b> {'🟢 ' + to_small_caps('online') if engine.userbot_connected else '🔴 ' + to_small_caps('offline')}\n"
                                f"• 👥 <b>{to_small_caps('total registered users')}:</b> <code>{len(get_registered_users())}</code>\n"
                                f"• ⚡ <b>{to_small_caps('total bypasses')}:</b> <code>{engine.total_bypasses}</code>\n"
                                f"• ✅ <b>{to_small_caps('successful')}:</b> <code>{engine.successful_bypasses}</code>\n"
                                f"• ❌ <b>{to_small_caps('failed')}:</b> <code>{engine.failed_bypasses}</code>\n"
                                f"• 🎯 <b>{to_small_caps('dzhq provider')}:</b> <code>{DZHQ_BOT}</code> ({dzhq_mode})\n"
                                f"• 🎯 <b>{to_small_caps('alex provider')}:</b> <code>{ALEX_BOT}</code> (Direct DM)\n"
                                f"• 🚀 <b>{to_small_caps('mini app url')}:</b> {mini_app_status}"
                            )
                            await bot_api.send_message(chat_id, stats_text, reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)
                        else:
                            denied_msg = (
                                f"⛔ <b>{to_small_caps('access denied!')}</b>\n\n"
                                f"<i>{to_small_caps('this command is strictly restricted to the bot owner.')}</i>"
                            )
                            await bot_api.send_message(chat_id, denied_msg, reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)

                    elif text.startswith("/bypass"):
                        url_to_bypass = extract_input_url(msg)
                        if url_to_bypass:
                            asyncio.create_task(process_user_link(chat_id, user_id, url_to_bypass, reply_msg_id=msg.get("message_id"), first_name=user.get("first_name")))
                        else:
                            bypass_help = (
                                f"⚠️ <b>{to_small_caps('please provide a link')}</b>:\n"
                                f"<code>/bypass https://example.com/shortlink</code>\n\n"
                                f"<i>Or simply paste any supported shortener link directly into the chat!</i>"
                            )
                            await bot_api.send_message(chat_id, bypass_help, reply_to_message_id=msg.get("message_id"), disable_web_page_preview=True)

                    else:
                        target = extract_input_url(msg)
                        if target:
                            asyncio.create_task(process_user_link(chat_id, user_id, target, reply_msg_id=msg.get("message_id"), first_name=user.get("first_name")))

                # 2. Handle Callback Queries
                elif "callback_query" in u:
                    cq = u["callback_query"]
                    cq_id = cq["id"]
                    cq_data = cq.get("data", "")
                    cq_msg = cq.get("message", {})
                    chat_id = cq_msg.get("chat", {}).get("id")
                    msg_id = cq_msg.get("message_id")
                    user = cq.get("from", {})
                    user_id = user.get("id")
                    first_name = html.escape(user.get("first_name", "Friend") or "Friend")
                    if user_id:
                        register_user(user_id)

                    await bot_api.answer_callback_query(cq_id)

                    if cq_data == "cmd_fsub_check":
                        is_member = await check_user_fsub(user_id)
                        if is_member:
                            await bot_api.answer_callback_query(cq_id, text="✅ Membership verified! Welcome.")
                            start_text = (
                                f"{to_small_caps('welcome')} {first_name} 🌹\n\n"
                                f"{to_small_caps('this is the fastest and powerful auto link bypass bot ∆')}\n\n"
                                f"⚡ <b>{to_small_caps('providerbotz engine')}</b>\n"
                                f"{to_small_caps('send any supported shortener link below to bypass instantly.')}\n\n"
                                f"📢 <b>{to_small_caps('official updates')}:</b> @ProviderBotz"
                            )
                            start_btns = get_start_buttons(user_id=user_id)
                            edit_res = await bot_api.edit_message_text(chat_id, msg_id, start_text, reply_markup=start_btns, disable_web_page_preview=True)
                            if not edit_res.get("ok"):
                                await bot_api.edit_message_caption(chat_id, msg_id, start_text, reply_markup=start_btns)
                        else:
                            await bot_api.answer_callback_query(
                                cq_id,
                                text="❌ You haven't joined @ProviderBotz yet! Please join first.",
                                show_alert=True
                            )

                    elif cq_data == "cmd_home":
                        start_text = (
                            f"{to_small_caps('welcome')} {first_name} 🌹\n\n"
                            f"{to_small_caps('this is the fastest and powerful auto link bypass bot ∆')}\n\n"
                            f"⚡ <b>{to_small_caps('providerbotz engine')}</b>\n"
                            f"{to_small_caps('send any supported shortener link below to bypass instantly.')}\n\n"
                            f"📢 <b>{to_small_caps('official updates')}:</b> @ProviderBotz"
                        )
                        start_btns = get_start_buttons(user_id=user_id)
                        edit_res = await bot_api.edit_message_text(chat_id, msg_id, start_text, reply_markup=start_btns, disable_web_page_preview=True)
                        if not edit_res.get("ok"):
                            await bot_api.edit_message_caption(chat_id, msg_id, start_text, reply_markup=start_btns)

                    elif cq_data == "cmd_help":
                        help_text = (
                            f"📖 <b>{to_small_caps('help guide')}</b>\n\n"
                            f"1. <b>{to_small_caps('send a link')}</b>: Simply paste any supported shortlink.\n"
                            f"2. <b>{to_small_caps('automatic processing')}</b>: The bot resolves the link through automatic processing.\n"
                            f"3. <b>{to_small_caps('clean result')}</b>: Only the pure final destination URL is returned.\n"
                            f"4. <b>{to_small_caps('copy link')}</b>: Tap on the link to copy instantly.\n\n"
                            f"🛡 <i>{to_small_caps('powered by')} {DEVELOPER}</i>"
                        )
                        await bot_api.edit_message_text(chat_id, msg_id, help_text, reply_markup=get_help_buttons(), disable_web_page_preview=True)

                    elif cq_data == "cmd_about":
                        about_text = (
                            f"ℹ️ <b>{to_small_caps('about')} ShortnerBypass</b>\n\n"
                            f"• <b>{to_small_caps('developer')}</b>: {DEVELOPER}\n"
                            f"• <b>{to_small_caps('engines')}</b>: ProviderBotz V3.0.0\n"
                            f"• <b>{to_small_caps('speed')}</b>: High-Speed Async Telethon Userbot\n"
                            f"• <b>{to_small_caps('mini app')}</b>: Obsidian Red Glassmorphism Dashboard\n\n"
                            f"🚀 <i>{to_small_caps('crafted for speed and reliability')}</i>"
                        )
                        await bot_api.edit_message_text(chat_id, msg_id, about_text, reply_markup=get_about_buttons(), disable_web_page_preview=True)

                    elif cq_data == "cmd_close":
                        await bot_api.delete_message(chat_id, msg_id)

                    elif cq_data.startswith("retry:"):
                        token = cq_data.split("retry:", 1)[1]
                        url_to_retry = _RETRY_CACHE.get(token, token)
                        if url_to_retry:
                            asyncio.create_task(process_user_link(chat_id, user.get("id"), url_to_retry, reply_msg_id=msg_id, first_name=user.get("first_name")))

        except asyncio.CancelledError:
            break
        except Exception as e:
            _trace("POLLING", f"Polling error: {e}")
            await asyncio.sleep(2)

# ══════════════════════════════════════════════════════════════
#  FLASK SERVER & API
# ══════════════════════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = SECRET_KEY

GLOBAL_ASYNC_LOOP: Optional[asyncio.AbstractEventLoop] = None

@app.before_request
def auto_detect_host_url():
    global _CURRENT_PUBLIC_URL
    if not _CURRENT_PUBLIC_URL or _CURRENT_PUBLIC_URL.startswith("http://localhost"):
        proto = request.headers.get("X-Forwarded-Proto") or ("https" if request.is_secure else "http")
        host = request.headers.get("X-Forwarded-Host") or request.host
        if host and not host.startswith("localhost") and not host.startswith("127.0.0.1"):
            _CURRENT_PUBLIC_URL = f"{proto}://{host}".rstrip("/")
        elif request.host_url:
            detected = request.host_url.rstrip("/")
            if not detected.startswith("http://localhost"):
                _CURRENT_PUBLIC_URL = detected

@app.route("/", methods=["GET"])
def route_index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        return send_file(index_path)
    return "<h1>ShortnerBypass — Telegram Mini App Ready</h1>", 200

@app.route("/health", methods=["GET"])
def route_health():
    return jsonify({
        "status": "ok",
        "service": "ShortnerBypass",
        "developer": DEVELOPER,
        "public_url": get_auto_public_url(),
        "userbot_online": engine.userbot_connected,
        "bot_api_online": bool(bot_api)
    }), 200

@app.route("/bypass", methods=["GET"])
def route_bypass():
    raw_url = request.args.get("url") or request.args.get("link") or ""
    raw_url = raw_url.strip()

    if not raw_url:
        return jsonify({
            "status": False,
            "developer": DEVELOPER,
            "message": "Missing 'url' query parameter. Example: /bypass?url=https://..."
        }), 400

    if not raw_url.startswith(("http://", "https://")):
        raw_url = "https://" + raw_url

    if not GLOBAL_ASYNC_LOOP:
        return jsonify({
            "status": False,
            "developer": DEVELOPER,
            "message": "Engine async loop is not initialized"
        }), 503

    raw_uid = request.args.get("uid") or request.args.get("user_id")
    api_user_id = int(raw_uid) if raw_uid and raw_uid.lstrip("-").isdigit() else None
    api_first_name = request.args.get("fname") or request.args.get("first_name") or ("Mini App User" if api_user_id else "API Client")
    job_id, _ = engine.create_job(raw_url, user_id=api_user_id, source="api", first_name=api_first_name)

    try:
        future = asyncio.run_coroutine_threadsafe(execute_bypass_job(job_id), GLOBAL_ASYNC_LOOP)
        result = future.result(timeout=MAX_BYPASS_TIMEOUT_SEC + 5)
        status_code = 200 if result.get("status") is True else 422
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            "status": False,
            "developer": DEVELOPER,
            "message": f"Bypass request timed out or encountered an error: {e}"
        }), 504
    finally:
        engine.cleanup_job(job_id)

@app.route("/admin/status", methods=["GET"])
def route_admin_status():
    uptime = int(time.time() - engine.start_time)
    with engine.jobs_lock:
        active_count = len(engine.active_jobs)

    return jsonify({
        "developer": DEVELOPER,
        "public_url": get_auto_public_url(),
        "uptime_sec": uptime,
        "active_jobs": active_count,
        "total_bypasses": engine.total_bypasses,
        "successful_bypasses": engine.successful_bypasses,
        "failed_bypasses": engine.failed_bypasses,
        "providers": {
            "dzhq": {"configured": bool(DZHQ_BOT), "group": DZHQ_GROUP, "entity_resolved": bool(engine.dzhq_group_entity)},
            "alex_dm": {"configured": bool(ALEX_BOT)}
        }
    }), 200

# ══════════════════════════════════════════════════════════════
#  STARTUP & LIFECYCLE
# ══════════════════════════════════════════════════════════════
async def main_async():
    global GLOBAL_ASYNC_LOOP
    GLOBAL_ASYNC_LOOP = asyncio.get_running_loop()
    load_registered_users()

    # 1. Start Telethon Userbot (Strictly handles DZHQ Group + Alex DM)
    if TELEGRAM_API_ID and TELEGRAM_API_HASH and TELEGRAM_SESSION:
        logger.info("Connecting Telethon Userbot...")
        try:
            userbot = TelegramClient(
                StringSession(TELEGRAM_SESSION),
                TELEGRAM_API_ID,
                TELEGRAM_API_HASH,
                connection=ConnectionTcpAbridged,
                auto_reconnect=True
            )
            await userbot.start()
            if await userbot.is_user_authorized():
                engine.userbot = userbot
                engine.userbot_connected = True

                # Resolve DZHQ group entity if explicitly configured
                if DZHQ_GROUP:
                    try:
                        engine.dzhq_group_entity = await userbot.get_entity(DZHQ_GROUP)
                        logger.info(f"✅ DZHQ Group resolved: {getattr(engine.dzhq_group_entity, 'title', DZHQ_GROUP)}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not resolve DZHQ Group ({DZHQ_GROUP}): {e}. Note: DZHQ requires this group.")
                else:
                    logger.info("ℹ️ DZHQ Group is not configured. (DZHQ bot modders only allow group mode). Alex DM will handle bypasses.")

                try:
                    d_ent = await userbot.get_entity(DZHQ_BOT)
                    engine.dzhq_bot_id = d_ent.id
                    logger.info(f"✅ DZHQ Bot resolved: {DZHQ_BOT} (ID: {d_ent.id})")
                except Exception as e:
                    logger.warning(f"⚠️ Could not resolve {DZHQ_BOT}: {e}")

                try:
                    a_ent = await userbot.get_entity(ALEX_BOT)
                    engine.alex_bot_id = a_ent.id
                    logger.info(f"✅ Alex Bot resolved: {ALEX_BOT} (ID: {a_ent.id})")
                except Exception as e:
                    logger.warning(f"⚠️ Could not resolve {ALEX_BOT}: {e}")

                # Note: /start is NEVER sent to Alex DM or external bots to protect the Telethon userbot account from bans
                logger.info(f"🛡️ Userbot initialized safely for {ALEX_BOT} (only valid URLs will be forwarded on demand)")

                setup_userbot_handlers(userbot)
                me = await userbot.get_me()
                logger.info(f"✅ Userbot connected: {me.first_name} (@{getattr(me, 'username', 'N/A')})")
            else:
                logger.error("❌ Telethon Session is not authorized. Check TELEGRAM_SESSION.")
        except Exception as e:
            logger.error(f"❌ Userbot startup failed: {e}")
    else:
        logger.warning("⚠️ Telethon Userbot credentials missing in .env (API_ID, API_HASH, or TELEGRAM_SESSION).")

    # 2. Launch Telegram Bot Polling (with Real Colored Buttons)
    polling_task = asyncio.create_task(run_bot_polling())

    # 3. Print Startup Banner
    detected_url = get_auto_public_url()
    dzhq_flow_desc = f"Group Flow ({DZHQ_GROUP})" if DZHQ_GROUP else "Not set (Requires authorized group)"
    mini_app_desc = f"{detected_url} (Manual in code)" if MANUAL_MINI_APP_URL else f"{detected_url} (Auto)"
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ProviderBotz Auto Bypass
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Flask: running (Port {PORT})
Public Bot API: {'online (@' + BOT_USERNAME + ')' if BOT_TOKEN else 'offline'}
Button Styles: PRIMARY (Blue), SUCCESS (Green), DANGER (Red)
Telethon Userbot: {'connected' if engine.userbot_connected else 'offline'}
DZHQ: {dzhq_flow_desc}
Alex DM: DM Flow ({ALEX_BOT})
Mini App Link: {mini_app_desc}
Health: {detected_url}/health
Mini App: {detected_url}/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""", flush=True)

    await polling_task

def run_flask_thread():
    logger.info(f"Flask HTTP server starting on port {PORT}...")
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False, threaded=True)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask_thread, daemon=True, name="FlaskThread")
    flask_thread.start()

    try:
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 ProviderBotz stopped.")
