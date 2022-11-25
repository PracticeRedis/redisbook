from fastapi import FastAPI, Depends
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket
from starlette.staticfiles import StaticFiles
import asyncio
import uvloop
import uvicorn
import aioredis
import datetime

HOST = "0.0.0.0"
PORT = 8080
REDIS_HOST = HOST
REDIS_PORT = 6379
STREAM_MAX_LEN = 1000

app = FastAPI()

# index.htmlの静的ファイルの表示を有効にする
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redisへの接続処理。
# コネクションプーリングを使用
redis = aioredis.from_url(
    'redis://' + '127.0.0.1')

# メッセージの読み込み処理を定義
async def read_message(websocket: WebSocket, join_info: dict):
    connected = True
    is_first = True
    stream_id = '$'
    while connected:
        try:
            count = 1 if is_first else 100
            # `XREAD COUNT 100 BLOCK 100000 STREAMS room1 $`のような形式でコマンドを実行し、新規メッセージの受付および読み込み
            results = await redis.xread(
                    streams={join_info['room']: stream_id},
                    count=count,
                    block=100000
            )
            for room, events in results:
                if join_info['room'] != room.decode('utf-8'):
                    continue
                for e_id, e in events:
                    now = datetime.datetime.now()

                    # WebSocketを通して、同じチャンネルに参加しているユーザー全員にメッセージを送信
                    await websocket.send_text(f"{now.strftime('%H:%M')} {e[b'msg'].decode('utf-8')}")

                    # 最後に受け取ったIDを保存しておき、`XREAD COUNT 100 BLOCK 100000 STREAMS room1 <ID>`のような形式でIDを指定して実行すると、続きからメッセージを受け取ることができる
                    stream_id = e_id
                if is_first:
                    is_first = False
        except:
            await redis.close()
            connected = False

# メッセージの書き込み処理を定義
async def write_message(websocket: WebSocket, join_info: dict):
    await notify(join_info, 'joined')

    connected = True
    while connected:
        try:
            data = await websocket.receive_text()
            # `XADD room1 MAXLEN 1000 * username Taro msg "Hello, everyone!"`のような形式でコマンドを実行し、新規メッセージの書き込み
            await redis.xadd(join_info['room'],
                            {
                                'username': join_info['username'],
                                'msg': data
                            },
                            id=b'*',
                            maxlen=STREAM_MAX_LEN)
        except:
            # For example, if user closes the browser tab, other users will see the message, "username has left"
            await notify(join_info, 'left')
            await redis.close()
            connected = False


# ユーザーがチャットルームに入った時に、ルーム内の全ユーザーに"Taro has joined"のようなメッセージ書き込み
async def notify(join_info: dict, action: str):
    # `XADD room1 MAXLEN 1000 * username Taro msg "Taro has joined"`のような形式でコマンドを実行し、新規メッセージの書き込み
    await redis.xadd(join_info['room'],
                    {'msg': f"{join_info['username']} has {action}"},
                    id=b'*',
                    maxlen=STREAM_MAX_LEN)

async def get_joininfo(username: str = None, room: str = None):
    return {"username": username, "room": room}

# WebSocketによる通信に使用。async/awaitを使用
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, join_info : dict = Depends(get_joininfo)):
    await websocket.accept()
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    await asyncio.gather(write_message(websocket, join_info), read_message(websocket, join_info))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
