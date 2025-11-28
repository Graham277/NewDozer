import base64
import io
import os

import discord
import requests
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

            data_request = requests.get(f"https://www.thebluealliance.com/api/v3/team/frc{team}", headers=headers)

            if data_request.status_code != 200:
                return await interaction.followup.send(f"Team {team} does not exist on The Blue Alliance.")

            data = data_request.json()

            if data is None:
                return await interaction.followup.send(
                    f"Team {team} exists, but has no data."
                )

            # Remove keys we don't want
            keys_to_remove = [
                "team_number"
                "address",
                "postal_code",
                "gmaps_place_id",
                "gmaps_url",
                "lat",
                "lng",
                "location_name",
                "key"
            ]
            for key in keys_to_remove:
                data.pop(key, None)

            # Rename name to sponsors
            data["sponsors"] = data.pop("name", None)

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
            output_lines = []
            for key in desired_order:
                if key in data:
                    value = data[key] if data[key] is not None else "None"
                    output_lines.append(f"**{key.replace('_', ' ').title()}**: {value}")
            output = "\n".join(output_lines)

            avatar_request = requests.get(
                f"https://www.thebluealliance.com/api/v3/team/frc{team}/media/2026",
                headers=headers
            )

            file = None
            avg_color_hex = None

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
                    file = discord.File(
                        io.BytesIO(raw_image),
                        filename="avatar.png"
                    )

            if not output:
                output = "No data available for this team."

            embed = discord.Embed(
                title=f"Team {team} Data",
                description=output,
                color=avg_color_hex if avg_color_hex else discord.Color.default()
            )

            if file:
                embed.set_thumbnail(url="attachment://avatar.png")
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            return await interaction.followup.send(f"An error occurred:\n```\n{e}\n```")


async def setup(bot):
    await bot.add_cog(TeamData(bot))
