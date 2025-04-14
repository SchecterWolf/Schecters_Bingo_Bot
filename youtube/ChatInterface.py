__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .ChatMessage import ChatMessage

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config

from google.auth.exceptions import MutualTLSChannelError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from game.Result import Result

from collections import deque
from typing import Any, List, Optional

class ChatInterface:
    __LOGGER = ClassLogger(__name__)
    __SCOPES = ["https://www.googleapis.com/auth/youtube"]

    def __init__(self):
        self.chatID: Optional[str] = None
        self.pageToken: Any = None
        self.yt: Any = None

        self.numMaxChatMsgs = Config().getConfig("YTMaxChatMsgs", 0)
        self.messageIDs = deque()

    def init(self) -> Result:
        ChatInterface.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Getting youtube credential...")
        ret = Result(False)
        oauthCred = None

        # Read in the saved token
        try:
            oauthCred = Credentials.from_authorized_user_file(Config().getConfig("YTTokenFile"), ChatInterface.__SCOPES)
        except ValueError as e:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Failed to create ouath cred: {str(e)}")

        # Create the youtube resource object
        if oauthCred:
            try:
                self.yt = build("youtube", "v3", credentials=oauthCred)
            except MutualTLSChannelError as e:
                ChatInterface.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Failed to set up youtube resource: {str(e)}")

        if self.yt:
            ret.result = True
        else:
            ret.responseMsg = "Failed to initialize the youtube chat interface."

        return ret

    def getMessages(self) -> List[ChatMessage]:
        if not self.yt:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Youtube interface not initialized, aborting")
            return []
        if not self.chatID and not self._fetchStreamID():
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Unable to get chat ID for the livestream, aborting sending message.")
            return []

        response = None
        try:
            request = self.yt.liveChatMessages().list(
                        liveChatId=self.chatID,
                        part="id,snippet,authorDetails",
                        pageToken=self.pageToken,
                    )
            response = request.execute()
        except Exception:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Failed to send get message request.")

        ret: List[ChatMessage] = []
        if response:
            self.pageToken = response.get("nextPageToken")
            try:
                for message in response.get("items", []):
                    msg = message.get("snippet", {}).get("displayMessage", "")
                    mod = message.get("authorDetails", {}).get("isChatModerator", False)
                    author = message.get("authorDetails", {}).get("displayName", "unknown")
                    ret.append(ChatMessage(msg, mod, author))
            except Exception:
                ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Failed to access chat messages from response.")

        return ret

    def sendMessage(self, message: str) -> bool:
        if not self.yt:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Youtube interface not initialized, aborting")
            return False
        if not self.chatID and not self._fetchStreamID():
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Unable to get chat ID for the livestream, aborting sending message.")
            return False

        try:
            request = self.yt.liveChatMessages().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "liveChatId": self.chatID,
                                "type": "textMessageEvent",
                                "textMessageDetails": {
                                    "messageText": f"[BINGO] {message}"
                                }
                            }
                        }
                    )
            response = request.execute()

            if not response:
                ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Chat message request failed.")
            elif self.numMaxChatMsgs != 0:
                msgID = response.get("id", "")
                if msgID:
                    self.messageIDs.append(msgID)

        except Exception:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Send message request failed.")

        if self.chatID:
            self._delOldMessages(self.chatID)

        return self.chatID != None

    def _delOldMessages(self, chatID: str):
        # 0 = unlimited messages
        if self.numMaxChatMsgs == 0:
            return

        while len(self.messageIDs) > self.numMaxChatMsgs:
            msgID = self.messageIDs.popleft()
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Removing older chat message ID {msgID}")
            try:
                self.yt.liveChatMessages().delete(id=msgID).execute()
            except Exception as e:
                ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Failed to delete old chat message: {e}")

    def _fetchStreamID(self) -> bool:
        if self.chatID:
            return True
        elif not self.yt:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Youtube interface not initialized, aborting")
            return False

        # Query for stream
        try:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Attempting to get stream ID for channel ({Config().getConfig('YTChannelID')})...")
            # Lookup all channel videos
            request = self.yt.search().list(
                        part="id",
                        channelId=Config().getConfig("YTChannelID"),
                        eventType="live",
                        type="video"
                    )
            response = request.execute()
        except Exception as e:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Failed to send search query message: {e}")
            return False

        # Lookup stream info
        try:
            videoID = response["items"][0]["id"]["videoId"]
            request = self.yt.videos().list(
                        part="liveStreamingDetails",
                        id=videoID
                    )
            response = request.execute()
        except Exception:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Failed to look up channel videos.")
            self.chatID = None
            return False

        # Get livestream chat ID
        try:
            self.chatID = response["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
        except Exception:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Failed to get livestream chat ID.")
            self.chatID = None
            return False

        return True

