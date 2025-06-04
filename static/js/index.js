const ws = new WebSocket("ws://localhost:8765");

ws.onopen = () => {
  ws.send(JSON.stringify({ type: "list_rooms" }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "room_list") {
    const container = document.getElementById("room-list");
    if (data.rooms.length === 0) {
      container.innerHTML = "<p>当前暂无房间，您可以创建一个。</p>";
      return;
    }
    container.innerHTML = "<h3><span class='emoji'>📜</span> 可加入房间：</h3>";
    data.rooms.forEach(room => {
      const btn = document.createElement("button");
      btn.innerHTML = `<span class="emoji">🃏</span> ${room.room_name}（ID: ${room.room_id.slice(0, 8)}）`;
      btn.onclick = () => joinRoom(room.room_id);
      container.appendChild(btn);
    });
  }

  if (data.type === "room_created") {
    localStorage.setItem("chosen_room_id", data.room_id);
    window.location.href = "client.html";
  }

  if (data.type === "error") {
    alert("❌ 错误：" + data.message);
  }
};

function createRoom() {
  const name = prompt("请为新房间输入一个名称（例如\"大乱斗房\"）");
  if (!name || !name.trim()) {
    alert("房间名称不能为空！"); //TODO：可以为空，若空则不返回名称
    return;
  }
  ws.send(JSON.stringify({ type: "create_room", room_name: name.trim() }));
}

function joinRoom(roomId) {
  localStorage.setItem("chosen_room_id", roomId);
  window.location.href = "client.html";
}

function autoJoin() {
  localStorage.setItem("chosen_room_id", "AUTO");
  window.location.href = "client.html";
}
