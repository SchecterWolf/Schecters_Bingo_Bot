# 🎯 Schecter's Bingo Bot

A configurable, event-driven Discord bingo bot designed for livestream communities.

<details>
<summary>📚 Table of Contents</summary>

* [About the Bot](#about-the-bot)
* [How to Install](#how-to-install)
* [Configuration Options](#configuration-options)
* [How To Run](#how-to-run)
* [TODO](#todo)

</details>

---

## 🎮 About the Bot

**Schecter’s Bingo Bot** is a configurable Discord bingo bot designed to be played while a content creator is livestreaming.

The bingo game is **event-driven**, meaning slots on player boards are marked based on events that occur during the livestream. The bot optionally includes a **YouTube livestream interface**, allowing it to post game status updates directly to the livestream chat.

The bot tracks **player high scores** across games and supports two gameplay modes:

* **Casual Mode**
  Players can freely mark their own bingo boards.

* **Regular Mode**
  Slot mark requests must be approved by an admin.

⚠️ Currently, the bot only supports **running one bingo game per Discord server at a time**.

---

## 🛠️ How to Install

### Required Dependencies

* Linux
* Python 3
* SQLite3
* pip
* bash
* git

### Installation Steps

1️⃣ Clone the repository:

```bash
git clone https://github.com/SchecterWolf/Schecters_Bingo_Bot.git
```

2️⃣ Initialize the database:

```bash
cd util
./InitDB.sh
```

3️⃣ Create and configure a Discord bot:

* Follow the official Discord guide to register a bot and obtain a token.

* Enable the following **Privileged Intents**:

  * Server Members Intent
  * Message Content Intent

* Required **Bot Permissions**:

  * View Channels
  * Send Messages
  * Attach Files
  * Read Message History
  * Use Slash Commands

Place the bot token string into:

```
config/token.txt
```

4️⃣ Configure `config.json` (see next section).

5️⃣ Ensure the **Bingo Channel** and **Admin Channel** have these permissions:

* View Channel
* Manage Channel
* Send Messages
* Embed Links
* Attach Files
* Manage Messages
* Pin Messages
* Bypass Slowmode

---

## ⚙️ Configuration Options

Each field in `config.json`:

* **SkipServer** – *(Optional)* List of server IDs to ignore. Useful if bot is added to multiple servers.
* **BonusBingo** – Bonus points for getting a bingo.
* **BonusGamesPlayed** – Bonus points per game played.
* **BonusSlotsCalled** – Bonus points per slot marked.
* **CardSize** – Size of the bingo board.
* **CasualMode** – `true` = players mark boards themselves, `false` = admin approval required.
* **ChannelAdmin** – Discord channel ID for bingo admin channel.
* **ChannelBingo** – Discord channel ID for bingo game channel.
* **ChannelGeneral** – *(Optional)* General chat channel ID.
* **Debug** – *(Optional)* Enables debug slash commands.
* **DiscordLink** – *(Optional)* Used by YouTube interface for announcements.
* **EXPEnabled** – Not used. Set to `false`.
* **EXPMultiplier** – Not used.
* **Font** – System font path used for high score image.
* **FontSmall** – System font path for smaller score text.
* **GameMasterRole** – Name of Discord role allowed to manage game.
* **GameTypes** – List of supported bingo game types. Each must have its own JSON config file (e.g., `FiveM.json`).
* **LogLevel** – Logging level: `critical`, `error`, `warn`, `info`, `debug`, `none`.
* **MaxRequests** – Max call requests per player in regular mode.
* **Mode** – Only supports `"discord"` currently.
* **ReqTimeoutMin** – Timeout when player requests are repeatedly rejected.
* **RetroactiveCalls** – `true` = new players get previously called slots marked.
* **RolesPlayable** – *(Optional)* List of roles allowed to play. Empty = all roles allowed.
* **StreamerName** – Name of the livestream content creator.
* **TokenFile** – Path to bot token file (usually `config/token.txt`).
* **UseFreeSpace** – Include free space slot on board.
* **UseRecovery** – Enable crash recovery support.
* **YTChannelID** – Required if YouTube interface enabled.
* **YTCredFile** – YouTube API credentials file (usually `config/client_secret.json`).
* **YTEnabled** – Enable YouTube livestream chat integration.
* **YTMaxChatMsgs** – Max messages sent to livestream chat at once.
* **YTTokenFile** – YouTube API token file (usually `config/yt_token.json`).

---

## ▶️ How To Run

1️⃣ Navigate to project directory:

```bash
cd Schecters_Bingo_Bot
```

2️⃣ Setup / activate virtual environment:

```bash
source ./venv.sh
```

> On first run, this installs all required Python dependencies.

3️⃣ Start the bot:

```bash
./BingoBot.py
```

### 🔁 Auto-Run on Startup (Debian Example)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/bingobot.service
```

Example service:

```ini
[Unit]
Description=Schecter's Bingo Bot
After=network.target

[Service]
User=YOUR_USER
WorkingDirectory=/path/to/Schecters_Bingo_Bot
ExecStart=/bin/bash -c "source ./venv.sh && ./BingoBot.py"
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable + start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bingobot
sudo systemctl start bingobot
```

---

## 🧩 TODO

* Some unit tests were broken in the last two commits and need updating.
* The YouTube interface must be refactored — the current SDK integration can cause program crashes.

  * A non-API approach will likely be required for sending livestream chat messages.
* The bot only works **out-of-the-box with a single server configuration**.

  * Multi-server support exists partially in code but requires further architectural changes.

---

⭐ Contributions, bug reports, and feature requests are welcome.

