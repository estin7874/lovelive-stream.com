#!/bin/sh

. `dirname $0`/../settings.sh

echo "db.createCollection('tweets', {capped: true, size: 10737418240, max: 10000000})" | mongo $MONGO_HOST:$MONGO_PORT/$MONGO_DBNAME
