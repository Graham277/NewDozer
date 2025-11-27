import discord
from discord.ext import commands
from discord import app_commands
import os

class ScoringGuide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="scoring_guide", description="Send an image of the scoring guide")
    async def scoring_guide(self, interaction: discord.Interaction):
        img_path = os.path.join(os.path.dirname(__file__), "../images/ScoringGuide.png")
        file = discord.File(img_path, filename="ScoringGuide.png")
        await interaction.response.send_message(file=file)

async def setup(bot):
    await bot.add_cog(ScoringGuide(bot))
