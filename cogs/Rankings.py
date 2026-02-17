import os

import discord
import requests
import statbotics
from discord import app_commands
from discord.ext import commands


class Rankings(commands.Cog):
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
        name="rankings",
        description="Get the rankings from an event"
    )
    # This is how parameters are created for slash commands. Remove if no parameters
    @app_commands.describe(
        event_key="Event key. ex. '2025oncmp1' (2025 Ontario DCMP Science) or '2025onham' (2025 McMaster U Event)"
    )
    async def rankings(self, interaction: discord.Interaction, event_key: str):

        await interaction.response.defer()

        try:
            tba_key = os.getenv("tba_key")
            headers = {"X-TBA-Auth-Key": tba_key}

            data_request = requests.get(f"https://www.thebluealliance.com/api/v3/event/{event_key}/rankings", headers=headers)

            if data_request.status_code == 401:
                return await interaction.followup.send(f"Provide a valid TBA auth key to use TBA commands")

            if data_request.status_code == 404:
                return await interaction.followup.send("Invalid event key")

            if data_request.status_code != 200:
                print(data_request.status_code)
                return await interaction.followup.send(f"TBA did not provide a response")

            data = data_request.json()

            if not data or 'rankings' not in data:
                return await interaction.followup.send("No ranking data found for this event.")

            # Spaces per section
            header = f"{'Rank':<4} | {'Team':<4} | {'RP':<3} | {'RS':<4} | {'W-L-T':<8}\n"
            divider = "-" * len(header) + "\n"
            
            rows = ""
            for entry in data['rankings'][:10]: # top 10 teams
                rank = entry['rank']
                team = entry['team_key'].replace('frc', '')
                rec = entry['record']
                wlt = f"{rec['wins']}-{rec['losses']}-{rec['ties']}"
                rp = entry['extra_stats'][0]
                ranking_score = round(rp / entry['matches_played'], 2)

                rows += f"{rank:<4} | {team:<4} | {rp:<3} | {ranking_score:<4} | {wlt:<8}\n"

            final_table = f"```\n{header}{divider}{rows}```"

            sb = statbotics.Statbotics()
            name = sb.get_event(event_key, ['name'])
            name = name['name']

            embed = discord.Embed(
                title=f"Rankings for {name}",
                description=final_table,
                color=discord.Color.light_gray()
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            return await interaction.followup.send(f"An error occurred:\n```\n{e}\n```")


async def setup(bot):
    await bot.add_cog(Rankings(bot))
