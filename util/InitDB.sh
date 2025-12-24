#!/usr/bin/bash

DB_FILE="../resources/data/data.sqlite"
TABLE_PLAYERS="PLAYERS"
TABLE_BANNED="BANNED"
TABLE_RECOVERY="RECOVER"
TABLE_RECOVER_PLAYERS="RECPLAYERS"
TABLE_RECOVER_PLAYER_CELLS="RECPLAYERCELLS"
TABLE_RECOVER_REQUESTS="RECREQUESTS"

TABLE_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE name='$TABLE_PLAYERS';")
TABLE_BANNED_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE name='$TABLE_BANNED';")
TABLE_RECOVER_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE name='$TABLE_RECOVERY';")
TABLE_RECOVER_PLAYERS_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE name='$TABLE_RECOVER_PLAYERS';")
TABLE_RECOVER_PLAYERS_CELLS_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE name='$TABLE_RECOVER_PLAYER_CELLS';")
TABLE_RECOVER_REQUESTS_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE name='$TABLE_RECOVER_REQUESTS';")

if [ "$TABLE_EXISTS" = "$TABLE_PLAYERS" ]; then
    echo "Table $TABLE_PLAYERS already exists, skipping."
else
    echo "Creating $TABLE_PLAYERS table..."
    sqlite3 "$DB_FILE" << EOF
CREATE TABLE IF NOT EXISTS $TABLE_PLAYERS (
    id INTEGER PRIMARY KEY,
    userid INTEGER NOT NULL,
    guildid INTEGER DEFAULT 0,
    name TEXT NOT NULL,
    bingos INTEGER DEFAULT 0,
    calls INTEGER DEFAULT 0,
    games INTEGER DEFAULT 0,
    bingosmonth INTEGER DEFAULT 0,
    callsmonth INTEGER DEFAULT 0,
    gamesmonth INTEGER DEFAULT 0,
    timestampmonth INTEGER DEFAULT 0,
    bingosweek INTEGER DEFAULT 0,
    callsweek INTEGER DEFAULT 0,
    gamesweek INTEGER DEFAULT 0,
    timestampweek INTEGER DEFAULT 0
);
EOF
    echo "Table $TABLE_PLAYERS created."
fi

if [ "$TABLE_BANNED_EXISTS" = "$TABLE_BANNED" ]; then
    echo "Table $TABLE_BANNED already exists, skipping."
else
    echo "Creating $TABLE_BANNED table..."
    sqlite3 "$DB_FILE" << EOF
CREATE TABLE IF NOT EXISTS $TABLE_BANNED (
    id INTEGER PRIMARY KEY,
    userid INTEGER NOT NULL,
    name TEXT NOT NULL,
    timestamp INTEGER NOT NULL
);
EOF
    echo "Table $TABLE_BANNED created."
fi

if [ "$TABLE_RECOVER_EXISTS" = "$TABLE_RECOVERY" ]; then
    echo "Table $TABLE_RECOVERY already exists, skipping."
else
    echo "Creating $TABLE_RECOVERY table..."
    sqlite3 "$DB_FILE" << EOF
CREATE TABLE IF NOT EXISTS $TABLE_RECOVERY (
    id INTEGER PRIMARY KEY,
    guildid INTEGER NOT NULL,
    gamestate TEXT NOT NULL,
    gametype TEXT NOT NULL,
    timestarted INTEGER DEFAULT 0,
    calledbings TEXT NOT NULL DEFAULT '[]',
    kickedplayers TEXT NOT NULL DEFAULT '[]',
    playerbingos TEXT NOT NULL DEFAULT '[]',
    timesaved INTEGER NOT NULL
);
EOF
fi

if [ "$TABLE_RECOVER_PLAYERS_EXISTS" = "$TABLE_RECOVER_PLAYERS" ]; then
    echo "Table $TABLE_RECOVER_PLAYERS already exists, skipping."
else
    echo "Creating $TABLE_RECOVER_PLAYERS table..."
    sqlite3 "$DB_FILE" << EOF
CREATE TABLE IF NOT EXISTS $TABLE_RECOVER_PLAYERS (
    id INTEGER NOT NULL,
    playerid INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    valid INTEGER DEFAULT 0,
    rejectedreqs INTEGER DEFAULT 0,
    rejectedtime REAL NOT NULL DEFAULT 0.0,
    cardid INTEGER NOT NULL,
    hasbingo INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES $TABLE_RECOVERY(id)
    ON DELETE CASCADE
);
EOF
fi

if [ "$TABLE_RECOVER_PLAYERS_CELLS_EXISTS" = "$TABLE_RECOVER_PLAYER_CELLS" ]; then
    echo "Table $TABLE_RECOVER_PLAYER_CELLS already exists, skipping."
else
    echo "Creating $TABLE_RECOVER_PLAYER_CELLS table..."
    sqlite3 "$DB_FILE" << EOF
CREATE TABLE IF NOT EXISTS $TABLE_RECOVER_PLAYER_CELLS (
    id INTEGER NOT NULL,
    bingid INTEGER PRIMARY KEY,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    maked INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES $TABLE_RECOVER_PLAYERS(playerid)
    ON DELETE CASCADE
);
EOF
fi

if [ "$TABLE_RECOVER_REQUESTS_EXISTS" = "$TABLE_RECOVER_REQUESTS" ]; then
    echo "Table $TABLE_RECOVER_REQUESTS already exists, skipping."
else
    echo "Creating $TABLE_RECOVER_REQUESTS table..."
    sqlite3 "$DB_FILE" << EOF
CREATE TABLE IF NOT EXISTS $TABLE_RECOVER_REQUESTS (
    id INTEGER NOT NULL,
    bingid INTEGER PRIMARY KEY,
    playerids TEXT NOT NULL,
    FOREIGN KEY (id) REFERENCES $TABLE_RECOVERY(id)
    ON DELETE CASCADE
);
EOF
fi

