# This slash command returns the current status of the blue alliance (down completely, datafeed down, up, not logged in, etc.)

import os

import discord
import requests
import statbotics
from discord import app_commands
from discord.ext import commands

class StatboticsStatus(commands.Cog):
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
        name="statbotics_status",
        description="Get the current status of statbotics"
    )
    async def status(self, interaction: discord.Interaction):

        await interaction.response.defer()

        try:

            sb = statbotics.Statbotics()
            try:
                sb.get_team(2200)
                is_stat_api = True
            except:
                is_stat_api = False

            try:
                requests.get("https://statbotics.io/")
                web_status = "Statbotics website appears to be functioning correctly"
            except:
                web_status = "Statbotics website is not functioning correctly"

            if is_stat_api:
                embed = discord.Embed(
                    title=f"Statbotics Status",
                    description="Statbotics API appears to be functioning correctly\n"
                                f"{web_status}",
                    color=discord.Color.dark_blue()
                )
            else:
                embed = discord.Embed(
                    title=f"Statbotics Status",
                    description="Statbotics API appears to *not* be functioning correctly\n"
                                f"{web_status}",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            return await interaction.followup.send(f"An error occurred:\n```\n{e}\n```")


async def setup(bot):
    await bot.add_cog(StatboticsStatus(bot))
