# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import os
import yaml
import json
from bson import json_util
import pymongo


config = yaml.load(open(os.path.dirname(os.path.realpath(__file__)) + '/../config/default.yaml'))
mongo_client = pymongo.MongoClient(config['mongo']['host'], config['mongo']['port'])
db = mongo_client[config['mongo']['db']]


def update_user_info(user_info):
    user = json.loads(user_info, object_hook=json_util.object_hook)

    current_user = db.users.find_one({'_id': user['_id']})
    if not current_user:
        try:
            db.users.insert(user)
        except pymongo.errors.DuplicateKeyError:
            pass
    else:
        update = {}
        if user['name'] != current_user['name']:
            update['name'] = user['name']
        if user['screen_name'] != current_user['screen_name']:
            update['screen_name'] = user['screen_name']
        if user['image'] != current_user['image']:
            update['image'] = user['image']
        if user['description'] != current_user['description']:
            update['description'] = user['description']
        if user['location'] != current_user['location']:
            update['location'] = user['location']
        if user['url'] != current_user['url']:
            update['url'] = user['url']

        if any(update):
            update['updated_at'] = user['updated_at']
            db.users.update({'_id': user['_id']}, {"$set": update})


def update_user_last_tweet_at(user_id, user_last_tweet_at):
    last_tweet_at = json.loads(user_last_tweet_at, object_hook=json_util.object_hook)

    db.users.find_and_modify({'_id': user_id}, {'$set': last_tweet_at})
