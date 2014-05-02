#!/bin/sh

. `dirname $0`/../settings.sh

echo '[start river tweets]'
curl -XPUT http://$ES_HOST:$ES_PORT/_river/tweets/_meta -d "
{
    \"type\": \"mongodb\", 
    \"mongodb\": { 
        \"db\": \"twitter\", 
        \"collection\": \"tweets\", 
        \"servers\": [
            {\"host\": \"$MONGO_HOST\", \"port\": $MONGO_PORT}
        ]
    },
    \"index\": { 
        \"name\": \"tweets\", 
        \"type\": \"tweet\" 
    }
}"
echo ''

echo '[start river users]'
curl -XPUT http://$ES_HOST:$ES_PORT/_river/users/_meta -d "
{
    \"type\": \"mongodb\", 
    \"mongodb\": { 
        \"db\": \"twitter\", 
        \"collection\": \"users\", 
        \"servers\": [
            {\"host\": \"$MONGO_HOST\", \"port\": $MONGO_PORT}
        ]
    },
    \"index\": { 
        \"name\": \"users\", 
        \"type\": \"user\" 
    }
}"
echo ''
