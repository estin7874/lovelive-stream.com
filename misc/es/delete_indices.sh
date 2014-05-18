#!/bin/sh

. `dirname $0`/../settings.sh

echo '[delete index tweets]'
curl -XDELETE http://$ES_HOST:$ES_PORT/tweets
echo ''

echo '[delete index users]'
curl -XDELETE http://$ES_HOST:$ES_PORT/users
echo ''
