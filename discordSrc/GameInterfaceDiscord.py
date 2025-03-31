__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .AdminChannel import AdminChannel
from .BingoChannel import BingoChannel
from .CallNoticeEmbed import CallNoticeEmbed
from .GameGuild import GameGuild
from .IAsyncDiscordGame import IAsyncDiscordGame
from .MockUserDMChannel import MockUserDMChannel
from .TaskProcessor import TaskProcessor, TaskUpdateUserDMs
from .UserDMChannel import UserDMChannel

from config.ClassLogger import ClassLogger
from config.Config import Config
from config.Log import LogLevel

from game.ActionData import ActionData
from game.Binglets import Binglets
from game.CallRequest import CallRequest
from game.Game import GameState
from game.NotificationMessageMaker import MakePlayersBingoNotif, MakePlayersCallNotif
from game.Player import Player
from game.Result import Result
from game.Sync import sync_aware

from typing import Set, cast

from youtube.GameInterfaceYoutube import GameInterfaceYoutube

class GameInterfaceDiscord(IAsyncDiscordGame):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client, gameGuild: GameGuild):
        super().__init__(gameGuild)
        self.bot = bot
        self.initialized = False
        self.taskProcessor = TaskProcessor(self.bot.loop)

        if Config().getConfig("YTChannelID") and False: # TODO SCH comment back in once im done testing the refactor
            self.YTiface = GameInterfaceYoutube()
        else:
            self.YTiface = None

        # Game view states
        self.viewState = GameState.IDLE
        self.debugMode = Config().getConfig("Debug", False)

    async def init(self) -> Result:
        if self.initialized:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, "Game interface has already been initialized, skipping.")
            return Result(True)

        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord interface initializing.")
        ret = Result(True)

        # Init the game obj
        if not self.game.initGame(self.gameGuild.persistentStats):
            ret.result = False
            ret.responseMsg = "There was a problem initializing the game."

        # Bingo view init
        if ret.result:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Creating BingoChannel.") # TODO SCH
            self.channelBingo = BingoChannel(self.bot, self.gameGuild)

        # Admin view init
        if ret.result:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Creating AdminChannel.") # TODO SCH
            self.channelAdmin = AdminChannel(self.gameGuild)

        # Set internal states
        if ret.result:
            self.viewState = GameState.IDLE
            ret = await self._crankStateViews()

        # Setup the youtube iface
        if ret.result and self.YTiface:
            ret = self.YTiface.init()

        # Task processor init
        if ret.result:
            self.taskProcessor.init()

        self.initialized = ret.result

        if self.initialized:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_INFO, f"Discord interface initialized successfully.")
        else:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Discord interface failed to initialize: {ret.responseMsg}")

        return ret

    async def start(self) -> Result:
        self.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord game interface starting.")
        ret = Result(True)

        # Verify initialized
        if not self.initialized:
            ret.result = False
            ret.responseMsg = "Bot has not been initialized, cannot start the game."

        # Start the game
        if ret.result:
            ret = self.game.startGame()

        # Set the discord state views
        if ret.result:
            ret = await self._crankStateViews()

        if ret.result and self.YTiface:
            self.YTiface.start()

        if ret.result:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord game interface successfully started.")

        return ret

    async def destroy(self) -> Result:
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, f"Guild game destroyed: {self.gameGuild.guildID}.")
        await self.stop()
        self.game.destroyGame()
        if self.YTiface:
            self.YTiface.destroy()
        return Result(True)

    async def stop(self) -> Result:
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, f"Stopping game for guild ID {self.gameGuild.guildID}.")
        # We have to grab the list of players before stopping the game because they get cleared
        players = self.game.getAllPlayers()
        self.game.stopGame()
        if self.YTiface:
            self.YTiface.stop()
        await self._crankStateViews()

        # Update the user DM views
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, "Attemping to set stopped view to all players") # TODO SCH rm
        for player in players:
            if player.ctx:
                await player.ctx.setViewStopped()

        # Stop the task processor
        self.taskProcessor.stop()

        return Result(True)

    @sync_aware
    async def pause(self) -> Result:
        if self.YTiface:
            self.YTiface.pause()
        return Result(False)

    @sync_aware
    async def resume(self) -> Result:
        if self.YTiface:
            self.YTiface.resume()
        return Result(False)

    @sync_aware
    async def addPlayer(self, data: ActionData) -> Result:
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Attempting to add player...")
        ret = Result(False)
        interaction: discord.Interaction = data.get("interaction")
        user = interaction.user

        # Verify initialized
        if not self.initialized:
            ret.responseMsg = "Discord interface not initialized, cannot add player."
        elif isinstance(user, discord.Member):
            ret.responseMsg = "Invalid interaction user type"
        elif not user.dm_channel and not self.debugMode:
            ret.responseMsg = "Interaction issued with an empty DM channel, cannot add player."
        else:
            ret.result = True

        # Add player to game
        if ret.result:
            ret = self.game.addPlayer(user.display_name, user.id)

        # Start the player DM view
        if ret.result:
            player = cast(Player, ret.additional)

            if user.dm_channel:
                GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Creating UserDMChannel for user {user.display_name}") # TODO SCH rm
                dmChannel = UserDMChannel(self.gameGuild.guildID, user.dm_channel, player)
            else:
                GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Creating MockUserDMChannel for user {user.display_name}") # TODO SCH rm
                mockChannel: discord.DMChannel = data.get("mockDMChannel")
                dmChannel = MockUserDMChannel(mockChannel, player)

            player.ctx = dmChannel
            await dmChannel.setViewStarted()

        if ret.result and self.YTiface:
            self.YTiface.addPlayer(data)

        if not ret.result:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
            if interaction.user.dm_channel:
                await interaction.user.dm_channel.send(ret.responseMsg)

        return ret

    @sync_aware
    async def makeCall(self, data: ActionData) -> Result:
        index: int = data.get("index")
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Call made for index: {index}")

        # Verify initialized
        if not self.initialized:
            return Result(False, response="Discord interface not initialized, cannot make a call.")

        # Make game call
        ret = self.game.makeCall(index)

        # Update all of players boards that had a match
        markedPlayers: Set[Player] = set()
        newBingos: Set[Player] = set()
        if ret.result:
            markedPlayers, newBingos = ret.additional
            bingStr = Binglets().getBingFromIndex(index).bingStr

            # Add all players with new bingos
            for player in newBingos:
                notifStr = f"Congratulations {player.card.getCardOwner()}, you have a BINGO!"
                task = TaskUpdateUserDMs(notifStr, player)
                self.taskProcessor.addTask(task)

            # Add the rest of the players
            for player in markedPlayers.difference(newBingos):
                notifStr = f"[Slot marked] {bingStr}"
                task = TaskUpdateUserDMs(notifStr, player)
                self.taskProcessor.addTask(task)

        # Remove any matching call requests
        if ret.result:
            await self._intrlDeleteRequest(index)

        # Update the bingo channel with the call notice
        newPlayerBingos = ""
        if ret.result:
            newPlayerBingos = MakePlayersBingoNotif(list(newBingos))
            noticeEmbed = CallNoticeEmbed(Binglets().getBingFromIndex(index), list(markedPlayers), newPlayerBingos)
            await self.channelBingo.refreshGameStatus()
            await self.channelBingo.sendNoticeItem(embed=noticeEmbed, file=noticeEmbed.file)
        else:
            await self.channelAdmin.sendNotice(f"(ERROR) {ret.responseMsg}")
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)

        # Send notification to the YT livestream
        if ret.result and self.YTiface:
            newPlayerCalls = MakePlayersCallNotif(list(markedPlayers), 4)
            data = ActionData(index=index, newPlayerCalls=newPlayerCalls, newPlayerBingos=newPlayerBingos)
            self.YTiface.makeCall(data)

        return ret

    @sync_aware
    async def requestCall(self, data: ActionData) -> Result:
        callRequest: CallRequest = data.get("callRequest")
        # Verify initialized
        if not self.initialized and not self.channelAdmin:
            return Result(False, response="Discord interface not initialized, cannot handle request.")

        # Make a call request to the game
        ret = self.game.requestCall(callRequest)

        # Update the admin channel view
        if ret.result:
            await self.channelAdmin.addCallRequest(ret.additional)

        # Let the player know that their call request was successfull
        if ret.result and callRequest.players and callRequest.players[0].ctx:
            await callRequest.players[0].ctx.sendNotice(ret.responseMsg)

        # Send notification to livestream
        if ret.result and self.YTiface:
            self.YTiface.requestCall(ActionData(callRequest=ret.additional))

        return ret

    @sync_aware
    async def deleteRequest(self, data: ActionData) -> Result:
        index: int = data.get("index")
        return await self._intrlDeleteRequest(index)

    async def _intrlDeleteRequest(self, index: int) -> Result:
        # Verify initialized
        if not self.initialized or not self.channelAdmin:
            return Result(False, response="Discord interface not initialized, cannot handle request.")

        # Delete  call request in the game
        ret = self.game.deleteRequest(index)

        # Update the admin channel view
        if ret.result:
            await self.channelAdmin.delCallRequest(index)

        return ret

    async def _crankStateViews(self) -> Result:
        ret = Result(True)
        gameState = self.game.getGameState().additional
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Cranking state views to ({gameState})...")

        # Init the views to the new game state
        if gameState == GameState.IDLE and self.viewState == GameState.IDLE:
            if self.channelAdmin:
                await self.channelAdmin.setViewNew()
            if self.channelBingo:
                await self.channelBingo.setViewNew()

        # Setup the bingo channels to starting state
        elif gameState == GameState.STARTED and self.viewState != GameState.STARTED:
            if self.channelAdmin:
                await self.channelAdmin.setViewStarted()
            if self.channelBingo:
                await self.channelBingo.setViewStarted()
            players = self.game.getAllPlayers()
            for player in players:
                await player.ctx.setViewStarted()

        # Set the views to the stopped state
        elif gameState == GameState.STOPPED:
            if self.channelAdmin:
                await self.channelAdmin.setViewStopped()
            if self.channelBingo:
                await self.channelBingo.setViewStopped()

        # Invalid state(s)
        else:
            ret.result = False
            ret.responseMsg = "Game and interface views are in invalid state pairs, " +\
                f"Game has state ({gameState}), Interface has view state ({self.viewState})"

        if ret.result:
            self.viewState = gameState

        return ret

