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

from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord
from game.ActionData import ActionData
from game.Game import GameState

from unittest.mock import MagicMock

@pytest.fixture(scope="function")
def mock_GameInterfaceDiscord(monkeypatch):
    """
    Properly initializes a new instance of GameInterfaceDiscord.
    Makes sure to stop the internal TaskProcessor after a test is finished.

    Args:
        monkeypatch: Test mocking fixture

    Returns:
        GameInterfaceDiscord: New iface instance
    """
    instances = []

    def _make():
        mockedGuilds = Mocks.makeMockGuild()

        # We don't want to use the YT iface for these tests
        Utils.disableYTConfig(monkeypatch)

        # Don't worry about rankings for this test
        Utils.disableLeaderboardRankings(mockedGuilds)

        iface = GameInterfaceDiscord(Mocks.makeMockBot(), mockedGuilds, Const.TEST_GAME_TYPE)
        instances.append(iface)

        return iface

    yield _make

    # Make sure to stop the task processor, or the test will hang forever
    for inst in instances:
        inst.taskProcessor.stop()

@pytest.mark.asyncio
async def test_InterfaceInitializes(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()
    result = await iface.init()

    assert result.result is True
    assert iface.game.state is GameState.IDLE
    assert iface.viewState is GameState.IDLE
    assert iface.channelAdmin is not None
    assert iface.channelBingo is not None
    assert iface.taskProcessor.running is True
    assert iface.initialized is True

@pytest.mark.asyncio
async def test_DoubleInitIsBenignFromAllStates(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()

    for state in Utils.getAllGameStatesOrder():
        await Utils.setDiscordIfaceToState(iface, state)

        # Skip the valid state.
        if state == GameState.NEW:
            continue

        result = await iface.init()

        assert result.result is True
        assert iface.game.state is state
        assert iface.viewState is state

@pytest.mark.asyncio
async def test_InvalidGameTypeYieldsInitError(monkeypatch):
    mockedGuilds = Mocks.makeMockGuild()
    Utils.disableYTConfig(monkeypatch)
    iface = GameInterfaceDiscord(Mocks.makeMockBot(), mockedGuilds, "InvalidGameType")

    result = await iface.init()

    assert result.result is False
    assert "invalid game mode" in result.responseMsg
    assert iface.initialized is False
    assert iface.game.state is GameState.NEW
    assert iface.viewState is GameState.NEW
    assert iface.taskProcessor.running is False

@pytest.mark.asyncio
async def test_GameSuccessfullyStarts(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()
    result = await iface.init()

    # Make sure the iface initialized correctly
    assert result.result is True

    result = await iface.start()

    assert result.result is True
    assert iface.game.state is GameState.STARTED
    assert iface.viewState is GameState.STARTED
    assert iface.channelBingo is not None
    assert iface.channelBingo.showAddBtn is True
    assert iface.channelBingo._BingoChannel__MSG_GLOBAL_STATS in iface.channelBingo._messageIDs # type: ignore[attr-defined]
    assert iface.channelBingo._BingoChannel__MSG_GAME_STATUS in iface.channelBingo._messageIDs # type: ignore[attr-defined]
    assert iface.channelBingo._BingoChannel__MSG_ADD_PLAYER in iface.channelBingo._messageIDs # type: ignore[attr-defined]
    assert iface.channelAdmin._AdminChannel__MSG_GAME_CONTROLS in iface.channelAdmin._messageIDs # type: ignore[attr-defined]
    assert iface.channelAdmin._AdminChannel__MSG_MAKE_CALL in iface.channelAdmin._messageIDs # type: ignore[attr-defined]

@pytest.mark.asyncio
async def test_GameDoesNotStartWithoutInitialization(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()
    result = await iface.start()

    assert result.result is False
    assert "not been initialized" in result.responseMsg
    assert iface.game.state is GameState.NEW
    assert iface.viewState is GameState.NEW
    assert iface.taskProcessor.running is False

@pytest.mark.asyncio
async def test_StartingGameFromInvalidStateIsError(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()

    for state in Utils.getAllGameStatesOrder():
        await Utils.setDiscordIfaceToState(iface, state)

        # Skip the valid states
        if state == GameState.IDLE or state == GameState.PAUSED or state == GameState.STARTED:
            continue

        result = await iface.start()

        assert result.result is False, f"Starting game expect to fail from the {state} state."
        assert "cannot start" in result.responseMsg.lower()
        assert iface.game.state is state
        assert iface.viewState is state

@pytest.mark.asyncio
async def test_GameSuccessfullyPauses(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()
    result = await iface.init()

    # Make sure the iface initialized correctly
    assert result.result is True

    # Make sure the game started correctly
    result = await iface.start()
    assert result.result is True

    # Make sure the interaction is followed up on
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.response = MagicMock()
    mockInteraction.response.is_done.return_value = True

    # Verify finalize callback
    mockFinalize = MagicMock()

    # Pause the iface
    data = ActionData(interaction=mockInteraction)
    data.add(**{ActionData.FINALIZE_FUNCT: mockFinalize.finalize})
    result = await iface.pause.__wrapped__(iface, data)

    assert result.result is True
    assert iface.game.state is GameState.PAUSED
    assert iface.viewState is GameState.PAUSED
    assert iface.channelAdmin._AdminChannel__MSG_MAKE_CALL not in iface.channelAdmin._messageIDs # type: ignore[attr-defined]
    assert iface.channelBingo._BingoChannel__MSG_ADD_PLAYER not in iface.channelBingo._messageIDs # type: ignore[attr-defined]
    mockInteraction.followup.send.assert_called_once() # Verify followup action
    mockFinalize.finalize.assert_called_once() # Verify finalize called

@pytest.mark.asyncio
async def test_PausingGameFromInvalidStateIsError(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()

    for state in Utils.getAllGameStatesOrder():
        await Utils.setDiscordIfaceToState(iface, state)

        # Skip the valid state
        if state == GameState.STARTED or state == GameState.PAUSED:
            continue

        data = ActionData(interaction=Mocks.makeMockInteraction())
        result = await iface.pause.__wrapped__(iface, data)

        assert result.result is False, f"Expected fail when pausing from the {state} state."
        assert iface.game.state is state
        assert iface.viewState is state

@pytest.mark.asyncio
async def test_ChangingToValidStateFromPausedSucceeds(mock_GameInterfaceDiscord):
    for state in [GameState.STARTED, GameState.STOPPED, GameState.DESTROYED]:
        iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()
        await Utils.setDiscordIfaceToState(iface, GameState.PAUSED)

        if state == GameState.STARTED:
            result = await iface.start()
        elif state == GameState.STOPPED:
            result = await iface.stop()
        else:
            result = await iface.destroy()

        assert result.result is True, f"Expected success when changing to the {state} state."
        assert iface.game.state is state
        assert iface.viewState is state

        await iface.destroy()

@pytest.mark.asyncio
async def test_GameSuccessfullyStops(mock_GameInterfaceDiscord):
    iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()

    # Change the iface to the started state
    for state in [GameState.IDLE, GameState.STARTED]:
        await Utils.setDiscordIfaceToState(iface, state)

    result = await iface.stop()

    assert result.result is True
    assert iface.game.state is GameState.STOPPED
    assert iface.viewState is GameState.STOPPED
    assert iface.channelAdmin._AdminChannel__MSG_MAKE_CALL not in iface.channelAdmin._messageIDs # type: ignore[attr-defined]
    assert iface.channelBingo._BingoChannel__MSG_ADD_PLAYER not in iface.channelBingo._messageIDs # type: ignore[attr-defined]
    assert iface.taskProcessor.running is False

@pytest.mark.asyncio
async def test_StoppingGameFromInvalidStateFails(mock_GameInterfaceDiscord):
    for state in [GameState.DESTROYED]:
        iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()
        await Utils.setDiscordIfaceToState(iface, state)

        result = await iface.stop()

        assert result.result is False, f"Stopping game is expected to fail from the {state} state."
        assert "Cannot stop" in result.responseMsg

@pytest.mark.asyncio
async def test_StoppingGameFromValidStatesIsSuccess(mock_GameInterfaceDiscord):
    for state in [GameState.NEW, GameState.IDLE, GameState.STARTED, GameState.PAUSED]:
        iface: GameInterfaceDiscord = mock_GameInterfaceDiscord()
        await Utils.setDiscordIfaceToState(iface, state)

        result = await iface.stop()

        assert result.result is True
        assert iface.game.state is GameState.STOPPED, f"Expected success when stopping from the {state} state."
        assert iface.viewState is GameState.STOPPED, f"Expected success when stopping from the {state} state."

