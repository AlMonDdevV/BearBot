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

The token is read from the DISCORD_TOKEN environment variable, or from a
.env file next to this script if the env var is not set.
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
