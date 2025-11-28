import discord
from discord.ext import commands
from discord import app_commands
import os

class ScoringGuide(commands.Cog):
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
        name="scoring_guide",
        description="Send the image of the scoring guide of points"
    )

    async def scoring_guide(self, interaction: discord.Interaction):
        img_path = os.path.join(os.path.dirname(__file__), "../images/ScoringGuide.png")
        file = discord.File(img_path, filename="ScoringGuide.png")
        await interaction.response.send_message(file=file)

async def setup(bot):
    await bot.add_cog(ScoringGuide(bot))