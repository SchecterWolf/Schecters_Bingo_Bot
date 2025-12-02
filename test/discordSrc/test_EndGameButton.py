__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import asyncio
import discord
import pytest
import pytest_asyncio

import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from discordSrc.EndGameButton import EndGameButton
from discordSrc.GameControllerDiscord import GameControllerDiscord
from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord

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
async def test_ButtonEndsGameSuccessfully(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    button = EndGameButton()

    mockInteraction = Mocks.makeMockInteraction()
    await button.button_callback(mockInteraction)
    await asyncio.sleep(0)

    assert iface.game.state == GameState.DESTROYED
    mockInteraction.response.defer.assert_called_once_with(thinking=True)

@pytest.mark.asyncio
async def test_DoubleClickingButtonFails(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    button = EndGameButton()

    mockInteraction = Mocks.makeMockInteraction()
    await button.button_callback(mockInteraction)
    await asyncio.sleep(0)

    assert iface.game.state == GameState.DESTROYED
    mockInteraction.response.defer.assert_called_once_with(thinking=True)

    mockInteraction = Mocks.makeMockInteraction()
    await button.button_callback(mockInteraction)
    await asyncio.sleep(0)

    mockInteraction.response.send_message.assert_called_once_with("Failed to process command", ephemeral=True)

@pytest.mark.asyncio
async def test_InvalidGuildIDDoesNothing(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    button = EndGameButton()

    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.guild_id = Const.TEST_GUILD_ID + 1
    await button.button_callback(mockInteraction)
    await asyncio.sleep(0)

    assert iface.game.state == GameState.STARTED

@pytest.mark.asyncio
async def test_NoGuildIDFails():
    button = EndGameButton()
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.guild_id = None
    await button.button_callback(mockInteraction)
    await asyncio.sleep(0)

    mockInteraction.response.send_message.assert_called_once_with("Invalid interaction arg.", ephemeral=True)

@pytest.mark.asyncio
async def test_MissingGameControllerFails(monkeypatch):
    from game.GameStore import GameStore
    monkeypatch.setattr(GameStore, "getController", lambda self: None)

    button = EndGameButton()
    mockInteraction = Mocks.makeMockInteraction()
    await button.button_callback(mockInteraction)
    await asyncio.sleep(0)

    mockInteraction.response.send_message.assert_called_once_with("Failed to process command", ephemeral=True)

@pytest.mark.asyncio
async def test_ButtonAddsToView():
    button = EndGameButton()
    view = discord.ui.View()

    button.addToView(view)

    assert len(view.children) == 1
    assert view.interaction_check == button.interactionCheck
    assert isinstance(view.children[0], discord.ui.Button)

