__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discordSrc.GameInterfaceDiscord as GameInterfaceDiscordModule

from . import Classes as Classes
from . import Mocks as Mocks

from config.Config import Config
from discordSrc.GameInterfaceDiscord import GameInterfaceDiscord
from game.ActionData import ActionData
from game.Game import GameState

from typing import Any

def disableBanSaving(iface: GameInterfaceDiscord):
    def noOP(*args, **kwargs):
        pass
    iface.game.bannedPlayers.flush = noOP

def setMockedUserDMChannel(monkeypatch):
    monkeypatch.setattr(GameInterfaceDiscordModule, "UserDMChannel", Classes.TestingUserDMChannel)

def setMockedAdminChannel(monkeypatch):
    monkeypatch.setattr(GameInterfaceDiscordModule, "AdminChannel", Classes.TestingAdminChannel)

def setMockedBingoChanel(monkeypatch):
    monkeypatch.setattr(GameInterfaceDiscordModule, "BingoChannel", Classes.TestingBingoChannel)

def setMockedTaskProcessor(monkeypatch):
    monkeypatch.setattr(GameInterfaceDiscordModule, "TaskProcessor", Classes.TestingTaskProcessor)

def disableYTConfig(monkeypatch):
    overrideConfig(monkeypatch, "YTEnabled", False)

def overrideConfig(monkeypatch, key: str, val: Any):
    overrideConfig.configDict[key] = val
    origGetConfig = Config.getConfig
    def mockGetConfig(self, configStr, default: Any = ""):
        if configStr in overrideConfig.configDict:
            return overrideConfig.configDict[configStr]
        return origGetConfig(self, configStr, default)
    monkeypatch.setattr(Config, "getConfig", mockGetConfig)
overrideConfig.configDict = {}

def disableLeaderboardRankings(mockedGuilds):
    mockedGuilds.persistentStats.getTopPlayer.return_value = None

def setDebugConfig(monkeypatch, val: bool):
    overrideConfig(monkeypatch, "Debug", val)

def setRetroactiveCalls(monkeypatch, val: bool):
    overrideConfig(monkeypatch, "RetroactiveCalls", val)

def setUseFreeSpace(monkeypatch, val: bool):
    overrideConfig(monkeypatch, "UseFreeSpace", val)

def getAllGameStatesOrder():
    return [GameState.NEW, GameState.IDLE, GameState.STARTED, GameState.PAUSED, GameState.STOPPED, GameState.DESTROYED]

async def setDiscordIfaceToState(iface: GameInterfaceDiscord, state: GameState):
    if state == GameState.NEW:
        assert iface.viewState is GameState.NEW
        assert iface.game.state is GameState.NEW
        return

    await iface.init()
    if state == GameState.IDLE:
        assert iface.viewState is GameState.IDLE
        assert iface.game.state is GameState.IDLE
        return

    await iface.start()
    if state == GameState.STARTED:
        assert iface.viewState is GameState.STARTED
        assert iface.game.state is GameState.STARTED
        return

    await iface.pause.__wrapped__(iface, ActionData(interaction=Mocks.makeMockInteraction()))
    if state == GameState.PAUSED:
        assert iface.viewState is GameState.PAUSED
        assert iface.game.state is GameState.PAUSED
        return

    await iface.stop()
    if state == GameState.STOPPED:
        assert iface.viewState is GameState.STOPPED
        assert iface.game.state is GameState.STOPPED
        return

    await iface.destroy()
    if state == GameState.DESTROYED:
        assert iface.viewState is GameState.DESTROYED
        assert iface.game.state is GameState.DESTROYED

