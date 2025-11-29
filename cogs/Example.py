# This file is meant to be an example of how to create commands and is not loaded in main.py
# After making your command file add a line to load it in main.py
# The line will look like this in the load_extensions function:
# await bot.load_extension("cogs.Example")

import os

import discord
from discord import app_commands
from discord.ext import commands


class Example(commands.Cog):
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
    # name must be lowercase and can only contain certain special characters like hyphens and underscores
    @app_commands.command(
        name="example_test",
        description="Put a description of the command here"
    )
    async def example(self, interaction: discord.Interaction):

        # To return results, either send a message or send an embed
        # Remove the option you won't be using, as you can only respond once

        # Message:
        await interaction.response.send_message("This is an example")

        # Embed:
        embed = discord.Embed(
            title=f"Description of content here",
            description="Some description here",
            color=discord.Color.default()
        )
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Example(bot))
