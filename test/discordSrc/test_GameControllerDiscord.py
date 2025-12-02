__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import pytest
import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from discordSrc.GameControllerDiscord import GameControllerDiscord
from game.GameStore import GameStore
from game.Result import Result

from unittest.mock import MagicMock

@pytest.fixture(scope="module")
def mock_GameControllerDiscord():
    mockedGuilds = {Const.TEST_GUILD_ID: Mocks.makeMockGuild()}

    # Don't worry about rankings for this test
    mockedGameGuild = mockedGuilds.get(Const.TEST_GUILD_ID)
    assert mockedGameGuild is not None
    Utils.disableLeaderboardRankings(mockedGameGuild)

    return GameControllerDiscord(MagicMock(), mockedGuilds)

@pytest.mark.asyncio
async def test_CantStopANonExistingGame(mock_GameControllerDiscord):
    controller: GameControllerDiscord = mock_GameControllerDiscord
    result: Result = await controller._stopGameInternal.__wrapped__(controller, Const.TEST_GUILD_ID)

    assert result.result is False
    assert GameStore().getGame(Const.TEST_GUILD_ID) is None

@pytest.mark.asyncio
async def test_CantStartAGameForAnInvalidGuild(mock_GameControllerDiscord):
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.guild.id = 123456789

    controller: GameControllerDiscord = mock_GameControllerDiscord
    result: Result = await controller._startGameInternal.__wrapped__(controller, mockInteraction)

    assert result.result is False
    assert GameStore().getGame(Const.TEST_GUILD_ID) is None

@pytest.mark.asyncio
async def test_StartGame(mock_GameControllerDiscord, monkeypatch):
    """
    Test that the discord game controller properly starts a bingo game

    Verifies that the start function returns a positive result, and that
    a game exists for the test guild ID.
    """
    # Add the game type to this interaction
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.data = {'custom_id': "FiveM"}

    # We don't want to use YT iface for this test
    Utils.disableYTConfig(monkeypatch)

    # Mock the TaskProcessor, since we're not testing its functionality at this level
    # and it causes warnings to be thrown
    monkeypatch.setattr("discordSrc.GameInterfaceDiscord.TaskProcessor", MagicMock())

    controller = mock_GameControllerDiscord
    result: Result = await controller._startGameInternal.__wrapped__(controller, mockInteraction)

    assert result.result is True
    assert GameStore().getGame(Const.TEST_GUILD_ID) is not None

@pytest.mark.asyncio
async def test_CantStartAnAlreadyStartedGame(mock_GameControllerDiscord):
    controller: GameControllerDiscord = mock_GameControllerDiscord
    result: Result = await controller._startGameInternal.__wrapped__(controller, Mocks.makeMockInteraction())

    assert result.result is False
    assert GameStore().getGame(Const.TEST_GUILD_ID) is not None

@pytest.mark.asyncio
async def test_EndGame(mock_GameControllerDiscord):
    controller: GameControllerDiscord = mock_GameControllerDiscord
    result: Result = await controller._stopGameInternal.__wrapped__(controller, Const.TEST_GUILD_ID)

    assert result.result is True
    assert GameStore().getGame(Const.TEST_GUILD_ID) is None

