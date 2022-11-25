require 'sinatra'
require 'sinatra/reloader'
require 'redis'
require 'mysql2'

# Redisへの接続処理
redis = Redis.new

# MySQLへの接続処理
mysql = Mysql2::Client.new(:host => '127.0.0.1', :username => 'app', :password => 'P@ssw0rd', :database => 'sample')

# トップページ取得のためのGETメソッド
get '/' do
    erb :index
end

# トップページから非同期通信に使用されるPOSTメソッド
post '/vote' do
    # 各候補者に投票した人を追加
    if !params[:candidate].empty? && !params[:voter].empty?
      # 永続化のためにMySQLにデータを追加
      insert_statement = mysql.prepare("INSERT INTO votes (candidate, voter) VALUES (?, ?)")
      result = insert_statement.execute(params[:candidate], params[:voter])

      # `SADD candidate:1 hayashier`のような形式でコマンドを実行し、Redisにデータを追加
      redis.sadd(params[:candidate], params[:voter])
    end

    # `SCAN 0 MATCH candidate:*`のような形式でコマンドを実行し、候補者の一覧を取得
    cursor = 0
    candidates = []
    loop {
      cursor, keys = redis.scan(cursor, :match => "candidate:*")
      candidates += keys
      break if cursor == "0"
    }

    # キャッシュからメッセージが取得できない場合に、別途バックエンドとなるMySQLからデータの取得処理およびRedisへの保存
    if candidates.length <= 1
      # 永続化のためにMySQLにデータを追加
      select_statement = mysql.prepare("SELECT candidate, voter FROM votes")
      result = select_statement.execute()
      counts = {}
      candidates = []
      result.each { |element|
        # `SADD candidate:1 hayashier`のような形式でコマンドを実行し、Redisにデータを追加
        redis.sadd(element["candidate"], element["voter"])
        candidates += [element["candidate"]]
      }
    end

    counts = {}
    candidates.each { |candidate|
      # `SCAN 0 MATCH candidate:*`のような形式でコマンドを実行し、各候補者の投票人数をカウント
      counts[candidate] = redis.scard(candidate)
    }
    counts = counts.sort.to_h
    counts.to_json
end
