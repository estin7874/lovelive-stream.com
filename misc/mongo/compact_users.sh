#!/bin/sh

. `dirname $0`/../settings.sh

echo "
// Get a the current collection size.
var storage = db.users.storageSize();
var total = db.users.totalSize();

print('Storage Size: ' + tojson(storage));

print('TotalSize: ' + tojson(total));

print('-----------------------');
print('Running db.repairDatabase()');
print('-----------------------');

// Run repair
db.repairDatabase()

// Get new collection sizes.
var storage_a = db.users.storageSize();
var total_a = db.users.totalSize();

print('Storage Size: ' + tojson(storage_a));
print('TotalSize: ' + tojson(total_a));
" | mongo $MONGO_HOST:$MONGO_PORT/$MONGO_DBNAME
