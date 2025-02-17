__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import textwrap

from PIL import Image, ImageDraw, ImageFont

from config.Config import Config
from config.ClassLogger import ClassLogger
from config.Globals import GLOBALVARS
from config.Log import LogLevel

from game.Card import Card
from typing import List, Tuple

class CardImgCreator:
    __BG_BOARDER = 30
    __OPACITY = 115
    __SIZE_CELLS = 160
    __SIZE_LINE_WDTH = 2
    __SIZE_TEXT = 20

    def createGraphicalCard(self, card: Card) -> Tuple[str, str]:
        gridOverlay = self._createGridOverlay(card)
        gridWidth, gridHeight = gridOverlay.size
        background = Image.open(GLOBALVARS.IMAGE_CARD_BG).convert("RGBA")

        # Resize the BG
        background = background.resize((gridWidth + CardImgCreator.__BG_BOARDER, gridHeight + CardImgCreator.__BG_BOARDER))

        # Composite the grid over the background layer
        background.paste(gridOverlay, (int(CardImgCreator.__BG_BOARDER / 2), int(CardImgCreator.__BG_BOARDER / 2)), mask=gridOverlay)

        # Save to the file system, since the discord API requires it
        cardName = f"{card.getCardOwner()}.png"
        cardFile = f"{GLOBALVARS.DIR_CARD_IMAGES}/{cardName}"
        background.save(cardFile, format="PNG")

        return cardFile, cardName

    def _createGridOverlay(self, card: Card) -> Image.Image:
        cellStrs: List[List[str]] = self._getCellStrs(card)
        rows = len(cellStrs)
        cols = len(cellStrs[0])
        width = cols * CardImgCreator.__SIZE_CELLS
        height = rows * CardImgCreator.__SIZE_CELLS

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Use the FONT type if possible, otherwise use the builtin default
        fontPath = Config().getConfig("Font")
        try:
            font = ImageFont.truetype(fontPath, CardImgCreator.__SIZE_TEXT)
        except IOError:
            ClassLogger(__name__).log(LogLevel.LEVEL_WARN, f"Unable to load font \"{fontPath}\", using PIL default.")
            font = ImageFont.load_default()

        for i in range(rows):
            for j in range(cols):
                topLeft = (j * CardImgCreator.__SIZE_CELLS, i * CardImgCreator.__SIZE_CELLS)
                bottomRight = ((j + 1) * CardImgCreator.__SIZE_CELLS, (i + 1) * CardImgCreator.__SIZE_CELLS)

                # Color in the cells, white = unmarked and red = marked
                if card.isCellMarked(i, j):
                    fillColor = (255, 0, 0, CardImgCreator.__OPACITY) # Red
                else:
                    fillColor = (255, 255, 255, CardImgCreator.__OPACITY) # White
                draw.rectangle([topLeft, bottomRight], fill=fillColor)

                # Draw the borders
                draw.rectangle([topLeft, bottomRight], outline=(0, 0, 0, 255), width=CardImgCreator.__SIZE_LINE_WDTH)

                # Calculate spacing
                text = cellStrs[i][j]
                bbox = draw.multiline_textbbox((0, 0,), text, font=font)
                textWidth = bbox[2] - bbox[0]
                textHeight = bbox[3] - bbox[1]
                textX = topLeft[0] + (CardImgCreator.__SIZE_CELLS - textWidth) / 2
                textY = topLeft[1] + (CardImgCreator.__SIZE_CELLS - textHeight) / 2

                draw.multiline_text((textX, textY), text, fill=(0, 0, 0, 255), font=font, align="center")

                # Get the text dimensions
                #textWidth = draw.textlength(text, font=font)
                #bbox = font.getbbox(text)
                #textHeight = bbox[3] - bbox[1]

                # Draw the text string
                #textX = topLeft[0] + (CardImgCreator.__SIZE_CELLS - textWidth) / 2
                #textY = topLeft[1] + (CardImgCreator.__SIZE_CELLS - textHeight) / 2
                #draw.text((textX, textY), text, fill=(0, 0, 0, 255), font=font)

        return overlay

    def _getCellStrs(self, card: Card) -> list:
        """Gets the cards cell strings in 'pretty' format wrapping"""
        cells = card.getCellsStr()
        colWidth = [max(len(word) for row in cells for word in str(row[col]).split()) for col in range(len(cells[0]))]
        wrappedLines = []

        for row in cells:
            wrappedRow = []
            for col, cell in enumerate(row):
                words = str(cell).split()
                wrappedCell = "\n".join(textwrap.fill(" ".join(words), width=colWidth[col]).split("\n"))
                wrappedRow.append(wrappedCell)
            wrappedLines.append(wrappedRow)

        return wrappedLines

