var mongoose = require('mongoose')
var _ = require('underscore');

var model;
if (_.indexOf(mongoose.modelNames(), 'Tweet')) {
  var TweetSchema = new mongoose.Schema({
    _id: String,
  , user_id: String,
  , text: String,
  , created_at Date,
  , rt_source_id: String,
  }, {
    capped: {size: 10737418240, max: 10000000, autoIndexId: true} // maxSize: 10GB
  });
  model = mongoose.model('Tweet', TweetSchema, 'tweets');
}
else {
  model = mongoose.model('Tweet');
}

module.exports = model;
