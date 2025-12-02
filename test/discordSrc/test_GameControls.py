__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import discord
import pytest

import test.utils.Const as Const

from discordSrc.EndGameButton import EndGameButton
from discordSrc.GameControls import GameControls, GameControlState
from discordSrc.PauseGameButton import PauseGameButton
from discordSrc.ResumeGameButton import ResumeGameButton

from typing import cast

@pytest.mark.asyncio
async def test_SetRunningSucceeds():
    ctrls = GameControls(Const.TEST_GUILD_ID)
    assert len(ctrls.children) == 0

    ctrls.setControllsState(GameControlState.RUNNING)

    assert len(ctrls.children) == 2
    assert isinstance(ctrls.children[0], discord.ui.Button)
    assert cast(discord.ui.Button, ctrls.children[0]).label == PauseGameButton._PauseGameButton__btn_label # type: ignore[attr-defined]
    assert isinstance(ctrls.children[1], discord.ui.Button)
    assert cast(discord.ui.Button, ctrls.children[1]).label == EndGameButton._EndGameButton__btn_label # type: ignore[attr-defined]

@pytest.mark.asyncio
async def test_SetPausedSucceeds():
    ctrls = GameControls(Const.TEST_GUILD_ID)
    ctrls.setControllsState(GameControlState.PAUSED)

    assert len(ctrls.children) == 2
    assert isinstance(ctrls.children[0], discord.ui.Button)
    assert cast(discord.ui.Button, ctrls.children[0]).label == ResumeGameButton._ResumeGameButton__btn_label # type: ignore[attr-defined]
    assert isinstance(ctrls.children[1], discord.ui.Button)
    assert cast(discord.ui.Button, ctrls.children[1]).label == EndGameButton._EndGameButton__btn_label # type: ignore[attr-defined]

@pytest.mark.asyncio
async def test_SetEndedSucceeds():
    ctrls = GameControls(Const.TEST_GUILD_ID)
    ctrls.setControllsState(GameControlState.ENDED)

    assert len(ctrls.children) == 2
    assert isinstance(ctrls.children[0], discord.ui.Button)
    assert cast(discord.ui.Button, ctrls.children[0]).label == "Start New Game (FiveM)"
    assert cast(discord.ui.Button, ctrls.children[1]).label == "Start New Game (RedM)"
