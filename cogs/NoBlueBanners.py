import discord
from discord.ext import commands
from discord import app_commands
import os

class NoBlueBanners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Guild syncing
    guild_ids = []
    main = os.getenv("guild_id")
    dev = os.getenv("dev_guild_id")
    if main:
        guild_ids.append(int(main))
    if dev:
        guild_ids.append(int(dev))
    @app_commands.guilds(*guild_ids)

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
