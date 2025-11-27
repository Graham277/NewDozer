import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load all cogs on startup
@bot.event
async def on_ready():
    await bot.tree.sync(guild=None)
    print("Slash commands synced.")

async def load_extensions():
    await bot.load_extension("cogs.ScoringGuide")

if __name__ == "__main__":
    import asyncio
    asyncio.run(load_extensions())

    from dotenv import load_dotenv
    import os
    load_dotenv()
    token = os.getenv("token")
    bot.run(token)
