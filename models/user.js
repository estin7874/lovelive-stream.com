var mongoose = require('mongoose')
  , _ = require('underscore');

var model;
if (_.indexOf(mongoose.modelNames(), 'User')) {
  var UserSchema = new mongoose.Schema({
    _id: String
  , name: String
  , screen_name: String
  , image: String
  , description: String
  , location: String
  , last_tweet_at: Date
  , updated_at: {type: Date, index: true}
  });
  model = mongoose.model('User', UserSchema, 'users');
}
else {
  model = mongoose.model('User');
}

module.exports = model;
