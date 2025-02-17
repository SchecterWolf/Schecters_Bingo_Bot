__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from config.ClassLogger import ClassLogger
from config.Config import Config
from config.Log import LogLevel

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from typing import Any, List, Union

class ChatInterface:
    __LOGGER = ClassLogger(__name__)
    __SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    def __init__(self):
        self.initialized = False
        self.chatID: Union[str, None] = None
        self.pageToken: Any = None

    def init(self):
        ChatInterface.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Getting youtube credential...")
        flow = InstalledAppFlow.from_client_secrets_file(Config().getConfig("YTCredFile"), ChatInterface.__SCOPES)
        oauthCred = flow.run_local_server()
        self.yt = build("youtube", "v3", credentials=oauthCred)
        self.initialized = True

    def getMessages(self) -> List[str]:
        if not self.initialized:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Youtube interface not initialized, aborting")
            return []
        if not self._fetchStreamID() and not self.chatID:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Unable to get chat ID for the livestream, aborting sending message.")
            return []

        response = None
        try:
            request = self.yt.liveChatMessages().list(
                        liveChatId=self.chatID,
                        part="snippet,authorDetails",
                        pageToken=self.pageToken,
                    )
            response = request.execute()
        except Exception:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Failed to send get message request.")
            self.chatID = None

        ret: List[str] = []
        if response:
            self.pageToken = response.get("nextPageToken")
            try:
                for message in response.get("items", []):
                    ret.append(message["snippet"]["displayMessage"])
            except Exception:
                ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Failed to access chat messages from response.")
                self.chatID = None

        return ret

    def sendMessage(self, message: str) -> bool:
        if not self.initialized:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Youtube interface not initialized, aborting")
            return False
        if not self._fetchStreamID() and not self.chatID:
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
                self.chatID = None

        except Exception:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Send message request failed.")
            self.chatID = None

        return self.chatID != None

    def _fetchStreamID(self) -> bool:
        if self.chatID:
            return True
        elif not self.initialized:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Youtube interface not initialized, aborting")
            return False

        # Query for stream
        try:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Attempting to get stream ID...")
            # Lookup all channel videos
            request = self.yt.search().list(
                        part="id",
                        channelId=Config().getConfig("YTChannelID"),
                        eventType="live",
                        type="video"
                    )
            response = request.execute()
        except Exception:
            ChatInterface.__LOGGER.log(LogLevel.LEVEL_ERROR, "Failed to send search query message.")
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

