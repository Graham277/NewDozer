# This file is meant to be an example of how to create commands that use the TBA api and statbotics lib
# and is not loaded in main.py
# For info on the tba api: https://www.thebluealliance.com/apidocs/v3
# For info on the statbotics api: https://www.statbotics.io/docs/python
# After making your command file add a line to load it in main.py
# The line will look like this in the load_extensions function:
# await bot.load_extension("cogs.ExampleAPI")

import os

import discord
import requests
import statbotics
from discord import app_commands
from discord.ext import commands


class ExampleAPI(commands.Cog):
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
    async def example_api(self, interaction: discord.Interaction, parameter_name: int):

        await interaction.response.defer()

        try:
            tba_key = os.getenv("tba_key")
            headers = {"X-TBA-Auth-Key": tba_key}

            if not parameter_name:
                parameter_name = "Default here"

            data_request = requests.get(f"https://www.thebluealliance.com/api/v3/", headers=headers)

            if data_request.status_code == 401:
                return await interaction.followup.send(f"Provide a valid TBA auth key to use TBA commands")

            if data_request.status_code != 200:
                return await interaction.followup.send(f"TBA did not provide a response")

            data = data_request.json()

            if data is None:
                return await interaction.followup.send(
                    "No data."
                )

            sb = statbotics.Statbotics()
            stat_data = sb.get_team(2200)
            stat_data = stat_data["name"]

            # To return results, either send a message or send an embed
            # Remove the option you won't be using, as you can only respond once

            # Message:
            await interaction.followup.send_message("Example message here")

            # Embed:
            embed = discord.Embed(
                title=f"Description of content here",
                description="Here's the example data:\n" + data + stat_data,
                color=discord.Color.default()
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            return await interaction.followup.send(f"An error occurred:\n```\n{e}\n```")


async def setup(bot):
    await bot.add_cog(ExampleAPI(bot))
