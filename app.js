#!/usr/bin/env node

// require('v8-profiler');

var version = '0.0.2'
  , bodyParser = require('body-parser')
  , config = require('config')
  , errorhandler = require('errorhandler')
  , express = require('express')
  , log4js = require('log4js')
  , http = require('http')
  , methodOverride = require('method-override')
  , morgan = require('morgan')
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
app.set('domain', config.app.server.bind_address || 'localhost');
app.set('port', process.env.PORT || config.app.server.port || 3000);
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ect');
app.engine('.ect', renderer.render);
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: true}));
app.use(methodOverride());
app.use(morgan('combined'));
app.use(express.static(path.join(__dirname, 'public')));

var env = process.env.NODE_ENV || 'development';
// development only
if ('development' == env) {
  app.use(errorhandler({
    dumpExceptions: true,
    showStack: true
  }));
}
if ('production' == env) {
  app.use(express.errorHandler());
}

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
