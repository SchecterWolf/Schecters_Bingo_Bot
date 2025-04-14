__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"


import test.utils.Const as Const

from discordSrc.CallNoticeEmbed import CallNoticeEmbed

from game.Bing import Bing
from game.Binglets import Binglets
from game.NotificationMessageMaker import MakePlayersBingoNotif
from game.Player import Player

def test_InitsCorrectly():
    bing: Bing = Binglets(Const.TEST_GAME_TYPE).getBingFromIndex(1)

    markedPlayers = []
    NUM_TEST_PLAYERS = 5
    for i in range(NUM_TEST_PLAYERS):
        markedPlayers.append(Player(f"Player{i}", Const.TEST_MOCK_VALID_USER_ID + i))

    bingoStr = MakePlayersBingoNotif([markedPlayers[0], markedPlayers[1]])

    embed = CallNoticeEmbed(bing, markedPlayers, bingoStr)
    assert embed.title == f"\u200b\n\U00002757 {bing.bingStr} \U00002757\n\u200b"
    assert len(embed.fields) == 4
    assert embed.fields[0].name == "\U0001F3C5 BINGOS \U0001F3C5"
    assert embed.fields[0].value == bingoStr
    assert embed.fields[1].name == "\u200b"
    assert embed.fields[1].value == "\u200b"
    assert embed.fields[2].name == CallNoticeEmbed._CallNoticeEmbed__FIELD_MARKED_TITLE # type: ignore[attr-defined]
    assert embed.fields[2].value == "\u00A0"
    assert embed.fields[3].name == CallNoticeEmbed._CallNoticeEmbed__FIELD_MARKED_COL # type: ignore[attr-defined]
    assert embed.fields[3].value == "\n".join(p.card.getCardOwner() for p in markedPlayers)

def test_InitWithOnlyPlayers():
    NUM_TEST_PLAYERS = 10
    markedPlayers = []
    for i in range(NUM_TEST_PLAYERS):
        markedPlayers.append(Player(f"Player{i}", Const.TEST_MOCK_VALID_USER_ID + i))

    bing: Bing = Binglets(Const.TEST_GAME_TYPE).getBingFromIndex(2)
    embed = CallNoticeEmbed(bing, markedPlayers, "")

    assert embed.title == f"\u200b\n\U00002757 {bing.bingStr} \U00002757\n\u200b"
    assert len(embed.fields) == 3
    assert embed.fields[0].name == CallNoticeEmbed._CallNoticeEmbed__FIELD_MARKED_TITLE # type: ignore[attr-defined]
    assert embed.fields[0].value == "\u00A0"
    assert embed.fields[1].name == CallNoticeEmbed._CallNoticeEmbed__FIELD_MARKED_COL # type: ignore[attr-defined]
    assert embed.fields[1].value == "\n".join(p.card.getCardOwner() for p in markedPlayers[:CallNoticeEmbed._CallNoticeEmbed__MAX_ROW_COUNT]) # type: ignore[attr-defined]
    assert embed.fields[2].name == CallNoticeEmbed._CallNoticeEmbed__FIELD_MARKED_COL # type: ignore[attr-defined]
    assert embed.fields[2].value == "\n".join(p.card.getCardOwner() for p in markedPlayers[CallNoticeEmbed._CallNoticeEmbed__MAX_ROW_COUNT + 1:]) # type: ignore[attr-defined]

