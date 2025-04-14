__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import pytest
import random
import time

import test.utils.Classes as Classes
import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from config.ClassLogger import ClassLogger, LogLevel

from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord
from discordSrc.MockUserDMChannel import MockUserDMChannel

from game.ActionData import ActionData
from game.Bing import Bing
from game.Binglets import Binglets
from game.CallRequest import CallRequest
from game.Game import GameState
from game.Player import Player
from game.Result import Result

from enum import Enum
from typing import List, Optional, cast

@pytest.fixture(scope="function")
def mock_GameInterfaceDiscord(monkeypatch):
    mockedGuilds = Mocks.makeMockGuild()

    # We don't want to use the YT iface for these tests
    Utils.disableYTConfig(monkeypatch)

    # Enable debug because we want the bot to use the internal MockUserDMChannel
    Utils.setDebugConfig(monkeypatch, True)

    # Don't worry about rankings for this test
    Utils.disableLeaderboardRankings(mockedGuilds)

    # Mock the tracking classes
    Utils.setMockedUserDMChannel(monkeypatch)
    Utils.setMockedAdminChannel(monkeypatch)
    Utils.setMockedBingoChanel(monkeypatch)
    Utils.setMockedTaskProcessor(monkeypatch)

    iface = GameInterfaceDiscord(Mocks.makeMockBot(), mockedGuilds, Const.TEST_GAME_TYPE)
    yield iface

    # Make sure to stop the task processor, or the test will hang forever
    iface.taskProcessor.stop()

@pytest.mark.stress
@pytest.mark.asyncio
async def test_GameCanAdd100Players(mock_GameInterfaceDiscord, monkeypatch):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Override the setViewStarted DM Channel function so we can create players quicker
    # for the test
    origSetViewStarted = _overridePlayerViewStarted(monkeypatch)

    maxTimeoutSec = 10
    counter = 0
    testUserLimit = 100
    while counter < testUserLimit:
        cast(Classes.TestingBingoChannel, iface.channelBingo).resetTracking()

        playerName = f"Player {counter + 1}"
        playerID = -1 - counter

        # Add the user
        mockInteraction = Mocks.makeMockInteraction()
        mockInteraction.user = Mocks.makeMockUserWNOChannel(playerName, playerID)
        mockDMChannel = Mocks.makeMockDMChannel(mockInteraction.user)
        data = ActionData(
                    interaction=mockInteraction,
                    mockDMChannel=mockDMChannel
                )
        result: Result = await iface.addPlayer.__wrapped__(iface, data)
        player: Player = result.additional
        player.ctx.setViewStarted = origSetViewStarted

        assert result.result is True
        assert result.additional is not None
        assert result.additional in iface.game.players
        assert len(iface.game.players) == counter + 1
        assert player.valid is True
        assert player.card.getCardID() is not ""
        assert player.card.getCardOwner() == playerName
        assert player.card.hasBingo() is False
        assert player.card.getNumMarked() == 1
        assert player.ctx._channel == mockDMChannel
        assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True

        counter += 1

    # Make sure we can pause
    startTime = time.time()
    await Utils.setDiscordIfaceToState(iface, GameState.PAUSED)
    stopTime = time.time()
    assert stopTime - startTime < maxTimeoutSec, f"Pausing game not completed in less than {maxTimeoutSec} seconds"

    # Make sure we can resume
    data = ActionData(interaction=Mocks.makeMockInteraction())
    startTime = time.time()
    result: Result = await iface.resume.__wrapped__(iface, data)
    stopTime = time.time()
    assert result.result is True
    assert iface.viewState is GameState.STARTED
    assert iface.game.state is GameState.STARTED
    assert len(iface.game.players) == testUserLimit
    assert stopTime - startTime < maxTimeoutSec, f"Resuming game not completed in less than {maxTimeoutSec} seconds"

    # Make sure we can stop
    startTime = time.time()
    await Utils.setDiscordIfaceToState(iface, GameState.STOPPED)
    stopTime = time.time()
    assert len(iface.game.players) == 0
    assert stopTime - startTime < maxTimeoutSec, f"Stopping game not completed in less than {maxTimeoutSec} seconds"

@pytest.mark.stress
@pytest.mark.asyncio
async def test_MakingCallWith100PlayersDoesNotTimeOut(mock_GameInterfaceDiscord, monkeypatch):
    """
    Test that making a slot call with 100 players does not exceed a threshold time
    """
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Override the setViewStarted DM Channel function so we can create players quicker
    # for the test
    origSetViewStarted = _overridePlayerViewStarted(monkeypatch)

    # Add 100 players
    counter = 0
    testUserLimit = 100
    while counter < testUserLimit:
        cast(Classes.TestingBingoChannel, iface.channelBingo).resetTracking()

        playerName = f"Player {counter + 1}"
        playerID = -1 - counter

        # Add the user
        mockInteraction = Mocks.makeMockInteraction()
        mockInteraction.user = Mocks.makeMockUserWNOChannel(playerName, playerID)
        mockDMChannel = Mocks.makeMockDMChannel(mockInteraction.user)
        data = ActionData(
                    interaction=mockInteraction,
                    mockDMChannel=mockDMChannel
                )
        result: Result = await iface.addPlayer.__wrapped__(iface, data)
        assert result.result is True
        assert result.additional is not None
        cast(Player, result.additional).ctx.setViewStarted = origSetViewStarted

        counter += 1

    # Make a slot call
    data = ActionData(interaction=Mocks.makeMockInteraction(), index=1)
    result: Result = await iface.makeCall.__wrapped__(iface, data)
    assert result.result is True

    # Make sure the tasks take less than 2.5 minutes
    timeoutSec = 150
    assert cast(Classes.TestingTaskProcessor, iface.taskProcessor).processPendingTasks(timeoutSec), f"Processing tasks took longer than {timeoutSec} seconds."
    for task in cast(Classes.TestingTaskProcessor, iface.taskProcessor).addedTasks:
        assert task.taskExecuted

@pytest.mark.stress
@pytest.mark.asyncio
async def test_BotIsResponsiveWhileProcessingTasks(mock_GameInterfaceDiscord, monkeypatch):
    """
    Test that the bot can still process other game calls while a large number
    of tasks are being processed by the TaskProcessor
    """
    maxTimeoutSec = 30

    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    Utils.setUseFreeSpace(monkeypatch, False)
    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Override the setViewStarted DM Channel function so we can create players quicker
    # for the test
    origSetViewStarted = _overridePlayerViewStarted(monkeypatch)

    finalizeAddPlayerStopTimestamp = 0.0
    finalizeBanPlayerStopTimestamp = 0.0
    finalizeDelRequestStopTimestamp = 0.0
    finalizeKickPlayerStopTimestamp = 0.0
    finalizeMakeCallStopTimestmap = 0.0
    finalizeRequestStopTimestamp = 0.0

    def finalizeAddPlayerCallback():
        nonlocal finalizeAddPlayerStopTimestamp
        finalizeAddPlayerStopTimestamp = time.time()
    def finalizeBanPlayerCallback():
        nonlocal finalizeBanPlayerStopTimestamp
        finalizeBanPlayerStopTimestamp = time.time()
    def finalizeDelRequestCallback():
        nonlocal finalizeDelRequestStopTimestamp
        finalizeDelRequestStopTimestamp = time.time()
    def finalizeKickPlayerCallback():
        nonlocal finalizeKickPlayerStopTimestamp
        finalizeKickPlayerStopTimestamp = time.time()
    def finalizeMakeCallCallback():
        nonlocal finalizeMakeCallStopTimestmap
        finalizeMakeCallStopTimestmap = time.time()
    def finalizeRequestCallback():
        nonlocal finalizeRequestStopTimestamp
        finalizeRequestStopTimestamp = time.time()

    # Add 100 players
    counter = 0
    testUserLimit = 100
    players: List[Player] = []
    while counter < testUserLimit:
        cast(Classes.TestingBingoChannel, iface.channelBingo).resetTracking()

        playerName = f"Player {counter + 1}"
        playerID = -1 - counter

        # Add the user
        mockInteraction = Mocks.makeMockInteraction()
        mockInteraction.user = Mocks.makeMockUserWNOChannel(playerName, playerID)
        mockDMChannel = Mocks.makeMockDMChannel(mockInteraction.user)
        data = ActionData(
                    interaction=mockInteraction,
                    mockDMChannel=mockDMChannel
                )
        result: Result = await iface.addPlayer.__wrapped__(iface, data)
        assert result.result is True
        assert result.additional is not None
        cast(Player, result.additional).ctx.setViewStarted = origSetViewStarted

        players.append(result.additional)
        counter += 1

    # Start the mock processor
    mockTaskProcessor.startProcessing()

    # In order to stress the bot, make a call
    data = ActionData(interaction=Mocks.makeMockInteraction(), index=1)
    result: Result = await iface.makeCall.__wrapped__(iface, data)
    assert result.result is True
    assert Bing("", 1) in iface.game.calledBings

    # Making a call request while the bot is processing the former call should be responsive
    player: Player = random.choice(players)
    binglist: List[List[Bing]] = player.card.getCardBings()
    requestBing: Bing = binglist[random.randrange(len(binglist))][random.randrange(len(binglist[0]))]
    # Make sure the request bing does not match the bing index we previously made a call for
    while requestBing.bingIdx == 1:
        requestBing: Bing = binglist[random.randrange(len(binglist))][random.randrange(len(binglist[0]))]

    req = CallRequest(player, requestBing)
    data = ActionData(
                interaction=Mocks.makeMockInteraction(),
                callRequest=req,
                **{ActionData.FINALIZE_FUNCT: finalizeRequestCallback}
            )
    finalizeRequestStartTimestamp = time.time()
    result = await iface.requestCall.__wrapped__(iface, data)
    elapsedTime = finalizeRequestStopTimestamp - finalizeRequestStartTimestamp
    assert result.result is True
    assert len(iface.game.requestedCalls) == 1
    assert elapsedTime <= maxTimeoutSec, f"Request call timeout exceeded. Took {elapsedTime} seconds."

    # In order to stress the bot, make a another call
    data = ActionData(
                interaction=Mocks.makeMockInteraction(),
                index=2,
                **{ActionData.FINALIZE_FUNCT: finalizeMakeCallCallback}
            )
    finalizeMakeCallStartTimestamp = time.time()
    result = await iface.makeCall.__wrapped__(iface, data)
    elapsedTime = finalizeMakeCallStopTimestmap - finalizeMakeCallStartTimestamp
    assert result.result is True
    assert Bing("", 2) in iface.game.calledBings
    assert elapsedTime <= maxTimeoutSec, f"make call timeout exceeded. Took {elapsedTime} seconds."

    # Make another request
    player: Player = random.choice(players)
    binglist: List[List[Bing]] = player.card.getCardBings()
    requestBing: Bing = binglist[random.randrange(len(binglist))][random.randrange(len(binglist[0]))]
    while requestBing.bingIdx not in [1, 2]:
        requestBing: Bing = binglist[random.randrange(len(binglist))][random.randrange(len(binglist[0]))]

    req = CallRequest(player, requestBing)
    data = ActionData(
                interaction=Mocks.makeMockInteraction(),
                callRequest=req,
                **{ActionData.FINALIZE_FUNCT: finalizeRequestCallback}
            )
    finalizeDelRequestStartTimestamp = time.time()
    result = await iface.requestCall.__wrapped__(iface, data)
    elapsedTime = finalizeDelRequestStopTimestamp - finalizeDelRequestStartTimestamp
    assert result.result is True
    assert len(iface.game.requestedCalls) == 2
    assert elapsedTime <= maxTimeoutSec, f"Request call timeout exceeded. Took {elapsedTime} seconds."

    # Deleting a call request should be responsive
    data = ActionData(
                interaction=Mocks.makeMockInteraction,
                index=requestBing.bingIdx,
                **{ActionData.FINALIZE_FUNCT: finalizeDelRequestCallback}
            )
    result = await iface.deleteRequest.__wrapped__(iface, data)
    assert result.result is True
    assert len(iface.game.requestedCalls) == 1

    # Adding a new player should be responsive
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUserWNOChannel("New Player", Const.TEST_MOCK_VALID_USER_ID + counter)
    mockDMChannel = Mocks.makeMockDMChannel(mockInteraction.user)
    data = ActionData(
                interaction=mockInteraction,
                mockDMChannel=mockDMChannel,
                **{ActionData.FINALIZE_FUNCT: finalizeAddPlayerCallback}
            )
    finalizeAddPlayerStartTimestamp = time.time()
    result = await iface.addPlayer.__wrapped__(iface, data)
    elapsedTime = finalizeAddPlayerStopTimestamp - finalizeAddPlayerStartTimestamp
    assert result.result is True
    assert len(iface.game.players) == testUserLimit + 1
    assert elapsedTime <= maxTimeoutSec, f"Add player timeout exceeded. Took {elapsedTime} seconds."

    # Kicking a player should be responsive
    player = players[0]
    mockUser = Mocks.makeMockUserWNOChannel(player.card.getCardOwner(), player.userID)
    data = ActionData(
                member=mockUser,
                **{ActionData.FINALIZE_FUNCT: finalizeKickPlayerCallback}
            )
    finalizeKickPlayerStartTimestamp = time.time()
    result = await iface.kickPlayer.__wrapped__(iface, data)
    elapsedTime = finalizeKickPlayerStopTimestamp - finalizeKickPlayerStartTimestamp
    assert result.result is True
    assert len(iface.game.players) == testUserLimit
    assert player.userID in iface.game.kickedPlayers
    assert elapsedTime <= maxTimeoutSec, f"Kick player timeout exceeded. Took {elapsedTime} seconds."

    # Banning a player should be responsive
    def noOp(*args, **kwargs):
        pass
    iface.game.bannedPlayers.flush = noOp # Don't write out to file io
    player = players[1]
    mockUser = Mocks.makeMockUserWNOChannel(player.card.getCardOwner(), player.userID)
    data = ActionData(
                member=mockUser,
                **{ActionData.FINALIZE_FUNCT: finalizeBanPlayerCallback}
            )
    finalizeBanPlayerStartTimestamp = time.time()
    result = await iface.banPlayer.__wrapped__(iface, data)
    elapsedTime = finalizeBanPlayerStopTimestamp - finalizeBanPlayerStartTimestamp
    assert result.result is True
    assert iface.game.bannedPlayers.isBanned(player.userID)
    assert elapsedTime <= maxTimeoutSec, f"Ban player timeout exceeded. Took {elapsedTime} seconds."

    mockTaskProcessor.stopProcessing()

    # Make sure banned players are flushed (Singletons persist accross tests)
    iface.game.bannedPlayers.data = {}

@pytest.mark.stress
@pytest.mark.asyncio
async def test_BotCanChangeStatesWhileProcessingTasks(mock_GameInterfaceDiscord, monkeypatch):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Override the setViewStarted DM Channel function so we can create players quicker
    # for the test
    origSetViewStarted = _overridePlayerViewStarted(monkeypatch)

    maxTimeoutSec = 3

    # Add 100 players
    counter = 0
    testUserLimit = 100
    while counter < testUserLimit:
        cast(Classes.TestingBingoChannel, iface.channelBingo).resetTracking()

        playerName = f"Player {counter + 1}"
        playerID = -1 - counter

        # Add the user
        mockInteraction = Mocks.makeMockInteraction()
        mockInteraction.user = Mocks.makeMockUserWNOChannel(playerName, playerID)
        mockDMChannel = Mocks.makeMockDMChannel(mockInteraction.user)
        data = ActionData(
                    interaction=mockInteraction,
                    mockDMChannel=mockDMChannel
                )
        result: Result = await iface.addPlayer.__wrapped__(iface, data)
        assert result.result is True
        cast(Player, result.additional).ctx.setViewStarted = origSetViewStarted

        counter += 1

    # Start the mock processor
    mockTaskProcessor.startProcessing()

    # In order to stress the bot, make a call
    data = ActionData(interaction=Mocks.makeMockInteraction(), index=1)
    result: Result = await iface.makeCall.__wrapped__(iface, data)
    assert result.result is True

    # Pause the game
    startTime = time.time()
    result = await iface.pause.__wrapped__(iface, ActionData(interaction=Mocks.makeMockInteraction()))
    endTime = time.time()
    assert result.result is True
    assert endTime - startTime <= maxTimeoutSec, f"Pausing the game timed out, took {endTime - startTime} seconds."

    # Resume the game (started)
    startTime = time.time()
    result = await iface.resume.__wrapped__(iface, ActionData(interaction=Mocks.makeMockInteraction()))
    endTime = time.time()
    assert result.result is True
    assert endTime - startTime <= maxTimeoutSec, f"Resuming the game timed out, took {endTime - startTime} seconds."

    # Stop the game
    startTime = time.time()
    result = await iface.stop()
    endTime = time.time()
    assert result.result is True
    assert endTime - startTime <= maxTimeoutSec, f"Stopping the game timed out, took {endTime - startTime} seconds."

    mockTaskProcessor.stopProcessing()

@pytest.mark.stress
@pytest.mark.asyncio
async def test_BotHandlesChaoticRequestsWithManyPlayers(mock_GameInterfaceDiscord, monkeypatch):
    _logger = ClassLogger("test_BotHandlesChaoticRequestsWithManyPlayers")

    """
    This test will simulate a game with many players makeing call requests, making calls,
    pausing/resuming, deleting requests, random player adds, and stopping the game.
    """
    class Action(Enum):
        AddPlayer = 1,
        KickPlayer = 2,
        BanPlayer = 3,
        MakeCall = 4,
        RequestCall = 5,
        DeleteRequest = 6,
        PauseGame = 7,
        ResumeGame = 8

    numChaosIterations = 1000
    maxTimeoutSecState = 3

    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    Utils.setUseFreeSpace(monkeypatch, False)
    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Override the setViewStarted DM Channel function so we can create players quicker
    # for the test
    origSetViewStarted = _overridePlayerViewStarted(monkeypatch)

    # Banning a player should be responsive
    def noOp(*args, **kwargs):
        pass
    iface.game.bannedPlayers.flush = noOp # Don't write out to file io

    # Add 100 players to stress the bot
    playerCounter = 0
    testUserLimit = 100
    players: List[Player] = []
    while playerCounter < testUserLimit:
        cast(Classes.TestingBingoChannel, iface.channelBingo).resetTracking()

        playerName = f"Player {playerCounter + 1}"
        playerID = -1 - playerCounter

        # Add the user
        mockInteraction = Mocks.makeMockInteraction()
        mockInteraction.user = Mocks.makeMockUserWNOChannel(playerName, playerID)
        mockDMChannel = Mocks.makeMockDMChannel(mockInteraction.user)
        data = ActionData(
                    interaction=mockInteraction,
                    mockDMChannel=mockDMChannel
                )
        result: Result = await iface.addPlayer.__wrapped__(iface, data)
        assert result.result is True
        assert result.additional is not None
        cast(Player, result.additional).ctx.setViewStarted = origSetViewStarted

        players.append(result.additional)
        playerCounter += 1

    # Start the mock processor
    mockTaskProcessor.startProcessing()

    chaosCounter = 0
    while chaosCounter < numChaosIterations:
        randomAction = random.choice(list(Action))

        _logger.log(LogLevel.LEVEL_DEBUG, f"Performing chaos action ({chaosCounter} of {numChaosIterations}): {randomAction}")
        if randomAction == Action.AddPlayer:
            await _chaosAddPlayer(iface, players, origSetViewStarted, maxTimeoutSecState)
            playerCounter = len(players)
        elif randomAction == Action.KickPlayer:
            await _chaosKickPlayer(iface, players, maxTimeoutSecState)
            playerCounter = len(players)
        elif randomAction == Action.BanPlayer:
            await _chaosBanPlayer(iface, players, maxTimeoutSecState)
            playerCounter = len(players)
        elif randomAction == Action.MakeCall:
            await _chaosMakeCall(iface, maxTimeoutSecState)
        elif randomAction == Action.RequestCall:
            await _chaosRequestCall(iface, maxTimeoutSecState)
        elif randomAction == Action.DeleteRequest:
            await _chaosDeleteRequest(iface, maxTimeoutSecState)
        elif randomAction == Action.PauseGame:
            await _chaosPauseGame(iface, maxTimeoutSecState)
        elif randomAction == Action.ResumeGame:
            await _chaosResumeGame(iface, maxTimeoutSecState)

        chaosCounter += 1

    _logger.log(LogLevel.LEVEL_DEBUG, f"Finished chaos actions, shutting down the task processor")
    mockTaskProcessor.stopProcessing()

    # Make sure banned players are flushed (Singletons persist accross tests)
    iface.game.bannedPlayers.data = {}

async def _chaosAddPlayer(iface: GameInterfaceDiscord, players: List[Player], overrideViewStarted, timeout: int):
    newPlayerID = players[-1].userID - 1 if players else -1
    while (Player("", newPlayerID) in iface.game.players
           or iface.game.bannedPlayers.isBanned(newPlayerID)
           or newPlayerID in iface.game.kickedPlayers):
        newPlayerID -= 1
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUserWNOChannel(f"New Player {abs(newPlayerID)}", newPlayerID)
    mockDMChannel = Mocks.makeMockDMChannel(mockInteraction.user)

    stopTime = 0.0
    def finalize():
        nonlocal stopTime
        stopTime = time.time()

    data = ActionData(
                interaction=mockInteraction,
                mockDMChannel=mockDMChannel,
                **{ActionData.FINALIZE_FUNCT: finalize}
            )
    startTime = time.time()
    result = await iface.addPlayer.__wrapped__(iface, data)
    elapsedTime = stopTime - startTime
    if iface.game.state is GameState.PAUSED:
        assert result.result is False, f"Expected add player failure when game is paused."
        assert result.additional is None
    else:
        assert result.result is True, f"Failed to add player: {result.responseMsg}"
        assert result.additional is not None
        assert result.additional in iface.game.players
        cast(Player, result.additional).ctx.setViewStarted = overrideViewStarted
        players.append(result.additional)
    assert elapsedTime <= timeout, f"Add player (ID {newPlayerID}) timeout exceeded. Took {elapsedTime} seconds."

async def _chaosKickPlayer(iface: GameInterfaceDiscord, players: List[Player], timeout: int):
    if not players:
        return

    player = players.pop(random.randrange(len(players)))
    mockUser = Mocks.makeMockUserWNOChannel(player.card.getCardOwner(), player.userID)

    stopTime = 0.0
    def finalize():
        nonlocal stopTime
        stopTime = time.time()

    data = ActionData(
                member=mockUser,
                **{ActionData.FINALIZE_FUNCT: finalize}
            )
    startTime = time.time()
    result = await iface.kickPlayer.__wrapped__(iface, data)
    elapsedTime = stopTime - startTime
    assert result.result is True, f"Failed to kick player: {result.responseMsg}"
    assert elapsedTime <= timeout, f"Kick player (ID {player.userID}) timeout exceeded. Took {elapsedTime} seconds."
    assert player not in iface.game.players

async def _chaosBanPlayer(iface: GameInterfaceDiscord, players: List[Player], timeout: int):
    if not players:
        return

    # Banning a player should be responsive
    def noOp(*args, **kwargs):
        pass
    iface.game.bannedPlayers.flush = noOp # Don't write out to file io

    player = players.pop(random.randrange(len(players)))
    mockUser = Mocks.makeMockUserWNOChannel(player.card.getCardOwner(), player.userID)

    stopTime = 0.0
    def finalize():
        nonlocal stopTime
        stopTime = time.time()

    data = ActionData(
                member=mockUser,
                **{ActionData.FINALIZE_FUNCT: finalize}
            )
    startTime = time.time()
    result = await iface.banPlayer.__wrapped__(iface, data)
    elapsedTime = stopTime - startTime
    assert result.result is True, f"Failed to ban player: {result.responseMsg}"
    assert elapsedTime <= timeout, f"Ban player (ID {player.userID}) timeout exceeded. Took {elapsedTime} seconds."
    assert player not in iface.game.players

async def _chaosMakeCall(iface: GameInterfaceDiscord, timeout):
    # Get a random bing to call
    bing: Bing = random.choice(Binglets(iface.game.gameType).getBingletsCopy())

    stopTime = 0.0
    def finalize():
        nonlocal stopTime
        stopTime = time.time()

    data = ActionData(
                interaction=Mocks.makeMockInteraction(),
                index=bing.bingIdx,
                **{ActionData.FINALIZE_FUNCT: finalize}
            )
    startTime = time.time()
    result: Result = await iface.makeCall.__wrapped__(iface, data)
    elapsedTime = stopTime - startTime
    if iface.game.state is GameState.PAUSED:
        assert result.result is False, f"Expected make call to fail when the game is paused"
    else:
        assert result.result is True, f"Failed to make call: {result.responseMsg}"
        assert bing in iface.game.calledBings
        # Make sure a request with the same ID does not exist
        for req in iface.game.requestedCalls:
            assert req.requestBing.bingIdx != bing.bingIdx, f"Request for bing index ({bing.bingIdx}) still exists after the make call action."
    assert elapsedTime <= timeout, f"Make call for bing (Index {bing.bingIdx}) timeout exceeded. Took {elapsedTime} seconds."

async def _chaosRequestCall(iface: GameInterfaceDiscord, timeout):
    if not iface.game.players:
        return

    # Select a player that does not have a bingo already
    player: Optional[Player] = None
    tried: List[int] = []
    while not player:
        _player: Player = random.choice(list(iface.game.players))
        if _player.userID not in tried:
            tried.append(_player.userID)

        if not _player.card.hasBingo():
            player = _player
        # Bail if we have exhausted trying all players
        elif len(tried) >= len(iface.game.players):
            break

    # Give up if we couldn't find a suitable player
    if not player:
        return

    stopTime = 0.0
    def finalize():
        nonlocal stopTime
        stopTime = time.time()

    # Pick a bing at random from the player that hasnt been marked yet
    bings: List[List[Bing]]= player.card.getCardBings()
    bing: Bing = random.choice(random.choice(bings))
    _orig = bing
    x: int = bing.x
    y: int = bing.y
    while bing.marked:
        y = (y + 1) % len(bings)
        if y == 0:
            x = (x + 1) % len(bings[0])

        bing = bings[x][y]
        assert bing.bingIdx != _orig.bingIdx, f"Player (ID {player.userID}), doesn't have an unmarked bing, even though their card hasnt been marked as a bingo."

    # Check if the bing has already been requested before
    numPlayersRequested = 0
    requestExists = False
    for req in iface.game.requestedCalls:
        if req.requestBing.bingIdx == bing.bingIdx:
            requestExists = True
            numPlayersRequested = len(req.players)
            if req.hasPlayer(player):
                numPlayersRequested -= 1
            break

    req = CallRequest(player, bing)
    data = ActionData(
                interaction=Mocks.makeMockInteraction(),
                callRequest=req,
                **{ActionData.FINALIZE_FUNCT: finalize}
            )
    startTime = time.time()
    result = await iface.requestCall.__wrapped__(iface, data)
    reqResponse: CallRequest = result.additional
    elapsedTime = stopTime - startTime
    if iface.game.state is GameState.PAUSED:
        assert result.result is False, f"Expected request to fail when the game is paused."
        assert result.additional is None
    else:
        assert result.result is True, f"Failed to request call: {result.responseMsg}"
        assert result.additional is not None
        assert len(reqResponse.players) == numPlayersRequested + 1
        if not requestExists:
            assert req == reqResponse
        assert reqResponse.hasPlayer(player)
    assert elapsedTime <= timeout, f"Request call timeout exceeded. Took {elapsedTime} seconds."

async def _chaosDeleteRequest(iface: GameInterfaceDiscord, timeout):
    # Get a random bing to call
    bing: Bing = random.choice(Binglets(iface.game.gameType).getBingletsCopy())

    stopTime = 0.0
    def finalize():
        nonlocal stopTime
        stopTime = time.time()

    # Check if the bing has already been requested before
    hasRequest = False
    for req in iface.game.requestedCalls:
        if req.requestBing.bingIdx == bing.bingIdx:
            hasRequest = True
            break

    data = ActionData(
                interaction=Mocks.makeMockInteraction,
                index=bing.bingIdx,
                **{ActionData.FINALIZE_FUNCT: finalize}
            )
    startTime = time.time()
    result = await iface.deleteRequest.__wrapped__(iface, data)
    elapsedTime = stopTime - startTime
    if hasRequest:
        assert result.result is True, f"Failed to delete request: {result.responseMsg}"
    else:
        assert result.result is False, f"Failed to delete request: {result.responseMsg}"
    assert elapsedTime <= timeout, f"Request call timeout exceeded. Took {elapsedTime} seconds."

async def _chaosPauseGame(iface: GameInterfaceDiscord, timeout):
    startTime = time.time()
    result = await iface.pause.__wrapped__(iface, ActionData(interaction=Mocks.makeMockInteraction()))
    endTime = time.time()
    assert result.result is True, f"Failed to pause the game: {result.responseMsg}"
    assert iface.viewState is GameState.PAUSED
    assert iface.game.state is GameState.PAUSED
    assert endTime - startTime <= timeout, f"Pausing the game timed out, took {endTime - startTime} seconds."

async def _chaosResumeGame(iface: GameInterfaceDiscord, timeout):
    data = ActionData(interaction=Mocks.makeMockInteraction())
    startTime = time.time()
    result: Result = await iface.resume.__wrapped__(iface, data)
    stopTime = time.time()
    assert result.result is True, f"Failed to resume the game: {result.responseMsg}"
    assert iface.viewState is GameState.STARTED
    assert iface.game.state is GameState.STARTED
    assert stopTime - startTime < timeout, f"Resuming game not completed in less than {timeout} seconds"

def _overridePlayerViewStarted(monkeypatch):
    """
    Override the player's user DM's setViewStarted function to noOP. This is
    so large numbers of players can be added quickly in stress tests
    """
    async def noOp(self):
        pass

    origSetViewStarted = MockUserDMChannel.setViewStarted
    monkeypatch.setattr(MockUserDMChannel, "setViewStarted", noOp)

    return origSetViewStarted

