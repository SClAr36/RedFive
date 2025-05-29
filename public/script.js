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
    roomStatus.textContent = "🎲 欢迎加入红五冲冲冲游戏！请设置昵称并准备";

    ws.onopen  = () => { log.textContent += "✅ 已连接服务器\n"; };
    ws.onclose = () => { log.textContent += "🔌 连接关闭\n"; };

    let hand = [];
    let currentNickname = '';

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "welcome":
            log.textContent  = `欢迎加入房间 ${data.room_id}，${data.player_id}，你是玩家 ${data.player_number}\n`;
            roomStatus.textContent = `👋 欢迎加入房间 ${data.room_id}，你是玩家 ${data.player_number}`;
            break;

          case "player_join":
            log.textContent += `👤 玩家${data.player_id} (玩家${data.player_number}) 加入了房间 ${data.room_id}\n`;
            break;

          case "nickname_set":
            log.textContent += `📛 玩家${data.player_id} (玩家${data.player_number}) 设置昵称为 ${data.nickname}\n`;
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
            // const teamA = [];
            // const teamB = [];
            //寻找每个玩家所属队伍
            // data.players.forEach(p => {
              // if (p.player_team === 0) {
                // teamA.push(p.player_name);
              // } else {
                // teamB.push(p.player_name);
              // }
            // });
            //更新分队信息
            // const msg = `分队完成：<br>
            // 🟥 队A成员：${teamA.join('，')}<br>
            // 🟦 队B成员：${teamB.join('，')}`;
            // addChatMessage("系统", msg, false);
            //附加一条更新玩家编号的广播
            // const numMsg = data.players
              // .map(p => {
                // const color = (p.player_number % 2 === 0) ? '#FF8A80' : '#7CAEFF';
                // const bullet = `<span style="color:${color}">●</span>`;
                // return `${bullet} ${p.player_name} ➜ 玩家 ${p.player_number}`;
              // })
              // .join("<br>");
            // addChatMessage("系统", `更新后的玩家序号为：<br>${numMsg}`, false);
            // break;

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
            roomStatus.textContent = `🎯 本轮主数：${data.rank_input}，主花色：${data.suit_input}`;
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
              el.textContent = card + " ";
              hiddenDiv.appendChild(el);
            });
            break;

          case "play_card":
            const cardsHtml = data.cards.map(card => {
              const suit = card.slice(-1);
              const className = suit === '♥' ? 'card-heart' : 
                                suit === '♦' ? 'card-diamond' :
                                suit === '♠' ? 'card-spade' : 'card-club';
              return `<span class="${className}">${card}</span>`;
            }).join(", ");
            playLog.innerHTML += `🕹️ ${data.player_name} 出了牌：${cardsHtml}<br>下一个出牌的玩家是${data.expected_player}\n`;
            
            // 只有特定牌型（AAK, KKA, QQK, KKQ）才播放动画
            if (isSpecialCardPattern(data.cards)) {
              playGifAnimation();
            }
            break;

          case "trick_done":
            playLog.innerHTML += `🎉 本轮 玩家 ${data.winner_player_number} 赢得了本轮！${data.winning_team_id} 队获得了 ${data.trick_points} 分！\n`;
            // 更新分数
            if (data.result) {
              teamAScore.textContent = data.result[0] || 0;
              teamBScore.textContent = data.result[1] || 0;
            }
            break;

          case "deal_done":
            playLog.innerHTML += `本局已结束！庄家藏牌为${data.hidden}\n庄队获得 ${data.dealer_score} 分\n擂队获得 ${data.challenger_score} 分\n下局庄家 ${data.next_dealer}, 下局主数 ${data.next_trump_rank}\n `;
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
      const rank = card.slice(0, -1); const suit = card.slice(-1);

      const rankEl = document.createElement("div"); rankEl.className = "card-rank"; rankEl.textContent = rank;
      const suitEl = document.createElement("div"); suitEl.className = "card-suit"; suitEl.textContent = suit;

      cardEl.appendChild(rankEl); cardEl.appendChild(suitEl);
      if (['♥','♦','♠','♣'].includes(suit)) cardEl.setAttribute('data-suit', suit);

      cardEl.style.zIndex = index;
      cardEl.onclick = () => cardEl.classList.toggle("selected");
      return cardEl;
    }

    function sendPlay() {
      const selectedCards = [];
      document.querySelectorAll(".card.selected").forEach(card => {
        const rank = card.querySelector(".card-rank").textContent;
        const suit = card.querySelector(".card-suit").textContent;
        selectedCards.push(rank + suit);
      });
      if (selectedCards.length === 0) { alert("请先选择要出的牌！"); return; }
      ws.send(JSON.stringify({ type: "play_card", cards: selectedCards }));
      document.querySelectorAll(".card.selected").forEach(card => card.classList.remove("selected"));
    }

    function hideCards() {
      const selectedCards = [];
      document.querySelectorAll(".card.selected").forEach(card => {
        const rank = card.querySelector(".card-rank").textContent;
        const suit = card.querySelector(".card-suit").textContent;
        selectedCards.push(rank + suit);
      });
      // if (selectedCards.length !== 8) { alert="请选择恰好 8 张牌作为底牌！"; return; }
      ws.send(JSON.stringify({ type: "hide_cards", cards: selectedCards }));
      document.querySelectorAll(".card.selected").forEach(card => card.classList.remove("selected"));
    }

    // GIF动画控制
    function playGifAnimation() {
      const gifOverlay = document.getElementById('gif-overlay');
      const gifImg = document.getElementById('gif-animation');
      
      // 显示动画
      gifOverlay.classList.add('show');
      
      // 重置GIF动画（通过重新设置src）
      const originalSrc = gifImg.src;
      gifImg.src = '';
      gifImg.src = originalSrc;
      
      // 1.3秒后隐藏动画
      setTimeout(() => {
        gifOverlay.classList.remove('show');
      }, 1300);
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

    // 检查是否为特定牌型（AAK, KKA, QQK, KKQ）
    function isSpecialCardPattern(cards) {
      if (cards.length !== 3) return false;
      
      // 提取牌面值（去掉花色）
      const ranks = cards.map(card => card.slice(0, -1)).sort();
      
      // 检查是否为指定的牌型组合
      const pattern = ranks.join('');
      const specialPatterns = ['AAK', 'AKK', 'KQQ', 'QQK'];
      
      return specialPatterns.includes(pattern);
    }