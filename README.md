# 红五冲冲冲 🔥🃏
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SClAr36/RedFive)

一个使用 Python 后端 + WebSocket 通信 + HTML 前端 构建的多人在线托撮牌游戏 —— 红五！

## 🎮 项目介绍

红五是一款四人对抗类升级托撮牌游戏。本项目实现了红五游戏的完整流程，包括：

* 分队与发牌
* 主牌设定与底牌藏牌
* 出牌与轮次判定
* 得分与胜负结算
* 聊天系统与游戏日志

前端通过 WebSocket 与 Python 后端实时通信，支持多人同步在线操作。

---

## 🌟 功能亮点

* 实时 WebSocket 通信
* 玩家昵称、队伍、准备状态管理
* 手牌展示与交互选牌
* 底牌隐藏与出牌逻辑
* 出牌记录与实时得分显示
* 游戏聊天功能
* 抽弧式游戏日志面板

---

## 🚀 快速启动方式

### 1. 安装依赖

确保你已安装 Python 3.7+ 以及 `websockets` 包：

```bash
pip install websockets
```

### 2. 启动服务器

在项目根目录下运行：

```bash
python main.py
```

默认监听地址为 `ws://localhost:8765`

### 3. 本地启动前端

直接用浏览器打开 `client.html` 文件即可

### 4. 远程联机环境

如果想远程联机游戏，需要确保:

* 服务器机启动 `main.py`
* 打开 8765 端口，确保其可供外部 WebSocket 连接
* 修改 `client.html`中 WebSocket 地址：

```javascript
const ws = new WebSocket("ws://<server_ip>:8765");
```

其中 `<server_ip>` 是服务器的公网 IP 或内网 IP

如果服务器有 HTTPS/网站配置，请考虑使用 nginx 转发 WebSocket 连接

---

## 📌 游戏说明

1. 玩家访问前端页面后自动连接服务器
2. 设置昵称后，点击加入队伍 A / B
3. 所有玩家准备完毕后，发起发牌并随机设置主花色
4. 玩家出牌、赢牌、得分自动更新
5. 可通过日志与聊天面板查看游戏记录与实时交流

---

## 📄 TODO / 已知问题

* 支持完整游戏逻辑判断(从2打到A)
* 房间超时与重连机制
* 完善多房间并行

---

## 🙌 项目成员

- [@SClAr36](https://github.com/SClAr36) — 项目负责人 & 后端开发 & 前端框架
- [@lvxj99](https://github.com/lvxj99) — 前端开发与界面设计
- [@dreamthreebs](https://github.com/dreamthreebs) — 测试与质量保证（QA）  