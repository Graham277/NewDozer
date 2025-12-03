import os

import discord
import statbotics
from discord import app_commands
from discord.ext import commands


class Watch(commands.Cog):
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
        name="watch",
        description="Get the url for the livestream of an event"
    )
    # This is how parameters are created for slash commands. Remove if no parameters
    @app_commands.describe(
        event_key="Event key. ex. '2025oncmp1' (2025 Ontario DCMP Science) or '2025onham' (2025 McMaster U Event)"
    )
    async def watch(self, interaction: discord.Interaction, event_key: str):

        await interaction.response.defer()

        try:
            sb = statbotics.Statbotics()
            data = sb.get_event(event_key, ['name', 'district', 'status', 'video'])

            if data['status'] == "Completed":
                await interaction.followup.send(f"{data['name']} {event_key[:4]} is completed and can no longer be viewed")
            else :
            # Embed:
                embed = discord.Embed(
                    title=f"Watch {data['name']}",
                    description=f"View here: {data['video']}",
                    color=discord.Color.blurple() # No reason for this colour, it's just fun
                )
                await interaction.followup.send(embed=embed)

        except Exception as e:
            return await interaction.followup.send(f"An error occurred:\n```\n{e}\n```")


async def setup(bot):
    await bot.add_cog(Watch(bot))
