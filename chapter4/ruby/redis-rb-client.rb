require 'redis'

redis = Redis.new

redis.set('foo', 'bar');
value = redis.get('foo');
puts value
