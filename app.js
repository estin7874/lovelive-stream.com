#!/usr/bin/env node

// require('v8-profiler');

var version = '0.0.1'
  , config = require('config')
  , express = require('express')
  , log4js = require('log4js')
  , http = require('http')
  , redis = require('redis')
  , path = require('path')
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
  , io = require('socket.io')(server)
  , RedisAdapter = require('socket.io-redis')({'host': config.redis.port, 'port': config.redis.host})

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

// redis pub/sub subscribe
subscriber.subscribe('stream');

// emit updates
io.adapter(RedisAdapter);
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
