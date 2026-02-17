# This slash command returns the current status of the blue alliance (down completely, datafeed down, up, not logged in, etc.)

import os

import discord
import requests
import statbotics
from discord import app_commands
from discord.ext import commands

class TBAStatus(commands.Cog):
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
        name="tba_status",
        description="Get the current status of the blue alliance"
    )
    async def status(self, interaction: discord.Interaction):

        await interaction.response.defer()

        try:

            tba_key = os.getenv("tba_key")
            headers = {"X-TBA-Auth-Key": tba_key}

            data_request = requests.get(f"https://www.thebluealliance.com/api/v3/status", headers=headers)

            if data_request.status_code == 401:
                return await interaction.followup.send(f"Not logged into TBA. \nProvide valid TBA auth key to use TBA commands")

            if data_request.status_code != 200:
                return await interaction.followup.send(f"Could not access TBA")

            data = data_request.json()

            if data is None:
                return await interaction.followup.send(
                    "TBA can be accessed, but no data was returned"
                )

            is_datafeed_down = data["is_datafeed_down"]

            if is_datafeed_down:
                embed = discord.Embed(
                    title=f"TBA Status",
                    description="The Blue Alliance's datafeed is currently down",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title=f"TBA Status",
                    description="The Blue Alliance appears to be working",
                    color=discord.Color.dark_blue()
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            return await interaction.followup.send(f"An error occurred:\n```\n{e}\n```")


async def setup(bot):
    await bot.add_cog(TBAStatus(bot))
