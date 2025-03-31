__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IContentItem import IContentItem

from config.ClassLogger import ClassLogger
from config.Log import LogLevel
from discord.ui import View, Button
from game.ActionData import ActionData
from game.GameStore import GameStore
from typing import cast

class AddPlayerButton(View, IContentItem):
    __LOGGER = ClassLogger(__name__)

    __btn_label = "Play The Stream Bingo!"
    __btn_id = "bingo_button"

    __btn_confirm_label = "Begin Playing Bingo"
    __btn_confirm_id = "confirm_bingo_button"

    def __init__(self, gameID: int):
        View.__init__(self, timeout=None)
        IContentItem.__init__(self, "Join the game!")

        self.gameID = gameID
        self.confirmMsgID = -1

        button = Button(
            label=AddPlayerButton.__btn_label,
            style=discord.ButtonStyle.primary,
            custom_id=AddPlayerButton.__btn_id)
        button.callback = self.button_callback
        self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        AddPlayerButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Add player button pressed.")
        dmView = View(timeout=None)
        button = Button(
            label=AddPlayerButton.__btn_confirm_label,
            style=discord.ButtonStyle.success,
            custom_id=AddPlayerButton.__btn_confirm_id
            )
        button.callback = self.confirm_callback
        dmView.add_item(button)

        # TODO SCH Use a vulger language filter to check username before adding
        #           Useful libs: better_profanity, profanity-check
        try:
            message = await interaction.user.send(self._getGreeting(cast(discord.User, interaction.user)), view=dmView)
            self.confirmMsgID = message.id

            await interaction.response.send_message('Please check your DMs to begin playing!', ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(self._getCheckErrMessage, ephemeral=True)

    async def confirm_callback(self, interaction: discord.Interaction):
        AddPlayerButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Confirm add player button pressed.")
        # Remove the confirmation button regardless of success/failure
        channel = interaction.user.dm_channel
        if channel and self.confirmMsgID != -1:
            message = await channel.fetch_message(self.confirmMsgID)
            await message.delete()
            self.confirmMsgID = -1

        # Add the player to the game
        AddPlayerButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Calling add player callback...") # TODO SCH rm

        game = GameStore().getGame(self.gameID)
        if game:
            # TODO SCH Check if i even need to assign to an unused var (because of the sync_aware decorator)
            _ = game.addPlayer(ActionData(interaction=interaction, displayName=interaction.user.display_name))

    def _getGreeting(self, user: discord.User) -> str:
        return f"Greetings {user.display_name}!\n" +\
                "Schecter's Bingo Bot kindly invites you to play the Max livestream " +\
               f"bingo game!\nPlease click the \"{AddPlayerButton.__btn_confirm_label}\" " +\
                "button to begin playing, good luck!"

    def _getCheckErrMessage(self) -> str:
        return "I couldn't send you a DM :(\n" +\
                "Please enable the allow DM setting:\n1. Go to your discord settings\n" +\
                "2. Go to the 'Content & Social' section\n3. Under the 'Social " +\
                " permissions' section, select this server from the dropdown menu\n" +\
                "4. Toggle the 'Allow DMs from other memebers in this server' setting\n" +\
                f"5. Re-click the '{AddPlayerButton.__btn_label}' button"

