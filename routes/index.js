var redis = require('redis')
  , mongoose = require('mongoose')
  , elasticsearch = require('elasticsearch');

module.exports.index = function(config) {
  return function(req, res) {
    req.socket.setTimeout(Infinity);
    var k = req.query.k ? req.query.k : null;
    var tweets = [];
    if (!k) {
      var client = redis.createClient(config.redis.port, config.redis.host)
      client.lrange('recent_tweets', 0, 19, function (err, data) {
        data.forEach(function (d) {
          tweets.push(JSON.parse(d));
        });
        res.render('index', {
          k: k,
          tweets: tweets
        });
      });
    } else {
      res.render('index', {
        k: k,
        tweets: tweets
      });
    }
  }
};

module.exports.users = function(config) {
  return function(req, res) {
    var k = req.query.k ? req.query.k : null;

    var userlist = [];
    if (!k) {
      // get from mongo
      require('../models/user.js');
      var db = mongoose.createConnection('mongodb://' + config.mongo.host + '/' + config.mongo.db)
      var User = db.model('User');
      var q = User.find().sort({'updated_at': -1}).limit(20);
      q.exec(function (err, data) {
        res.render('users', {
          k: k,
          users: data
        });
      });
    } else {
      // get from es
      var es = new elasticsearch.Client({
        host: config.elasticsearch.host + ':' + config.elasticsearch.port,
        log: 'trace'
      });
      userlist = es.search({
        index: tweets,
        type: tweet,
        body: {
          multi_match: {
            query: k,
            fileds: ['name', 'screen_name']
          }
        }
      });
    }
  };
};

module.exports.about = function(config) {
  return function(req, res) {
    //req.socket.setTimeout(Infinity);
    var searchKeys = [];
    config.twitter.search.queries.forEach(function(query) {
      keys = query.split(' OR ');
      keys.forEach(function(k) {
        if (searchKeys.indexOf(k) == -1) {
          searchKeys.push(k);
        }
      });
    });
    res.render('about', {
      search_keys: searchKeys,
      streaming_track: config.twitter.filter.track
    });
  };
};
