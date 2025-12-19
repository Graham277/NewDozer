import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

import SheetsManager

load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
disable_attendance = False

@bot.event
async def on_ready():
    guild_id = os.getenv("guild_id")
    dev_guild_id = os.getenv("dev_guild_id")

    guilds = []
    if guild_id:
        guilds.append(discord.Object(id=int(guild_id)))
    if dev_guild_id:
        guilds.append(discord.Object(id=int(dev_guild_id)))

    for guild in guilds:
        synced = await bot.tree.sync(guild=guild)
        print(f"Cleared and synced {len(synced)} commands to {guild.id}")

async def load_extensions():
    await bot.load_extension("cogs.ScoringGuide")
    await bot.load_extension("cogs.NoBlueBanners")
    if not disable_attendance:
        await bot.load_extension("cogs.MarkHere")
    print("Extensions all loaded")

if __name__ == "__main__":
    # parse command line
    for arg in sys.argv[1:]:
        match arg:
            case "--disable-attendance":
                if not disable_attendance:
                    disable_attendance = True
                else:
                    print(f"Duplicate argument {arg}")
                    os._exit(2)
            case "--import-secrets":
                if disable_attendance:
                    print(f"Cannot combine {arg} and --disable-attendance")
                    os._exit(2)
                # search for secrets and import them into the keyring
                manager = SheetsManager.SheetManager()
                manager.import_secrets()
                print("Success! Make sure to never leave the keys in plaintext (keep an encrypted copy on another machine).")
                sys.exit(0)
            case _:  # default
                print(f"Unrecognized argument {arg}")

    import asyncio
    asyncio.run(load_extensions())
    token = os.getenv("token")
    bot.run(token)
