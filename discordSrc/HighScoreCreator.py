__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IDiscordGraphical import IDiscordGraphical

from PIL import Image, ImageDraw
from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from game.PersistentStats import PersistentStats

class HighScoreCreator(IDiscordGraphical):
    __LOGGER = ClassLogger(__name__)

    __BOARD_TITLE_WIDTH = 1750
    __BOARD_TITLE_HEIGHT = 405

    __FONT_SIZE_TITLE = 140

    __XPOS_TITLE = 340
    __YPOS_TITLE = 650

    def __init__(self, bot: discord.Client, globalStats: PersistentStats):
        super().__init__(bot)

        self.globalStats = globalStats
        self.fontName = Config().getConfig("Font")
        self.cType = ""

    async def createLeaderboard(self, cType: str) -> discord.File:
        self.cType = cType
        return await self.createAsset()

    async def createAsset(self) -> discord.File:
        # TODO SCH add cType check
        HighScoreCreator.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Creating high scores graphic")
        highScoreGraphic = Image.open(GLOBALVARS.IMAGE_HIGH_SCORES).convert("RGBA")
        draw = ImageDraw.Draw(highScoreGraphic)

        sn = Config().getConfig("StreamerName")
        title = f"{self.globalStats.getCanonicalCType(self.cType)}\n\
{sn} Livestream Bingo\nHigh Scores"
        self._drawTitleName(draw, title, self.fontName,
                            fontSize=(HighScoreCreator.__FONT_SIZE_TITLE, HighScoreCreator.__FONT_SIZE_TITLE),
                            pos=(HighScoreCreator.__XPOS_TITLE, HighScoreCreator.__YPOS_TITLE),
                            sizeMax=(HighScoreCreator.__BOARD_TITLE_WIDTH, HighScoreCreator.__BOARD_TITLE_HEIGHT))

        return self._convertFile(highScoreGraphic, "highscores.png")

