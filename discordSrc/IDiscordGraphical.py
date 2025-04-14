__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import aiohttp
import discord

from PIL import Image, ImageDraw, ImageFont
from abc import ABC, abstractmethod
from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS
from game.PersistentStats import PlayerOrdinal
from io import BytesIO
from typing import Tuple, Union

Coord = Tuple[int, int]
Size = Tuple[int, int]
class IDiscordGraphical(ABC):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client):
        super().__init__()
        self.bot = bot

    @abstractmethod
    async def createAsset(self) -> discord.File:
        pass

    async def _getDiscordAvatar(self, playerOrd: PlayerOrdinal, avatarSize: int) -> Image.Image:
        avatar = None

        user = None
        if playerOrd.playerID >= 0:
            user = await self.bot.fetch_user(playerOrd.playerID)

        if not user:
            IDiscordGraphical.__LOGGER.log(LogLevel.LEVEL_WARN, f"Could not fetch user \"{playerOrd.name}\"({playerOrd.playerID})")
        else:
            playerOrd.name = user.display_name
            async with aiohttp.ClientSession() as session:
                async with session.get(user.display_avatar.url) as response:
                    data = await response.read()
                    avatar = Image.open(BytesIO(data)).convert("RGBA")

        # Load default avatar if the player icon could not be retrieved for whatever reason
        if not avatar:
            avatar = Image.open(GLOBALVARS.IMAGE_MISSING_PLAYER_ICON).convert("RGBA")

        return avatar.resize((avatarSize, avatarSize))

    def _drawTitleName(self, draw: ImageDraw.ImageDraw, titleName: str, fontName: str, fontSize: Size, pos: Coord, sizeMax: Size):
        fontTitle = None
        nameFits = False
        textWidth = 0
        textHeight = 0
        titleSize = fontSize[0]

        while not nameFits:
            fontTitle = self._getFont(fontName, titleSize)
            bbox = draw.multiline_textbbox((0, 0), titleName, font=fontTitle)
            textWidth = bbox[2] - bbox[0]
            textHeight = bbox[3] - bbox[1]

            nameFits = textWidth <= sizeMax[0] and textHeight <= sizeMax[1]
            if not nameFits:
                titleSize -= 2

            if titleSize < fontSize[1]:
                IDiscordGraphical.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Title too long \"{titleName}\", skipping drawing title.")
                break

        if nameFits:
            xPos = pos[0] + (sizeMax[0] - textWidth) / 2
            yPos = pos[1] + (sizeMax[1] - textHeight) / 2
            draw.multiline_text((xPos, yPos), titleName, fill=(0, 0, 0, 255), font=fontTitle, align="center")

    def _convertFile(self, image: Image.Image, name: str) -> discord.File:
        with BytesIO() as imageData:
            image.save(imageData, "PNG")
            imageData.seek(0)
            file = discord.File(imageData, name)
        return file

    def _getFont(self, fontName: str, fontSize: int) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
            try:
                font = ImageFont.truetype(fontName, fontSize)
            except Exception:
                IDiscordGraphical.__LOGGER.log(LogLevel.LEVEL_ERROR,
                                            f"Unable to load font \"{fontName}\", using PIL default.")
                font = ImageFont.load_default()

            return font

