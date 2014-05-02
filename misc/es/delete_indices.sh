#!/bin/sh

. `dirname $0`/../settings.sh

echo '[stop river tweets]'
curl -XDELETE http://$ES_HOST:$ES_PORT/tweets
echo ''

echo '[stop river users]'
curl -XDELETE http://$ES_HOST:$ES_PORT/users
echo ''
