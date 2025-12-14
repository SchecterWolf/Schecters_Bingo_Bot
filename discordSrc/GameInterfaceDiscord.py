__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio
import discord

from .AdminChannel import AdminChannel
from .BingoChannel import BingoChannel
from .CallNoticeEmbed import CallNoticeEmbed
from .GameGuild import GameGuild
from .IAsyncDiscordGame import IAsyncDiscordGame
from .Mee6Controller import Mee6Controller
from .MockUserDMChannel import MockUserDMChannel
from .TaskPauseUserDMs import TaskPauseUserDMs
from .TaskProcessor import TaskProcessor
from .TaskStartUserDMs import TaskStartUserDMs
from .TaskStopUserDMs import TaskStopUserDMs
from .TaskUpdateUserDMs import TaskUpdateUserDMs
from .UserDMChannel import UserDMChannel

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS

from game.ActionData import ActionData
from game.Binglets import Binglets
from game.CallRequest import CallRequest
from game.Game import GameState
from game.NotificationMessageMaker import MakePlayersBingoNotif, MakePlayersCallNotif
from game.Player import Player
from game.Result import Result
from game.Sync import sync_aware

from typing import Optional, Set, cast

from youtube.GameInterfaceYoutube import GameInterfaceYoutube

class GameInterfaceDiscord(IAsyncDiscordGame):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client, gameGuild: GameGuild, gameType: str):
        super().__init__(gameGuild, gameType)
        self.bot = bot
        self.initialized = False
        self.taskProcessor = TaskProcessor(self.bot.loop)
        self.mee6Controller: Optional[Mee6Controller] = None
        self.lock = asyncio.Lock()
        self.YTiface: Optional[GameInterfaceYoutube] = None
        self.channelAdmin = None
        self.channelBingo = None

        Config().resetConfig()
        Binglets(gameType).reset()

        if Config().getConfig("YTEnabled", False):
            self.YTiface = GameInterfaceYoutube(self)

        if Config().getConfig("EXPEnabled", False):
            self.mee6Controller = Mee6Controller(gameGuild.channelAdmin)

        # Game view states
        self.viewState = GameState.NEW
        self.debugMode = Config().getConfig("Debug", False)

    async def init(self) -> Result:
        if self.initialized:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, "Game interface has already been initialized, skipping.")
            return Result(True)

        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord interface initializing.")
        ret = Result(True)

        if self.game.gameType != GLOBALVARS.GAME_TYPE_DEFAULT and self.game.gameType not in Config().getConfig("GameTypes", []):
            ret.result = False
            ret.responseMsg = f"Game started with an invalid game mode type \"{self.game.gameType}\""

        # Init the game obj
        if ret.result and not self.game.initGame(self.gameGuild.persistentStats):
            ret.result = False
            ret.responseMsg = "There was a problem initializing the game."

        # Bingo view init
        if ret.result:
            self.channelBingo = BingoChannel(self.bot, self.gameGuild)

        # Admin view init
        if ret.result:
            self.channelAdmin = AdminChannel(self.gameGuild, self.game.gameType)

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
        async with self.lock:
            return await self._start()

    async def _start(self) -> Result:
        self.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord game interface starting.")
        ret = Result(True)

        # Verify initialized
        if not self.initialized:
            ret.result = False
            ret.responseMsg = "Bot has not been initialized, cannot start the game."

        # Make sure the game isn't already started
        if self.viewState == GameState.STARTED:
            return ret

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
        async with self.lock:
            return await self._destroy()

    async def _destroy(self) -> Result:
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, f"Guild game destroyed: {self.gameGuild.guildID}.")
        await self._stop()
        self.game.destroyGame()
        if self.YTiface:
            self.YTiface.destroy()

        self.viewState = GameState.DESTROYED

        return Result(True)

    async def stop(self) -> Result:
        async with self.lock:
            return await self._stop()

    async def _stop(self) -> Result:
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, f"Stopping game for guild ID {self.gameGuild.guildID}.")

        # Make sure the game isn't already stopped
        if self.viewState == GameState.STOPPED:
            return Result(True)

        # We have to grab the list of players before stopping the game because they get cleared
        players = self.game.getAllPlayers()

        ret = self.game.stopGame()
        if not ret.result:
            return ret

        if self.YTiface:
            self.YTiface.stop()

        # Update the user DM views
        for player in players:
            self.taskProcessor.addTask(TaskStopUserDMs(player))

        if self.mee6Controller:
            await self.mee6Controller.issueEXP(players)

        await self._crankStateViews()

        # Stop the task processor
        self.taskProcessor.stop()

        return Result(True)

    @sync_aware
    async def pause(self, data: ActionData) -> Result:
        self.taskProcessor.pause()
        async with self.lock:
            ret = await self._pause(data)
        self.taskProcessor.resume()
        return ret

    async def _pause(self, data: ActionData) -> Result:
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_INFO, f"Pausing bingo game.")

        # Make sure the game isn't already paused
        if self.viewState == GameState.PAUSED:
            return Result(True)

        # Pause the internal game
        ret = self.game.pauseGame()
        if not ret.result:
            return ret

        # Send pause to the YT iface, we don't care if its successful or not
        if self.YTiface:
            self.YTiface.pause()

        await self._crankStateViews()
        await self._followup(data)

        self.finalizeAction(data)
        return Result(True)

    @sync_aware
    async def resume(self, data: ActionData) -> Result:
        self.taskProcessor.pause()
        async with self.lock:
            ret = await self._resume(data)
        self.taskProcessor.resume()
        return ret

    async def _resume(self, data: ActionData) -> Result:
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_INFO, f"Resuming bingo game.")

        # Make sure the game isn't already started:
        if self.viewState == GameState.STARTED:
            return Result(True)

        self.game.resumeGame()
        if self.YTiface:
            self.YTiface.resume()

        await self._crankStateViews()
        await self._followup(data)

        self.finalizeAction(data)
        return Result(True)

    @sync_aware
    async def addPlayer(self, data: ActionData) -> Result:
        self.taskProcessor.pause()
        async with self.lock:
            ret = await self._addPlayer(data)
        self.taskProcessor.resume()
        return ret

    async def _addPlayer(self, data: ActionData) -> Result:
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Attempting to add player...")
        ret = Result(False)
        interaction: discord.Interaction = data.get("interaction")
        user = interaction.user

        # Verify initialized
        if not self.initialized:
            ret.responseMsg = "Discord interface not initialized, cannot add player."
        elif not user.dm_channel and not self.debugMode:
            ret.responseMsg = "Interaction issued with an empty DM channel, cannot add player."
        else:
            ret.result = True

        # Add player to game
        if ret.result:
            ret = self.game.addPlayer(user.display_name, user.id)

        # Start the player DM view
        if ret.result and not ret.additional:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_ERROR, "Internal error! Was expecting a play in additionals.")
            ret.result = False
        elif ret.result:
            player = cast(Player, ret.additional)

            if user.dm_channel:
                dmChannel = UserDMChannel(self.gameGuild.guildID, user.dm_channel, player)
            else:
                mockChannel: discord.DMChannel = data.get("mockDMChannel")
                dmChannel = MockUserDMChannel(mockChannel, player)

            player.ctx = dmChannel
            await dmChannel.setViewStarted()

        # Update the bingo channel game status embed
        # Note: The 'refresh' attr is not normally used except for the bulk add debug command,
        #       which sets it to false so the bingo channel isn't spammed
        refresh = data.get("refresh") if data.has("refresh") else True
        if ret.result and refresh and self.channelBingo:
            await self.channelBingo.refreshGameStatus()

        if ret.result and self.YTiface:
            data.add(displayName=user.display_name)
            self.YTiface.addPlayer(data)

        if ret.result:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Successfully added player {user.display_name} ({user.id})")
        else:
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
            if interaction.user.dm_channel:
                await interaction.user.dm_channel.send(ret.responseMsg)

        self.finalizeAction(data)
        return ret

    @sync_aware
    async def kickPlayer(self, data: ActionData) -> Result:
        self.taskProcessor.pause()
        async with self.lock:
            ret = await self._kickPlayer(data)
        self.taskProcessor.resume()
        return ret

    async def _kickPlayer(self, data: ActionData) -> Result:
        ret = Result(False)
        user: discord.Member = data.get("member")
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Kicking player {user.display_name} ({user.id})")

        if not self.initialized:
            ret.responseMsg = "Discord interface not initialized, cannot kick player."
            return ret

        # Kick the player from the game
        ret = self.game.kickPlayer(user.id)

        # Refresh views
        if ret.result and self.channelBingo:
            await self.channelBingo.refreshGameStatus()

        # Update the user view
        if ret.result:
            action = "banned" if data.has("banned") else "kicked"
            kickedPlayer = cast(Player, ret.additional)
            if kickedPlayer.ctx:
                await kickedPlayer.ctx.setViewKicked(action)

        if ret.result and self.YTiface:
            data.add(displayName=user.display_name)
            self.YTiface.kickPlayer(data)

        self.finalizeAction(data)
        return ret

    @sync_aware
    async def banPlayer(self, data: ActionData) -> Result:
        self.taskProcessor.pause()
        async with self.lock:
            ret = await self._banPlayer(data)
        self.taskProcessor.resume()
        return ret

    async def _banPlayer(self, data: ActionData) -> Result:
        data.add(banned=True)
        ret = await self._kickPlayer(data)
        user: discord.Member = data.get("member")
        GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Banning player {user.display_name} ({user.id})")

        # Ban player regardless of kickPlayer result
        self.game.banPlayer(user.id, user.display_name)
        ret.result = True # Banning always succeeds

        if self.YTiface:
            data.add(displayName=user.display_name)
            self.YTiface.kickPlayer(data)

        self.finalizeAction(data)
        return ret

    @sync_aware
    async def makeCall(self, data: ActionData) -> Result:
        self.taskProcessor.pause()
        async with self.lock:
            ret = await self._makeCall(data)
        self.taskProcessor.resume()
        return ret

    async def _makeCall(self, data: ActionData) -> Result:
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
            bingStr = Binglets(self.game.gameType).getBingFromIndex(index).bingStr

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
            data.add(exempt=True)
            await self._deleteRequest(data)

        # Update the bingo channel with the call notice
        newPlayerBingos = ""
        if ret.result and self.channelBingo:
            newPlayerBingos = MakePlayersBingoNotif(list(newBingos))
            noticeEmbed = CallNoticeEmbed(Binglets(self.game.gameType).getBingFromIndex(index), list(markedPlayers), newPlayerBingos)
            await self.channelBingo.refreshGameStatus()
            await self.channelBingo.sendNoticeItem(embed=noticeEmbed, file=noticeEmbed.file)
        elif self.channelAdmin:
            await self.channelAdmin.sendNotice(f"(ERROR) {ret.responseMsg}")
            GameInterfaceDiscord.__LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)

        # Send notification to the YT livestream
        if ret.result and self.YTiface:
            newPlayerCalls = MakePlayersCallNotif(list(markedPlayers), 2)
            data = ActionData(index=index, newPlayerCalls=newPlayerCalls, newPlayerBingos=newPlayerBingos)
            self.YTiface.makeCall(data)

        self.finalizeAction(data)
        return ret

    @sync_aware
    async def requestCall(self, data: ActionData) -> Result:
        self.taskProcessor.pause()
        async with self.lock:
            ret = await self._requestCall(data)
        self.taskProcessor.resume()
        return ret

    async def _requestCall(self, data: ActionData) -> Result:
        callRequest: CallRequest = data.get("callRequest")
        # Verify initialized
        if not self.initialized and not self.channelAdmin:
            return Result(False, response="Discord interface not initialized, cannot handle request.")

        # Make a call request to the game
        ret = self.game.requestCall(callRequest)

        # Update the admin channel view
        if ret.result and self.channelAdmin:
            await self.channelAdmin.addCallRequest(ret.additional)

        # Let the player know that their call request was successfull
        player = callRequest.getPrimaryRequester()
        if ret.result and player.ctx:
            await player.ctx.sendNotice(ret.responseMsg)

        # Send notification to livestream
        if ret.result and self.YTiface:
            self.YTiface.requestCall(ActionData(callRequest=ret.additional))

        self.finalizeAction(data)
        return ret

    @sync_aware
    async def deleteRequest(self, data: ActionData) -> Result:
        self.taskProcessor.pause()
        async with self.lock:
            ret = await self._deleteRequest(data)
        self.taskProcessor.resume()
        return ret

    async def _deleteRequest(self, data: ActionData) -> Result:
        index: int = data.get("index")
        exempt: bool = data.get("exempt") if data.has("exempt") else False

        # Verify initialized
        if not self.initialized or not self.channelAdmin:
            return Result(False, response="Discord interface not initialized, cannot handle request.")

        # Delete  call request in the game
        ret = self.game.deleteRequest(index, exempt)

        # Update the admin channel view
        if ret.result and self.channelAdmin:
            await self.channelAdmin.delCallRequest(index)

        self.finalizeAction(data)
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

        # Set the bingo channels to starting state
        elif gameState == GameState.STARTED and self.viewState != GameState.STARTED:
            if self.channelBingo:
                await self.channelBingo.setViewStarted()
            if self.channelAdmin:
                await self.channelAdmin.setViewStarted()
            for player in self.game.getAllPlayers():
                self.taskProcessor.addTask(TaskStartUserDMs(player))

        # Set the views to paused state
        elif gameState == GameState.PAUSED and self.viewState != GameState.PAUSED:
            if self.channelAdmin:
                await self.channelAdmin.setViewPaused()
            if self.channelBingo:
                await self.channelBingo.setViewPaused()
            for player in self.game.getAllPlayers():
                self.taskProcessor.addTask(TaskPauseUserDMs(player))

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

    async def _followup(self, data: ActionData):
        interaction: discord.Interaction = data.get("interaction")
        # TODO SCH Audit if 'not' should be in this conditional. Update tests
        if not interaction.response.is_done():
            return

        msg: Optional[discord.WebhookMessage] = await interaction.followup.send(content=".", ephemeral=True)
        if msg:
            await cast(discord.WebhookMessage, msg).delete()

    def finalizeAction(self, data: ActionData):
        finalize = None

        if data.has(ActionData.FINALIZE_FUNCT):
            finalize = data.get(ActionData.FINALIZE_FUNCT)

        if callable(finalize):
            finalize()

