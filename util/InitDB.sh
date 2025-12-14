#!/usr/bin/bash

DB_FILE="../resources/data/data.sqlite"
TABLE_PLAYERS="PLAYERS"
TABLE_BANNED="BANNED"

TABLE_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE name='$TABLE_PLAYERS';")
TABLE_BANNED_EXISTS=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE name='$TABLE_BANNED';")

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
    echo "Table $TABLE_PLAYERS already exists, skipping."
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
