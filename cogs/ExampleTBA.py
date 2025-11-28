import os

import discord
import requests
from discord import app_commands
from discord.ext import commands

class ExampleTBA(commands.Cog):
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
        name="example_with_tba",
        description="Your description here"
    )

    # This is how parameters are created for slash commands. Remove if no parameters
    @app_commands.describe(
        parameter_name="Description of the parameter"
    )
    async def example_tba(self, interaction: discord.Interaction, parameter_name: int):

        await interaction.response.defer()

        try:
            tba_key = os.getenv("tba_key")
            headers = {"X-TBA-Auth-Key": tba_key}

            if not parameter_name:
                parameter_name = "Default here"

            data_request = requests.get(f"https://www.thebluealliance.com/api/v3/", headers=headers)

            if data_request.status_code != 200:
                return await interaction.followup.send(f"Does not exist on TBA")

            data = data_request.json()

            if data is None:
                return await interaction.followup.send(
                    "No data."
                )

            embed = discord.Embed(
                title=f"Description of content here",
                description=data,
                color=discord.Color.default()
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            return await interaction.followup.send(f"An error occurred:\n```\n{e}\n```")


async def setup(bot):
    await bot.add_cog(ExampleTBA(bot))
