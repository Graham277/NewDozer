import time
from math import floor

import discord
from discord.ext import commands
from discord import app_commands
import os

from AttendanceCodeCommunicator import AttendanceCodeCommunicator


class MarkHere(commands.Cog):

    communicator: AttendanceCodeCommunicator

    def __init__(self, bot):
        self.bot = bot
        self.communicator = AttendanceCodeCommunicator("db.sqlite")
        self.communicator.run() # starts background threa

    # Guild syncing
    guilds = [
        int(os.getenv("guild_id")) if os.getenv("guild_id") else None,
        int(os.getenv("dev_guild_id")) if os.getenv("dev_guild_id") else None,
    ]
    guilds = [g for g in guilds if g is not None]  # remove missing ones
    @app_commands.guilds(*guilds)

    # name must be lowercase and can only contain certain special characters like hyphens and underscores
    @app_commands.command(
        name='markhere',
        description='Mark yourself "present" on the attendance sheet.'
    )

    async def mark_here(self, interaction: discord.Interaction, code: int):

        timestamp = floor(time.time())
        if code not in self.communicator.db_temp:
            await interaction.response().send_message(content=f"Code does not exist! Was it typed correctly?")
            return
        # if code is no longer valid
        if timestamp > self.communicator.db_temp[code]:
            await interaction.response().send_message(content=f"Code is no longer valid!")
            return

        # so commit the record to memory
        self.communicator.db_connection.execute("INSERT INTO Attendance (user, timestamp) VALUES (?, ?)", (interaction.user.name, timestamp))
        await interaction.response().send_message(content=f"Marked {interaction.user.name} as present (code: {code})")

async def setup(bot):
    await bot.add_cog(MarkHere(bot))
