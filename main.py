import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

import SheetsManager

# Secrets are stored in a dotenv, so we must load it before trying to access it
# Before running, see if there is an environment variable called
# DOZER_DOTENV_PATH.
# If so, load it from there.
dotenv_path = os.getenv("DOZER_DOTENV_PATH")
if not dotenv_path:
    dotenv_path = None
load_dotenv(dotenv_path=dotenv_path)

# Set up the bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
disable_attendance = False

# This is run when the bot is started by discord.py, it syncs the commands to the guilds specified
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
        print(f"Synced {len(synced)} commands to {guild.id}")


# Loads all the slash commands so they can be added to the bot and synced
async def load_extensions():
    await bot.load_extension("cogs.ScoringGuide")
    await bot.load_extension("cogs.NoBlueBanners")
    await bot.load_extension("cogs.TeamData")
    await bot.load_extension("cogs.Status")
    await bot.load_extension("cogs.Watch")
    if not disable_attendance:
        await bot.load_extension("cogs.MarkHere")
    print("Extensions all loaded")


# Loads slash commands, starts the bot
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
