__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio
import pytest
import pytest_asyncio

import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from discordSrc.GameControllerDiscord import GameControllerDiscord
from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord
from discordSrc.MakeCallView import MakeCallView

from game.Binglets import Binglets
from game.Game import GameState
from game.GameStore import GameStore

from typing import cast

@pytest_asyncio.fixture(scope="function")
async def mock_GameInterfaceDiscord(monkeypatch):
    mockedGuilds = Mocks.makeMockGuild()

    # Disable YT iface for these tests
    Utils.disableYTConfig(monkeypatch)

    # Disable rankings
    Utils.disableLeaderboardRankings(mockedGuilds)

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
async def test_PopulatesCorrectlyFiveM():
    mcv = MakeCallView(Const.TEST_GUILD_ID, Const.TEST_GAME_TYPE)
    bingCategories = list(Binglets(Const.TEST_GAME_TYPE).getBingDict().keys())

    assert mcv.gameID == Const.TEST_GUILD_ID
    assert len(mcv.callSelects) == len(bingCategories)
    assert len(mcv.children) == len(bingCategories)

    for i in range(len(mcv.callSelects)):
        sv = mcv.callSelects[i]
        assert sv.gameID == Const.TEST_GUILD_ID
        assert sv.placeholderVal == f"Calls for {bingCategories[i]}"
        assert sv.placeholder == f"Calls for {bingCategories[i]}"
        assert sv.max_values == 1
        assert sv.min_values == 1
        assert len(sv.options) <= 25

@pytest.mark.asyncio
async def test_PopulatesCorrectlyRedM():
    REDM_GAME_TYPE = "RedM"
    mcv = MakeCallView(Const.TEST_GUILD_ID, REDM_GAME_TYPE)
    bingCategories = list(Binglets(REDM_GAME_TYPE).getBingDict().keys())

    assert mcv.gameID == Const.TEST_GUILD_ID
    assert len(mcv.callSelects) == len(bingCategories)
    assert len(mcv.children) == len(bingCategories)

    for i in range(len(mcv.callSelects)):
        sv = mcv.callSelects[i]
        assert sv.gameID == Const.TEST_GUILD_ID
        assert sv.placeholderVal == f"Calls for {bingCategories[i]}"
        assert sv.placeholder == f"Calls for {bingCategories[i]}"
        assert sv.max_values == 1
        assert sv.min_values == 1
        assert len(sv.options) > 0
        assert len(sv.options) <= 25

@pytest.mark.asyncio
async def test_InitFailsWithInvalidGameType():
    INVALID_GAME_TYPE = "INVALID"
    mcv = MakeCallView(Const.TEST_GUILD_ID, INVALID_GAME_TYPE)

    assert len(mcv.callSelects) == 0
    assert len(mcv.children) == 0

@pytest.mark.asyncio
async def test_SelectFailsWithInvalidGameID(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    INVALID_GAME_ID = 67
    mcv = MakeCallView(INVALID_GAME_ID, Const.TEST_GAME_TYPE)
    assert len(mcv.callSelects) > 0

    # Make a select call request
    mockInteraction = Mocks.makeMockInteraction()
    mcv.callSelects[0]._values = ['1']
    await mcv.callSelects[0].callback(mockInteraction)
    await asyncio.sleep(0)

    assert mcv._interactExpired is False
    assert len(mcv.callSelects) > 0
    assert len(mcv.children) > 0
    assert len(iface.game.calledBings) == 0
    mockInteraction.message.edit.assert_called_once_with(view=mcv)
    mockInteraction.response.defer.assert_called_once()

@pytest.mark.asyncio
async def test_SelectFailsWithInvalidBingID(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    mcv = MakeCallView(Const.TEST_GUILD_ID, Const.TEST_GAME_TYPE)

    mockInteraction = Mocks.makeMockInteraction()
    mcv.callSelects[0]._values = ['100000']
    await mcv.callSelects[0].callback(mockInteraction)
    await asyncio.sleep(0)

    assert mcv._interactExpired is False
    assert len(iface.game.calledBings) == 0
    mockInteraction.message.edit.assert_called_once_with(view=mcv)
    mockInteraction.response.defer.assert_called_once()

@pytest.mark.asyncio
async def test_SelectFailsWithNoSelection(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    mcv = MakeCallView(Const.TEST_GUILD_ID, Const.TEST_GAME_TYPE)
    assert len(mcv.callSelects) > 0

    mockInteraction = Mocks.makeMockInteraction()
    await mcv.callSelects[0].callback(mockInteraction)
    await asyncio.sleep(0)

    assert mcv._interactExpired is False
    assert len(iface.game.calledBings) == 0
    mockInteraction.message.edit.assert_not_called()
    mockInteraction.response.defer.assert_not_called()

@pytest.mark.asyncio
async def test_SelectMakeCallRequestSuccessfully(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    mcv = MakeCallView(Const.TEST_GUILD_ID, Const.TEST_GAME_TYPE)
    assert len(mcv.callSelects) > 0

    mockInteraction = Mocks.makeMockInteraction()
    mcv.callSelects[0]._values = ['1']
    await mcv.callSelects[0].callback(mockInteraction)
    await asyncio.sleep(0)

    assert mcv._interactExpired is False
    assert len(iface.game.calledBings) == 1
    assert next(iter(iface.game.calledBings)).bingIdx == 1
    mockInteraction.message.edit.assert_called_once_with(view=mcv)
    mockInteraction.response.defer.assert_called_once()

