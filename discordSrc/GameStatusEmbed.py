__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord
import os
import textwrap

from .IAsyncDiscordGame import IAsyncDiscordGame

from discord import Embed
from config.ClassLogger import ClassLogger, LogLevel
from config.Config import GLOBALVARS
from game.GameStore import GameStore
from game.IGameInterface import IGameInterface
from game.PersistentStats import PlayerOrdinal, PersistentStats
from typing import Deque, List, cast

class GameStatusEmbed(Embed):
    __LOGGER = ClassLogger(__name__)
    __STATS_EMBED_AUTHOR = "Active Livestream Bingo: FiveM" # TODO SCH 'FiveM' will need to be configurable
    __ORDINALS = ["1st", "2nd", "3rd"]
    __ORDINAL_EMOJI = ["\U0001F947", "\U0001F948", "\U0001F949"]
    __INLINE_SPACER = "\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0"
    __INLINE_SPACER_BIGGER = f"{__INLINE_SPACER}{__INLINE_SPACER}"

    __FIELD_CALLS = "\U0001F5E3 Slots Called"
    __FIELD_PLAYERS = "\U0001F465 Active Players"
    __FIELD_TOP_PLAYERS = "Current Top Players"

    __LENGTH_MAX_CALLS = 25
    __WIDTH_MAX_BINGOS = 75

    def __init__(self, gameID: int):
        super().__init__()

        _iconName = os.path.basename(GLOBALVARS.IMAGE_BINGO_ICON)
        self.file = discord.File(GLOBALVARS.IMAGE_BINGO_ICON, filename=_iconName)
        self.gameID = gameID

        # Embed members
        self.set_author(name=GameStatusEmbed.__STATS_EMBED_AUTHOR, icon_url=f"attachment://{_iconName}")
        self.color = discord.Color.blue()

        self.refreshStats()

    def refreshStats(self):
        GameStatusEmbed.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Refreshing active game stats embed.")
        self.clear_fields()

        game = GameStore().getGame(self.gameID)
        if game:
            self._refreshTopPlayers(game)
            self._refreshPlayers(game)
            self._refreshCalls(game)

    def _refreshTopPlayers(self, game: IGameInterface):
        iface = cast(IAsyncDiscordGame, game)

        players = iface.game.getAllPlayers()
        topPlayers: Deque[PlayerOrdinal] = Deque()

        bingoBonus = iface.gameGuild.persistentStats.getBonus(PersistentStats.DATA_ITEM_BINGOS)
        callBonus = iface.gameGuild.persistentStats.getBonus(PersistentStats.DATA_ITEM_CALLS)

        # Top player title
        self.add_field(name=GameStatusEmbed.__FIELD_TOP_PLAYERS, value="\u00A0", inline=False)

        # Calculate top session players
        for player in players:
            pl = PlayerOrdinal(-1, player.card.getCardOwner())
            bingo = 1 if player.card.hasBingo() else 0
            slots = player.card.getNumMarked()
            points = (bingo * bingoBonus) + (slots * callBonus)
            pl.stats[PersistentStats.ITEM_TOTAL][PersistentStats.DATA_ITEM_BINGOS] = bingo
            pl.stats[PersistentStats.ITEM_TOTAL][PersistentStats.DATA_ITEM_CALLS] = slots
            pl.points[PersistentStats.ITEM_TOTAL] = points

            if points:
                idx = 0
                for index, qStat in enumerate(topPlayers):
                    if points > qStat.points[PersistentStats.ITEM_TOTAL]:
                        break
                    idx = index + 1
                topPlayers.insert(idx, pl)
                if len(topPlayers) > 3:
                    topPlayers.pop()

        for index, player in enumerate(topPlayers):
            bingos = player.stats[PersistentStats.ITEM_TOTAL][PersistentStats.DATA_ITEM_BINGOS]
            slots = player.stats[PersistentStats.ITEM_TOTAL][PersistentStats.DATA_ITEM_CALLS]
            val=f"\
__**{player.name}**__\n\
Bingos {bingos}\n\
{GameStatusEmbed.__INLINE_SPACER_BIGGER}{bingos * bingoBonus} Pts\n\
Slots Marked {slots}{GameStatusEmbed.__INLINE_SPACER}\n\
{GameStatusEmbed.__INLINE_SPACER_BIGGER}{slots * callBonus} Pts\n\
**{player.points[PersistentStats.ITEM_TOTAL]} Pts Total**"
            self.add_field(name=f"{GameStatusEmbed.__ORDINAL_EMOJI[index]} {GameStatusEmbed.__ORDINALS[index]} Player",
                           value=val, inline=True)


        # Pad out empty fields so we can get a new row for the next line item (Bingos)
        offset = len(topPlayers) if topPlayers else 0
        pad = 3 - len(topPlayers)
        for i in range(pad):
            self.add_field(name=f"{GameStatusEmbed.__ORDINAL_EMOJI[i + offset]} {GameStatusEmbed.__ORDINALS[i + offset]}", value="N/A", inline=True)

        self._addFieldSeparator()

    def _refreshPlayers(self, game: IGameInterface):
        allPlayers = game.game.getAllPlayers()
        players = "" if allPlayers else "[NONE]"

        for player in allPlayers:
            if players:
                players += ", "
            players += player.card.getCardOwner()

        players = textwrap.fill(players, width=GameStatusEmbed.__WIDTH_MAX_BINGOS)
        self.add_field(name=f"{GameStatusEmbed.__FIELD_PLAYERS} ({len(allPlayers)})", value=players, inline=False)
        self._addFieldSeparator()

    def _refreshCalls(self, game: IGameInterface):
        calledStrs: List[List[str]] = [[]]
        for slot in game.game.getCalls():
            calledRow = calledStrs[-1]
            if len(calledRow) >= GameStatusEmbed.__LENGTH_MAX_CALLS:
                calledStrs.append([slot.bingStr])
            else:
                calledStrs[-1].append(slot.bingStr)

        if not calledStrs[0]:
            self.add_field(name=GameStatusEmbed.__FIELD_CALLS, value="[NONE]", inline=False)
        else:
            for row in calledStrs:
                self.add_field(name=GameStatusEmbed.__FIELD_CALLS, value="\n".join(row), inline=True)

    def _addFieldSeparator(self):
        self.add_field(name="\u200b", value="\u200b", inline=False)

