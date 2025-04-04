__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from pathlib import Path

class GLOBALVARS:
    PROJ_ROOT = str(Path(__file__).parent.parent)

    DIR_RESOURCES = PROJ_ROOT + "/resources"
    DIR_CARD_IMAGES = DIR_RESOURCES + "/cards"
    DIR_DATA = DIR_RESOURCES + "/data"

    FILE_CONFIG_GENERAL = PROJ_ROOT + "/config/config.json"
    FILE_CONFIG_BINGLETS = PROJ_ROOT + "/config/binglets.json"
    FILE_BANNED_DATA = DIR_DATA + "/banned.json"
    FILE_GAME_DATA = DIR_DATA + "/game.json"
    FILE_PLAYER_DATA = DIR_DATA + "/players.json"

    IMAGE_BINGO_ICON = DIR_RESOURCES + "/assets/BingoIcon.png"
    IMAGE_CALL_ICON = DIR_RESOURCES + "/assets/CallIcon.png"
    IMAGE_CARD_BG = DIR_RESOURCES + "/assets/CardBG.jpg"
    IMAGE_GLOBAL_BOARD = DIR_RESOURCES + "/assets/GameGlobalBoard.png"
    IMAGE_MISSING_PLAYER_ICON = DIR_RESOURCES + "/assets/MissingPlayerIcon.png"

    CHANNEL_BINGO = "bingo"
    CHANNEL_ADMIN_BINGO ="bingo-admin"

    GAME_MSG_ENDED = "{StreamerName} livestream bingo has ended."
    GAME_MSG_PAUSED = "{StreamerName} livestream bingo game is paused."
    GAME_MSG_RESUMED = "{StreamerName} livestream bingo game has been resumed."
    GAME_MSG_STARTED = "{StreamerName} livestream bingo game has been started!"
    GAME_MSG_JOIN = "To play the livestream bingo, visit our discord and click the \"Play Bingo\" in the bingo channel!"

    GAME_NIGHTBOT_CMD_DISCORD = "!discord"

