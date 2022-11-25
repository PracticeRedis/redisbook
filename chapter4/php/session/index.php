<?php

session_start();

echo "session_id=" . session_id() . " ";
$count = isset($_SESSION['count']) ? $_SESSION['count'] : 0;

$_SESSION['count'] = ++$count;

echo $count;
