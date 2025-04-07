__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .GameControllerDiscord import GameControllerDiscord
from .GameGuild import GameGuild
from .HighScoreCreator import HighScoreCreator
from .ICommandHandler import ICommandHandler
from .PlayerStat import PlayerStat
from .RankImgCreator import RankImgCreator

from config.ClassLogger import ClassLogger, LogLevel
from discord.app_commands.commands import Command
from game.GameStore import GameStore
from game.PersistentStats import PersistentStats
from typing import Optional, cast

ScoreChoices = [
    discord.app_commands.Choice(name="All-time", value=PersistentStats.ITEM_TOTAL),
    discord.app_commands.Choice(name="Monthly", value=PersistentStats.ITEM_MONTH),
    discord.app_commands.Choice(name="Weekly", value=PersistentStats.ITEM_WEEK)
]
COOLDOWN = 60.0

class PlayerCommandHandler(ICommandHandler):
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        super().__init__()
        self.commandTimestamps: dict[str, float] = {}
        self.listCommands = [
            Command(
                name="rank",
                description="Get player game rank",
                callback=self.playerRank
            ),
            Command(
                name="leaderboard",
                description="Show the game leaderboard",
                callback=self.leaderboard
            ),
            Command(
                name="stats",
                description="Get detailed player game stats",
                callback=self.stats
            )
        ]

    @discord.app_commands.describe(member="Player to get rank of")
    @discord.app_commands.checks.cooldown(rate=1, per=COOLDOWN, key=lambda i: (i.guild_id, i.user.id))
    async def playerRank(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        PlayerCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Slash command playerRank called.")
        playerID = interaction.user.id if not member else member.id
        playerName = interaction.user.name if not member else member.name
        guild: Optional[GameGuild] = await self._getGuild(interaction)

        # Make sure the guild instance exists
        if not guild:
            await interaction.response.send_message("\U00002753 Error processing command.")
            return

        # Send back in-work response
        await interaction.response.defer(thinking=True)

        # Get player ordinal
        playerOrd = guild.persistentStats.getPlayer(playerID)
        if not playerOrd:
            await interaction.followup.send(f"\U00002753 Can't find player data for \"{playerName}\".", ephemeral=True)
            return

        # Create rank image, and send followup
        await interaction.followup.send(file=await RankImgCreator(interaction.client, playerOrd).createAsset())

    @discord.app_commands.describe(group="Leaderboard class type. Default = All-time")
    @discord.app_commands.choices(group=ScoreChoices)
    @discord.app_commands.checks.cooldown(rate=1, per=COOLDOWN, key=lambda i: i.guild.id if i.guild else i.user.id)
    async def leaderboard(self, interaction: discord.Interaction, group: Optional[str]):
        PlayerCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Slash command leaderboard (high scores) called.")
        guild: Optional[GameGuild] = await self._getGuild(interaction)

        # This is an expensive command, so disable during a running game
        if GameStore().getGame(interaction.guild_id or -1):
            await interaction.response.send_message("\U00002753 Leaderboard command is disabled while a game is running.")
            return

        # Make sure the guild instance exists
        if not guild:
            await interaction.response.send_message("\U00002753 Error processing command.")
            return

        # Make sure group is valid
        if not group or (group != PersistentStats.ITEM_TOTAL and\
                group != PersistentStats.ITEM_MONTH and\
                group != PersistentStats.ITEM_WEEK):
            group = PersistentStats.ITEM_TOTAL

        # Send back in-work response
        await interaction.response.defer(thinking=True)

        # Create high score graphic, and send followup
        await interaction.followup.send(file=await HighScoreCreator(interaction.client, guild.persistentStats).createLeaderboard(group))

    # This just returns an embed with the detailed player info
    @discord.app_commands.describe(member="Player to get detailed game stats for")
    async def stats(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        PlayerCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Slash command playerRank called.")
        playerID = interaction.user.id if not member else member.id
        playerName = interaction.user.name if not member else member.name
        guild: Optional[GameGuild] = await self._getGuild(interaction)
        playerOrd = guild.persistentStats.getPlayer(playerID) if guild else None

        # Make sure the guild instance exists
        if not guild:
            await interaction.response.send_message("\U00002753 Error processing command.")
            return

        if not playerOrd:
            await interaction.followup.send(f"\U00002753 Can't find player data for \"{playerName}\".", ephemeral=True)
            return

        # Send back in-work response
        await interaction.response.defer(thinking=True)

        # Get player ordinal
        await interaction.followup.send(embed=await PlayerStat(interaction.client, playerOrd).getEmbed())

    async def _getGuild(self, interaction: discord.Interaction) -> Optional[GameGuild]:
        guild: Optional[GameGuild] = None
        controller = GameStore().getController()

        if controller:
            dController = cast(GameControllerDiscord, controller)
            guild = dController.getGuild(interaction.guild_id or -1)

        if not guild:
            gName = interaction.guild.name if interaction.guild else "N/A"
            await interaction.response.send_message(f"\U0000274C There is no server registered for \"{gName}\"")

        return guild

