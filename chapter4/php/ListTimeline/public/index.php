<?php

use \Psr\Http\Message\ServerRequestInterface as Request;
use \Psr\Http\Message\ResponseInterface as Response;

require 'vendor/autoload.php';

$app = new \Slim\App;

$container = $app->getContainer();

// トップページをテンプレートエンジンのTwigでレンダリング
$container['view'] = function ($container) {
    // テンプレートエンジンのディレクトリを指定して起動（templates）
    $view = new \Slim\Views\Twig('templates', []);

    $router = $container->get('router');
    $uri = \Slim\Http\Uri::createFromEnvironment(new \Slim\Http\Environment($_SERVER));
    $view->addExtension(new \Slim\Views\TwigExtension($router, $uri));

    return $view;
};

// トップページの表示
$app->get('/', function ($request, $response) {
    // templates以下のtimeline.htmlをひな形に描画
    return $this->view->render($response, 'timeline.html', []);
});

// トップページからメッセージのリストを非同期に取得
$app->post('/timeline', function ($request, $response) {
    $user = $request->getParsedBodyParam('user');
    $message = $request->getParsedBodyParam('message');
    $isFirst = $request->getParsedBodyParam('isFirst');

    $key = 'timeline';

    // Redisへの接続処理
    $redis = new Redis();
    $redis->connect('127.0.0.1',6379);

    // MySQLへの接続処理
    $db = new PDO('mysql:host=127.0.0.1;dbname=sample;charset=utf8mb4', 'app', 'P@ssw0rd');

    // 投稿されたメッセージを保存
    if ($isFirst === 'false') {
        // Redisへの保存はキャッシュ用途なので、バックエンドとなるRDBMSのMySQLにINSERT文で保存
        $statement = $db->prepare("INSERT INTO timeline (name, message) VALUES (:name, :message)");
        $statement->bindParam(':name', $user, PDO::PARAM_STR);
        $statement->bindValue(':message', $message, PDO::PARAM_STR);
        $statement->execute();
    }

    // `LRANGE timeline 0 9`のような形式でコマンドを実行することで、直近10件の投稿を取得
    $messages = $redis->lRange($key, 0, 9);

    // キャッシュからメッセージが取得できない場合に、別途バックエンドとなるMySQLからデータの取得処理およびRedisへの保存
    if (empty($messages)) {
        $redis->delete($key);
        $messages = [];
        // MySQLからSELECT文で直近10件の投稿を取得
        $statement = $db->query("SELECT name,message FROM timeline ORDER BY id DESC LIMIT 10", PDO::FETCH_ASSOC);
        foreach($statement as $row) {
            $record = $row['name'] . ': ' . $row['message'];
            $messages[] = $record;

            // `RPUSH timeline hayashier:hello`のような形式でコマンドを実行して、MySQLから取得したデータをRedisにも保存
            $redis->rPush($key, $record);
        }
        // `EXPIRE timeline 60`のような形式でコマンドを実行して、RedisのリストにTTLとして60秒を設定
        $redis->expire($key, 60);
    }

    return json_encode($messages);
});

$app->run();
