__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import pytest
import pytest_asyncio

import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from config.Config import Config, GLOBALVARS
from game.Game import GameState

from discordSrc.BingoChannel import BingoChannel

from unittest.mock import ANY, call

@pytest_asyncio.fixture(scope="function")
async def mock_BingoChannel(monkeypatch):
    mockGameGuild = Mocks.makeMockGuild()
    Utils.disableLeaderboardRankings(mockGameGuild)

    # Set the config to return Schecter for the StreamerName key
    Utils.overrideConfig(monkeypatch, "StreamerName", "Schecter")

    return BingoChannel(Mocks.makeMockBot(), mockGameGuild)

@pytest.mark.asyncio
async def test_SetViewStartedSuccessful(mock_BingoChannel):
    bingoChannel: BingoChannel = mock_BingoChannel
    await bingoChannel.setViewStarted()

    assert BingoChannel._IChannelInterface__MSG_NOTICE not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GLOBAL_STATS in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GAME_STATUS in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_ADD_PLAYER in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert bingoChannel.showAddBtn is True
    assert bingoChannel.gameStatus.file is not None
    assert bingoChannel._channel.send.call_args_list == [
            call(file=ANY),
            call(embed=bingoChannel.gameStatus, file=bingoChannel.gameStatus.file),
            call(content=bingoChannel.addPlayer.msgStr, view=bingoChannel.addPlayer)]

@pytest.mark.asyncio
async def test_SetViewPausedSuccessful(mock_BingoChannel):
    bingoChannel: BingoChannel = mock_BingoChannel
    await bingoChannel.setViewPaused()

    assert BingoChannel._IChannelInterface__MSG_NOTICE in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GLOBAL_STATS not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GAME_STATUS not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_ADD_PLAYER not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert bingoChannel.showAddBtn is False
    assert bingoChannel._channel.send.call_args_list == [
            call(content=f"NOTICE: {Config().getFormatConfig('StreamerName', GLOBALVARS.GAME_MSG_PAUSED)}")]

@pytest.mark.asyncio
async def test_SetViewStoppedSuccessful(mock_BingoChannel):
    bingoChannel: BingoChannel = mock_BingoChannel
    await bingoChannel.setViewStopped()

    assert BingoChannel._IChannelInterface__MSG_NOTICE in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GLOBAL_STATS in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GAME_STATUS in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_ADD_PLAYER not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert bingoChannel.showAddBtn is False
    assert bingoChannel._channel.send.call_args_list == [
            call(file=ANY),
            call(embed=bingoChannel.gameStatus),
            call(content=f"NOTICE: {Config().getFormatConfig('StreamerName', GLOBALVARS.GAME_MSG_ENDED)}")]

@pytest.mark.asyncio
async def test_RefreshGameStatusSuccessful(mock_BingoChannel):
    bingoChannel: BingoChannel = mock_BingoChannel
    await bingoChannel.refreshGameStatus()

    assert BingoChannel._IChannelInterface__MSG_NOTICE not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GLOBAL_STATS not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GAME_STATUS in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_ADD_PLAYER not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert bingoChannel.showAddBtn is False
    assert bingoChannel._channel.send.call_args_list == [
            call(embed=bingoChannel.gameStatus)]


@pytest.mark.asyncio
async def test_SendNoticeItemAddsPlayerButton(mock_BingoChannel):
    bingoChannel: BingoChannel = mock_BingoChannel
    bingoChannel.showAddBtn = True
    await bingoChannel.sendNotice("Hello world")

    assert BingoChannel._IChannelInterface__MSG_NOTICE in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GLOBAL_STATS not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GAME_STATUS not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_ADD_PLAYER not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert bingoChannel._channel.send.call_args_list == [
            call(content="NOTICE: Hello world", view=bingoChannel.addPlayer)]

@pytest.mark.asyncio
async def test_SendNoticeItemSkipsPlayerButton(mock_BingoChannel):
    bingoChannel: BingoChannel = mock_BingoChannel
    await bingoChannel.sendNotice("Hello world")

    assert BingoChannel._IChannelInterface__MSG_NOTICE in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GLOBAL_STATS not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_GAME_STATUS not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert BingoChannel._BingoChannel__MSG_ADD_PLAYER not in bingoChannel._messageIDs # type: ignore[attr-defined]
    assert bingoChannel._channel.send.call_args_list == [
            call(content="NOTICE: Hello world")]

@pytest.mark.asyncio
async def test_DoubleCallingFunctionSkips(monkeypatch):
    def makeBingoChannel(monkeypatch) -> BingoChannel:
        mockGameGuild = Mocks.makeMockGuild()
        Utils.disableLeaderboardRankings(mockGameGuild)
        Utils.overrideConfig(monkeypatch, "StreamerName", "Schecter")
        return BingoChannel(Mocks.makeMockBot(), mockGameGuild)

    for state in Utils.getAllGameStatesOrder():
        if state == GameState.STARTED:
            bingoChannel = makeBingoChannel(monkeypatch)
            await bingoChannel.setViewStarted()
            await bingoChannel.setViewStarted()
            assert bingoChannel._channel.send.call_args_list == [
                    call(file=ANY),
                    call(embed=bingoChannel.gameStatus, file=bingoChannel.gameStatus.file),
                    call(content=bingoChannel.addPlayer.msgStr, view=bingoChannel.addPlayer)]
        elif state == GameState.PAUSED:
            bingoChannel = makeBingoChannel(monkeypatch)
            await bingoChannel.setViewPaused()
            await bingoChannel.setViewPaused()
            assert bingoChannel._channel.send.call_args_list == [
                    call(content=f"NOTICE: {Config().getFormatConfig('StreamerName', GLOBALVARS.GAME_MSG_PAUSED)}")]
        elif state == GameState.STOPPED:
            bingoChannel = makeBingoChannel(monkeypatch)
            await bingoChannel.setViewStopped()
            await bingoChannel.setViewStopped()
            assert bingoChannel._channel.send.call_args_list == [
                    call(file=ANY),
                    call(embed=bingoChannel.gameStatus),
                    call(content=f"NOTICE: {Config().getFormatConfig('StreamerName', GLOBALVARS.GAME_MSG_ENDED)}")]

