<?php

$redis = new Redis();

// Redisと接続
$redis->connect("127.0.0.1",6379);

$redis->set('foo', 'bar');
$value = $redis->get('foo');
echo $value;
