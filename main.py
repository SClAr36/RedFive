import asyncio
import json
import websockets

from room_manager import RoomManager
from models.enums import Rank, RANK_STR_TO_ENUM
from models.cards import Cards

manager = RoomManager()

async def handler(ws):
    print("新玩家连接")
    try:
        player = manager.assign_player(ws)
        room = manager.get_room(ws)
        game = room.active_game

        player_number = room.players.index(player)

        await ws.send(json.dumps({
            "type": "welcome",
            "room_id": room.room_id,
            "player_id": player.player_id,
            "player_number": player_number
        }))

        await manager.broadcast(room, {
            "type": "player_join",
            "room_id": room.room_id,
            "player_id": player.player_id,
            "player_number": player_number
        }, exclude_ws=ws)

        async for raw in ws:
            data = json.loads(raw)
            print(f"[{player.player_id}] 发送: {data}")

            if data["type"] == "set_nickname":
                player.nickname = data["nickname"]
                await manager.broadcast(room, {
                    "type": "nickname_set",
                    "player_id": player.player_id,
                    "player_number": player_number,
                    "nickname": player.nickname
                }, exclude_ws=ws)

            elif data["type"] == "message":
                name = player.nickname or f"玩家 {player_number}"
                await manager.broadcast(room, {
                    "type": "chat",
                    "player_id": player.player_id,
                    "player_number": player_number,
                    "player_name": name,
                    "content": data["content"]
                }, exclude_ws=ws)

            elif data["type"] == "ready":
                player.is_ready = True
                await manager.broadcast(room, {
                    "type": "ready_status",
                    "player_id": player.player_id,
                    "player_number": player_number,
                    "player_name": player.nickname or f"玩家 {player_number}"
                }, exclude_ws=ws)

            elif data["type"] == "deal_cards":
                if len(room.players) < 4:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "玩家人数不足"
                    }))
                    continue

                # if not all(p.is_ready for p in room.players):
                #     await ws.send(json.dumps({
                #         "type": "error",
                #         "message": "还有玩家未准备"
                #     }))
                #     continue

                if "rank_input" not in data or "suit_input" not in data:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "缺少主数或主花色"
                    }))
                    continue

                rank_input = RANK_STR_TO_ENUM[data["rank_input"]]  # ✅ 正确映射
                suit_input = data["suit_input"]

                await manager.broadcast(room, {
                    "type": "deal_start",
                    "rank_input": rank_input.name,
                    "suit_input": suit_input
                })

                hidden, sorted_hands = Cards.deal_and_sort(rank_input.name, suit_input)

                for idx, p in enumerate(room.players):
                    p.hand = sorted_hands[idx]
                    p.hidden_cards = []
                    target_ws = next(w for w, pl in manager.ws_to_player.items() if pl is p)
                    await target_ws.send(json.dumps({
                        "type": "your_hand",
                        "hand": p.hand
                    }))

                await manager.broadcast(room, {
                    "type": "deal_done",
                    "room_id": room.room_id
                })

            elif data["type"] == "play_card":
                cards = data["cards"]
                if all(c in player.hand for c in cards):
                    for c in cards:
                        player.hand.remove(c)
                    await manager.broadcast(room, {
                        "type": "play_card",
                        "player_id": player.player_id,
                        "player_number": player_number,
                        "player_name": player.nickname or f"玩家 {player_number}",
                        "cards": cards
                    })
                    await ws.send(json.dumps({
                        "type": "your_hand",
                        "hand": player.hand
                    }))
                else:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "你出的牌不在手牌中"
                    }))

            elif data["type"] == "hide_cards":
                cards = data["cards"]
                if len(cards) != 8 or not all(c in player.hand for c in cards):
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "藏牌失败：必须是你手中的8张牌"
                    }))
                else:
                    for c in cards:
                        player.hand.remove(c)
                    player.hidden_cards = cards
                    await ws.send(json.dumps({
                        "type": "your_hand",
                        "hand": player.hand
                    }))
                    await ws.send(json.dumps({
                        "type": "your_hidden",
                        "cards": cards
                    }))

    except websockets.exceptions.ConnectionClosed:
        print("连接关闭")

    finally:
        if ws in manager.ws_to_player:
            player = manager.ws_to_player[ws]
            room = manager.get_room(ws)
            player_number = room.players.index(player)
            name = player.nickname or f"玩家 {player_number}"

            await manager.broadcast(room, {
                "type": "player_leave",
                "player_id": player.player_id,
                "player_number": player_number,
                "player_name": name,
                "room_id": room.room_id
            }, exclude_ws=ws)

            room.players.remove(player)
            del manager.ws_to_player[ws]
            if not room.players:
                del manager.rooms[room.room_id]


async def main():
    print("服务器启动在 ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
