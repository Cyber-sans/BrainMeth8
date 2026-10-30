#!/usr/bin/env python3
"""Read approved Discord channels and refresh MOTDoftheDay's two-line quote pool.

Requires a Discord bot token, guild ID, and explicitly selected channel IDs,
or an explicit opt-in to all bot-accessible non-NSFW text channels.

The Minecraft MOTDoftheDay mod rotates at 120 s; this process refreshes
its quote pool every 600 s. It requires no Discord webhook, RCON, server
restart, additional Python packages or Minecraft client modification.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import random
import re
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://discord.com/api/v10"
CONFIG_PATH = Path(os.getenv("DISCORD_MOTD_CONFIG", "/motd/config.json"))
TOKEN_FILE = Path(os.getenv("DISCORD_MOTD_TOKEN_FILE", "/run/secrets/discord_motd_token"))
GUILD = os.getenv("DISCORD_MOTD_GUILD_ID", "").strip()
CHANNELS = [
    channel.strip()
    for channel in os.getenv("DISCORD_MOTD_CHANNEL_IDS", "").split(",")
    if channel.strip()
]
ALL_PUBLIC = os.getenv("DISCORD_MOTD_ALL_PUBLIC", "0") == "1"
REFRESH_SECONDS = 600
COLORS = ("§b", "§d", "§5")
SNOWFLAKE = re.compile(r"\d{16,22}\Z")
URL_OR_MENTION = re.compile(r"(?i)(https?://|www\.|discord\.gg/|<[@#:&]|@everyone|@here)")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f§]")
MARKDOWN = re.compile(r"[*_`~|]")
SPACES = re.compile(r"\s+")


def neon(text: str) -> str:
    i = 0
    result = []
    for letter in text:
        if letter.isspace():
            result.append(letter)
        else:
            result.append(COLORS[i % len(COLORS)] + letter)
            i += 1
    return "".join(result)


def clean_quote(message: dict) -> str | None:
    if message.get("type", 0) not in (0, 19):
        return None
    if message.get("author", {}).get("bot") or message.get("webhook_id"):
        return None
    raw = message.get("content")
    if not isinstance(raw, str) or not raw.strip():
        return None
    # Never promote links, ping commands, usernames or possible formatting
    # control codes from arbitrary Discord messages to public server status.
    if URL_OR_MENTION.search(raw):
        return None
    cleaned = MARKDOWN.sub("", CONTROL.sub(" ", raw))
    cleaned = SPACES.sub(" ", cleaned).strip().strip('"“”')
    if not 12 <= len(cleaned) <= 52:
        return None
    if not any(letter.isalpha() for letter in cleaned):
        return None
    return cleaned


def clean_username(message: dict) -> str | None:
    """Return a safe Discord username for public MOTD attribution."""
    author = message.get("author")
    if not isinstance(author, dict):
        return None
    username = author.get("username")
    if not isinstance(username, str):
        return None
    username = re.sub(r"[^A-Za-z0-9._]", "", username).strip("._")
    if not username:
        return None
    # Keep the complete quote visible beside Brainmeth's server name.
    return username if len(username) <= 18 else username[:17] + "…"


def discord_json(path: str, token: str):
    url = API + path
    for attempt in range(2):
        request = Request(
            url,
            headers={
                "Authorization": f"Bot {token}",
                "User-Agent": "BrainmethDiscordMOTD/1.0",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=25) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code == 429 and attempt == 0:
                try:
                    delay = min(float(json.loads(exc.read())["retry_after"]), 60.0)
                except (ValueError, KeyError, TypeError):
                    delay = 10.0
                time.sleep(max(delay, 1.0))
                continue
            # Include the failed API endpoint and Discord's numeric error
            # code, never the Authorization header or bot token.
            try:
                detail = json.loads(exc.read())
                code = detail.get("code", "unknown")
                description = str(detail.get("message", exc.reason))[:160]
            except (ValueError, TypeError, AttributeError):
                code, description = "unknown", str(exc.reason)
            raise RuntimeError(
                f"Discord GET {path}: HTTP {exc.code} "
                f"(Discord code {code}: {description})"
            ) from exc
    raise RuntimeError("Discord API rate-limit retries exhausted")


def eligible_channels(token: str) -> list[str]:
    if CHANNELS:
        return CHANNELS
    if not ALL_PUBLIC:
        raise RuntimeError(
            "Set DISCORD_MOTD_CHANNEL_IDS, or explicitly opt in using "
            "DISCORD_MOTD_ALL_PUBLIC=1. Never grant the bot Administrator."
        )
    result = discord_json(f"/guilds/{GUILD}/channels", token)
    if not isinstance(result, list):
        raise RuntimeError("Discord returned an unexpected channel listing")
    channels = [
        channel["id"]
        for channel in result
        if channel.get("type") == 0 and not channel.get("nsfw", False)
    ]
    return channels[:60]


def refresh(token: str) -> None:
    channels = eligible_channels(token)
    if not channels:
        raise RuntimeError("No eligible Discord channels")
    collected: set[tuple[str, str]] = set()
    failed = 0
    for channel in channels:
        if not SNOWFLAKE.fullmatch(channel):
            raise ValueError("Invalid Discord channel ID")
        try:
            items = discord_json(f"/channels/{channel}/messages?limit=100", token)
            if not isinstance(items, list):
                raise ValueError("Unexpected Discord messages response")
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
            # Discord returns 403 for channels the bot cannot read; keep
            # updating from permitted channels rather than requiring admin.
            failed += 1
            logging.warning("Skipping channel %s: %s", channel, exc)
            continue
        entries = [
            (quote, username)
            for msg in items
            if (quote := clean_quote(msg))
            and (username := clean_username(msg))
        ]
        random.shuffle(entries)
        collected.update(entries[:25])

    if not collected:
        logging.warning("No eligible quotes (%d channels failed); keeping existing MOTD", failed)
        return

    quotes = random.sample(sorted(collected), min(len(collected), 120))
    messages = [
        neon('"' + quote + '"') + "\n§7- " + neon(username)
        for quote, username in quotes
    ]
    config = {
        "Enabled": True,
        "MOTD": {"Interval": 120, "Messages": messages},
        "Overrides": {},
    }
    new_content = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    if CONFIG_PATH.exists() and CONFIG_PATH.read_text(encoding="utf-8") == new_content:
        return

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=CONFIG_PATH.parent, prefix=".discord-motd-", suffix=".json")
    staging = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(new_content)
            output.flush()
            os.fsync(output.fileno())
        staging.chmod(0o644)
        staging.replace(CONFIG_PATH)  # Valid complete JSON, no partial reads.
        # MOTDoftheDay's Java watcher listens for ENTRY_MODIFY *only*.
        # A rename emits ENTRY_CREATE, so make one safe modification to the
        # already-complete JSON file to force its live reload.
        with CONFIG_PATH.open("a", encoding="utf-8") as output:
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
    finally:
        staging.unlink(missing_ok=True)
    logging.info("Refreshed %d Discord MOTD quotes (%d channels inaccessible)", len(messages), failed)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not SNOWFLAKE.fullmatch(GUILD):
        raise SystemExit("Set DISCORD_MOTD_GUILD_ID to a Discord server ID")
    if not TOKEN_FILE.is_file():
        raise SystemExit(f"Missing Discord bot token file: {TOKEN_FILE}")
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit("Discord bot token file is empty")
    if not CHANNELS and not ALL_PUBLIC:
        raise SystemExit("Choose quote channels or explicitly opt in to non-NSFW public channels")
    logging.info("Discord MOTD sync started for guild %s; interval=%ds", GUILD, REFRESH_SECONDS)
    while True:
        try:
            refresh(token)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
            logging.error("Discord MOTD refresh failed: %s", exc)
        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()
