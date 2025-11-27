import discord
from discord.ext import commands
from discord import app_commands
import os

class NoBlueBanners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Guild syncing
    guilds = [
        int(os.getenv("guild_id")) if os.getenv("guild_id") else None,
        int(os.getenv("dev_guild_id")) if os.getenv("dev_guild_id") else None,
    ]
    guilds = [g for g in guilds if g is not None]  # remove missing ones
    @app_commands.guilds(*guilds)

    @app_commands.command(
        name="nobluebanners",
        description="🤨" # This is an emoji
    )

    async def no_blue_banners(self, interaction: discord.Interaction):
        img_path = os.path.join(os.path.dirname(__file__), "../images/NoBlueBanners.png")
        file = discord.File(img_path, filename="NoBlueBanners.png")
        await interaction.response.send_message(file=file)

async def setup(bot):
    await bot.add_cog(NoBlueBanners(bot))
