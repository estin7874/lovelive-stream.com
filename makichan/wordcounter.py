#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import sys
import os
import re
import time
import yaml
import json
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal

import redis
from elasticsearch import Elasticsearch
import pymongo
import MeCab


reload(sys)
sys.setdefaultencoding('utf-8')


SPECIAL_CHARS_REGEXP = re.compile(r'^(?:[!-/:-@[-`{-~]|[0-9])+$')
EXCLUDE_REGEXP = re.compile(r'(?:https*://[^\s]+|#[^\s]+|@[^\s]+)')


def create_bag_of_nouns(tagger, text):
    enc_text = EXCLUDE_REGEXP.sub('', text.encode('utf-8'))

    node = tagger.parseToNode(enc_text)
    nouns = []
    pending = []
    words = ''
    word_count = defaultdict(int)
    while node:
        features = node.feature.split(',')
        #print(node.surface, node.posid, node.feature)
        #if len(pending) > 0:
        #    print('[pending]:' + ''.join(pending))
        """
        if features[0] == '名詞':  # noun
            noun = node.surface.strip()
            if SPECIAL_CHARS_REGEXP.search(noun, re.U):
                pending = []
            elif len(pending) == 0:
                pending = [noun]
            elif re.search('[ぁ-ん|ァ-ン|一-龥]$', pending[-1], re.U) and \
                    re.search(r'^[ぁ-ん|ァ-ン|一-龥]', noun, re.U):
                pending.append(noun)
            elif len(pending) > 0 and len(''.join(pending)) > 2:
                nouns.append(''.join(pending))
                pending = [noun]
            else:
                pending = [noun]
        elif len(pending) > 0:
            nouns.append(''.join(pending))
            pending = []
        node = node.next
        """

        if features[0] == '名詞' or features[1] == '連体化' or \
                (features[0] == '記号' and features[1] == '一般'):
            words += node.surface
        elif words != '':
            word_count[words] += 1
            words = ''
        node = node.next
    return word_count.keys()


def fetch_statuses(db, es, start, end, q=None):
    if q:
        body = {
          'filter': {
            'range': {
              'created_at': {
                'from': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'to': end.strftime('%Y-%m-%dT%H:%M:%SZ')
              }
            }
          },
          'query': {
            'match': {
              'text': q
            }
          }          
        }
        es_result = es.search(index='tweets', doc_type='tweet', body=body)
        ids = [x['_id'] for x in es_result['hits']['hits']]
        return db.tweets.find({'_id': {'$in': ids}})

    else:
        return db.tweets.find({'created_at': {'$gte': start, '$lte': end}})


def count_users(es, start, end, q=None):
    """
    body = {
      'filter': {
        'range': {
          'created_at': {
            'from': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to': end.strftime('%Y-%m-%dT%H:%M:%SZ')
          }
        }
      },
      'facets': {
        'users': {
          'terms': {
            'field': 'user_id',
            'size': 1000000
          }
        }
      }
    }
    """
    body = {
      'filter': {
        'range': {
          'created_at': {
            'from': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to': end.strftime('%Y-%m-%dT%H:%M:%SZ')
          }
        }
      }
    }
    if q:
        body['query'] = {
          'match': {
            'text': q
          }
        }

    result = es.search(index='tweets', doc_type='tweet', body=body)
    #return len(result['facets']['users']['terms'])
    return result['hits']['total']


def main():
    config = yaml.load(open(os.path.dirname(os.path.realpath(__file__)) + '/../config/default.yaml'))

    mongo_client = pymongo.MongoClient(config['mongo']['host'], config['mongo']['port'])
    db = mongo_client[config['mongo']['db']]

    es = Elasticsearch([{'host': config['elasticsearch']['host'], 'port': config['elasticsearch']['port']}])

    pool = redis.ConnectionPool(host=config['redis']['host'], port=config['redis']['port'], db=0)
    redis_client = redis.Redis(connection_pool=pool)

    tagger = MeCab.Tagger('mecabrc')

    exclude_regexp = re.compile(config['app']['aggregator']['exclude'])

    while True:
        utcnow = datetime.utcnow()
        #start = utcnow + relativedelta(minutes=-1, seconds=-30)
        start = utcnow + relativedelta(hours=-1, seconds=-30)
        end = utcnow + relativedelta(seconds=-30)

        recent_statuses = fetch_statuses(db, es, start, end)

        # bag of nouns
        bag_of_nouns = []
        for status in recent_statuses:
            if 'rt_source_id' in status or exclude_regexp.search(status['text'], re.U):
                continue
            nouns = create_bag_of_nouns(tagger, status['text'])
            for noun in nouns:
                if noun not in bag_of_nouns:
                    bag_of_nouns.append(noun)

        num_start = utcnow + relativedelta(hours=-1)
        num_end = utcnow
        dom_start = utcnow + relativedelta(days=-1)
        dom_end = utcnow + relativedelta(hours=-1)

        num_all = count_users(es, num_start, num_end)
        dom_all = count_users(es, dom_start, dom_end) 

        utcnow_expire = int(time.mktime((utcnow + relativedelta(hours=1)).timetuple()))

        for noun in bag_of_nouns:
            try:
                noun.decode('utf-8')
            except UnicodeDecodeError:
                continue

            # calc score
            # cf. http://sssslide.com/www.slideshare.net/dara/buzztter
            score = Decimal(count_users(es, num_start, num_end, noun)) / num_all \
                  - Decimal(count_users(es, dom_start, dom_end, noun)) / dom_all

            if score > 0:
                redis_client.zadd('hot_words', noun, round(float(score), 12))
                redis_client.hset('hot_words_expires', noun, utcnow_expire)

        expires = redis_client.hgetall('hot_words_expires')
        for key, expire in expires.items():
            if expire >= utcnow_expire:
                redis_client.hdel('hot_words_expire', noun)
                redis_client.zrem('hot_words', noun)

        hot_words = redis_client.zrange('hot_words', 0, 19)
        for w in hot_words:
            print(w)
        #redis_client.publish('stream', json.dumps({'hot_words': hot_words}))

        #break
        time.sleep(config['app']['wordcounter']['interval'])

if __name__ == '__main__':
    main()
