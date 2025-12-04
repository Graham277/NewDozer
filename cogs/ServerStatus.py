# This file is meant to be an example of how to create commands and is not loaded in main.py
# After making your command file add a line to load it in main.py
# The line will look like this in the load_extensions function:
    # await self.load_extension("cogs.Example")

import discord
import requests
from discord.ext import commands
from discord import app_commands
import os

class ServerStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Guild syncing
    guilds = [
        int(os.getenv("guild_id")) if os.getenv("guild_id") else None,
        int(os.getenv("dev_guild_id")) if os.getenv("dev_guild_id") else None,
    ]
    guilds = [g for g in guilds if g is not None]  # remove missing ones
    @app_commands.guilds(*guilds)

    # name must be lowercase and can only contain certain special characters like hyphens and underscores
    @app_commands.command(
        name="status",
        description="Check if TBA, Statbotics and the FIRST API are online"
    )

    async def execute(self, interaction: discord.Interaction):

        # get status
        tba_response = requests.get('https://www.thebluealliance.com/api/v3/status')
        tba_status = tba_response.status_code
        tba_datafeed_down = None
        tba_downtime_events = None
        if tba_status == 200:
            tba_datafeed_down = tba_response.json()['is_datafeed_down']
            tba_downtime_events = tba_response.json()['down_events']

        stat_response = requests.get('https://www.statbotics.io/event/api?rand=${dayjs().unix()}')
        stat_status = stat_response.status_code

        frc_response = requests.get('https://frc-api.firstinspires.org/v3.0?rand=${dayjs().unix()}')
        frc_status = frc_response.status_code

        # format everything

        message = "# Server Status\n"
        message += "**The Blue Alliance**"
        message += f"Status: {f"OK ({tba_status})" if tba_status < 400 else f"DOWN ({tba_status})"}\n"
        message += f"Is datafeed up? {":x:" if tba_datafeed_down else ":white_check_mark:"}\n"

        # send it
        await interaction.response.send_message(message)


async def setup(bot):
    await bot.add_cog(ServerStatus(bot))
