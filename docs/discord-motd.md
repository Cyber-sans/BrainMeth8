# Brainmeth Discord quotes -> rotating server-list MOTD

This is **production only**. No clients or AutoModpack updates are required.
Uses MOTDoftheDay 1.1.0 (NeoForge 1.21.1) and a tiny optional Python
Discord API sidecar. MOTD changes every **120 seconds**; the quote pool is
refreshed every **10 minutes**, with no Minecraft restart. The first MOTD line displays the Discord **quote**; the second shows
**- username** (long usernames are abbreviated). The server name is not repeated.
Each displayed quote and its attribution use one randomly selected colour:
cyan (§b), pink (§d), or purple (§5), rather than alternating per letter.

**Discord invite:** https://discord.gg/TgKuKGA7u

## 1. Create and authorize a Discord bot

1. Open https://discord.com/developers/applications > New Application > Bot.
2. Enable **Message Content Intent** under Bot > Privileged Gateway Intents.
3. Under OAuth2/Installation, add the bot to the Brainmeth Discord server.
   Give it only **View Channels** and **Read Message History**.
   Do **not** grant Administrator or Manage Server.
4. Discord Settings > Advanced > Developer Mode. Right-click the Brainmeth
   server > **Copy Server ID**.
5. The reader selects **#motb** by channel name by default. Grant the bot
   View Channel and Read Message History for #motb, and ensure the channel is
   an ordinary, non-NSFW text channel.

The invite alone does not authorize reading server history. This integration
uses a real Discord bot and the official API, not a self-bot/user token.

## 2. Store the secret and IDs on cropduster

From a shell in `/srv/minecraft/brainmeth/server-1211`:

```bash
mkdir -p secrets
nano secrets/discord-motd-token.txt
# Paste only the bot token, not the Discord invite or client secret.
chmod 600 secrets/discord-motd-token.txt
nano .env
```

Add these **separate** lines to `.env` (don't remove existing settings):

```dotenv
DISCORD_MOTD_GUILD_ID=YOUR_DISCORD_SERVER_ID
DISCORD_MOTD_CHANNEL_NAME=motb
```

The Docker Compose service defaults to **#motb** even if you omit
`DISCORD_MOTD_CHANNEL_NAME`. A legacy `DISCORD_MOTD_ALL_PUBLIC=1`
setting will **not** override this channel restriction, but you may
remove that old setting from `.env` for clarity.

For an alternative explicit set of channel IDs, set
`DISCORD_MOTD_CHANNEL_NAME=` (empty) and
`DISCORD_MOTD_CHANNEL_IDS=111...,222...`.
To explicitly use all eligible non-NSFW text channels, leave both channel
name and IDs empty and set `DISCORD_MOTD_ALL_PUBLIC=1`. Prefer #motb:
these quotes are shown publicly in Minecraft's multiplayer list.

## 3. Deploy mod and activate the sync

```bash
cd /srv/minecraft/brainmeth/server-1211
git -c core.fileMode=false pull --ff-only
bash scripts/deploy.sh prod
docker compose --profile discord-motd up -d discord-motd
```

Production deployment installs the MOTDoftheDay JAR and seeds
`/srv/minecraft/brainmeth/prod-1211/config/motdoftheday/config.json`
only if absent. Docker's Discord sidecar can be started after the
Minecraft server is running. It does not touch `server.properties`.

## 4. Verify

```bash
docker inspect brainmeth1211-prod --format '{{.State.Health.Status}}'
docker logs --tail 60 brainmeth1211-discord-motd
docker logs --tail 100 brainmeth1211-prod 2>&1 | grep -Ei 'MOTDoftheDay|Changing MOTD|Done \\('
```

Expected from the sidecar: `Refreshed N Discord MOTD quotes`.
Refresh the multiplayer server list to see the current quote.
It chooses random quotes from a cached pool, so a quote can occasionally
repeat. The bot excludes links, Discord mentions, bots, webhooks, NSFW
channels during all-public discovery, and messages above 52 characters.
Discord Message Content Intent is needed to read ordinary message text.

## 5. Disable or roll back

Stop the Discord reader (the current quote pool will keep rotating):

```bash
docker compose --profile discord-motd stop discord-motd
```

To return fully to the static `.env` MOTD, stop the reader, remove only
the server-side mod JAR, then restart Minecraft. Note that a subsequent
`scripts/deploy.sh prod` currently reinstalls the mod:

```bash
docker compose --profile discord-motd stop discord-motd
rm -f /srv/minecraft/brainmeth/prod-1211/mods/motdoftheday-1.1.0.jar
docker restart -t 120 brainmeth1211-prod
```

Credentials are read from `secrets/discord-motd-token.txt` on the
host and are **not** stored in Git. Never paste this token into chat or
commit it.
