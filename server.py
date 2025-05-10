import asyncio
import websockets
import json
from collections import defaultdict
import uuid

from deal_cards import deal_and_sort

MAX_PLAYERS = 4

# 房间池：room_id -> [(ws, player_number), ...]
rooms = defaultdict(list)

# 房间 -> 可用编号集合（0~3）
room_numbers = defaultdict(lambda: set(range(MAX_PLAYERS)))

# ws -> room_id, player_id, player_number
player_info = {}

# 房间准备状态：room_id -> {player_number: bool}
room_ready_state = defaultdict(dict)

async def broadcast(room_id, message, sender_ws=None):
    for ws, _ in rooms[room_id]:
        if ws != sender_ws:
            try:
                await ws.send(message)
            except websockets.exceptions.ConnectionClosed:
                print("连接断开，跳过发送")

def assign_room(ws):
    for room_id, players in rooms.items():
        if len(players) < MAX_PLAYERS:
            available_numbers = room_numbers[room_id]
            player_number = min(available_numbers)
            available_numbers.remove(player_number)
            rooms[room_id].append((ws, player_number))
            return room_id, player_number

    # 创建新房间
    new_room_id = str(uuid.uuid4())[:8]
    player_number = 0
    room_numbers[new_room_id].remove(player_number)
    rooms[new_room_id].append((ws, player_number))
    return new_room_id, player_number

async def handler(ws):
    print("新玩家连接")
    try:
        room_id, player_number = assign_room(ws)
        player_id = str(uuid.uuid4())[:8]
        player_info[ws] = {
            "room_id": room_id,
            "player_id": player_id,
            "player_number": player_number
        }
        room_ready_state[room_id][player_number] = False
        print(player_info[ws])

        await ws.send(json.dumps({
            "type": "welcome",
            "room_id": room_id,
            "player_id": player_id,
            "player_number": player_number
        }))        
        await broadcast(room_id, json.dumps({
            "type": "player_join",
            "room_id": room_id,
            "player_id": player_id,
            "player_number": player_number
        }), sender_ws=ws)

        async for msg in ws:
            data = json.loads(msg)
            print(f"[{player_id}] 发送: {data}")

            if data["type"] == "message":
                await broadcast(room_id, json.dumps({
                    "type": "chat",
                    "player_id": player_id,
                    "player_number": player_number,
                    "content": data["content"]
                }), sender_ws=ws)

            if data["type"] == "ready":
                room_ready_state[room_id][player_number] = True
                await broadcast(room_id, json.dumps({
                    "type": "ready_status",
                    "player_id": player_id,
                    "player_number": player_number,
                }), sender_ws=ws)

            if data["type"] == "deal_cards":
                if len(room_ready_state[room_id]) < MAX_PLAYERS:
                    await ws.send(json.dumps({
                        "type": "error", 
                        "message": "玩家没有到齐"
                    }))
#               elif all(room_ready_state[room_id].values()) == False:
#                   await ws.send(json.dumps({
#                       "type": "error", 
#                       "message": "还有玩家没有准备"
#                   }))

                else:                        
                    await broadcast(room_id, json.dumps({
                        "type": "deal_start"
                    }), sender_ws=ws)
                    hidden, players = deal_and_sort("2", "♠")
                    
                    for ws_i, player_i in rooms[room_id]:                        
                        player_info[ws_i]["hand"] = players[player_i]
                        player_info[ws_i]["hidden"] = []  # 初始无底牌

                        await ws_i.send(json.dumps({
                            "type": "your_hand",
                            "hand": players[player_i]
                        }))
                       
                    await broadcast(room_id, json.dumps({
                        "type": "deal_done",
                        "room_id": room_id
                    }))
            
            elif data["type"] == "play_card":
                cards_played = data["cards"]
                hand = player_info[ws].get("hand", [])
                
                if all(card in hand for card in cards_played):
                    # 从手牌中移除已出的牌
                    for card in cards_played:
                        hand.remove(card)
                    player_info[ws]["hand"] = hand

                    # 广播此玩家出牌
                    await broadcast(room_id, json.dumps({
                        "type": "play_card",
                        "player_id": player_id,
                        "player_number": player_number,
                        "cards": cards_played
                    }))
                    # 发送剩余手牌给该玩家
                    await ws.send(json.dumps({
                        "type": "your_hand",
                        "hand": hand
                    }))
                else:
                    await ws.send(json.dumps({
                        "type": "error", 
                        "message": "你出的牌不在手牌中"
                    }))

            elif data["type"] == "hide_cards":
                cards = data["cards"]
                hand = player_info[ws].get("hand", [])

                if len(cards) != 8 or not all(card in hand for card in cards):
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "藏牌失败：必须是你手中的8张牌"
                    }))
                else:
                    # 从手牌中移除，存为底牌
                    for card in cards:
                        hand.remove(card)
                    player_info[ws]["hand"] = hand
                    player_info[ws]["hidden"] = cards

                    # 返回更新后的手牌和底牌
                    await ws.send(json.dumps({
                        "type": "your_hand",
                        "hand": hand
                    }))
                    await ws.send(json.dumps({
                        "type": "your_hidden",
                        "cards": cards
                    }))
    
    except websockets.exceptions.ConnectionClosed:
        print("玩家断开连接")
    
    finally:
        if ws in player_info:
            info = player_info.pop(ws)
            room_id = info["room_id"]
            number = info["player_number"]

            # 移除玩家
            rooms[room_id] = [(w, n) for w, n in rooms[room_id] if w != ws]
            room_ready_state[room_id].pop(number, None)
            room_numbers[room_id].add(number)

            if not rooms[room_id]:
                del rooms[room_id]
                del room_ready_state[room_id]
                del room_numbers[room_id]
            
            await broadcast(room_id, json.dumps({
                "type": "player_leave",
                "player_number": number,
                "room_id": room_id
            }))

async def main():
    print("服务器启动在 ws://localhost:8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

asyncio.run(main())
