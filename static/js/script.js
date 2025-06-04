const handDiv   = document.getElementById("card-container");
    const log       = document.getElementById('log');
    const playLog   = document.getElementById('play-log');
    const roomStatus = document.getElementById("room-status");
    const ws        = new WebSocket("ws://localhost:8765");
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message');
    const teamAScore = document.getElementById('team-a-score');
    const teamBScore = document.getElementById('team-b-score');

    /* 抽屉面板元素 */
    const toggleLogBtn = document.getElementById('toggle-log-btn');
    const logPanel     = document.getElementById('log-panel');
    const closeLogBtn  = document.getElementById('close-log-btn');

    /* 日志面板控制 */
    toggleLogBtn.addEventListener('click', () => {
      logPanel.classList.toggle('open');
    });
    closeLogBtn.addEventListener('click', () => {
      logPanel.classList.remove('open');
    });

    // 初始化房间状态
    const roomId = localStorage.getItem("chosen_room_id");

    if (!roomId) {
      alert("❗ 未检测到房间信息，请先从首页选择或创建房间！");
      window.location.href = "index.html";
    } else {
      console.log("准备连接房间 ID:", roomId);
    }

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "join_room", room_id: roomId }));
    };

    roomStatus.textContent = "🎲 欢迎加入红五冲冲冲游戏！请设置昵称并准备";

    ws.onclose = () => { log.textContent += "🔌 连接关闭\n"; };

    let hand = [];
    let currentNickname = '';

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "room_joined":
            log.textContent  = `欢迎加入房间"${data.room_name}"(${data.room_id.slice(0, 8)})，${data.player_id.slice(0, 8)}，你是玩家 ${data.player_number}\n`;
            roomStatus.textContent = `👋 欢迎加入房间 ${data.room_name}，你是玩家 ${data.player_number}`;
            break;

          case "player_join":
            log.textContent += `👤 玩家${data.player_id.slice(0, 8)} (玩家${data.player_number}) 加入了房间\n`;
            break;

          case "nickname_set":
            log.textContent += `📛 玩家${data.player_id.slice(0, 8)} (玩家${data.player_number}) 设置昵称为 ${data.nickname}\n`;
            if (data.player_name === currentNickname) {
              currentNickname = data.nickname;
            }
            break;

          case "chat":
            addChatMessage(data.player_name, data.content, data.player_name === currentNickname);
            break;

          case "ready_status":
            log.textContent += `🃏 ${data.player_name} 准备好了\n`;
            /* roomStatus.textContent = `🃏 ${data.player_name} 已准备，等待发牌...`; */
            break;

          case "team_selected":
            addChatMessage("系统", `${data.player_name}加入了${data.team_id === 0 ? 'A' : 'B'}队`, false);
            break;

          case "update_teams":
            // 这是队伍序号一起显示的版本
            const teamA = [];
            const teamB = [];
            // 寻找之前分队信息
            data.players.forEach(p => {
              const text = `${p.player_name} ➜ 玩家 ${p.player_number}`;
              if (p.player_team === 0) {
                teamA.push(text);
              } else {
                teamB.push(text);
              }
            });
            
            const msg = `分队完成！<br>
            🟥 队 A：<br>${teamA.join("<br>")}<br><br>
            🟦 队 B：<br>${teamB.join("<br>")}`;
            
            addChatMessage("系统", msg, false);
            break;

          case "personal_update":
            roomStatus.textContent = `${data.player_name}，你现在是玩家 ${data.player_number}，你属于 ${data.team_id === 0 ? 'A' : 'B'} 队`;
            if (data.trump_rank !== null) {
              roomStatus.textContent += `，你们队的主数是 ${data.trump_rank}`;
            }
            break;

            case "team_cleared":
            addChatMessage("系统", `分队取消，请全体玩家重新选择队伍`, false);
            break;

          case "confirm_start_default_game":
            const startDefault = confirm(
              data.message || "是否以默认设置开始游戏？\n\n" +
              "主数：2；庄家为第一位玩家\n\n" +
              "【确定】开始默认游戏\n【取消】自己选择主数(和庄家)"
            );
            // 如果用户选择了默认设置，则发送开始游戏请求
            if (startDefault) {
              ws.send(JSON.stringify({ type: "start_default_game" }));
            } else {
              // 用户想自定义主数，弹出 prompt 框输入主数
              promptTrump("start_free_game");
            }
            break;
          
          case "confirm_start_new":
            const startNew = confirm(data.message || "检测到上盘游戏未结束，是否开始新游戏？\n\n" +
              "【确定】开始新游戏\n【取消】继续这盘游戏"
            );
            if (startNew) {
              ws.send(JSON.stringify({ type: "start_new_game",
                "confirmed": true
               }));
            }
            break;

          case "request_trump_rank":
            promptTrump("continue_previous_game");
            break;

          case "deal_start":
            roomStatus.textContent = `🎯 本轮主数：${data.rank_input}，主花色：${data.suit_input}，庄家是“${data.dealer}”，${data.dealer_team === 0 ? 'A' : 'B'}队坐庄`;
            log.textContent += `🎲 开始发牌！主数是 ${data.rank_input}，主花色是 ${data.suit_input}\n`;
            // 重置分数
            teamAScore.textContent = "0";
            teamBScore.textContent = "0";
            break;

          case "deal_ready":
            log.textContent += `✅ 房间 ${data.room_id} 发牌完成！\n`;
            break;

          case "your_hand":
            hand = data.hand;
            log.textContent += `🃏 你的手牌更新（${hand.length} 张）\n`;
            updateHandDisplay();
            break;

          case "your_hidden":
            const hiddenDiv = document.getElementById("hidden");
            hiddenDiv.innerHTML = "";
            data.cards.forEach(card => {
              const el = document.createElement("span");
              if (card === "JOKER1") {
                el.innerHTML = "🃏";
                el.className = "joker-small";
              } else if (card === "JOKER2") {
                el.innerHTML = "🃏";
                el.className = "joker-big";
              } else {
                el.textContent = card;
              }
              hiddenDiv.appendChild(el);
            });
            break;

          case "play_card":
            const cardsHtml = data.cards.map(card => {
              if (card === "JOKER1") {
                return `<span class="card-joker joker-small">🃏</span>`;
              } else if (card === "JOKER2") {
                return `<span class="card-joker joker-big">🃏</span>`;
              } else {
                const suit = card.slice(-1);
                const className = suit === '♥' ? 'card-heart' : 
                                  suit === '♦' ? 'card-diamond' :
                                  suit === '♠' ? 'card-spade' : 'card-club';
                return `<span class="${className}">${card}</span>`;
              }
            }).join(", ");
            playLog.innerHTML += `🕹️ ${data.player_name} 出了牌：${cardsHtml}` + (data.expected_player ? `<br>下一个出牌的玩家是${data.expected_player}` : "") + `\n`;
            // 自动滚动到底部
            playLog.scrollTop = playLog.scrollHeight;
            
            // 只有特定牌型才播放动画
            if (data.celebrate_cue == "siu!!!") {
              playGifAnimation("static/assets/cr7-siuuuuu.gif");
            } else if (data.celebrate_cue == "KING!") {
              playGifAnimation("static/assets/king.gif");
            } else if (data.celebrate_cue == "tractor!") {
              playGifAnimation("static/assets/tractor.gif");
            } else if (data.celebrate_cue == "lulu!") {
              playGifAnimation("static/assets/lulu.gif");
            } else if (data.celebrate_cue == "dragon!!!") {
              playGifAnimation("static/assets/goodnight.gif");
            }
            break;

          case "trick_done":
            playLog.innerHTML += `🎉 本轮 ${data.winner_player_name} 赢得了本轮！${data.winning_team_id} 队获得了 ${data.trick_points} 分！<br>下一个出牌的玩家是${data.winner_player_name}\n`;
            playLog.scrollTop = playLog.scrollHeight;
            // 更新分数
            if (data.result) {
              teamAScore.textContent = data.result[0] || 0;
              teamBScore.textContent = data.result[1] || 0;
            }
            break;

          case "deal_done":
            playLog.innerHTML += `本局已结束！庄家藏牌为${data.hidden}\n庄队获得 ${data.dealer_score} 分\n擂队获得 ${data.challenger_score} 分\n下局庄家 ${data.next_dealer}, 下局主数 ${data.next_trump_rank}\n `;
            playLog.scrollTop = playLog.scrollHeight;
            break;
            
          case "error":
            alert("⚠️ 错误：" + data.message);
            break;

          case "player_leave":
            log.textContent += `👋 ${data.player_name} 离开了房间 ${data.room_id}\n`;
            break;

          default:
            log.textContent += `📩 收到未知类型消息: ${event.data}\n`;
        }

      } catch (e) {
        log.textContent += "📩 非 JSON 消息: " + e.data + "\n";
      }
    };

    /* -------------------- 辅助函数 -------------------- */
    function setNicknameWithPrompt() {
      const nickname = prompt("请输入你的昵称：");
      if (nickname && nickname.trim()) {
        currentNickname = nickname.trim();
        ws.send(JSON.stringify({ type: "set_nickname", nickname: currentNickname }));
        log.textContent += `📛 你设置的昵称是：${currentNickname}\n`;
      }
    }

    function clearLog()     { log.textContent = ""; }
    function clearPlayLog() { playLog.textContent = ""; }

    function sendMessage() {
      const message = messageInput.value.trim();
      if (!message) return;
      
      // 立即在聊天框中显示自己的消息
      addChatMessage(currentNickname || "你", message, true);
      
      // 发送到服务器
      ws.send(JSON.stringify({ type: "message", content: message }));
      
      // 清空输入框并保持焦点
      messageInput.value = "";
      messageInput.focus();
    }

    function handleChatInputKeyPress(event) {
      if (event.key === 'Enter') {
        sendMessage();
      }
    }

    function addChatMessage(sender, content, isSelf) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `message ${isSelf ? 'message-self' : 'message-other'}`;
      
      const senderDiv = document.createElement('div');
      senderDiv.className = 'message-sender';
      senderDiv.textContent = isSelf ? '你' : sender;
      
      const contentDiv = document.createElement('div');
      contentDiv.innerHTML = content
//      contentDiv.textContent = content;
      
      messageDiv.appendChild(senderDiv);
      messageDiv.appendChild(contentDiv);
      chatMessages.appendChild(messageDiv);
      
      // 自动滚动到底部
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function selectTeam(teamId) {
      ws.send(JSON.stringify({ type: "select_team", team_id: teamId }));
    }

    function updateTeam() {
      ws.send(JSON.stringify({ type: "team_update" }));
    }

    function clearTeam() {
      ws.send(JSON.stringify({ type: "clear_team" }));
    }
    
    function onStartGameClick() {
      ws.send(JSON.stringify({ type: "start_new_game" }));
    }
    
    function Ready() {
      ws.send(JSON.stringify({ type: "ready" }));
      log.textContent += "🃏 你准备好了\n";
      //roomStatus.textContent = "🃏 已准备，等待其他玩家...";
    }

    function continueGame() {
      ws.send(JSON.stringify({ type: "continue_previous_game" }));
    }

    function promptTrump(type) {
      const rank = prompt("请选择本局的主数（例如 2~A）");
      if (!rank || !["2","4","6","7","8","9","10","J","Q","K","A"].includes(rank.toUpperCase())) {
        alert("无效主数！"); return;
      }
      const suits = ["♠","♥","♣","♦"];
      const suit = suits[Math.floor(Math.random() * 4)];
      alert("系统随机抽取的主花色是：" + suit);
      ws.send(JSON.stringify({ type: type, rank_input: rank.toUpperCase(), suit_input: suit }));
    }

    function updateHandDisplay() {
      handDiv.innerHTML = "";
      const row1 = document.createElement("div"); row1.className = "card-row";
      const row2 = document.createElement("div"); row2.className = "card-row";

      const half = Math.ceil(hand.length / 2);
      const firstRowCards  = hand.slice(0, half);
      const secondRowCards = hand.slice(half);

      firstRowCards.forEach((card, idx) => row1.appendChild(createCardElement(card, idx)));
      secondRowCards.forEach((card, idx) => row2.appendChild(createCardElement(card, idx + half)));

      handDiv.appendChild(row1);
      handDiv.appendChild(row2);
    }

    function createCardElement(card, index) {
      const cardEl = document.createElement("div"); cardEl.className = "card";
      
      let rank, suit;
      
      // Handle JOKER cards specially
      if (card === "JOKER1") {
        // Create a large joker emoji for the entire card
        cardEl.classList.add("joker", "joker-small");
        cardEl.setAttribute('data-suit', 'joker1');
        cardEl.innerHTML = '<div class="joker-emoji">🃏</div>';
      } else if (card === "JOKER2") {
        // Create a large joker emoji for the entire card
        cardEl.classList.add("joker", "joker-big");
        cardEl.setAttribute('data-suit', 'joker2');
        cardEl.innerHTML = '<div class="joker-emoji">🃏</div>';
      } else {
        // Handle regular cards
        rank = card.slice(0, -1);
        suit = card.slice(-1);
        if (['♥','♦','♠','♣'].includes(suit)) cardEl.setAttribute('data-suit', suit);
        
        const rankEl = document.createElement("div"); rankEl.className = "card-rank"; rankEl.textContent = rank;
        const suitEl = document.createElement("div"); suitEl.className = "card-suit"; suitEl.textContent = suit;
        cardEl.appendChild(rankEl); cardEl.appendChild(suitEl);
      }

      cardEl.style.zIndex = index;
      cardEl.onclick = () => cardEl.classList.toggle("selected");
      return cardEl;
    }

    function sendPlay() {
      const selectedCards = [];
      document.querySelectorAll(".card.selected").forEach(card => {
        // Check if it's a joker card
        if (card.classList.contains("joker-small")) {
          selectedCards.push("JOKER1");
        } else if (card.classList.contains("joker-big")) {
          selectedCards.push("JOKER2");
        } else {
          // For regular cards, get rank and suit from elements
          const rank = card.querySelector(".card-rank").textContent;
          const suit = card.querySelector(".card-suit").textContent;
          selectedCards.push(rank + suit);
        }
      });
      if (selectedCards.length === 0) { alert("请先选择要出的牌！"); return; }
      ws.send(JSON.stringify({ type: "play_card", cards: selectedCards }));
      document.querySelectorAll(".card.selected").forEach(card => card.classList.remove("selected"));
    }

    function hideCards() {
      const selectedCards = [];
      document.querySelectorAll(".card.selected").forEach(card => {
        // Check if it's a joker card
        if (card.classList.contains("joker-small")) {
          selectedCards.push("JOKER1");
        } else if (card.classList.contains("joker-big")) {
          selectedCards.push("JOKER2");
        } else {
          // For regular cards, get rank and suit from elements
          const rank = card.querySelector(".card-rank").textContent;
          const suit = card.querySelector(".card-suit").textContent;
          selectedCards.push(rank + suit);
        }
      });
      // if (selectedCards.length !== 8) { alert="请选择恰好 8 张牌作为底牌！"; return; }
      ws.send(JSON.stringify({ type: "hide_cards", cards: selectedCards }));
      document.querySelectorAll(".card.selected").forEach(card => card.classList.remove("selected"));
    }

    // GIF动画控制
    function playGifAnimation(gifPath, duration = 1800) {
      const gifOverlay = document.getElementById('gif-overlay');
      const gifImg = document.getElementById('gif-animation');
      
      // 设置新的GIF路径
      if (gifPath) {
        gifImg.src = gifPath;
      }
      
      // 显示动画
      gifOverlay.classList.add('show');
      
      // 重置GIF动画（通过重新设置src）
      const originalSrc = gifImg.src;
      gifImg.src = '';
      gifImg.src = originalSrc;
      
      // 指定时长后隐藏动画
      setTimeout(() => {
        gifOverlay.classList.remove('show');
      }, duration);
    }

    // 下拉菜单控制
    function toggleDropdown() {
      document.getElementById("team-dropdown").closest('.dropdown').classList.toggle('active');
    }

    function closeDropdown() {
      document.getElementById("team-dropdown").closest('.dropdown').classList.remove('active');
    }

    // 点击外部关闭下拉菜单
    document.addEventListener('click', function(event) {
      const dropdown = document.querySelector('.dropdown');
      if (dropdown && !dropdown.contains(event.target)) {
        dropdown.classList.remove('active');
      }
    });