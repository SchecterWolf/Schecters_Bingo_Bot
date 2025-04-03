__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from game.CallRequest import CallRequest
from game.Player import Player
from typing import List

MARKED_PLAYER_LIMIT = 3

def MakePlayersCallNotif(players: List[Player], maxMention: int = MARKED_PLAYER_LIMIT) -> str:
    """
    Creates a notification string for all players that were able mark a call slot
    """
    markedListPlayers: List[str] = []
    for player in players[:maxMention]:
        markedListPlayers.append(player.card.getCardOwner())

    markedPlayers: str = ""
    if markedListPlayers:
        if len(markedListPlayers) == 1:
            markedPlayers = markedListPlayers[0]
        elif len(markedPlayers) == 2:
            markedPlayers = "and ".join(markedListPlayers)
        else:
            markedPlayers = ", ".join(markedListPlayers[:-1])
            markedPlayers += ", and " + markedListPlayers[-1]

        remaining = len(players) - len(markedListPlayers)
        if remaining > 0:
            markedPlayers += " +{remaining} other{'s' if remaining > 1 else ''}"
        markedPlayers += f" marked their card{'s' if len(players) > 1 else ''}!"

    return markedPlayers if markedPlayers else "No players had this slot on their cards!"

def MakePlayersBingoNotif(players: List[Player]) -> str:
    bingosStr = ""
    for player in players:
        if bingosStr:
            bingosStr += ", "
        bingosStr += player.card.getCardOwner()
    if bingosStr:
        bingosStr = f"New player bingos: {bingosStr}"
    return bingosStr

def MakeCallRequestNotif(request: CallRequest) -> str:
    reqStr = f"Slot \"{request.requestBing.bingStr}\" is requested by {request.getPrimaryRequester().card.getCardOwner()}"
    if len(request.players) < 2:
        reqStr += "."
    else:
        reqStr += f" and {len(request.players) - 1} other" + "s." if len(request.players) > 2 else "."

    return reqStr

