__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "schecterwolfe@gmail.com"

import pytest
import test.utils.Classes as Classes
import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from discordSrc.CallNoticeEmbed import CallNoticeEmbed
from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord
from discordSrc.TaskUserDMs import TaskUserDMs

from game.ActionData import ActionData
from game.Bing import Bing
from game.Binglets import Binglets
from game.CallRequest import CallRequest
from game.Game import GameState
from game.Player import Player
from game.Result import Result

from unittest.mock import MagicMock
from typing import Optional, cast

@pytest.fixture(scope="function")
def mock_GameInterfaceDiscord(monkeypatch):
    mockedGuilds = Mocks.makeMockGuild()

    # We don't want to use the YT iface for these tests
    Utils.disableYTConfig(monkeypatch)

    # Make sure we are using the debug setting when testing
    Utils.setDebugConfig(monkeypatch, True)

    # Don't worry about rankings for this test
    Utils.disableLeaderboardRankings(mockedGuilds)

    # Mock the tracking classes
    Utils.setMockedUserDMChannel(monkeypatch)
    Utils.setMockedAdminChannel(monkeypatch)
    Utils.setMockedBingoChanel(monkeypatch)

    iface = GameInterfaceDiscord(Mocks.makeMockBot(), mockedGuilds, Const.TEST_GAME_TYPE)
    yield iface

    # Make sure to stop the task processor, or the test will hang forever
    iface.taskProcessor.stop()

@pytest.fixture(scope="function")
def mock_GameInterfaceDiscordWNODebug(monkeypatch):
    mockedGuilds = Mocks.makeMockGuild()

    # We don't want to use the YT iface for these tests
    Utils.disableYTConfig(monkeypatch)

    # Disabling debug
    Utils.setDebugConfig(monkeypatch, False)

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

@pytest.mark.asyncio
async def test_SuccessfullyAddPlayer(mock_GameInterfaceDiscordWNODebug, monkeypatch):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    Utils.setRetroactiveCalls(monkeypatch, False)
    Utils.setUseFreeSpace(monkeypatch, False)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockInteraction = Mocks.makeMockInteraction()
    testUserName = "Schecter Wolf"
    mockInteraction.user = Mocks.makeMockUser(testUserName)
    mockDMChannel = mockInteraction.user.dm_channel
    mockInteraction.user.id = Const.TEST_MOCK_VALID_USER_ID
    mockFinalize = MagicMock()
    data = ActionData(
                interaction=mockInteraction,
                **{ActionData.FINALIZE_FUNCT: mockFinalize.finalize}
            )

    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional

    assert result.result is True
    assert result.additional is not None
    assert player in iface.game.players
    assert player.valid is True
    assert player.card.getCardID() is not ""
    assert player.card.getCardOwner() == testUserName
    assert player.card.hasBingo() is False
    assert player.card.getNumMarked() == 0
    assert player.ctx._channel == mockDMChannel
    assert cast(Classes.TestingUserDMChannel, player.ctx).setViewStartedCalled is True
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True
    mockFinalize.finalize.assert_called_once()

    # Test adding a player with free spaces enabled
    Utils.setUseFreeSpace(monkeypatch, True)
    testUserName = "Maxamili"
    data = _makeValidAddPlayerData(testUserName)
    data.get("interaction").user.id = Const.TEST_MOCK_VALID_USER_ID + 1

    result: Result = await iface.addPlayer.__wrapped__(iface, data)

    assert result.result is True
    assert result.additional is not None
    assert result.additional in iface.game.players
    assert cast(Player, result.additional).card.getCardOwner() == testUserName
    assert cast(Player, result.additional).card.hasBingo() is False
    assert cast(Player, result.additional).card.getNumMarked() == 1

@pytest.mark.asyncio
async def test_SuccessfullyAddPlayerInDebug(mock_GameInterfaceDiscord, monkeypatch):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    Utils.setRetroactiveCalls(monkeypatch, False)
    Utils.setUseFreeSpace(monkeypatch, False)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockInteraction = Mocks.makeMockInteraction()
    testUserName = "Schecter Wolf"
    mockInteraction.user = Mocks.makeMockUserWNOChannel(testUserName)
    mockDMChannel = Mocks.makeMockDMChannel(mockInteraction.user)
    mockFinalize = MagicMock()
    data = ActionData(
                interaction=mockInteraction,
                mockDMChannel=mockDMChannel,
                **{ActionData.FINALIZE_FUNCT: mockFinalize.finalize}
            )

    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player = result.additional

    assert result.result is True
    assert result.additional is not None
    assert result.additional in iface.game.players
    assert player.valid is True
    assert player.card.getCardID() is not ""
    assert player.card.getCardOwner() == testUserName
    assert player.card.hasBingo() is False
    assert player.card.getNumMarked() == 0
    assert player.ctx._channel == mockDMChannel
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True
    mockFinalize.finalize.assert_called_once()

@pytest.mark.asyncio
async def test_AddingInvalidPlayerFails(mock_GameInterfaceDiscordWNODebug):
    def testFailure(interface: GameInterfaceDiscord, result: Result):
        assert result.result is False
        assert result.additional is None
        assert len(iface.game.players) == 0
        if result.additional:
            assert cast(Classes.TestingUserDMChannel, result.additional.ctx).setViewStartedCalled is False
        assert cast(Classes.TestingBingoChannel, interface.channelBingo).refreshGameStatusCalled is False

    # Set the game to the valid started state
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Test not sending in the needed action data attributes throws exception
    with pytest.raises(ValueError):
        await iface.addPlayer.__wrapped__(iface, ActionData())

    # Test user not having a valid DM channel when not running in debug mode
    data = _makeValidAddPlayerData()
    data.get("interaction").user.dm_channel = None
    result = await iface.addPlayer.__wrapped__(iface, data)
    testFailure(iface, result)
    assert "empty DM channel" in result.responseMsg

    # Test user not having a valid user ID
    data = _makeValidAddPlayerData()
    data.get("interaction").user.id = -1
    result = await iface.addPlayer.__wrapped__(iface, data)
    testFailure(iface, result)
    assert "invalid ID" in result.responseMsg

    # Test user with vulger name can't be added
    data = _makeValidAddPlayerData()
    data.get("interaction").user.display_name = "Fuck You"
    result = await iface.addPlayer.__wrapped__(iface, data)
    testFailure(iface, result)
    assert "Player's name" in result.responseMsg

    # Test user can't be double added
    data = _makeValidAddPlayerData()
    result = await iface.addPlayer.__wrapped__(iface, data)
    assert result.result is True
    result = await iface.addPlayer.__wrapped__(iface, data)
    assert result.result is False
    assert "already playing" in result.responseMsg
    assert len(iface.game.players) == 1

@pytest.mark.asyncio
async def test_AddingPlayerInInvalidStatesFails(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord

    for state in Utils.getAllGameStatesOrder():
        await Utils.setDiscordIfaceToState(iface, state)

        # Skip the only valid state a player can be added in
        if state == GameState.STARTED:
            continue

        data = _makeValidAddPlayerData()
        result: Result = await iface.addPlayer.__wrapped__(iface, data)

        assert result.result is False, f"Add player result is expected to be False when in state {state}."
        assert result.additional is None
        assert len(iface.game.players) == 0
        if state == GameState.NEW:
            assert "interface not initialized" in result.responseMsg
        else:
            assert "New players cannot be added" in result.responseMsg
        if result.additional:
            assert cast(Classes.TestingUserDMChannel, result.additional.ctx).setViewStartedCalled is False
        if iface.channelBingo:
            assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is False

@pytest.mark.asyncio
async def test_SuccessfullyKickPlayer(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add player to the game
    data = _makeValidAddPlayerData()
    user = data.get("interaction").user
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Make the player have an outstanding call request
    mockInteraction = Mocks.makeMockInteraction()
    bing = player.card.getCardBings()[0][0]
    req = CallRequest(player, bing)
    data = ActionData(
                interaction=mockInteraction,
                callRequest=req
            )
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    # Add another
    data = _makeValidAddPlayerData("King")
    data.get("interaction").user.id = Const.TEST_MOCK_VALID_USER_ID + 1
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    assert result.result is True

    _resetTrackingClasses(iface)

    # Kick the first player I added. Only the ID matters
    data = ActionData(member=user)
    result: Result = await iface.kickPlayer.__wrapped__(iface, data)

    assert result.result is True
    assert result.additional == player
    assert Const.TEST_MOCK_VALID_USER_ID in iface.game.kickedPlayers
    assert player not in iface.game.players
    for req in iface.game.requestedCalls:
        assert req.hasPlayer(player) is False
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True
    assert cast(Classes.TestingUserDMChannel, player.ctx).setViewKickedCalled is True

@pytest.mark.asyncio
async def test_KickingPlayerInValidStateSucceeds(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add a player for each state we will test in
    playerID = Const.TEST_MOCK_VALID_USER_ID
    for state in [GameState.STARTED, GameState.PAUSED]:
        data = _makeValidAddPlayerData()
        data.get("interaction").user.id = playerID
        result: Result = await iface.addPlayer.__wrapped__(iface, data)
        assert result.result is True

        playerID += 1

    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Test kicking player from a state
    playerID = Const.TEST_MOCK_VALID_USER_ID
    for state in [GameState.STARTED, GameState.PAUSED]:
        # iface should already be started
        if state != GameState.STARTED:
            await Utils.setDiscordIfaceToState(iface, state)

        _resetTrackingClasses(iface)

        # Kick player
        user = Mocks.makeMockUser("player")
        user.id = playerID
        data = ActionData(member=user)
        result: Result = await iface.kickPlayer.__wrapped__(iface, data)

        # Verify kicked
        player = Player("", playerID)
        assert result.result is True, f"Player ID {playerID} failed to be kicked."
        assert result.additional == player
        assert playerID in iface.game.kickedPlayers
        assert player not in iface.game.players
        for req in iface.game.requestedCalls:
            assert req.hasPlayer(player) is False
        assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True
        assert cast(Classes.TestingUserDMChannel, result.additional.ctx).setViewKickedCalled is True

        playerID += 1

@pytest.mark.asyncio
async def test_KickingInvalidPlayerFails(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    nonExistPlayerID = 69420

    # Attempting to kick when the iface is not initialized fails
    user = Mocks.makeMockUser("Wessy")
    user.id = nonExistPlayerID
    kickData = ActionData(member=user)
    result: Result = await iface.kickPlayer.__wrapped__(iface, kickData)
    assert result.result is False
    assert "not initialized" in result.responseMsg
    assert iface.channelBingo is None

    # Add player to the game
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Test not sending in the needed action data attributes throws exception
    with pytest.raises(ValueError):
        await iface.kickPlayer.__wrapped__(iface, ActionData())

    _resetTrackingClasses(iface)

    # Kicking a player that doesn't exist fails
    result: Result = await iface.kickPlayer.__wrapped__(iface, kickData)
    assert result.result is False
    assert result.additional is None
    assert "No player" in result.responseMsg
    assert nonExistPlayerID not in iface.game.kickedPlayers
    assert player in iface.game.players # Make sure the original player is not kicked
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is False

@pytest.mark.asyncio
async def test_SuccessfullyBanPlayer(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Disable ban saving
    Utils.disableBanSaving(iface)

    # Add player to the game
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Make the player have an outstanding call request
    mockInteraction = Mocks.makeMockInteraction()
    bing = player.card.getCardBings()[0][0]
    req = CallRequest(player, bing)
    data = ActionData(
                interaction=mockInteraction,
                callRequest=req
            )
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    # Add another
    data = _makeValidAddPlayerData()
    user = data.get("interaction").user
    data.get("interaction").user.id = Const.TEST_MOCK_VALID_USER_ID + 1
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    playerBanned: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    _resetTrackingClasses(iface)

    # Ban the first player I added. Only the ID matters
    data = ActionData(member=user)
    result: Result = await iface.banPlayer.__wrapped__(iface, data)

    assert result.result is True
    assert result.additional is playerBanned
    assert player in iface.game.players # Make sure the original player is not banned
    assert result.additional not in iface.game.players
    assert iface.game.bannedPlayers.isBanned(playerBanned.userID)
    for req in iface.game.requestedCalls:
        assert req.hasPlayer(playerBanned) is False
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True
    assert cast(Classes.TestingUserDMChannel, playerBanned.ctx).setViewKickedCalled is True

    # Make sure banned players are flushed (Singletons persist accross tests)
    iface.game.bannedPlayers.data = {}

@pytest.mark.asyncio
async def test_BanningPlayerInValidStatesSucceeds(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)
    playerID = Const.TEST_MOCK_VALID_USER_ID

    # Disable ban saving
    Utils.disableBanSaving(iface)

    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add a player for each state we will test in
    for state in Utils.getAllGameStatesOrder():
        # Skip adding a player in this state, because it should be
        # impossible for players to be added while the game is NEW or IDLE
        if state == GameState.NEW or state == GameState.IDLE:
            continue

        data = _makeValidAddPlayerData()
        data.get("interaction").user.id = playerID
        result: Result = await iface.addPlayer.__wrapped__(iface, data)
        assert result.result is True

        playerID += 1

    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Test banning player from a state
    playerID = Const.TEST_MOCK_VALID_USER_ID
    for state in Utils.getAllGameStatesOrder():
        # Skip adding a player in this state, because it should be
        # impossible for players to be added while the game is NEW or IDLE
        if state == GameState.NEW or state == GameState.IDLE:
            continue

        # iface should already be started, but we need to test for this state
        if state != GameState.STARTED:
            await Utils.setDiscordIfaceToState(iface, state)

        _resetTrackingClasses(iface)

        # Ban player
        user = Mocks.makeMockUser("player")
        user.id = playerID
        data = ActionData(member=user)
        result: Result = await iface.banPlayer.__wrapped__(iface, data)

        # Verify banned
        player = Player("", playerID)
        assert result.result is True
        if state is not GameState.STOPPED and state is not GameState.DESTROYED:
            assert result.additional is not None
            assert player.userID == result.additional.userID
            assert playerID in iface.game.kickedPlayers, f"Player ID {playerID} should be kicked for the {state} game state."
            assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True
            assert cast(Classes.TestingUserDMChannel, result.additional.ctx).setViewKickedCalled is True
        assert player not in iface.game.players
        assert iface.game.bannedPlayers.isBanned(playerID)
        for req in iface.game.requestedCalls:
            assert req.hasPlayer(player) is False

        playerID += 1

    mockTaskProcessor.stopProcessing()

    # Make sure banned players are flushed (Singletons persist accross tests)
    iface.game.bannedPlayers.data = {}

@pytest.mark.asyncio
async def test_BanningInvalidPlayerFails(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)

    # Disable ban saving
    Utils.disableBanSaving(iface)

    # Add player to the game
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Test not sending in the needed action data attributes throws exception
    with pytest.raises(ValueError):
        await iface.banPlayer.__wrapped__(iface, ActionData())

    _resetTrackingClasses(iface)

    # Banning a player that doesn't exist fails
    nonExistPlayerID = 69420
    user = Mocks.makeMockUser("Devil")
    user.id = nonExistPlayerID
    kickData = ActionData(member=user)
    result: Result = await iface.banPlayer.__wrapped__(iface, kickData)
    assert result.result is True # Banning always returns true
    assert iface.game.bannedPlayers.isBanned(nonExistPlayerID) is True
    assert Const.TEST_MOCK_VALID_USER_ID not in iface.game.kickedPlayers # Make sure the original player is not kicked
    assert player in iface.game.players # Make sure the original player is not kicked
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is False

    mockTaskProcessor.stopProcessing()

    # Make sure banned players are flushed (Singletons persist accross tests)
    iface.game.bannedPlayers.data = {}

@pytest.mark.asyncio
async def test_SuccessfullyMakingCall(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)

    # Add player to the game
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Get a binglet from the added player's card
    bing = player.card.getCardBings()[0][0]

    # Add a call request to the game
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(
                interaction=mockInteraction,
                callRequest=req
            )
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    _resetTrackingClasses(iface, player)

    # Make a slot call
    mockInteraction = Mocks.makeMockInteraction()
    data = ActionData(interaction=mockInteraction, index=bing.bingIdx)
    result: Result = await iface.makeCall.__wrapped__(iface, data)
    markedPlayers, markedBingos = result.additional

    # Wait for the task process to finish
    mockTaskProcessor.processPendingTasks()

    # Verify success
    assert result.result is True
    assert len(markedPlayers) == 1
    assert len(markedBingos) == 0
    assert bing in iface.game.calledBings
    assert player in markedPlayers
    assert player.card.isCellMarked(bing.x, bing.y)
    for req in iface.game.requestedCalls:
        assert req.requestBing.bingIdx is not bing.bingIdx
    assert mockTaskProcessor.hasNoPendingTasks() is True
    assert len(mockTaskProcessor.taskIDs) == 0
    assert len(mockTaskProcessor.addedTasks) == 1
    assert mockTaskProcessor.addedTasks[0].internalTask.player == player
    assert mockTaskProcessor.addedTasks[0].taskExecuted is True
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).sendNoticeCalled is False
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True
    assert isinstance(cast(Classes.TestingBingoChannel, iface.channelBingo).noticeItem['embed'], CallNoticeEmbed)
    assert bing.bingStr in cast(Classes.TestingBingoChannel, iface.channelBingo).noticeItem['embed'].title
    assert next(iter(markedPlayers)) == player
    assert cast(Classes.TestingUserDMChannel, player.ctx).setBoardViewCalled is True
    assert cast(Classes.TestingUserDMChannel, player.ctx).refreshRequestViewCalled is True
    assert cast(Classes.TestingUserDMChannel, player.ctx).sendNoticeCalled is True

    # Calling slot for a kicked player does not mark their card
    mockTaskProcessor.addedTasks.clear()

    # Get a new bing from the player
    bing = player.card.getCardBings()[0][1]

    # Kick the first player I added. Only the ID matters
    user = Mocks.makeMockUser("David")
    user.id = Const.TEST_MOCK_VALID_USER_ID
    data = ActionData(member=user)
    result: Result = await iface.kickPlayer.__wrapped__(iface, data)
    assert result.result is True

    _resetTrackingClasses(iface)

    # Make a slot call
    mockInteraction = Mocks.makeMockInteraction()
    data = ActionData(interaction=mockInteraction, index=bing.bingIdx)
    result: Result = await iface.makeCall.__wrapped__(iface, data)
    markedPlayers, markedBingos = result.additional

    # Wait for the task process to finish
    mockTaskProcessor.processPendingTasks()

    # Verify success, but with not crediting kicked player
    assert result.result is True
    assert len(markedPlayers) == 0
    assert len(markedBingos) == 0
    assert bing in iface.game.calledBings
    assert not player.card.isCellMarked(bing.x, bing.y)
    assert mockTaskProcessor.hasNoPendingTasks() is True
    assert len(mockTaskProcessor.taskIDs) == 0
    assert len(mockTaskProcessor.addedTasks) == 0
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is True
    assert isinstance(cast(Classes.TestingBingoChannel, iface.channelBingo).noticeItem['embed'], CallNoticeEmbed)
    assert bing.bingStr in cast(Classes.TestingBingoChannel, iface.channelBingo).noticeItem['embed'].title

    mockTaskProcessor.stopProcessing()

@pytest.mark.asyncio
async def test_MakingInvalidCallFails(mock_GameInterfaceDiscordWNODebug, monkeypatch):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)
    Utils.setUseFreeSpace(monkeypatch, False)

    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add player to the game
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Test not sending in the needed action data attributes throws exception
    with pytest.raises(ValueError):
        await iface.makeCall.__wrapped__(iface, ActionData())

    # Get a binglet from the added player's card
    bing = player.card.getCardBings()[0][0]

    # Add a call request to the game
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(
                interaction=mockInteraction,
                callRequest=req
            )
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    _resetTrackingClasses(iface, player)

    # Making call with invalid index fails
    mockInteraction = Mocks.makeMockInteraction()
    data = ActionData(interaction=mockInteraction, index=1000000)
    result: Result = await iface.makeCall.__wrapped__(iface, data)

    mockTaskProcessor.processPendingTasks()

    assert result.result is False
    assert result.additional is None
    assert "invalid bing" in result.responseMsg
    assert len(iface.game.calledBings) == 0
    assert player.card.getNumMarked() == 0
    reqExists = False
    for req in iface.game.requestedCalls:
        if req.requestBing.bingIdx == bing.bingIdx:
            reqExists = True
    assert reqExists is True
    assert mockTaskProcessor.hasNoPendingTasks() is True
    assert len(mockTaskProcessor.taskIDs) == 0
    assert len(mockTaskProcessor.addedTasks) == 0
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).sendNoticeCalled is True
    assert "ERROR" in cast(Classes.TestingAdminChannel, iface.channelAdmin).noticeItems[0]
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is False
    assert cast(Classes.TestingBingoChannel, iface.channelBingo).sendNoticeItemCalled is False
    assert cast(Classes.TestingUserDMChannel, player.ctx).setBoardViewCalled is False
    assert cast(Classes.TestingUserDMChannel, player.ctx).refreshRequestViewCalled is False
    assert cast(Classes.TestingUserDMChannel, player.ctx).sendNoticeCalled is False

@pytest.mark.asyncio
async def test_MakingCallFromInvalidStateFails(mock_GameInterfaceDiscordWNODebug, monkeypatch):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)
    Utils.setUseFreeSpace(monkeypatch, False)
    player: Optional[Player] = None
    bing: Optional[Bing] = None

    # Test making call from invalid state
    for state in Utils.getAllGameStatesOrder():
        await Utils.setDiscordIfaceToState(iface, state)

        # Add player when the game is started
        if state == GameState.STARTED:
            data = _makeValidAddPlayerData()
            result: Result = await iface.addPlayer.__wrapped__(iface, data)
            assert result.result is True
            assert result.additional is not None

            # Get a binglet from the added player's card
            player = result.additional
            if player:
                bing = player.card.getCardBings()[0][0]

            # STARTED is a valid mode, skip
            continue

        _resetTrackingClasses(iface, player)

        # Make a slot call
        mockInteraction = Mocks.makeMockInteraction()
        idx = bing.bingIdx if bing else 0
        data = ActionData(interaction=mockInteraction, index=idx)
        result: Result = await iface.makeCall.__wrapped__(iface, data)

        mockTaskProcessor.processPendingTasks()

        assert result.result is False, f"Expected False when making a call while the game is {state}"
        assert result.additional is None
        if state == GameState.NEW:
            assert "interface not initialized" in result.responseMsg
        else:
            assert "Cannot make a call" in result.responseMsg
        assert len(iface.game.calledBings) == 0
        reqExists = False
        for req in iface.game.requestedCalls:
            if req.requestBing.bingIdx == idx:
                reqExists = True
        assert reqExists is False
        assert mockTaskProcessor.hasNoPendingTasks() is True
        assert len(mockTaskProcessor.taskIDs) == 0
        for task in mockTaskProcessor.addedTasks:
            assert task.getType() != TaskUserDMs.TaskType.UPDATE
        if iface.channelAdmin:
            assert cast(Classes.TestingAdminChannel, iface.channelAdmin).sendNoticeCalled is True
            assert "ERROR" in cast(Classes.TestingAdminChannel, iface.channelAdmin).noticeItems[0]
        if iface.channelBingo:
            assert cast(Classes.TestingBingoChannel, iface.channelBingo).refreshGameStatusCalled is False
            assert cast(Classes.TestingBingoChannel, iface.channelBingo).sendNoticeItemCalled is False
        if player:
            assert player.card.getNumMarked() == 0
            assert cast(Classes.TestingUserDMChannel, player.ctx).setBoardViewCalled is False
            assert cast(Classes.TestingUserDMChannel, player.ctx).refreshRequestViewCalled is False

@pytest.mark.asyncio
async def test_SuccessfullyMakingCallRequest(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add test player
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Get a binglet from the added player's card
    bing = player.card.getCardBings()[0][0]

    _resetTrackingClasses(iface, player)

    # Make a call request
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)

    assert result.result is True
    assert result.additional == req
    assert "Request for" in result.responseMsg
    assert len(iface.game.requestedCalls) == 1
    assert iface.game.requestedCalls[0] == req
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).addCallRequestCalled is True
    assert cast(Classes.TestingUserDMChannel, player.ctx).sendNoticeCalled is True
    assert "Request for" in cast(Classes.TestingUserDMChannel, player.ctx).noticeItems[0]

@pytest.mark.asyncio
async def test_SuccessfullyMakingCallRequestForMultiPlayers(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add test player 1
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Add test player 2
    data = _makeValidAddPlayerData()
    data.get("interaction").user.id = Const.TEST_MOCK_VALID_USER_ID + 1
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player2: Player = result.additional
    assert result.result is True, f"{result.responseMsg}"
    assert result.additional is not None

    # Get a binglet from the added player's card
    bing = player.card.getCardBings()[0][0]

    # Make sure both players have the same bing in their cards
    if not player2.card.getBingFromID(bing.bingIdx):
        player2.card.cells[0][0] = Bing(bing.bingStr, bing.bingIdx)

    # Make a call request for player 1
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    _resetTrackingClasses(iface)

    # Make a call request for player 2
    mockInteraction = Mocks.makeMockInteraction()
    req2 = CallRequest(player2, bing)
    data = ActionData(interaction=mockInteraction, callRequest=req2)
    result: Result = await iface.requestCall.__wrapped__(iface, data)

    assert result.result is True
    assert result.additional == req
    assert "Request for" in result.responseMsg
    assert len(iface.game.requestedCalls) == 1
    assert iface.game.requestedCalls[0] == req
    assert len(req.players) == 2
    assert player in req.players and player2 in req.players
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).addCallRequestCalled is True
    assert cast(Classes.TestingUserDMChannel, player.ctx).sendNoticeCalled is True
    assert cast(Classes.TestingUserDMChannel, player2.ctx).sendNoticeCalled is True
    assert "Request for" in cast(Classes.TestingUserDMChannel, player.ctx).noticeItems[0]
    assert "Request for" in cast(Classes.TestingUserDMChannel, player2.ctx).noticeItems[0]

@pytest.mark.asyncio
async def test_MutuallyExclusiveRequestSucceedsForMultiPlayers(mock_GameInterfaceDiscordWNODebug):
    """
    Test that making a mutually exclusive request for a slot between two players succeeds.
    The bing that only exists for player 1 only applies to them, and not player 2
    """
    pass

@pytest.mark.asyncio
async def test_MakingInvalidCallRequestFails(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    _resetTrackingClasses(iface)

    # Making a request for a non existing player fails
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(Player("", Const.TEST_MOCK_VALID_USER_ID), Binglets(Const.TEST_GAME_TYPE).getBingFromIndex(1))
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)

    assert result.result is False
    assert result.additional is None
    assert "has not been added" in result.responseMsg
    assert len(iface.game.requestedCalls) == 0
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).addCallRequestCalled is False

    # Add test player
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Test not sending in the needed action data attributes throws exception
    with pytest.raises(ValueError):
        await iface.requestCall.__wrapped__(iface, ActionData())

    _resetTrackingClasses(iface)

    # Making a request for a non existing slot fails
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, Bing("invalid slot", 1000000))
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)

    assert result.result is False
    assert result.additional is None
    assert "slot does not exist" in result.responseMsg
    assert len(iface.game.requestedCalls) == 0
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).addCallRequestCalled is False

    # Get a bing the doesn't exist in the players board
    idx = 1
    bing: Optional[Bing] = None
    while not bing:
        _b = player.card.getBingFromID(idx)
        if not _b:
            bing = Binglets(Const.TEST_GAME_TYPE).getBingFromIndex(idx)
        else:
            idx += 1

    # Make a request for a slot that the player does not have on his board fails
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)

    assert result.result is False
    assert result.additional is None
    assert "they do not have" in result.responseMsg
    assert len(iface.game.requestedCalls) == 0
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).addCallRequestCalled is False

@pytest.mark.asyncio
async def test_MakingCallRequestFromInvalidStateFails(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    player: Optional[Player] = None

    # Test making call from invalid state
    for state in Utils.getAllGameStatesOrder():
        await Utils.setDiscordIfaceToState(iface, state)

        # Add player when the game is in the started state
        if state == GameState.STARTED:
            data = _makeValidAddPlayerData()
            result: Result = await iface.addPlayer.__wrapped__(iface, data)
            player = result.additional
            assert result.result is True
            assert result.additional is not None
            continue

        _resetTrackingClasses(iface, player)

        # Make call request
        mockInteraction = Mocks.makeMockInteraction()
        req = CallRequest(player or Player("", Const.TEST_MOCK_VALID_USER_ID), Bing("Valid slot", 0))
        data = ActionData(interaction=mockInteraction, callRequest=req)
        result: Result = await iface.requestCall.__wrapped__(iface, data)

        assert result.result is False
        assert result.additional is None
        if state is GameState.NEW:
            assert "not initialized" in result.responseMsg
        else:
            assert "call cannot be made" in result.responseMsg
        assert len(iface.game.requestedCalls) == 0
        if iface.channelAdmin:
            assert cast(Classes.TestingAdminChannel, iface.channelAdmin).addCallRequestCalled is False
        if player:
            assert cast(Classes.TestingUserDMChannel, player.ctx).sendNoticeCalled is False

@pytest.mark.asyncio
async def test_SuccessfullyDeleteRequest(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    mockTaskProcessor = cast(Classes.TestingTaskProcessor, iface.taskProcessor)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add test player
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Get a binglet from the added player's card
    bing = player.card.getCardBings()[0][0]

    # Make a call request
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    _resetTrackingClasses(iface, player)

    # Delete the call request
    mockInteraction = Mocks.makeMockInteraction()
    data = ActionData(interaction=mockInteraction, index=bing.bingIdx)
    result: Result = await iface.deleteRequest.__wrapped__(iface, data)

    assert result.result is True
    assert "was removed" in result.responseMsg
    assert len(iface.game.requestedCalls) == 0
    assert player.rejectedRequests == 1
    assert player.rejectedTimestamp !=  0.0
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).delCallRequestCalled is True
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).deletedRequestIdx is bing.bingIdx

    mockTaskProcessor.stopProcessing()

@pytest.mark.asyncio
async def test_SuccessfullyDeleteRequestWhilePaused(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add test player
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Get a binglet from the added player's card
    bing = player.card.getCardBings()[0][0]

    # Make a call request
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    # Pause the game
    await iface.pause.__wrapped__(iface, ActionData(interaction=Mocks.makeMockInteraction()))
    assert iface.viewState is GameState.PAUSED
    assert iface.game.state is GameState.PAUSED

    _resetTrackingClasses(iface, player)

    # Delete the call request
    mockInteraction = Mocks.makeMockInteraction()
    data = ActionData(interaction=mockInteraction, index=bing.bingIdx)
    result: Result = await iface.deleteRequest.__wrapped__(iface, data)

    assert result.result is True
    assert "was removed" in result.responseMsg
    assert len(iface.game.requestedCalls) == 0
    assert player.rejectedRequests == 1
    assert player.rejectedTimestamp !=  0.0
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).delCallRequestCalled is True
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).deletedRequestIdx is bing.bingIdx

@pytest.mark.asyncio
async def test_SuccessfullyDeleteRequestExempt(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add test player
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Get a binglet from the added player's card
    bing = player.card.getCardBings()[0][0]

    _resetTrackingClasses(iface, player)

    # Make a call request
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    # Delete the call request
    mockInteraction = Mocks.makeMockInteraction()
    data = ActionData(interaction=mockInteraction, index=bing.bingIdx, exempt=True)
    result: Result = await iface.deleteRequest.__wrapped__(iface, data)

    assert result.result is True
    assert "was removed" in result.responseMsg
    assert len(iface.game.requestedCalls) == 0
    assert player.rejectedRequests == 0
    assert player.rejectedTimestamp == 0.0
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).delCallRequestCalled is True
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).deletedRequestIdx is bing.bingIdx

@pytest.mark.asyncio
async def test_MakingInvalidDeleteRequestFails(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add test player
    data = _makeValidAddPlayerData()
    result: Result = await iface.addPlayer.__wrapped__(iface, data)
    player: Player = result.additional
    assert result.result is True
    assert result.additional is not None

    # Get a binglet from the added player's card
    bing = player.card.getCardBings()[0][0]

    # Make a valid call request
    mockInteraction = Mocks.makeMockInteraction()
    req = CallRequest(player, bing)
    data = ActionData(interaction=mockInteraction, callRequest=req)
    result: Result = await iface.requestCall.__wrapped__(iface, data)
    assert result.result is True

    # Test not sending in the needed action data attributes throws exception
    with pytest.raises(ValueError):
        await iface.deleteRequest.__wrapped__(iface, ActionData())

    _resetTrackingClasses(iface, player)

    # Delete the call request that does not exist
    mockInteraction = Mocks.makeMockInteraction()
    data = ActionData(interaction=mockInteraction, index=42069)
    result: Result = await iface.deleteRequest.__wrapped__(iface, data)

    assert result.result is False
    assert "no outstanding request" in result.responseMsg
    assert len(iface.game.requestedCalls) == 1
    assert player.rejectedRequests == 0
    assert player.rejectedTimestamp == 0.0
    assert cast(Classes.TestingAdminChannel, iface.channelAdmin).delCallRequestCalled is False

@pytest.mark.asyncio
async def test_MakingDeleteRequestFromInvalidStateFails(mock_GameInterfaceDiscordWNODebug):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscordWNODebug

    player: Optional[Player] = None
    bing: Optional[Bing] = None

    # Test making call from invalid state
    for state in Utils.getAllGameStatesOrder():
        await Utils.setDiscordIfaceToState(iface, state)

        # Add player when the game is in the started state
        if state == GameState.STARTED:
            data = _makeValidAddPlayerData()
            result: Result = await iface.addPlayer.__wrapped__(iface, data)
            player = result.additional
            assert result.result is True
            assert result.additional is not None
            assert player is not None

            bing = player.card.getCardBings()[0][0]

        # Skipping valid states
        if state == GameState.STARTED or state == GameState.PAUSED:
            continue

        _resetTrackingClasses(iface)

        # Make a request in an invalid state
        mockInteraction = Mocks.makeMockInteraction()
        idx = bing.bingIdx if bing else 0
        data = ActionData(interaction=mockInteraction, index=idx)
        result: Result = await iface.deleteRequest.__wrapped__(iface, data)

        assert result.result is False
        if state == GameState.NEW:
            assert "interface not initialized" in result.responseMsg
        else:
            assert "while the bingo game is" in result.responseMsg
        assert len(iface.game.requestedCalls) == 0
        if player:
            assert player.rejectedRequests == 0
            assert player.rejectedTimestamp == 0.0
        if iface.channelAdmin:
            assert cast(Classes.TestingAdminChannel, iface.channelAdmin).delCallRequestCalled is False

def _resetTrackingClasses(iface: GameInterfaceDiscord, player: Optional[Player] = None):
    if iface.channelAdmin:
        cast(Classes.TestingAdminChannel, iface.channelAdmin).resetTracking()
    if iface.channelBingo:
        cast(Classes.TestingBingoChannel, iface.channelBingo).resetTracking()
    if player:
        cast(Classes.TestingUserDMChannel, player.ctx).resetTracking()

def _makeValidAddPlayerData(name = "Schecter Wolf") -> ActionData:
    mockInteraction = Mocks.makeMockInteraction()
    testUserName = name
    mockInteraction.user = Mocks.makeMockUser(testUserName)
    mockInteraction.user.id = Const.TEST_MOCK_VALID_USER_ID
    mockFinalize = MagicMock()
    return ActionData(
                interaction=mockInteraction,
                **{ActionData.FINALIZE_FUNCT: mockFinalize.finalize}
            )

