#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import sys
import os
import time
import signal
import re
import json
from bson import json_util
import yaml
from datetime import datetime
import urllib
import urllib2
import base64
import tweepy
import redis
import rq
import pymongo
import multiprocessing

from rqtasks import update_user_info, update_user_last_tweet_at


def process_on_status(status, db, redis_client, q_high, q_low, r, duration):
    if r.search(status.text, re.U):
        #print('[warn] exclude detected' + str(status.text), file=sys.stderr)
        return

    # insert tweet data (also check dups)
    tweet = {
        '_id': str(status.id),
        'user_id': str(status.user.id),
        'created_at': status.created_at}
    if hasattr(status, 'retweeted_status'):
        tweet['rt_source_id'] = str(status.retweeted_status.id)
    else:
        tweet['text'] = status.text
    try:
        db.tweets.insert(tweet)
    except pymongo.errors.DuplicateKeyError:
        return

    # update user info with job queue
    user_info = json.dumps({
        '_id': str(status.user.id),
        'name': status.user.name,
        'screen_name': status.user.screen_name,
        'image': status.user.profile_image_url_https,
        'description': status.user.description,
        'location': status.user.location,
        'url': status.user.url,
        'updated_at': status.created_at}, default=json_util.default)
    user_last_tweet_at = json.dumps({
        'last_tweet_at': status.created_at}, default=json_util.default)
    q_high.enqueue_call(func=update_user_info, args=(user_info,))
    q_low.enqueue_call(func=update_user_last_tweet_at, args=(str(status.user.id), user_last_tweet_at))

    # check if tweet is status retweeted
    if hasattr(status, 'retweeted_status'):
        return

    text = status.text
    for url in status.entities['urls']:
        text = text.replace(url['url'], url['expanded_url'])
    if 'media' in status.entities:
        for url in status.entities['media']:
            text = text.replace(url['url'], url['media_url_https'])

    mes = {
        'id': str(status.id),
        'name': status.user.name,
        'screen_name': status.user.screen_name,
        'image': status.user.profile_image_url_https,
        'text': text,
        'created_at': status.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    redis_client.publish('stream', json.dumps({'tweet': mes}))
    redis_client.lpush('recent_tweets', json.dumps(mes))
    redis_client.ltrim('recent_tweets', 0, 19)
    timestamp = time.mktime(status.created_at.timetuple())
    redis_client.hincrby('tweet_count', str(int(timestamp - (timestamp % duration))), 1)


class AppAuthHandler(tweepy.auth.AuthHandler):
    TOKEN_URL = 'https://api.twitter.com/oauth2/token'

    def __init__(self, consumer_key, consumer_secret):
        token_credential = urllib.quote(consumer_key) + ':' + urllib.quote(consumer_secret)
        credential = base64.b64encode(token_credential)

        value = {'grant_type': 'client_credentials'}
        data = urllib.urlencode(value)
        req = urllib2.Request(self.TOKEN_URL)
        req.add_header('Authorization', 'Basic ' + credential)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded;charset=UTF-8')

        response = urllib2.urlopen(req, data)
        json_response = json.loads(response.read())
        self._access_token = json_response['access_token']

    def apply_auth(self, url, method, headers, parameters):
        headers['Authorization'] = 'Bearer ' + self._access_token


class StreamListener(tweepy.StreamListener):

    def __init__(self, config):
        super(StreamListener,self).__init__()

        self.r = re.compile(config['app']['aggregator']['exclude'])

        self.mongo_client = pymongo.MongoClient(config['mongo']['host'], config['mongo']['port'])
        self.db = self.mongo_client[config['mongo']['db']]

        self.pool = redis.ConnectionPool(host=config['redis']['host'], port=config['redis']['port'], db=0)
        self.redis_client = redis.Redis(connection_pool=self.pool)
        self.q_high = rq.Queue('high', connection=self.redis_client)
        self.q_low = rq.Queue('low', connection=self.redis_client)

        self.counter_duration = len(config['twitter']['search']['queries']) * config['app']['counter']['duration_base']

    def on_status(self, status):
        process_on_status(status, self.db, self.redis_client, self.q_high, self.q_low, self.r, self.counter_duration)


def watch_counter(config):
    pool = redis.ConnectionPool(host=config['redis']['host'], port=config['redis']['port'], db=0)
    redis_client = redis.Redis(connection_pool=pool)

    delay = config['app']['counter']['delay']
    duration = len(config['twitter']['search']['queries']) * config['app']['counter']['duration_base']

    while True:
        utcnow_timestamp = time.mktime(datetime.utcnow().timetuple())
        count_timestamp = str(int((utcnow_timestamp - (utcnow_timestamp % duration) - duration * 2)))
        tweet_count = redis_client.hget('tweet_count', count_timestamp)
        if tweet_count:
            tps =  str(round(float(tweet_count) / duration, 1))
            redis_client.publish('stream', json.dumps({'counter': tps}))
            redis_client.hdel('tweet_count', count_timestamp)
        time.sleep(duration)


def agg_rest_search(config):
    auth = AppAuthHandler(config['twitter']['auth']['consumer_key'], config['twitter']['auth']['consumer_secret'])
    api = tweepy.API(auth)

    r = re.compile(config['app']['aggregator']['exclude'])

    mongo_client = pymongo.MongoClient(config['mongo']['host'], config['mongo']['port'])
    db = mongo_client[config['mongo']['db']]

    pool = redis.ConnectionPool(host=config['redis']['host'], port=config['redis']['port'], db=0)
    redis_client = redis.Redis(connection_pool=pool)
    q_high = rq.Queue('high', connection=redis_client)
    q_low = rq.Queue('low', connection=redis_client)

    queries = config['twitter']['search']['queries']
    counter_duration = len(queries) * config['app']['counter']['duration_base']

    since_ids = {}
    index = 0

    while True:
        try:
            if index in since_ids:
                response = api.search(q=queries[index], result_type='recent', count=100, since_id=since_ids[index])
            else:
                response = api.search(q=queries[index], result_type='recent', count=100)
        except tweepy.error.TweepError as e:
            print('[error] tweepy error detected. %s' % str(e), file=sys.stderr)
            time.sleep(config['app']['aggregator']['interval'] / 1000)
            continue
        except httplib.IncompleteRead as e:
            print('[error] httplib error detected. %s' % str(e), file=sys.stderr)
            time.sleep(config['app']['aggregator']['interval'] / 1000)
            continue

        for status in response:
            process_on_status(status, db, redis_client, q_high, q_low, r, counter_duration)

        if len(response) > 0:
            since_ids[index] = response[0].id
        if index == len(queries) - 1:
            index = 0
        time.sleep(config['app']['aggregator']['interval'] / 1000)


def agg_stream_filter(config):
    auth = tweepy.OAuthHandler(config['twitter']['auth']['consumer_key'], config['twitter']['auth']['consumer_secret'])
    auth.set_access_token(config['twitter']['auth']['access_token'], config['twitter']['auth']['access_token_secret'])

    tweepy.Stream(auth, StreamListener(config)).filter(track=config['twitter']['filter']['track'])


def main():
    config = yaml.load(open(os.path.dirname(os.path.realpath(__file__)) + '/../config/default.yaml'))

    processes = []

    processes.append(multiprocessing.Process(target=watch_counter, args=(config,)))
    processes.append(multiprocessing.Process(target=agg_rest_search, args=(config,)))
    processes.append(multiprocessing.Process(target=agg_stream_filter, args=(config,)))

    # for supervisord daemonize use
    # FIXME: AttributeError occurs on receiving SIGTERM/SIGQUIT (AttributeError: 'NoneType' object has no attribute 'terminate')
    def kill_processes(signum, frame):
        for p in processes:
            p.terminate()

    signal.signal(signal.SIGTERM, kill_processes)
    signal.signal(signal.SIGINT, kill_processes)
    signal.signal(signal.SIGQUIT, kill_processes)
    signal.signal(signal.SIGHUP, kill_processes)

    for p in processes:
        p.start()
    for p in processes:
        p.join()


if __name__ == '__main__':
    main()
