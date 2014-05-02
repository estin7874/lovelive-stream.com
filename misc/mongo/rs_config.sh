#!/bin/sh

. `dirname $0`/../settings.sh

echo "
config = {
    \"_id\" : \"rs\",
    \"version\" : 1,
    \"members\" : [
        {
            \"_id\" : 0,
            \"host\" : \"$MONGO_HOST:$MONGO_PORT\",
            \"priority\" : 0.5
        }
     ]
}
rs.initiate(config)
rs.config()
" | mongo $MONGO_HOST:$MONGO_PORT/$MONGO_DBNAME
