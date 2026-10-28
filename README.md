# 🐻 BearBot

![BearBot](assets/banner.svg)

**The link + image + mass-text poster for Discord — honeypot-guarded.**

BearBot is a separate poster bot from the BearAteTheHoneyPot family. It
posts images, links, and all-in-one embeds — and if the honeypot guard is
sitting next to it, **every post skips trap channels automatically**.

```
🤖 /allinone → 🐻 guard checks → ✅ posted (or honeypot skipped)
```

> Pair it with [BearAteTheHoneyPot](https://github.com/AlMonDdevV/BearAteTheHoneyPot)
> — drop `bearatethehoneypot.py` next to `bearbot.py` and the guard
> **auto-activates**. No config needed.

---

## 🛠️ Commands

| Command | What it does |
|---|---|
| `/image` | Post an image into a channel (optional caption) |
| `/link` | Post a link into a channel (optional message) |
| `/allinone` | Link + image + text in **one embed** — set `everywhere` to true to mass-post it |
| `/mass_text` | Mass-post text into every channel in every server (admin only) |

### Examples

```
/image     channel:#gallery image_url:https://example.com/pic.png caption:look at this 🐻
/link      channel:#general url:https://github.com/AlMonDdevV text:check out my repo
/allinone  channel:#promo link:https://myserver.com image_url:https://myserver.com/banner.png text:BIG announcement!
/mass_text hello everyone 🐻
```

The `--putlinkhere` part is just the **`url:` / `link:` parameter** — type or
paste your link there when the command pops up.

### Mass mode

- `/allinone ... everywhere:true` → the same embed goes to **every text
  channel in every server** the bot is in, with `1.5s` delay between posts
- `/mass_text <message>` → mass text everywhere (admin only)
- In both modes, honeypot channels are **skipped, not posted into**, and
  the console shows the count:

  ```
  [BearBot] mass run finished: 42 sent, 3 honeypots skipped
  ```

---

## 📁 What's in this repo

| File | What it is |
|---|---|
| `bearbot.py` | The bot — `/image`, `/link`, `/allinone`, `/mass_text` |
| `requirements.txt` | Dependencies (`discord.py`) |
| `.env.example` | Token template — copy to `.env`, never commit the real one |
| `assets/banner.svg` | Repo banner |
| `assets/banner-ai-prompt.txt` | Prompt to generate a fancy PNG banner with an image AI |

---

## 📦 Requirements

- Python **3.9+**
- [discord.py](https://pypi.org/project/discord.py/) 2.x

---

## 🚀 Quick start

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create an application → **Bot** tab → copy your **token**
3. Under **Privileged Gateway Intents**, enable:
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
4. Invite the bot with the `bot` + `applications.commands` scopes, and give
   it **Send Messages** + **Embed Links** permissions in the channels you
   want it to post in

```bash
git clone https://github.com/AlMonDdevV/BearBot.git
cd BearBot
pip install -r requirements.txt
copy .env.example .env        # Windows  (macOS/Linux: cp .env.example .env)
# → open .env and paste your bot token
python bearbot.py
```

You should see:

```
[BearBot] honeypot guard active (BearAteTheHoneyPot)   ← if the guard file is present
```

Then run the slash commands in Discord. Done. 🐻

---

## 🍯 Turning on the honeypot guard

BearBot runs fine standalone — but it shines when paired with the guard:

1. Download `bearatethehoneypot.py` from
   [BearAteTheHoneyPot](https://github.com/AlMonDdevV/BearAteTheHoneyPot)
2. Put it **next to `bearbot.py`**:

   ```
   BearBot/
   ├── bearbot.py
   ├── bearatethehoneypot.py   ← the guard
   ├── .env
   └── honeypots.json          ← auto-created shared blacklist
   ```

3. Start BearBot — it auto-loads the guard and routes **every send**
   (single posts and mass runs) through it. Channels named `honeypot`,
   `trap`, `bait`, `free-nitro-verify`, etc. get skipped with a log line:

   ```
   [BearAteTheHoneyPot] SKIPPED #honeypot (123456789) in Trap Server — honeypot detected
   ```

Both bots then **share the same `honeypots.json` blacklist** — flag a trap
once with `/flag_honeypot` and BearBot skips it forever.

---

## ⚙️ Configuration

Edit the constants at the top of `bearbot.py`:

```python
RATE_LIMIT_DELAY = 1.5   # seconds between mass posts — raise it if you hit rate limits
```

Banner color: `HONEY_GOLD` — change the RGB to re-theme every embed.

---

## 📄 Full Script

> Also available as [`bearbot.py`](bearbot.py)

```python
#!/usr/bin/env python3
"""
BearBot - link / image / all-in-one poster bot for Discord.

Slash commands:
  /image     <channel> <image_url> [caption]        post an image
  /link      <channel> <url> [text]                 post a link
  /allinone  <channel> <link> <image_url> <text>    link + image + text in one embed
             [everywhere=True]                      ...or mass-post it everywhere
  /mass_text <message>                              mass-post text to every channel

Honeypot guard: if `bearatethehoneypot.py` (BearAteTheHoneyPot) sits next to
this file, it is loaded automatically and every send goes through the bear,
so honeypot trap channels get skipped instead of getting the bot banned.
"""

import asyncio
import os
from typing import Optional

import discord
from discord.ext import commands

HONEY_GOLD = discord.Color.from_rgb(245, 185, 66)
GUARD_FILE = "bearatethehoneypot.py"
RATE_LIMIT_DELAY = 1.5  # seconds between mass posts (respect rate limits!)


def load_token() -> Optional[str]:
    """Read the bot token from the environment, or from a local .env file."""
    token = os.getenv("DISCORD_TOKEN")
    if token:
        return token.strip()
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DISCORD_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class BearBot(commands.Bot):
    async def setup_hook(self):
        # auto-load the honeypot guard if it sits next to this file
        guard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), GUARD_FILE)
        if os.path.exists(guard_path):
            try:
                await self.load_extension("bearatethehoneypot")
                print("[BearBot] honeypot guard active (BearAteTheHoneyPot)")
            except Exception as e:
                print(f"[BearBot] honeypot guard failed to load: {e}")
        await self.tree.sync()

    async def guarded_send(self, channel, content=None, **kwargs):
        """Send through the honeypot guard when available, else send directly."""
        pot = self.get_cog("BearAteTheHoneyPot")
        if pot is not None:
            return await pot.safe_send(channel, content, **kwargs)
        return await channel.send(content, **kwargs)


bot = BearBot(command_prefix="!", intents=intents)


async def _mass_send(interaction: discord.Interaction, **payload):
    """Post a payload to every text channel in every guild, skipping honeypots."""
    await interaction.response.send_message("🐻 leading the way...", ephemeral=True)
    sent, skipped = 0, 0
    for guild in bot.guilds:
        for channel in guild.text_channels:
            result = await bot.guarded_send(channel, **payload)
            if result:
                sent += 1
            else:
                skipped += 1
            await asyncio.sleep(RATE_LIMIT_DELAY)
    print(f"[BearBot] mass run finished: {sent} sent, {skipped} honeypots skipped")


@bot.tree.command(name="image", description="Post an image (honeypot-guarded)")
async def image_cmd(interaction: discord.Interaction, channel: discord.TextChannel,
                    image_url: str, caption: Optional[str] = None):
    """Post an image into a channel."""
    if not is_url(image_url):
        await interaction.response.send_message(
            "🐻 That image URL doesn't look right - it must start with http:// or https://",
            ephemeral=True,
        )
        return
    embed = discord.Embed(color=HONEY_GOLD)
    if caption:
        embed.description = caption
    embed.set_image(url=image_url)
    embed.set_footer(text="BearBot 🐻")
    sent = await bot.guarded_send(channel, embed=embed)
    if sent:
        await interaction.response.send_message(
            f"✅ image posted in {channel.mention}", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"🐻 skipped {channel.mention} - honeypot detected!", ephemeral=True
        )


@bot.tree.command(name="link", description="Post a link (honeypot-guarded)")
async def link_cmd(interaction: discord.Interaction, channel: discord.TextChannel,
                   url: str, text: Optional[str] = None):
    """Post a link (optionally with a message) into a channel."""
    if not is_url(url):
        await interaction.response.send_message(
            "🐻 That link doesn't look right - it must start with http:// or https://",
            ephemeral=True,
        )
        return
    embed = discord.Embed(title="🔗 open link", url=url, description=text, color=HONEY_GOLD)
    embed.set_footer(text="BearBot 🐻")
    sent = await bot.guarded_send(channel, embed=embed)
    if sent:
        await interaction.response.send_message(
            f"✅ link posted in {channel.mention}", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"🐻 skipped {channel.mention} - honeypot detected!", ephemeral=True
        )


@bot.tree.command(name="allinone",
                  description="Post link + image + text in one embed (or mass-post it)")
async def allinone_cmd(interaction: discord.Interaction, channel: discord.TextChannel,
                       link: str, image_url: str, text: str,
                       everywhere: Optional[bool] = None):
    """Post a link, an image and text together in one embed.

    Set `everywhere` to true to mass-post the same embed into every text
    channel in every server the bot is in (admin only, honeypots skipped).
    """
    if not is_url(link) or not is_url(image_url):
        await interaction.response.send_message(
            "🐻 Both the link and the image URL must start with http:// or https://",
            ephemeral=True,
        )
        return

    embed = discord.Embed(title="🔗 open link", url=link, description=text, color=HONEY_GOLD)
    embed.set_image(url=image_url)
    embed.set_footer(text="BearBot 🐻")

    if everywhere:
        if interaction.guild is None or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Admins only (in a server) for everywhere=true.", ephemeral=True
            )
            return
        await _mass_send(interaction, embed=embed)
        return

    sent = await bot.guarded_send(channel, embed=embed)
    if sent:
        await interaction.response.send_message(
            f"✅ all-in-one posted in {channel.mention}", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"🐻 skipped {channel.mention} - honeypot detected!", ephemeral=True
        )


@bot.tree.command(name="mass_text",
                  description="Post text in every channel, skipping honeypots (admin only)")
async def mass_text_cmd(interaction: discord.Interaction, message: str):
    if interaction.guild is None or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admins only (in a server).", ephemeral=True)
        return
    await _mass_send(interaction, content=message)


if __name__ == "__main__":
    token = load_token()
    if not token:
        raise SystemExit(
            "No token found. Set the DISCORD_TOKEN environment variable "
            "or create a .env file with DISCORD_TOKEN=your-token"
        )
    bot.run(token)
```

---

## ❓ FAQ

**Does mass-posting get my bot banned by Discord?**
It can — mass advertising against server rules or flooding too fast violates
Discord's ToS. The `1.5s` delay and the honeypot guard reduce the risk, but
respect each server's rules and Discord's rate limits.

**Self-bot / user account?**
No. Self-botting violates Discord's ToS and gets accounts terminated. Use a
bot token.

**The image doesn't show.**
The URL must be a **direct image link** (`.png`, `.jpg`, `.gif`, `.webp`) —
not a page that contains an image.

**Why `/mass_text` and not `/mass_image`?**
You can mass-post anything: use `/allinone ... everywhere:true` for
link + image + text mass-posting. `/mass_text` is the quick plain-text
version.

---

## 📜 License

MIT — do whatever you want, just don't blame the bear. See [LICENSE](LICENSE).

---

*BearBot posts it everywhere. The bear makes sure it's safe. 🐻📢🍯*
