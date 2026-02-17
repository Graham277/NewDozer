# This slash command returns simple data related to a team, given a team number
# It returns the data as an embed in discord
# It sends the "profile pic" of the team as the thumbnail of the embed
# The colour of the embed is determined by the average colour of the profile pic

import base64
import datetime
import io
import os

import discord
import requests
import statbotics
from PIL import Image
from discord import app_commands
from discord.ext import commands

class TeamData(commands.Cog):
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
        name="team_data",
        description="Fetches and returns data for the defined team"
    )
    @app_commands.describe(
        team="The team number to get data for"
    )
    async def team_data(self, interaction: discord.Interaction, team: int):

        await interaction.response.defer()

        try:
            tba_key = os.getenv("tba_key")
            headers = {"X-TBA-Auth-Key": tba_key}

            if not team:
                team = 2200

            # Get tba data
            tba_output = await get_tba_data(interaction, team, headers)

            # Get statbotics data
            mean_epa, overall_rank, district_rank = await get_statbotics_data(interaction, team)

            if mean_epa and overall_rank and district_rank and tba_output:
                output = (f"**EPA:** {mean_epa} "
                          f"\n**Global Rank (EPA):** {overall_rank} "
                          f"\n**District Rank (EPA):** {district_rank}\n")
                output += "\n".join(tba_output)
            else:
                output = "No data available for this team."

            # Get the avatar/pfp and the average color of it for the embed from a helper function
            avatar, avg_color_hex = get_avatar_and_color(team=team, headers=headers)

            # Create the embed to send
            embed = discord.Embed(
                title=f"Team {team} Data",
                description=output,
                color=avg_color_hex if avg_color_hex else discord.Color.default()
            )

            # If they have an avatar include it
            if avatar:
                embed.set_thumbnail(url="attachment://avatar.png")
                return await interaction.followup.send(embed=embed, file=avatar)
            else:
                return await interaction.followup.send(embed=embed)

        except Exception as e:
            return await interaction.followup.send(f"An error occurred:\n```\n{e}\n```")


async def get_tba_data(interaction: discord.Interaction, team, headers):
    data_request = requests.get(
        f"https://www.thebluealliance.com/api/v3/team/frc{team}",
        headers=headers
    )

    if data_request.status_code == 401:
        return await interaction.followup.send(f"Provide a valid TBA auth key to use TBA commands")

    if data_request.status_code != 200:
        return await interaction.followup.send(f"Team {team} does not exist on The Blue Alliance.")

    data = data_request.json()

    if data is None:
        return await interaction.followup.send(
            f"Team {team} exists, but has no data."
        )

    # Rename name to sponsors, since that's what it actually is
    data["sponsors"] = data.pop("name", None)

    # Set a desired order for them to be displayed
    desired_order = [
        "nickname",
        "rookie_year",
        "city",
        "state_prov",
        "country",
        "website",
        "sponsors"
    ]

    # Make the output human-readable and in order
    tba_output = []
    for key in desired_order:
        if key in data:
            value = data[key] if data[key] is not None else "None"

            tba_output.append(f"**{key.replace('_', ' ').title()}**: {value}")
    return tba_output

async def get_statbotics_data(interaction: discord.Interaction, team):
    sb = statbotics.Statbotics()
    year = datetime.datetime.now().year
    try:
        data = sb.get_team_year(team, year, ['epa'])
    except Exception as e:
        return await interaction.followup.send(f"An error occurred in statbotics:\n```\n{e}\n```")

    mean_epa = data["epa"]["total_points"]["mean"]
    overall_rank = data["epa"]["ranks"]["total"]["rank"]
    district_rank = data["epa"]["ranks"]["district"]["rank"]

    return mean_epa, overall_rank, district_rank


# Helper function to get the avatar of the team and calc it's average color
def get_avatar_and_color(team, headers):
    avatar_request = requests.get(
        f"https://www.thebluealliance.com/api/v3/team/frc{team}/media/2026",
        headers=headers
    )

    if avatar_request.status_code == 200:
        media_list = avatar_request.json()
        avatar_data = next(
            (m for m in media_list if m.get("type") == "avatar"), None
        )

        if avatar_data:
            # Decode the base64 image
            raw_image = base64.b64decode(
                avatar_data["details"]["base64Image"]
            )
            image = Image.open(io.BytesIO(raw_image))

            # Compute average color (lazy 1x1 resize method)
            pixel = image.resize((1, 1)).getpixel((0, 0))
            r, g, b = pixel[:3]  # take only RGB
            avg_color_hex = (r << 16) + (g << 8) + b

            # Prepare the image as a discord File
            avatar = discord.File(
                io.BytesIO(raw_image),
                filename="avatar.png"
            )

            return avatar, avg_color_hex
    return None, None


async def setup(bot):
    await bot.add_cog(TeamData(bot))
