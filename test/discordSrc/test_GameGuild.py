__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import test.utils.Const as Const

from discordSrc.GameGuild import GameGuild

from unittest.mock import MagicMock

def test_GameGuildInitCorrectly():
    mockGuildID = Const.TEST_GUILD_ID
    mockPersistance = MagicMock()
    mockBingoChannel = MagicMock()
    mockAdminChannel = MagicMock()

    gg = GameGuild(mockGuildID, mockPersistance, mockBingoChannel, mockAdminChannel)

    assert gg.guildID == mockGuildID
    assert gg.persistentStats == mockPersistance
    assert gg.channelBingo == mockBingoChannel
    assert gg.channelAdmin == mockAdminChannel

