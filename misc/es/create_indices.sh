#!/bin/sh

. `dirname $0`/../settings.sh

echo '[create index tweets]'
curl -XPUT http://$ES_HOST:$ES_PORT/tweets -d '
{
"settings": {
    "analysis": {
      "filter": {
        "pos_filter": {"type": "kuromoji_part_of_speech", "stoptags": ["助詞-格助詞-一般", "助詞-終助詞"]},
        "greek_lowercase_filter": {"type": "lowercase", "language": "greek"}},
      "analyzer": {
        "kuromoji_analyzer": {
          "type": "custom",
          "tokenizer": "kuromoji_tokenizer",
          "filter": ["kuromoji_baseform", "pos_filter", "greek_lowercase_filter", "cjk_width"]}}}},
  "mappings": {
    "tweet": {
      "_id": {"path": "_id"},
      "_timestamp": {"enabled": true, "path": "created_at"},
      "_source": {"enabled": false},
       "ignore_conflicts":true,
      "properties": {
        "_id" : {"type":"string", include_in_all: false, store: true},
        "user_id": {"type": "string"},
        "text" : {"type":"string", "store": true, "index": "analyzed", "analyzer": "kuromoji_analyzer"},
        "created_at" : {"type":"date"},
        "rt_source_id" : {"type":"string"}
      }
    }
  }
}'
echo ''

echo '[create index users]'
curl -XPUT http://$ES_HOST:$ES_PORT/users -d '
{
"settings": {
    "analysis": {
      "filter": {
        "pos_filter": {"type": "kuromoji_part_of_speech", "stoptags": ["助詞-格助詞-一般", "助詞-終助詞"]},
        "greek_lowercase_filter": {"type": "lowercase", "language": "greek"}},
      "analyzer": {
        "kuromoji_analyzer": {
          "type": "custom",
          "tokenizer": "kuromoji_tokenizer",
          "filter": ["kuromoji_baseform", "pos_filter", "greek_lowercase_filter", "cjk_width"]}}}},
  "mappings": {
    "user": {
      "_id": {"path": "_id"},
      "_timestamp": {"enabled": true, "path": "updated_at"},
      "_source": {"enabled": true},
       "ignore_conflicts": true,
       "properties": {
         "_id": {"type": "string"},
         "name": {"type":"string", "store": true, "index": "analyzed", "analyzer": "kuromoji_analyzer"},
         "screen_name": {"type":"string", "store": true},
         "image": {"type": "string"},
         "description": {"type": "string", "store": true, "index": "analyzed", "analyzer": "kuromoji_analyzer"},
         "location": {"type": "string", "store": true, "index": "analyzed", "analyzer": "kuromoji_analyzer"},
         "url": {"type": "string"},
         "last_tweet_at" : {"type":"date"},
         "updated_at" : {"type":"date"}
        }
      }
    }
  }
}'
echo ''
