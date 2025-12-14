__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "schecterwolfe@gmail.com"

import discord
from config.Config import Config
from functools import wraps

def require_gamemaster(func):
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction):
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            rolename = Config().getConfig("GameMasterRole", "-")
            if not member or not any(rolename == role.name for role in member.roles):
                await interaction.response.send_message(f"The role of \"{rolename}\" is required to use this feature.", ephemeral=True)
                return None
        return await func(self, interaction)
    return wrapper
