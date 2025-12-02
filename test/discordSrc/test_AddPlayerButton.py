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

import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from discordSrc.AddPlayerButton import AddPlayerButton
from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord

from game.Game import GameState
from game.GameStore import GameStore
from game.Player import Player
from game.Result import Result

from unittest.mock import MagicMock, ANY

@pytest.fixture(scope="function")
def mock_GameInterfaceDiscord(monkeypatch):
    mockedGuilds = Mocks.makeMockGuild()

    # Disable YT iface for these tests
    Utils.disableYTConfig(monkeypatch)

    # Enable debug
    Utils.setDebugConfig(monkeypatch, True)

    # Disable rankings
    Utils.disableLeaderboardRankings(mockedGuilds)

    iface = GameInterfaceDiscord(Mocks.makeMockBot(), mockedGuilds, Const.TEST_GAME_TYPE)

    # Add game to game store
    store = GameStore()
    if not store.getGame(Const.TEST_GUILD_ID):
        store.addGame(Const.TEST_GUILD_ID, iface)

    yield iface

    # RM the game from the store
    store.removeGame(Const.TEST_GUILD_ID)

    # Clean up task processor
    iface.taskProcessor.stop()

@pytest.mark.asyncio
async def test_ButtonSuccessfullyAddsPlayer(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUser(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)

    # Manually trigger the initial add player button click
    addButton = AddPlayerButton(Const.TEST_GUILD_ID)
    await addButton.button_callback(mockInteraction)

    assert Const.TEST_MOCK_VALID_USER_ID in addButton.confirmMsgIDs
    mockInteraction.user.send.assert_called_with(addButton._getGreeting(mockInteraction.user), view=ANY)
    mockInteraction.response.send_message.assert_called_with("Please check your DMs to begin playing!", ephemeral=True)

    # Manually trigger the confirm add player button click
    await addButton.confirm_callback(mockInteraction)

    # Let the queued task run
    await asyncio.sleep(0)

    assert Player(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID) in iface.game.players

@pytest.mark.asyncio
async def test_SimultaneousAddPlayerIsSuccessfull(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Manually trigger the 1st add player button click
    mockInteraction = Mocks.makeMockInteraction()
    mockUserFirst = Mocks.makeMockUser(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)
    mockInteraction.user = mockUserFirst
    addButton = AddPlayerButton(Const.TEST_GUILD_ID)
    await addButton.button_callback(mockInteraction)

    assert Const.TEST_MOCK_VALID_USER_ID in addButton.confirmMsgIDs
    mockInteraction.user.send.assert_called_with(addButton._getGreeting(mockInteraction.user), view=ANY)
    mockInteraction.response.send_message.assert_called_with("Please check your DMs to begin playing!", ephemeral=True)

    # Manually trigger the 1st add player button click
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUser("TestUser2", Const.TEST_MOCK_VALID_USER_ID + 1)
    addButton = AddPlayerButton(Const.TEST_GUILD_ID)
    await addButton.button_callback(mockInteraction)

    assert Const.TEST_MOCK_VALID_USER_ID + 1 in addButton.confirmMsgIDs
    mockInteraction.user.send.assert_called_with(addButton._getGreeting(mockInteraction.user), view=ANY)
    mockInteraction.response.send_message.assert_called_with("Please check your DMs to begin playing!", ephemeral=True)

    # Manually trigger the confirm add player button for the first player
    mockInteraction.user = mockUserFirst
    await addButton.confirm_callback(mockInteraction)

    # Let the queued task run
    await asyncio.sleep(0)

    assert Player(Const.TEST_USER_NAME, mockUserFirst.id) in iface.game.players

@pytest.mark.asyncio
async def test_DoubleAddButtonFails(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUser(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)

    # Manually trigger the initial add player button click
    addButton = AddPlayerButton(Const.TEST_GUILD_ID)
    await addButton.button_callback(mockInteraction)
    assert Const.TEST_MOCK_VALID_USER_ID in addButton.confirmMsgIDs

    # Manually trigger the confirm add player button click
    await addButton.confirm_callback(mockInteraction)

    # Let the queued task run
    await asyncio.sleep(0)

    assert Player(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID) in iface.game.players

    # Trigger the add player button again, after the player has already been added
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUser(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)
    await addButton.button_callback(mockInteraction)

    res: Result = iface.game.checkEligibleFromID(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)

    mockInteraction.response.send_message.assert_called_with(res.responseMsg, ephemeral=True)
    mockInteraction.user.send.assert_not_called()

@pytest.mark.asyncio
async def test_InvalidPlayerAddButtonFails(mock_GameInterfaceDiscord):
    _INVALID_USER_NAME = "Fucking User"

    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # User with invalid name
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUser(_INVALID_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)

    # Manually trigger the initial add player button click
    addButton = AddPlayerButton(Const.TEST_GUILD_ID)
    await addButton.button_callback(mockInteraction)

    res: Result = iface.game.checkEligibleFromID(_INVALID_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)

    assert Const.TEST_MOCK_VALID_USER_ID not in addButton.confirmMsgIDs
    mockInteraction.response.send_message.assert_called_with(res.responseMsg, ephemeral=True)

@pytest.mark.asyncio
async def test_DisabledUserDMAddButtonFails(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUser(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)

    # Make the user DM function throw an exception
    mockInteraction.user.send.side_effect = discord.Forbidden(MagicMock(), "Test forced exception")

    # Manually trigger the initial add player button click
    addButton = AddPlayerButton(Const.TEST_GUILD_ID)
    await addButton.button_callback(mockInteraction)

    mockInteraction.response.send_message.assert_called_with(addButton._getCheckErrMessage(), ephemeral=True)
    assert Player(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID) not in iface.game.players

@pytest.mark.asyncio
async def test_InvalidPlayerConfirmFails(mock_GameInterfaceDiscord):
    _INVALID_USER_NAME = "Fucking User"

    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUser(_INVALID_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)

    # Technically this is impossible, so I have to emulate as if the button_callback succeeded
    addButton = AddPlayerButton(Const.TEST_GUILD_ID)
    addButton.confirmMsgIDs[Const.TEST_MOCK_VALID_USER_ID] = 12345

    # Manually trigger the confirm add player button click
    await addButton.confirm_callback(mockInteraction)

    # Let the queued task run
    await asyncio.sleep(0)

    assert Player(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID) not in iface.game.players

@pytest.mark.asyncio
async def test_InvalidGameStateAddButtonFails(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord
    await Utils.setDiscordIfaceToState(iface, GameState.PAUSED)

    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = Mocks.makeMockUser(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)

    # Manually trigger the initial add player button click
    addButton = AddPlayerButton(Const.TEST_GUILD_ID)
    await addButton.button_callback(mockInteraction)

    assert Const.TEST_MOCK_VALID_USER_ID in addButton.confirmMsgIDs
    mockInteraction.user.send.assert_called_with(addButton._getGreeting(mockInteraction.user), view=ANY)
    mockInteraction.response.send_message.assert_called_with("Please check your DMs to begin playing!", ephemeral=True)

    # Manually trigger the confirm add player button click
    await addButton.confirm_callback(mockInteraction)

    # Let the queued task run
    await asyncio.sleep(0)

    assert Player(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID) not in iface.game.players

