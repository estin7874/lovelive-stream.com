/*
  LOVELIVE! STREAM
  lovelive-stream.com | @estin7874
*/

$(function() {

  // get specified querystring value
  var getQueryString = function(option) {
    var delimiter;
    if (!option || !option.hasOwnProperty('delimiter')) {
      delimiter = '&';
    } else {
      delimiter = option.delimiter;
    }
    
    var slicePoint = window.location.href.indexOf('?');
    if (slicePoint < 0) {
      return null;
    }
    
    var urlParams = window.location.href.slice(slicePoint + 1).split(delimiter);
    var queryStrings = {};
    for(var i in urlParams) {
      var queryString = urlParams[i].split('=');
      queryStrings[queryString[0]] = queryString[1];
    }
    
    return queryStrings;
  };

  // get '... ago' notation
  var getDuration = function(postedAt) {
    var delta = parseInt((new Date)/1000) - postedAt;
    var duration = null;
    if (delta <= 59) {
      duration = delta.toString() + '秒';
    } else if (delta <= 3599) {
      duration = Math.floor(delta / 60).toString() + '分';
    } else if (delta <= 86399){
      duration = Math.floor(delta / 3600).toString() + '時間';
    } else {
      duration = Math.floor(delta / 86400).toString() + '日';
    }
    return duration;
  };

  // add a tweet item to ul#tweets as a child
  var addItem = function(item) {
    $('#tweets').prepend(item);
  };

  // remove last item of ul#tweets
  var truncateItem = function(maxItems) {
    var n = $('#tweets').children().length;
    if (n / 2 > maxItems) {
      $('#tweets').children('li:last').remove();
    }
  };

  // image convert flags
  // turn off these flags on flood of tweets.
  var convertTwimg = true;
  var convertTwitpic = true;
  var convertTwipple = true;
  var convertPhotozou = true;

  // image regular expressions
  var regexTwimg = /https:\/\/pbs\.twimg\.com\/[^"]+/;
  var regexTwitpic = /http:\/\/twitpic.com\/([^\s]+)/;
  var regexTwipple = /http:\/\/p.twipple.jp\/([^\s]+)/;
  var regexPhotozou = /http:\/\/photozou.jp\/photo\/show\/[0-9]*\/([^\s]+)/;

  // rewrite link address text to link, img address text to img
  var processText = function(text) {
    var generateLink = function(url) {
      if(convertTwimg && url.match(regexTwimg)) {
        return url.replace(regexTwimg, '<br /><a href="$&"><img src="$&"></a>');
      } else if(convertTwitpic && url.match(regexTwitpic)) {
        return url.replace(regexTwitpic, '<br /><a href="$&"><img src="http://twitpic.com/show/full/$1"></a>');
      } else if(convertTwipple && url.match(regexTwipple)) {
        return url.replace(regexTwipple, '<br /><a href="$&"><img src="http://p.twipple.jp/show/large/$1"></a>');
      } else if(convertPhotozou && url.match(regexPhotozou)) {
        return url.replace(regexPhotozou, '<br /><a href="$&"><img src="http://photozou.jp/p/img/$1"></a>');
      } else if (url.length > 30) {
        return '<a href="' + url + '">' + url.substring(0, 29) + '..</a>';
      } else {
        return '<a href="' + url + '">' + url + '</a>';
      }
    };

    return text.replace(/https*[^\s]+/g, generateLink)
               .replace(/\@([\x30-\x39\x41-\x5A\x5F\x61-\x7A]+)/g, '<a href="https://twitter.com/$1">@$1</a>');
  };

  $('#tweets').children('.tweet').each(function() {
    var d = $(this).find('.date');
    d.text(getDuration(parseInt(d.attr('unixtime'))));
    var t = $(this).find('.text');
    t.html(processText(t.html()));
  });

  var k = getQueryString('k');
  var maxItems = 30;

  // connect to socket.io
  var socket = io.connect('http://' + location.host);
  socket.on('message', function (m) {
    var message = JSON.parse(m);
    if ('tweet' in message) {
      // update tweets
      var tweet = message['tweet'];
      var postedAt = parseInt(new Date(tweet.created_at)/1000);
      if (!k || tweet.text.indexOf(k) != -1) {
        var name = tweet.name.length > 12 ? tweet.name.substring(0, 11) : tweet.name;
        var html = '<div class="avatar"><a href="https://twitter.com/' + tweet.screen_name + '"><img src="' + tweet.image + '"></a></div>'
                 + '<div class="context"><div class="name"><a href="https://twitter.com/' + tweet.screen_name + '">' + name + '</a></div>'
                 + '<div class="date" unixtime="' + postedAt + '">' + getDuration(postedAt) + '</div>'
                 + '<div class="text">' + processText(tweet.text) + '</div></div>';
        addItem($('<li class="tweet"></li>').html(html));
        truncateItem(maxItems);
        delete html, postedAt, tweet, message;
      }
    } else if ('counter' in message) {
      // update counter
      $('#tps-val').text(message['counter']);
    } else if ('hot_words' in message) {
      var words = message['hot_words'];
      var html = '';
      words.forEach(function(i) {
        html += '<span class="word"> ' + words[i] + ' </span>';
      });
      $('#trend').html(html);
    }

    // update '... ago' notations of all tweets
    $('#tweets').children('.tweet').each(function() {
      var d = $(this).find('.date');
      d.text(getDuration(d.attr('unixtime')));
    });
  });

  /*$("body").bgswitcher({
     images: ["/images/bg/1.jpg", "/images/bg/2.jpg", "/images/bg/3.jpg"],
  });*/

});
