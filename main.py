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
from models.room import Room


manager = RoomManager()

# ！！！调用需注意：发牌函数本身不含主数！只是在 start_new_deal(...) 中载入主数为庄家主数。
# ！！！所以使用前庄家主数不能为 None！
# 设置庄家主数方法：
# 1. room.start_new_game(rank0, rank1) 中输入两个 rank 分别为 0、1 队主数
# 2. 直接设置 team.trump_rank
async def deal_cards(room: Room, suit: str, dealer: Player, dealer_team: Team):
    game = room.active_game
    deal = game.start_new_deal(suit, dealer, dealer_team)
    rank = dealer_team.trump_rank
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
    # 初始化玩家藏牌
    for idx, p in enumerate(game.players):
        p.hidden_cards.clear()  # 清空藏牌
        tar_ws = next(w for w, pl in manager.ws_to_player.items() if pl is p)
        await tar_ws.send(json.dumps({
            "type": "your_hidden",
            "cards": p.hidden_cards
        }))
    # 发送完牌完成消息 #TODO: 这里的deal_ready是多余的，deal_start就可以了
    await manager.broadcast(room, { 
        "type": "deal_ready",
        "room_id": room.room_id
    })
    deal.tricks = [Trick(trump_rank=deal.trump_rank, trump_suit=deal.trump_suit, starting_player_index=game.players.index(dealer))]


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
                await manager.broadcast(room, {
                    "type": "chat",
                    "player_id": player.player_id,
                    "player_number": player_number,
                    "player_name": player.nickname or f"玩家 {player_number} ",
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
                        "player_name": player.nickname or f"玩家 {player_number} ",
                        "team_id": choice,
                        "player_id": player.player_id
                    })#FIXME:当玩家没有修改昵称时，无法返回“以前”的玩家序号，前端会显示：“玩家1 to 玩家1”这种重复信息

            elif data["type"] == "ready":
                player.is_ready = True
                await manager.broadcast(room, {
                    "type": "ready_status",
                    "player_id": player.player_id,
                    "player_name": player.nickname or f"玩家 {player_number} "
                }, exclude_ws=ws)

            elif data["type"] == "team_update":
                # 先检查房间玩家是否已有四人
                if len(room.players) < 4:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "房间不足4人，无法分队"
                    }))
                    continue
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
                    "type": "update_teams",
                    "players": [{"player_id": p.player_id,
                                 "player_name": p.nickname or f"玩家 {p.player_number} ",
                                 "player_team": p.team_id,
                                 "player_number": p.player_number}
                    for p in room.players]
                })

            elif data["type"] == "clear_team":
                for p in room.players:
                    p.team_id = None
                room.teams[0].members = []
                room.teams[1].members = []
                await manager.broadcast(room, {
                    "type": "team_cleared"
                })

            elif data["type"] == "start_new_game": #FIXME：当上局没结束时开始新游戏需要清空hidden（传一个hidden消息）
            # —— 公共：任何 start_game 的请求，先检查分队是否已满 —— 
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
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "每队需要 2 名玩家才能开始游戏，请先完成分队。"
                    }))
                    continue
                # 情形 1：若没有正在进行的游戏，或已确认开始新游戏，询问是否开始默认游戏（庄家 0，两队主数 2）
                if room.active_game == None or data.get("confirmed", False) == True:
                    await ws.send(json.dumps({
                        "type": "confirm_start_default_game",
                        "message": "是否开始默认游戏？"
                    }))
                    continue
                # 情形 2：若有正在进行的游戏，且还未确认是否继续，先确认是否继续上局游戏
                elif room.active_game and data.get("confirmed", False) == False:
                    await ws.send(json.dumps({
                        "type": "confirm_start_new",
                        "message": "检测到上盘游戏尚未结束，是否开始新游戏？"
                    }))

            # 开始默认游戏
            elif data["type"] == "start_default_game":
                room.start_new_game(rank0="2", rank1="2") # 默认主数为 2
                suit = random.choice(['♠', '♥', '♣', '♦'])
                await deal_cards(room, suit, room.players[0], room.teams[0])
            
            # 开始独立游戏
            elif data["type"] == "start_free_game":
                # 将 0 队主数设为 rank_input
                game = room.start_new_game(rank0=data["rank_input"])
                await deal_cards(room, data["suit_input"], game.players[0], game.teams[0])
                                
            # 继续上局游戏
            elif data["type"] == "continue_previous_game":
                # 确认是否存在游戏记录
                if not room.active_game or not room.active_game.history:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "没有上一局游戏可供继续。"
                    }))
                    continue
                # 若存在，确认是否已设定庄家主数
                elif room.active_game.history:
                    game = room.active_game
                    last_deal = game.history[-1]
                    # 若庄家无主数，且未输入主数，请求输入主数
                    if last_deal.winner_team.trump_rank == None and "rank_input" not in data:
                        await ws.send(json.dumps({
                            "type": "request_trump_rank"
                        }))
                        continue
                    # 若庄家无主数，主数已输入
                    elif last_deal.winner_team.trump_rank == None and "rank_input" in data:
                        last_deal.winner_team.trump_rank = data["rank_input"]
                        await deal_cards(room, data["suit_input"], last_deal.next_dealer, last_deal.winner_team)
                    # 若庄家已有主数
                    else:
                        suit = random.choice(['♠', '♥', '♣', '♦'])
                        await deal_cards(room, suit, last_deal.next_dealer, last_deal.winner_team)

            elif data["type"] == "hide_cards":
                cards = data["cards"]
                deal = room.active_game.current_deal
                # 检查是否有正在进行的游戏
                if not deal:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "当前没有进行中的游戏"
                    }))
                    continue
                # 检查玩家是否是庄家
                if player.player_number != deal.dealer.player_number:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "只有庄家可以藏牌"
                    }))
                    continue
                # 检查藏牌数量和是否在手牌中
                if len(cards) != 8 or not all(c in player.hand for c in cards):
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "藏牌失败：必须是你手中的 8 张牌"
                    }))
                else:
                    for c in cards:
                        player.hand.remove(c)
                    player.hidden_cards = cards
                    room.active_game.current_deal.hidden_cards = cards
                    await ws.send(json.dumps({
                        "type": "your_hand",
                        "hand": player.hand
                    }))
                    await ws.send(json.dumps({
                        "type": "your_hidden",
                        "cards": cards
                    }))

            elif data["type"] == "play_card":
                cards = data["cards"]
                game = room.active_game
                deal = room.active_game.current_deal
                # 第一轮第一出前检查庄家是否已藏牌 
                trick = deal.tricks[-1] if deal.tricks else None
                if trick and trick.trick_number == 0 and trick.is_first_play:
                    # 如果庄家藏牌数不足 8 张，则阻止出牌
                    if len(deal.dealer.hidden_cards) < 8:
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
                trick = deal.tricks[-1] if deal.tricks else None
                trump_rank = deal.trump_rank
                trump_suit = deal.trump_suit
                # 使用 Trick 内部的出牌记录逻辑，若无错误 error_msg 为当前出牌玩家序号
                error_msg, celebrate = trick.record_play(player, cards, trump_rank, trump_suit)
                if error_msg not in range(4):
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": error_msg
                    }))
                    continue
                # 移除手牌中已出的牌
                for c in cards:
                    player.hand.remove(c)
                expected_number = (error_msg + 1) % 4
                expected_player = next(p for p in room.players if p.player_number == expected_number)
                # 广播出牌信息
                await manager.broadcast(room, {
                    "type": "play_card",
                    "player_id": player.player_id,
                    "player_number": player.player_number,
                    "player_name": player.nickname or f"玩家 {player.player_number}",
                    "cards": cards,
                    "celebrate_cue": celebrate,
                    "expected_player": expected_player.nickname or f"玩家 {expected_player.player_number} "
                })#FIXME：当trick结束时需要显示上一轮赢家为下一位玩家
                # 更新自己的手牌显示
                await ws.send(json.dumps({
                    "type": "your_hand",
                    "hand": player.hand
                }))
                # ✅ 所有玩家都出过牌，进入结算阶段
                if len(set(pn for pn, _, _ in trick.play_sequence)) == 4:
                    winner, max_card, team_id, points = trick.resolve()
                    result = deal.get_team_points()
                    await manager.broadcast(room, {
                        "type": "trick_done",
                        "winner_player_number": winner,
                        "winning_card": max_card,
                        "winning_team_id": team_id,
                        "trick_points": points,
                        "result": result
                    })
                    # 如果一整局deal结束，翻出底牌
                    if all(len(p.hand) == 0 for p in room.players):
                        #TODO：可以将player类中的 hidden cards去除，直接放在deal中
                        dealer_score, challenger_score, next_dealer_team, next_dealer, next_trump_rank = game.finish_current_deal()
                        await manager.broadcast(room, {
                            "type": "deal_done",
                            "dealer_score": dealer_score,
                            "challenger_score": challenger_score,
                            "next_dealer_team": next_dealer_team.team_id,
                            "next_dealer": next_dealer.nickname or f"玩家 {next_dealer.player_number}",
                            "next_trump_rank": next_trump_rank,
                            "hidden": deal.hidden_cards,
                        })
                        # 清空玩家手牌和藏牌
                        for p in game.players:
                            p.hand.clear()
                            p.hidden_cards.clear()
                            target_ws = next(w for w, pl in manager.ws_to_player.items() if pl is p)
                            await target_ws.send(json.dumps({
                                "type": "your_hidden",
                                "hand": p.hidden_cards
                            }))
                        game.current_deal = None # 清空当前 deal
                    else: 
                    # 在一般情况下加入新 Trick，胜者先出
                        new_trick = Trick(
                            trump_rank=deal.trump_rank,
                            trump_suit=deal.trump_suit,
                            trick_number=trick.trick_number + 1,
                            starting_player_index=winner,
                        )
                        deal.tricks.append(new_trick)

    #TODO：玩家退出后自动退队
    except websockets.exceptions.ConnectionClosed:
        print("连接关闭")#TODO：断线重连

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
