__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio
import discord
import pytest
import pytest_asyncio

import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from discordSrc.GameControllerDiscord import GameControllerDiscord
from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord
from discordSrc.MakeRequestView import MakeRequestView

from game.ActionData import ActionData
from game.Bing import Bing
from game.Binglets import Binglets
from game.Game import GameState
from game.GameStore import GameStore
from game.Player import Player

from typing import Optional, cast

@pytest_asyncio.fixture(scope="function")
async def mock_GameInterfaceDiscord(monkeypatch):
    mockedGuilds = Mocks.makeMockGuild()

    # Disable YT iface for these tests
    Utils.disableYTConfig(monkeypatch)

    # Disable rankings
    Utils.disableLeaderboardRankings(mockedGuilds)

    # Disable free space
    Utils.setUseFreeSpace(monkeypatch, False)

    # Set up the game store
    store = GameStore()
    store.addController(GameControllerDiscord(Mocks.makeMockBot(), {Const.TEST_GUILD_ID: mockedGuilds}))
    controller = store.getController()
    if controller:
        mockInteraction = Mocks.makeMockInteraction()
        mockInteraction.data = {'custom_id': Const.TEST_GAME_TYPE}
        controller.startGame(interaction=mockInteraction)
    await asyncio.sleep(0)

    game = GameStore().getGame(Const.TEST_GUILD_ID)
    assert game is not None
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, game)
    assert iface.game.state == GameState.STARTED

    yield iface

    iface.taskProcessor.stop()
    store = GameStore()
    controller = store.getController()
    if controller:
        controller.stopGame(guildID=Const.TEST_GUILD_ID)
    controller = None
    store.__controller = None
    await asyncio.sleep(0)

@pytest.mark.asyncio
async def test_RequestViewInitsSuccessfully(monkeypatch):
    # Disable free space
    Utils.setUseFreeSpace(monkeypatch, False)

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)

    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]
    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)

    assert mrv.gameID == Const.TEST_GUILD_ID
    assert mrv._player == player
    assert len(mrv.children) == 1
    assert len(playerBings) == len(mrv.select.options)
    assert mrv.select.callback == mrv.select_callback
    assert mrv.select.placeholder == MakeRequestView._MakeRequestView__SELECT_PLCHDR # type: ignore[attr-defined]
    assert mrv.select.custom_id == MakeRequestView._MakeRequestView__SELECT_ID # type: ignore[attr-defined]
    for i in range(len(playerBings)):
        bing = playerBings[i]
        opt: Optional[discord.SelectOption] = None

        # Im not sure of the ordering in the select, so just go through the options and find
        # the matching one.
        for op in mrv.select.options:
            if op.value == str(bing.bingIdx):
                opt = op
                break

        assert opt != None
        assert opt.label == f"[{bing.bingIdx}] {bing.bingStr}"
        assert opt.value == str(bing.bingIdx)

@pytest.mark.asyncio
async def test_RequestViewCanInitWithPlayerInvalidCard(monkeypatch):
    # Disable free space
    Utils.setUseFreeSpace(monkeypatch, False)

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)

    assert mrv.gameID == Const.TEST_GUILD_ID
    assert mrv._player == player
    assert len(mrv.children) == 1
    assert len(mrv.select.options) == 0
    assert mrv.select.callback == mrv.select_callback
    assert mrv.select.placeholder == MakeRequestView._MakeRequestView__SELECT_PLCHDR # type: ignore[attr-defined]
    assert mrv.select.custom_id == MakeRequestView._MakeRequestView__SELECT_ID # type: ignore[attr-defined]

@pytest.mark.asyncio
async def test_SuccessfullyMakeCallRequest(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    mockInteraction = Mocks.makeMockInteraction()
    mrv.select._values = [str(playerBings[0].bingIdx)]
    await mrv.select_callback(mockInteraction)
    await asyncio.sleep(0)

    assert mrv._interactExpired == False
    assert len(mrv.select._values) == 0
    assert len(iface.game.requestedCalls) == 1
    assert iface.game.requestedCalls[0].requestBing.bingIdx == playerBings[0].bingIdx
    assert iface.game.requestedCalls[0].getRequesterName() == player.card.getCardOwner()
    mockInteraction.response.defer.assert_called_once()
    mockInteraction.message.edit.assert_called_once_with(view=mrv)

@pytest.mark.asyncio
async def test_FailToMakeCallRequestWNoSelection(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    mockInteraction = Mocks.makeMockInteraction()
    await mrv.select_callback(mockInteraction)
    await asyncio.sleep(0)

    assert mrv._interactExpired == False
    assert len(mrv.select._values) == 0
    assert len(iface.game.requestedCalls) == 0
    mockInteraction.response.defer.assert_not_called()
    mockInteraction.message.edit.assert_not_called()

@pytest.mark.asyncio
async def test_FailToMakeCallRequestWInvalidGameID(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    INVALID_GUILD_ID = 10000

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(INVALID_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    mockInteraction = Mocks.makeMockInteraction()
    mrv.select._values = [str(playerBings[0].bingIdx)]
    await mrv.select_callback(mockInteraction)
    await asyncio.sleep(0)

    assert mrv._interactExpired == False
    assert len(mrv.select._values) == 0
    assert len(iface.game.requestedCalls) == 0
    mockInteraction.response.send_message.assert_called_once(f"Failed to process request", ephemeral=True)
    mockInteraction.message.edit.assert_called_once_with(view=mrv)

@pytest.mark.asyncio
async def test_FailToMakeCallRequestWExpiredInteract(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    INVALID_GUILD_ID = 10000

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(INVALID_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    # Make an initial call request, but don't sleep in order to
    # emulate making another call request while this request is
    # still processing
    mockInteraction = Mocks.makeMockInteraction()
    mrv.select._values = [str(playerBings[0].bingIdx)]
    await mrv.select_callback(mockInteraction)
    assert mrv._interactExpired is True

    # Make another call request
    mockInteraction2 = Mocks.makeMockInteraction()
    mrv.select._values = [str(playerBings[1].bingIdx)]
    await mrv.select_callback(mockInteraction)

    assert mrv._interactExpired is True
    assert len(mrv.select._values) == 0
    mockInteraction2.response.send_message.assert_called_once_with(f"\U0000FE0F Make request is still processing, please wait.")
    mockInteraction2.message.edit.assert_called_once_with(view=mrv)

    # Allow the request to process
    await asyncio.sleep(0)

    assert len(iface.game.requestedCalls) == 1
    assert iface.game.requestedCalls[0].requestBing.bingIdx == playerBings[0].bingIdx

@pytest.mark.asyncio
async def test_FailToMakeCallRequestWInvalidBing(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    INVALID_BING_IDX = 1000000
    mockInteraction = Mocks.makeMockInteraction()
    mrv.select._values = [str(INVALID_BING_IDX)]
    await mrv.select_callback(mockInteraction)
    await asyncio.sleep(0)

    assert mrv._interactExpired is False
    assert len(mrv.select._values) == 0
    assert len(iface.game.requestedCalls) == 0
    mockInteraction.response.send_message.assert_called_once_with("Requested call category does not exist in this players card, aborting.", ephemeral=True)

@pytest.mark.asyncio
async def test_FailToMakeCallRequestWhenPlayerWNoBing(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    # Get a valid Bing that the player does not have in their card
    testBing: Optional[Bing] = None
    for bing in Binglets(Const.TEST_GAME_TYPE).getBingletsCopy():
        if not any(b.bingIdx == bing.bingIdx for b in playerBings):
            testBing = bing
    assert testBing is not None

    mockInteraction = Mocks.makeMockInteraction()
    mrv.select._values = [str(testBing.bingIdx)]
    await mrv.select_callback(mockInteraction)
    await asyncio.sleep(0)

    assert mrv._interactExpired is False
    assert len(mrv.select._values) == 0
    assert len(iface.game.requestedCalls) == 0
    mockInteraction.response.send_message.assert_called_once_with("Requested call category does not exist in this players card, aborting.", ephemeral=True)

@pytest.mark.asyncio
async def test_FailToMakeCallRequestWMarkedBing(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    # Manually mark a the test player's slot
    player.card.markCell(playerBings[0])

    mockInteraction = Mocks.makeMockInteraction()
    mrv.select._values = [str(playerBings[0].bingIdx)]
    await mrv.select_callback(mockInteraction)
    await asyncio.sleep(0)

    assert mrv._interactExpired is False
    assert len(mrv.select._values) == 0
    assert len(iface.game.requestedCalls) == 0
    mockInteraction.response.send_message.assert_called_once_with(f"Slot \"{playerBings[0].bingStr}\" has already been marked!. If the square is not red, please wait for the board to update.", ephemeral=True)

@pytest.mark.asyncio
async def test_FailToExceedRequestLimit(mock_GameInterfaceDiscord, monkeypatch):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord

    # Set the max call limit to 2
    TEST_MAX_CALL_LIMIT = 2
    Utils.overrideConfig(monkeypatch, "MaxRequests", 2)

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    mockInteraction = Mocks.makeMockInteraction()
    for i in range(TEST_MAX_CALL_LIMIT + 1):
        mrv.select._values = [str(playerBings[i].bingIdx)]
        await mrv.select_callback(mockInteraction)
        await asyncio.sleep(0)

    assert mrv._interactExpired is False
    assert len(mrv.select._values) == 0
    assert len(iface.game.requestedCalls) == TEST_MAX_CALL_LIMIT
    mockInteraction.response.send_message.assert_called_with(f"\U0001F6D1 Request limit reached! You can only have up to {TEST_MAX_CALL_LIMIT} active requests at a time.", ephemeral=True)

@pytest.mark.asyncio
async def test_FailToCallRequestWhileTimedOut(mock_GameInterfaceDiscord, monkeypatch):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord

    # Set the max call limit to 2
    TEST_TIMEOUT_LIMIT = 2
    Utils.overrideConfig(monkeypatch, "ReqTimeoutMin", TEST_TIMEOUT_LIMIT)

    player = Player("TestPlayer", Const.TEST_MOCK_VALID_USER_ID)
    player.card.generateNewCard(Const.TEST_GAME_TYPE)
    playerBings = [item for sublist in player.card.getCardBings() for item in sublist]

    mrv = MakeRequestView(Const.TEST_GUILD_ID, player)
    assert len(playerBings) == len(mrv.select.options)
    assert len(playerBings) != 0

    # Make call request
    for i in range(MakeRequestView._MakeRequestView__REJECTION_LIMIT): # type: ignore[attr-defined]
        mockInteraction = Mocks.makeMockInteraction()
        mrv.select._values = [str(playerBings[i].bingIdx)]
        await mrv.select_callback(mockInteraction)
        await asyncio.sleep(0)

    # Reject the call requests
    for req in iface.game.requestedCalls:
        _ = iface.deleteRequest(ActionData(index=req.requestBing.bingIdx))
        await asyncio.sleep(0)

    # Make another call request
    mockInteraction = Mocks.makeMockInteraction()
    mrv.select._values = [str(playerBings[3].bingIdx)]
    await mrv.select_callback(mockInteraction)
    await asyncio.sleep(0)

    assert mrv._interactExpired is False
    assert len(mrv.select._values) == 0
    assert len(iface.game.requestedCalls) == 0
    mockInteraction.response.send_message.assert_called_once_with(f"\U0001F6D1 Your request by you has already been rejected {MakeRequestView._MakeRequestView.__REJECTION_LIMIT} times! Ignoring for {TEST_TIMEOUT_LIMIT} minutes!", ephemeral=True) # type: ignore[attr-defined]

@pytest.mark.asyncio
async def test_UnaddedPlayerFailsToMakeCallReq(mock_GameInterfaceDiscord):
    pass

