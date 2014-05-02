#!/bin/sh

. `dirname $0`/../settings.sh

echo '
db.tweets.drop()
db.users.drop()
' | mongo $MONGO_HOST:$MONGO_PORT/$MONGO_DBNAME
