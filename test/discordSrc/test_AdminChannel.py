__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import pytest
import pytest_asyncio

import game.NotificationMessageMaker as NotifMaker
import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from config.Config import Config
from config.Globals import GLOBALVARS

from discordSrc.AdminChannel import AdminChannel

from game.Bing import Bing
from game.CallRequest import CallRequest
from game.Game import GameState
from game.Player import Player

from unittest.mock import call

@pytest_asyncio.fixture(scope="function")
async def mock_AdminChannel(monkeypatch):
    mockGameGuild = Mocks.makeMockGuild()

    # Set the config to return Schecter for the StreamerName key
    Utils.overrideConfig(monkeypatch, "StreamerName", "Schecter")

    return AdminChannel(mockGameGuild, Const.TEST_GAME_TYPE)

@pytest.mark.asyncio
async def test_SetViewNewSuccessful(mock_AdminChannel):
    adminChannel: AdminChannel = mock_AdminChannel
    await adminChannel.setViewNew()

    assert AdminChannel._IChannelInterface__MSG_NOTICE in adminChannel._messageIDs # type: ignore[attr-defined]
    assert len(adminChannel.requestsViews) == 0
    assert adminChannel.gameControls.total_children_count == 0
    adminChannel._channel.send.assert_called_with(content="NOTICE: Setting up game...")

@pytest.mark.asyncio
async def test_SetViewStartedSuccessful(mock_AdminChannel):
    adminChannel: AdminChannel = mock_AdminChannel
    await adminChannel.setViewStarted()

    assert AdminChannel._IChannelInterface__MSG_NOTICE not in adminChannel._messageIDs # type: ignore[attr-defined]
    assert AdminChannel._AdminChannel__MSG_GAME_CONTROLS in adminChannel._messageIDs # type: ignore[attr-defined]
    assert AdminChannel._AdminChannel__MSG_MAKE_CALL in adminChannel._messageIDs # type: ignore[attr-defined]
    assert len(adminChannel.requestsViews) == 0
    assert adminChannel.gameControls.total_children_count == 2
    assert adminChannel._channel.send.call_args_list == [
            call(content=adminChannel.gameControls.msgStr, view=adminChannel.gameControls),
            call(content=adminChannel.callView.msgStr, view=adminChannel.callView)]

@pytest.mark.asyncio
async def test_SetViewPausedSuccessful(mock_AdminChannel):
    adminChannel: AdminChannel = mock_AdminChannel
    await adminChannel.setViewPaused()

    assert AdminChannel._IChannelInterface__MSG_NOTICE in adminChannel._messageIDs # type: ignore[attr-defined]
    assert AdminChannel._AdminChannel__MSG_GAME_CONTROLS in adminChannel._messageIDs # type: ignore[attr-defined]
    assert AdminChannel._AdminChannel__MSG_MAKE_CALL not in adminChannel._messageIDs # type: ignore[attr-defined]
    assert len(adminChannel.requestsViews) == 0
    assert adminChannel.gameControls.total_children_count == 2
    assert adminChannel._channel.send.call_args_list == [
            call(content=adminChannel.gameControls.msgStr, view=adminChannel.gameControls),
            call(content=f"NOTICE: {Config().getFormatConfig('StreamerName', GLOBALVARS.GAME_MSG_PAUSED)}")]

@pytest.mark.asyncio
async def test_SetViewStoppedSuccessful(mock_AdminChannel):
    adminChannel: AdminChannel = mock_AdminChannel
    await adminChannel.setViewStopped()

    assert AdminChannel._IChannelInterface__MSG_NOTICE in adminChannel._messageIDs # type: ignore[attr-defined]
    assert AdminChannel._AdminChannel__MSG_GAME_CONTROLS in adminChannel._messageIDs # type: ignore[attr-defined]
    assert AdminChannel._AdminChannel__MSG_MAKE_CALL not in adminChannel._messageIDs # type: ignore[attr-defined]
    assert len(adminChannel.requestsViews) == 0
    assert adminChannel.gameControls.total_children_count == 2
    assert adminChannel._channel.send.call_args_list == [
            call(content=adminChannel.gameControls.msgStr, view=adminChannel.gameControls),
            call(content=f"NOTICE: {Config().getFormatConfig('StreamerName', GLOBALVARS.GAME_MSG_ENDED)}")]

@pytest.mark.asyncio
async def test_AddCallRequestSuccessful(mock_AdminChannel):
    adminChannel: AdminChannel = mock_AdminChannel

    NUM_REQUEST_ADD = 20
    mockPlayer = Player(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)
    mockRequests = []
    mockRequestsMatching = []

    for i in range(NUM_REQUEST_ADD):
        mockBing = Bing(f"TestBing{i}", i)
        mockRequests.append(CallRequest(mockPlayer, mockBing))

    NUM_REQUEST_MATCHING_ADD = 5
    mockPlayer = Player("NewUser", Const.TEST_MOCK_VALID_USER_ID + 1)
    for i in range(NUM_REQUEST_MATCHING_ADD):
        mockBing = Bing(f"TestBing{i}", i)
        req = CallRequest(mockPlayer, mockBing)
        req.mergeRequests(mockRequests[i])
        mockRequestsMatching.append(req)

    for req in mockRequests:
        await adminChannel.addCallRequest(req)

    for req in mockRequestsMatching:
        await adminChannel.addCallRequest(req)

    assert len(adminChannel.requestsViews) == NUM_REQUEST_ADD

    # Test the INITIAL request calls
    listCalls = []
    for i in range(len(adminChannel.requestsViews)):
        req: CallRequest = mockRequests[i]
        reqView = adminChannel.requestsViews[i]

        assert reqView.viewID in adminChannel._messageIDs
        listCalls.append(call(content=NotifMaker.MakeCallRequestNotif(req), view=reqView))
    assert adminChannel._channel.send.call_args_list == listCalls

    # Test the UPDATED request calls
    listCalls.clear()
    for i in range(NUM_REQUEST_MATCHING_ADD):
        reqView = adminChannel.requestsViews[i]
        listCalls.append(call(content=reqView.viewText, view=reqView))
    messageID = adminChannel._messageIDs.get(adminChannel.requestsViews[0].viewID, -1)
    message = await adminChannel._channel.fetch_message(messageID)
    assert message.edit.call_args_list == listCalls

@pytest.mark.asyncio
async def test_DelCallRequestSuccessful(mock_AdminChannel):
    adminChannel: AdminChannel = mock_AdminChannel

    NUM_REQUEST_ADD = 20
    mockPlayer = Player(Const.TEST_USER_NAME, Const.TEST_MOCK_VALID_USER_ID)
    mockRequests = []

    for i in range(NUM_REQUEST_ADD):
        mockBing = Bing(f"TestBing{i}", i)
        mockRequests.append(CallRequest(mockPlayer, mockBing))

    for req in mockRequests:
        await adminChannel.addCallRequest(req)

    # Deleting a non-existing request ID does not affect the valid ones
    await adminChannel.delCallRequest(100)
    assert len(adminChannel.requestsViews) == NUM_REQUEST_ADD

    # Remove the 1st request
    await adminChannel.delCallRequest(0)

    assert len(adminChannel.requestsViews) == NUM_REQUEST_ADD - 1
    for reqView in adminChannel.requestsViews:
        assert reqView.callRequest.requestBing.bingIdx != 0

@pytest.mark.asyncio
async def test_DoubleCallingFunctionSkips(monkeypatch):
    def makeAdminChannel(monkeypatch) -> AdminChannel:
        mockGameGuild = Mocks.makeMockGuild()
        Utils.overrideConfig(monkeypatch, "StreamerName", "Schecter")
        return AdminChannel(mockGameGuild, Const.TEST_GAME_TYPE)

    for state in Utils.getAllGameStatesOrder():
        if state == GameState.NEW:
            adminChannel = makeAdminChannel(monkeypatch)

            await adminChannel.setViewNew()
            await adminChannel.setViewNew()

            adminChannel._channel.send.assert_called_once()
        elif state == GameState.STARTED:
            adminChannel = makeAdminChannel(monkeypatch)

            await adminChannel.setViewStarted()
            await adminChannel.setViewStarted()

            assert adminChannel._channel.send.call_count == 2
        elif state == GameState.PAUSED:
            adminChannel = makeAdminChannel(monkeypatch)

            await adminChannel.setViewPaused()
            await adminChannel.setViewPaused()

            assert adminChannel._channel.send.call_count == 2
        elif state == GameState.STOPPED:
            adminChannel = makeAdminChannel(monkeypatch)

            await adminChannel.setViewStopped()
            await adminChannel.setViewStopped()

            assert adminChannel._channel.send.call_count == 2

