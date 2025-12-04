import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

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
    await bot.load_extension("cogs.ServerStatus")
    await bot.load_extension("cogs.MarkHere")
    print("Extensions all loaded")

if __name__ == "__main__":
    import asyncio
    asyncio.run(load_extensions())
    token = os.getenv("token")
    bot.run(token)
