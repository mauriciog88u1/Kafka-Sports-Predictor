#!/bin/bash

API_KEY="638861"
BASE_URL="https://www.thesportsdb.com/api/v1/json"

echo "=== Testing Sports DB API Endpoints ==="

echo -e "\n1. Testing All Leagues Endpoint"
curl -s "${BASE_URL}/${API_KEY}/all_leagues.php" | jq '.'

echo -e "\n2. Testing Events Next Endpoint (for team 133602)"
curl -s "${BASE_URL}/${API_KEY}/eventsnext.php?id=133602" | jq '.'

echo -e "\n3. Testing Team Players Endpoint (for team 133602)"
curl -s "${BASE_URL}/${API_KEY}/lookup_all_players.php?id=133602" | jq '.'

echo -e "\n4. Testing Team Last Events Endpoint (for team 133602)"
curl -s "${BASE_URL}/${API_KEY}/eventslast.php?id=133602" | jq '.'

echo -e "\n5. Testing Event Stats Endpoint (using first event from eventsnext)"
EVENT_ID=$(curl -s "${BASE_URL}/${API_KEY}/eventsnext.php?id=133602" | jq -r '.events[0].idEvent')
if [ ! -z "$EVENT_ID" ]; then
    echo "Testing with event ID: $EVENT_ID"
    curl -s "${BASE_URL}/${API_KEY}/lookupeventstats.php?id=${EVENT_ID}" | jq '.'
fi

echo -e "\n6. Testing Event Lineup Endpoint"
if [ ! -z "$EVENT_ID" ]; then
    curl -s "${BASE_URL}/${API_KEY}/lookuplineup.php?id=${EVENT_ID}" | jq '.'
fi

echo -e "\n7. Testing League Table Endpoint"
LEAGUE_ID=$(curl -s "${BASE_URL}/${API_KEY}/eventsnext.php?id=133602" | jq -r '.events[0].idLeague')
SEASON=$(curl -s "${BASE_URL}/${API_KEY}/eventsnext.php?id=133602" | jq -r '.events[0].strSeason')
if [ ! -z "$LEAGUE_ID" ] && [ ! -z "$SEASON" ]; then
    echo "Testing with league ID: $LEAGUE_ID and season: $SEASON"
    curl -s "${BASE_URL}/${API_KEY}/lookuptable.php?l=${LEAGUE_ID}&s=${SEASON}" | jq '.'
fi 