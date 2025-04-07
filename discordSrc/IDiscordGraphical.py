__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import aiohttp
import discord

from PIL import Image
from abc import ABC, abstractmethod
from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS
from game.PersistentStats import PlayerOrdinal
from io import BytesIO

class IDiscordGraphical(ABC):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client):
        super().__init__()
        self.bot = bot

    async def _getDiscordAvatar(self, playerOrd: PlayerOrdinal, avatarSize: int) -> Image.Image:
        avatar = None
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

    @abstractmethod
    async def createAsset(self) -> discord.File:
        pass

