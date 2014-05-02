#!/usr/bin/env node

// require('v8-profiler');

var version = '0.0.1'
  , express = require('express')
  , log4js = require('log4js')
  , http = require('http')
  , redis = require('redis')
  , RedisStore = require('socket.io/lib/stores/redis')
  , path = require('path')
  , config = require('config')
  , ECT = require('ect')

  // routes
  , routes = require('./routes')

  // ect
  , renderer = ECT({watch: true, root: __dirname + '/views'})

  // logger
  , logger = log4js.getLogger()

  // express
  , app = express()
  , server = app.listen(config.app.server.port)
  , io = require('socket.io').listen(server, {'log level': 1})

  // redis
  , subscriber = redis.createClient(config.redis.port, config.redis.host)

// all environments
app.configure(function(){
  app.set('domain', config.app.server.bind_address || 'localhost');
  app.set('port', process.env.PORT || config.app.server.port || 3000);
  app.set('views', path.join(__dirname, 'views'));
  app.set('view engine', 'ect');
  app.engine('.ect', renderer.render)
  app.use(express.logger('dev'));
  app.use(express.json());
  app.use(express.urlencoded());
  app.use(express.methodOverride());
  app.use(app.router);
  app.use(express.static(path.join(__dirname, 'public')));
});

// development only
app.configure('development', function() {
  app.use(express.errorHandler({
    dumpExceptions: true,
    showStack: true
  }));
});
app.configure('production', function() {
  app.use(express.errorHandler());
});

// routes
routes.config = config;
app.get('/', routes.index(config));
app.get('/users', routes.users(config));
app.get('/about', routes.about(config));

var redisConf = {host: config.redis.host, port: config.redis.port};
io.set('store', new RedisStore({
  redisPub: redisConf,
  redisSub: redisConf,
  redisClient: redisConf
}));

// redis pub/sub subscribe
subscriber.subscribe('stream');

// emit updates
io.sockets.setMaxListeners(0);
io.sockets.on('connection', function(socket) {
  subscriber.on('message', function(channel, message) {
    socket.emit('message', message);
  });
});

// signal handling
process.on('SIGINT', function() {
  process.exit();
});
