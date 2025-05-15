import asyncio
import json
import websockets
from typing import List

from room_manager import RoomManager
from models.cards import Cards
from models.trick import Trick
from models.deal import Deal
from models.team import Team
from models.player import Player


manager = RoomManager()

deal = Deal(deal_number=0, dealer_team=0, challenger_team=1, trump_rank=None, trump_suit=None)

async def handler(ws):
    print("新玩家连接")
    try:
        player = manager.assign_player(ws)
        room = manager.get_room(ws)

        player_number = room.players.index(player)
        player.player_number = player_number


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

            elif data["type"] == "select_team":
                choice = data.get("team_id")
                if choice not in (0, 1):
                    await ws.send(json.dumps({"type": "error", "message": "无效队伍"}))
                # 如果之前已经选过队，先从旧队伍中移除
                if player.team_id is not None:
                    room.teams[player.team_id].remove_member(player)
            
                # 尝试加入新队伍
                err = room.teams[choice].add_member(player)
                if err:
                    # 加入失败，通知客户端，但不关闭连接
                    await ws.send(json.dumps({"type": "error", "message": err}))
                else:
                    # 加入成功，更新 player.team_id 并广播
                    player.team_id = choice
                    await manager.broadcast(room, {
                        "type": "team_selected",
                        "player_number": player.player_number,
                        "team_id": choice,
                        "player_id": player.player_id
                    })

            elif data["type"] == "ready":
                player.is_ready = True
                await manager.broadcast(room, {
                    "type": "ready_status",
                    "player_id": player.player_id,
                    "player_number": player_number,
                    "player_name": player.nickname or f"玩家 {player_number}"
                }, exclude_ws=ws)

            elif data["type"] == "team_update":
                # 1. 从 room.teams 直接取出已选队员
                team0 = room.teams[0].members      # 已在队 0 的玩家列表
                team1 = room.teams[1].members      # 已在队 1 的玩家列表
            
                # 2. 三种分队情况
                if not team0 and not team1:
                    # A. 两队都空 → 按 player_number 默认分配
                    ordered = sorted(room.players, key=lambda p: p.player_number)
                    team0[:] = [ordered[0], ordered[2]]
                    team1[:] = [ordered[1], ordered[3]]
                elif len(team0) == 2 and len(team1) == 2:
                    # B. 两队都满 → 保持现有 members，不改
                    pass
                else:
                    # C. 部分已选 → 先保留，再从未分队玩家里补齐
                    assigned = team0 + team1
                    unassigned = sorted(
                        [p for p in room.players if p not in assigned],
                        key=lambda p: p.player_number
                    )
                    for p in unassigned:
                        if len(team0) < 2:
                            team0.append(p)
                        elif len(team1) < 2:
                            team1.append(p)
                        else:
                            break
            
                # 3. 重新分配 player_number：队0→[0,2]，队1→[1,3]
                for tid, members in ((0, team0), (1, team1)):
                    nums = [tid, tid + 2]
                    for idx, p in enumerate(members):
                        p.team_id = tid
                        p.player_number = nums[idx]
            
                # 4. 按 player_number 排序 room.players
                room.players.sort(key=lambda p: p.player_number)
            
                # 5. 广播更新
                await manager.broadcast(room, {
                    "type": "update_player_numbers",
                    "players": [
                        {"player_id": p.player_id, "player_team": p.team_id, "player_number": p.player_number}
                        for p in room.players
                    ]
                })
            elif data["type"] == "clear_team":
                for p in room.players:
                    p.team_id = None
                room.teams[0].members = []
                room.teams[1].members = []

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

                rank_input = data["rank_input"]
                suit_input = data["suit_input"]

                await manager.broadcast(room, {
                    "type": "deal_start",
                    "rank_input": rank_input,
                    "suit_input": suit_input
                })

                hidden, sorted_hands = Cards.deal_and_sort(rank_input, suit_input)

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
               
                deal.deal_number += 1
                deal.trump_rank=rank_input
                deal.trump_suit=suit_input
                deal.tricks = [Trick(trump_rank=deal.trump_rank, trump_suit=deal.trump_suit, starting_player_index=0)]
                deal.dealer_team = room.teams[0]
                deal.challenger_team = room.teams[1]

            elif data["type"] == "play_card":
                cards = data["cards"]
                # —— 新增：第一轮第一出前检查庄家是否已藏牌 —— 
                trick = deal.tricks[-1] if deal.tricks else None
                if trick and trick.trick_number == 0 and trick.is_first_play:
                    # 根据 Trick.starting_player_index 找到当前第一出玩家（即庄家）
                    dealer_number = trick.starting_player_index
                    dealer_player = next(p for p in room.players if p.player_number == dealer_number)
                    # 如果藏牌数不足 8 张，则阻止出牌
                    if len(dealer_player.hidden_cards) < 8:
                        await ws.send(json.dumps({
                            "type": "error",
                            "message": "庄家还未藏牌！"
                        }))
                        continue
                # 检查所有牌都在手牌中
                if not all(c in player.hand for c in cards):
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "你出的牌不在手牌中"
                    }))
                    continue
            
                # 获取当前 Trick 实例
                # trick = room.active_game.current_deal.tricks[-1]
                trick = deal.tricks[-1] if deal.tricks else None
                trump_rank = deal.trump_rank
                trump_suit = deal.trump_suit
                # 使用 Trick 内部的出牌记录逻辑
                error_msg = trick.record_play(player, cards, trump_rank, trump_suit)
                if error_msg:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": error_msg
                    }))
                    continue
               
                # 移除手牌中已出的牌
                for c in cards:
                    player.hand.remove(c)
            
                # 广播出牌信息
                await manager.broadcast(room, {
                    "type": "play_card",
                    "player_id": player.player_id,
                    "player_number": player.player_number,
                    "player_name": player.nickname or f"玩家 {player.player_number}",
                    "cards": cards
                })
            
                # 更新自己的手牌显示
                await ws.send(json.dumps({
                    "type": "your_hand",
                    "hand": player.hand
                }))
                
                # ✅ 所有玩家都出过牌，进入结算阶段
                if len(set(pn for pn, _, _ in trick.play_sequence)) == 4:
                    winner, max_card, team_id, points = trick.resolve()
                    print("结算")
                    # 新 Trick，胜者先出
                    new_trick = Trick(
                        trump_rank=deal.trump_rank,
                        trump_suit=deal.trump_suit,
                        trick_number=trick.trick_number + 1,
                        starting_player_index=winner,
                    )
                    # room.active_game.current_deal.tricks.append(new_trick)
                    result = deal.get_team_points()
                    deal.tricks.append(new_trick)
                    print("新trick已添加")
                    await manager.broadcast(room, {
                        "type": "trick_done",
                        "winner_player_number": winner,
                        "winning_card": max_card,
                        "winning_team_id": team_id,
                        "trick_points": points,
                        "result": result
                    })
                # print(f"出完牌后, {trick.trick_number=}, {trick.play_sequence=}")
            
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
