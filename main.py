import asyncio
import json
import websockets
import random
from typing import List


from room_manager import RoomManager
from models.cards import Cards
from models.trick import Trick
from models.deal import Deal
from models.team import Team
from models.player import Player
from models.enums import Rank, RANK_STR_TO_ENUM


manager = RoomManager()

async def handler(ws):
    print("新玩家连接")
    try:
        player = manager.assign_player(ws)
        room = manager.get_room(ws)

        player_number = room.players.index(player)
        player.player_number = player_number
        player_name = player.nickname or f"玩家 {player_number}"
        
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
                await manager.broadcast(room, {
                    "type": "chat",
                    "player_id": player.player_id,
                    "player_number": player_number,
                    "player_name": player_name,
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
                        "player_name": player_name,
                        "team_id": choice,
                        "player_id": player.player_id
                    })

            elif data["type"] == "ready":
                player.is_ready = True
                await manager.broadcast(room, {
                    "type": "ready_status",
                    "player_id": player.player_id,
                    "player_name": player_name
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
                await manager.broadcast(room, {
                    "type": "team_cleared"
                })

            # —— 公共：任何 start_game 的请求，先检查分队是否已满 —— 
            if data["type"] == "start_game_default":
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
                if not all(len(team.members) == 2 for team in room.teams.values()):
                    # 只发错误给当前客户端即可，用 manager.send 或 ws.send_json
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "每队需要 2 名玩家才能开始游戏，请先完成分队。"
                    }))
                    # 跳过后续 start_game 逻辑，但不关闭连接
                    continue
        
            # ———— 点击“开始游戏”后的两种模式 ————
            if data["type"] == "start_game_default":
                # 1) 创建新一局 Game（默认各队 trump_rank＝Rank.TWO）
                room.start_new_game()
                # # 2) 随机选一个 suit 并启动第一个 Deal
                # suit = random.choice(['♠','♥','♣','♦'])
                # room.active_game.start_new_deal(suit, room.teams[0], room.teams[1])
                # room.active_game.current_deal.dealer_team = room.teams[0]
                # room.active_game.current_deal.challenger_team = room.teams[1]
                # # 3) 广播发牌开始
                # await manager.broadcast(room, {
                #     "type": "deal_start",
                #     "rank_input": room.active_game.current_deal.trump_rank,
                #     "suit_input": suit
                # })
        
            # elif data["type"] == "start_game_choose_trump":
            #     # 1) 先构造 Game（占位），但不立刻发牌
            #     room.start_new_game({0:room.teams[0].members,1:room.teams[1].members})
            #     # 2) 请求客户端弹出主数输入框
            #     await manager.broadcast(room, {"type": "prompt_team_trump"})
        
            # elif data["type"] == "set_team_trump":
            #     # 客户端返回所选主数
            #     rank_str = data["rank"]
            #     player_team = player.team_id
            #     room.teams[player_team].trump_rank = rank_str
            #     await manager.broadcast(room, {
            #         "type": "team_trump_set",
            #         "team_id": player.team_id,
            #         "trump_rank": rank_str
            #     })
            #     # 设完主数后，下一步请客户端选庄家
            #     await manager.broadcast(room, {"type": "prompt_dealer"})
        
            # if data["type"] == "set_dealer":
            #     # 客户端返回要做庄的队伍 ID
            #     dealer_team_id = player.team_id
            #     challenger_team_id = (dealer_team_id + 1) % 2
            #     # 更新 Game 里哪个队是庄家
            #     room.teams[dealer_team_id].is_dealer = True
            #     room.teams[challenger_team_id].is_dealer = False
            #     await manager.broadcast(room, {
            #         "type": "dealer_set",
            #         "dealer_team_id": dealer_team_id
            #     })
            #     # 庄家确定后，正式启动第一局 Deal
            #     suit = random.choice(['♠','♥','♣','♦'])
            #     room.active_game.start_new_deal(suit, dealer_team_id, challenger_team_id)
            #     await manager.broadcast(room, {
            #         "type": "deal_start",
            #         "rank_input": room.active_game.current_deal.trump_rank,
            #         "suit_input": suit
            #     })

            elif data["type"] == "deal_cards":
                # 情形 1：若已经开始一局默认游戏，创建一个新 deal，由玩家 0 坐庄
                if room.active_game and room.active_game.is_default:
                    game = room.active_game
                    suit = random.choice(['♠','♥','♣','♦'])
                    dealer = game.players[0]
                    dealer_team = game.teams[0]
                    rank = dealer_team.trump_rank
                    deal = game.start_new_deal(suit, dealer, dealer_team)
                # 情形 2：开始一局独立的 deal，玩家 0 坐庄，会将 trump_rank 信息计入庄队 0
                else:
                    team0_members = room.teams[0].members
                    team1_members = room.teams[1].members
                    if len(team0_members) != 2 or len(team1_members) != 2:
                        await ws.send(json.dumps({
                            "type": "error",
                            "message": "玩家还未分队"
                        }))
                        continue
                    # 开始独立游戏，请求输入主数
                    room.start_independent_deal_game()
                    if "rank_input" not in data or "suit_input" not in data:
                        await ws.send(json.dumps({
                            "type": "request_trump_input",
                            "message": "请输入主数和主花色以开始新的一局"
                        }))
                        continue  # 提前返回，等待下次调用
                    else:
                        # 第二步：收到了输入 → 设置 trump
                        game = room.active_game
                        rank = data["rank_input"]
                        suit = data["suit_input"]
                        dealer = game.players[0]
                        dealer_team = game.teams[0]
                        dealer_team.trump_rank = rank
                        deal = game.start_new_deal(suit, dealer, dealer_team)
                
                # 发送发牌消息并发牌
                await manager.broadcast(room, {
                    "type": "deal_start",
                    "rank_input": rank,
                    "suit_input": suit
                })
                deal.deal_to_players(suit, game.players, dealer, dealer_team)
                # 发送每个玩家的手牌
                for idx, p in enumerate(game.players):
                    target_ws = next(w for w, pl in manager.ws_to_player.items() if pl is p)
                    await target_ws.send(json.dumps({
                        "type": "your_hand",
                        "hand": p.hand
                    }))

                    # if p == deal.dealer:
                    #     await p.ws.send(json.dumps({
                    #         "type": "your_hidden",
                    #         "cards": deal.final_cards
                    #     }))
                # for idx, p in enumerate(room.players):
                #     p.hand = sorted_hands[idx]
                #     p.hidden_cards = []
                #     target_ws = next(w for w, pl in manager.ws_to_player.items() if pl is p)
                #     await target_ws.send(json.dumps({
                #         "type": "your_hand",
                #         "hand": p.hand
                #     }))
                # 发送完牌完成消息
                await manager.broadcast(room, {
                    "type": "deal_ready",
                    "room_id": room.room_id
                })
                game.current_deal.tricks = [Trick(trump_rank=deal.trump_rank, trump_suit=deal.trump_suit, starting_player_index=game.players.index(dealer))]

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

            elif data["type"] == "play_card": #TODO: 检查结束条件（藏牌清空！）
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
                if error_msg not in range(4):
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
                    "cards": cards,
                    "expected_player": (error_msg + 1) % 4
                })
                # 更新自己的手牌显示
                await ws.send(json.dumps({
                    "type": "your_hand",
                    "hand": player.hand
                }))
                # ✅ 所有玩家都出过牌，进入结算阶段
                if len(set(pn for pn, _, _ in trick.play_sequence)) == 4:
                    winner, max_card, team_id, points = trick.resolve()
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
                    await manager.broadcast(room, {
                        "type": "trick_done",
                        "winner_player_number": winner,
                        "winning_card": max_card,
                        "winning_team_id": team_id,
                        "trick_points": points,
                        "result": result
                    })
                    # 如果一整局deal结束，翻出底牌，并询问是否继续游戏（继承这局的信息往下打）
                    if all(len(p.hand) == 0 for p in room.players):
                        hidden = deal.dealer.hidden_cards
                        dealer_score, challenger_score, next_dealer, next_trump_rank = deal.finish_deal(hidden)
                        await manager.broadcast(room, {
                            "type": "deal_done",
                            "dealer_score": dealer_score,
                            "challenger_score": challenger_score,
                            "next_dealer": next_dealer,
                            "next_trump_rank": next_trump_rank,
                            "hidden": hidden
                        })
            
            elif data["type"] == "continue_game":
                room.active_game.start_new_deal
                # if use_same:
                #     room.start_new_deal(same_settings=True)
                # else:
                #     # 可能进入等待设定主数/主花色阶段
                #     await manager.broadcast(room, {
                #         "type": "prompt_trump_selection"
                #     })
            

                        
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
