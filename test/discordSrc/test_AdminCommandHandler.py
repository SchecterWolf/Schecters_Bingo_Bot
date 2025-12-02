__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import asyncio
import pytest

import test.utils.Const as Const
import test.utils.Mocks as Mocks
import test.utils.Utils as Utils

from discordSrc.AdminCommandHandler import AdminCommandHandler
from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord

from game.ActionData import ActionData
from game.BannedData import BannedData
from game.Bing import Bing
from game.CallRequest import CallRequest
from game.Game import GameState
from game.GameStore import GameStore
from game.Player import Player
from game.Result import Result

from typing import List, cast
from unittest.mock import MagicMock, call

@pytest.fixture(scope="function")
def mock_AdminCommandHandler(monkeypatch):
    store = GameStore()
    mockGuilds = Mocks.makeMockGuild()
    adminCmdHandler = AdminCommandHandler()

    # Make the make game iface
    Utils.disableYTConfig(monkeypatch)
    Utils.disableLeaderboardRankings(mockGuilds)
    iface = GameInterfaceDiscord(Mocks.makeMockBot(), mockGuilds, Const.TEST_GAME_TYPE)

    # Disable ban saving
    Utils.disableBanSaving(iface)

    # Add the game to the store
    if not store.getGame(Const.TEST_GUILD_ID):
        store.addGame(Const.TEST_GUILD_ID, iface)

    yield adminCmdHandler

    # RM the game from the store
    store.removeGame(Const.TEST_GUILD_ID)

    # Clean up task processor
    iface.taskProcessor.stop()

@pytest.mark.asyncio
async def test_KickPlayerSuccessful(mock_AdminCommandHandler):
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockUser = Mocks.makeMockUser("Admin", Const.TEST_MOCK_VALID_USER_ID)
    mockKickUser = Mocks.makeMockUser("Rando", Const.TEST_MOCK_VALID_USER_ID + 1)

    # Add the user to the game
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = mockKickUser
    result: Result = await iface.addPlayer.__wrapped__(iface, ActionData(interaction=mockInteraction))
    assert result.result is True

    # Test kicking the user
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = mockUser
    await adminCmdHandler.kickPlayer(mockInteraction, mockKickUser)
    await asyncio.sleep(0)

    assert mockKickUser.id in iface.game.kickedPlayers
    assert Player(mockKickUser.name, mockKickUser.id) not in iface.game.players

@pytest.mark.asyncio
async def test_KickingBotUserFails(mock_AdminCommandHandler):
    """
    Trying to kick the bot (which is a user) is invalid
    """
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockUser = Mocks.makeMockUser("Admin", Const.TEST_MOCK_VALID_USER_ID)
    mockKickUser = Mocks.makeMockUser("Bot", Const.TEST_BOT_ID)

    # Test kicking the bot
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.client.user = mockKickUser
    mockInteraction.user = mockUser
    await adminCmdHandler.kickPlayer(mockInteraction, mockKickUser)
    await asyncio.sleep(0)

    assert mockKickUser.id not in iface.game.kickedPlayers
    mockInteraction.response.send_message.assert_called_once_with(f"\U0001F6AB Can't use the bot for this command", ephemeral=True)

@pytest.mark.asyncio
async def test_BanPlayerSuccessful(mock_AdminCommandHandler):
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    Utils.disableBanSaving(iface)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockUser = Mocks.makeMockUser("Admin", Const.TEST_MOCK_VALID_USER_ID)
    mockBannedUser = Mocks.makeMockUser("Rando", Const.TEST_MOCK_VALID_USER_ID + 1)

    # Add the user to the game
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = mockBannedUser
    result: Result = await iface.addPlayer.__wrapped__(iface, ActionData(interaction=mockInteraction))
    assert result.result is True

    # Ban the user
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = mockUser
    await adminCmdHandler.banPlayer(mockInteraction, mockBannedUser)
    await asyncio.sleep(0)

    assert mockBannedUser.id in iface.game.kickedPlayers
    assert Player(mockBannedUser.name, mockBannedUser.id) not in iface.game.players
    assert iface.game.bannedPlayers.isBanned(mockBannedUser.id)

    # Reset banned data
    iface.game.bannedPlayers.data = {}

@pytest.mark.asyncio
async def test_BaningPreemptivePlayerSuccessful(mock_AdminCommandHandler):
    """
    Test that case that the admin command handler can ban a discord user
    from the game even if that user is not playing at the time.
    """
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    Utils.disableBanSaving(iface)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockUser = Mocks.makeMockUser("Admin", Const.TEST_MOCK_VALID_USER_ID)
    mockBannedUser = Mocks.makeMockUser("PreemptiveUser", Const.TEST_MOCK_VALID_USER_ID + 1000)

    # Ban the user
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = mockUser
    await adminCmdHandler.banPlayer(mockInteraction, mockBannedUser)
    await asyncio.sleep(0)

    assert BannedData().isBanned(mockBannedUser.id)
    mockInteraction.response.send_message.assert_called_once()

    # Reset banned data
    iface.game.bannedPlayers.data = {}

@pytest.mark.asyncio
async def test_BanningBotUserFails(mock_AdminCommandHandler):
    """
    Trying to ban the bot (which is a user) is invalid
    """
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    Utils.disableBanSaving(iface)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockUser = Mocks.makeMockUser("Admin", Const.TEST_MOCK_VALID_USER_ID)
    mockBannedUser = Mocks.makeMockUser("Bot", Const.TEST_BOT_ID)

    # Test banning the bot
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.client.user = mockBannedUser
    mockInteraction.user = mockUser
    await adminCmdHandler.banPlayer(mockInteraction, mockBannedUser)
    await asyncio.sleep(0)

    assert mockBannedUser.id not in iface.game.kickedPlayers
    assert not iface.game.bannedPlayers.isBanned(mockBannedUser.id)
    mockInteraction.response.send_message.assert_called_once_with(f"\U0001F6AB Can't use the bot for this command", ephemeral=True)

    # Reset banned data
    iface.game.bannedPlayers.data = {}

@pytest.mark.asyncio
async def test_UnBanPlayerSuccessful(mock_AdminCommandHandler):
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    Utils.disableBanSaving(iface)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockUser = Mocks.makeMockUser("Admin", Const.TEST_MOCK_VALID_USER_ID)
    mockBannedUser = Mocks.makeMockUser("PreemptiveUser", Const.TEST_MOCK_VALID_USER_ID + 1000)

    # Ban the user
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.user = mockUser
    await adminCmdHandler.banPlayer(mockInteraction, mockBannedUser)
    await asyncio.sleep(0)
    assert BannedData().isBanned(mockBannedUser.id)

    # Unban the user
    await adminCmdHandler.unbanPlayer(mockInteraction, mockBannedUser)
    await asyncio.sleep(0)

    assert not iface.game.bannedPlayers.isBanned(mockBannedUser.id)
    assert mockInteraction.response.send_message.call_args_list == [
            call(f"\U0000274C\U0001F528 Banning user {mockBannedUser.display_name} from all further games!"),
            call(f"\U0001F607 Unbanning user {mockBannedUser.display_name}")]

    # Reset banned data
    iface.game.bannedPlayers.data = {}

@pytest.mark.asyncio
async def test_UnBanningBotUserFails(mock_AdminCommandHandler):
    """
    Trying to ban the bot (which is a user) is invalid
    """
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    Utils.disableBanSaving(iface)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    mockUser = Mocks.makeMockUser("Admin", Const.TEST_MOCK_VALID_USER_ID)
    mockBannedUser = Mocks.makeMockUser("Bot", Const.TEST_BOT_ID)

    # Test unbanning the bot
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.client.user = mockBannedUser
    mockInteraction.user = mockUser
    await adminCmdHandler.unbanPlayer(mockInteraction, mockBannedUser)
    await asyncio.sleep(0)

    assert not iface.game.bannedPlayers.isBanned(mockBannedUser.id)
    mockInteraction.response.send_message.assert_called_once_with(f"\U0001F6AB Can't use the bot for this command", ephemeral=True)

    # Reset banned data
    iface.game.bannedPlayers.data = {}

@pytest.mark.asyncio
async def test_GameStatusCorrectlyReports(mock_AdminCommandHandler):
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    Utils.disableBanSaving(iface)
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Add some players
    NUM_TEST_PLAYERS = 10
    testPlayers = []
    for i in range(NUM_TEST_PLAYERS):
        mockInteraction = Mocks.makeMockInteraction()
        mockInteraction.user = Mocks.makeMockUser(f"TestUser{i}", Const.TEST_MOCK_VALID_USER_ID + i)
        testPlayers.append(mockInteraction.user)
        result: Result = await iface.addPlayer.__wrapped__(iface, ActionData(interaction=mockInteraction))
        assert result.result is True, result.responseMsg

    # Kick some player
    NUM_KICK_PLAYERS = 2
    kickedPlayers = []
    for i in range(NUM_KICK_PLAYERS):
        mockKickUser = Mocks.makeMockUser(f"TestUser{i}", Const.TEST_MOCK_VALID_USER_ID + i)
        kickedPlayers.append(mockKickUser)
        result: Result = await iface.kickPlayer.__wrapped__(iface, ActionData(member=mockKickUser))
        assert result.result is True

    # Ban some players
    NUM_BAN_PLAYERS = 2
    bannedPlayers = []
    for i in range(NUM_BAN_PLAYERS):
        j = i + NUM_KICK_PLAYERS
        mockBanUser = Mocks.makeMockUser(f"TestUser{i}", Const.TEST_MOCK_VALID_USER_ID + j)
        bannedPlayers.append(mockBanUser)
        result: Result = await iface.banPlayer.__wrapped__(iface, ActionData(member=mockBanUser))
        assert result.result is True

    # Give the 10th player a bingo
    calls = []
    result: Result = iface.game.getPlayer(testPlayers[NUM_TEST_PLAYERS - 1].id)
    assert result.result is True
    player: Player = cast(Player, result.additional)
    bings: List[List[Bing]] = player.card.getCardBings()
    for i in range(len(bings[0])):
        mockInteraction = Mocks.makeMockInteraction()
        data = ActionData(interaction=mockInteraction, index=bings[0][i].bingIdx)
        calls.append(bings[0][i].bingStr)
        result: Result = await iface.makeCall.__wrapped__(iface, data)
        assert result.result is True

    # Make 5 call request
    NUM_REQUESTS = 5
    requests = []
    for i in range(NUM_REQUESTS):
        mockplayer = testPlayers[NUM_KICK_PLAYERS + NUM_BAN_PLAYERS + i]

        # Get the player obj
        result: Result = iface.game.getPlayer(mockplayer.id)
        assert result.result is True
        player: Player = cast(Player, result.additional)

        # Get a bing that hasnt been marked by the player yet
        bing = None
        bings: List[List[Bing]] = player.card.getCardBings()
        x = 0
        y = 0
        while not bing:
            if not bings[x][y].marked:
                bing = bings[x][y]
            else:
                x = (x + 1) % len(bings[0])
                if x == 0:
                    y = (y + 1) % len(bings[0])

        # Make call request
        mockInteraction = Mocks.makeMockInteraction()
        req = CallRequest(player, bing)
        data = ActionData(interaction=mockInteraction, callRequest=req)
        requests.append(bing.bingStr)
        result: Result = await iface.requestCall.__wrapped__(iface, data)
        assert result.result is True

    # Overriding the default fetch_member function so that it returns one of the
    # test users we created in this test
    async def getTestUser(userID: int):
        user = MagicMock()
        for player in testPlayers:
            if player.id == userID:
                user = player
                break
        return user

    # Get game status
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.guild.fetch_member = getTestUser
    await adminCmdHandler.gameStatus(mockInteraction)
    await asyncio.sleep(0)

    mockInteraction.followup.send.assert_called_once()
    gameStatusText = mockInteraction.followup.send.call_args[0][0]

    # Check for game duration
    assert "Game elapsed time:" in gameStatusText

    # Check players
    for i in range(NUM_TEST_PLAYERS - NUM_KICK_PLAYERS - NUM_BAN_PLAYERS):
        i = i + NUM_BAN_PLAYERS + NUM_KICK_PLAYERS
        assert f"{testPlayers[i].name}:" in gameStatusText

    # Check kicked players
    assert ", ".join(p.name for p in kickedPlayers) in gameStatusText

    # Check banned players
    assert ", ".join(p.name for p in bannedPlayers) in gameStatusText

    # Check player bingos
    assert f"Player bingos: {testPlayers[NUM_TEST_PLAYERS - 1].name}" in gameStatusText

    # Check requests
    for req in requests:
        assert req in gameStatusText

    # Check calls
    for call in calls:
        assert call in gameStatusText

@pytest.mark.asyncio
async def test_GameStatusForInvalidGameFails(mock_AdminCommandHandler):
    adminCmdHandler: AdminCommandHandler = mock_AdminCommandHandler
    iface: GameInterfaceDiscord = cast(GameInterfaceDiscord, GameStore().getGame(Const.TEST_GUILD_ID))
    await Utils.setDiscordIfaceToState(iface, GameState.STARTED)

    # Get game status
    mockInteraction = Mocks.makeMockInteraction()
    mockInteraction.guild.id = Const.TEST_GUILD_ID + 1
    mockInteraction.guild.name = "FAKE"
    mockInteraction.guild_id = mockInteraction.guild.id
    await adminCmdHandler.gameStatus(mockInteraction)
    await asyncio.sleep(0)

    mockInteraction.response.send_message.assert_called_once_with("\U0000274C There is no active game for server FAKE", ephemeral=True)

