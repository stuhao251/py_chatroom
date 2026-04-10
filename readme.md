
# 💬 Python Chat Room（即时通讯聊天系统）

一个基于 **Python + Tkinter + Socket + HTTP + MySQL + 阿里云OSS** 实现的桌面端即时通讯系统，支持私聊、群聊、图片发送、表情、未读消息提示等功能，UI 风格参考微信。

---

## 🚀 项目特点

* ✅ 私聊 / 群聊实时通信（Socket）
* ✅ 登录 / 注册 / 修改个人信息（HTTP + MySQL）
* ✅ 好友管理（添加 / 删除）
* ✅ 群聊管理（创建 / 加入 / 退出 / 删除）
* ✅ 表情面板（自定义 emoji 选择）
* ✅ 图片发送与展示（Base64 + Tkinter 渲染）
* ✅ 未读消息红点提示
* ✅ 会话隔离（不同聊天对象独立缓存）
* ✅ 系统消息提示（删除好友 / 群聊等）
* ✅ 头像上传（阿里云 OSS 存储）

---

## 🧱 技术架构

### 整体架构

```
客户端（Tkinter GUI）
    ↓ HTTP（登录 / 注册 / 数据操作）
HTTP Server（Flask）
    ↓
MySQL 数据库



客户端
    ↓ Socket（实时通信）
Socket Server
```

---

## 🛠 技术栈

### 后端

* Python
* Flask（HTTP服务）
* Socket（长连接通信）
* MySQL（数据存储）

### 前端（桌面）

* Tkinter（GUI界面）
* Pillow（图片处理）

### 存储

* 阿里云 OSS（头像存储）

---

## 📂 项目结构（简化）

```
client/
│
├── client.py                  # 主客户端逻辑
├── login_window.py            # 登录界面
├── register_window.py         # 注册界面
├── main_window.py             # 主界面（微信风格UI）
├── update_info_window.py      # 修改个人信息页面
├── client_http_services.py    # HTTP请求封装
├── socket_service.py          # Socket通信封装
└── message_service.py         # 消息缓存 & 未读管理

server/
│
├── http_server.py             # Flask接口
├── socket_server.py           # Socket服务
└── database.py                # 数据库操作

```

---

## 📌 核心功能说明

### 🔐 登录 / 注册（HTTP）

* 使用 Flask 提供 REST API
* 密码加密存储（hash）
* 登录成功后返回用户信息

---

### 💬 实时聊天（Socket）

* 使用 TCP Socket 长连接
* 支持：

  * 私聊（point-to-point）
  * 群聊（broadcast）


---

### 🧑‍🤝‍🧑 好友系统

* 添加好友（双向关系）
* 删除好友（双向删除）
* 删除后：

  * 禁止继续发送消息
  * 客户端收到系统提示

---

### 👥 群聊系统

支持：

* 创建群聊
* 加入群聊
* 退出群聊
* 删除群聊（仅群主）

消息发送时服务端校验：

```python
群是否存在
用户是否在群中
```

否则返回：

```
[系统] 群聊已被删除 / 你已不在该群
```

---

### 🖼 图片发送

流程：

1. 客户端选择图片
2. 转为 Base64 编码
3. 通过 Socket 发送
4. 接收端解码并显示（Tkinter Text + image_create）

---

### 😊 表情系统

* 自定义 Emoji 面板（Toplevel窗口）
* 点击表情直接发送
* 表情作为文本处理

---

### 🔴 未读消息

* 每个会话维护未读计数
* 切换会话自动清零
* UI 显示红点提示

---

### 🧠 会话缓存机制（重点）

使用：

```python
chat_cache = {
    "private_1001": [...],
    "group_2001": [...]
}
```

实现：

* 不同聊天对象消息隔离
* 切换聊天自动加载历史内容

---

### 🖼 头像上传（OSS）

* 用户上传头像
* 服务端上传至阿里云 OSS
* 数据库存储 `object_key`
* 前端通过 URL 加载头像

---

## ⚠️ 关键设计点

### 1️⃣ HTTP + Socket 分离

| 功能             | 协议     |
| -------------- | ------ |
| 登录 / 注册 / 数据操作 | HTTP   |
| 聊天消息           | Socket |

---

### 2️⃣ 客户端本地缓存

* 提高聊天切换体验
* 支持未读消息统计

---

### 3️⃣ 服务端权限校验

* 防止：

  * 非好友聊天
  * 非群成员发消息
  * 群已删除仍发送

---

### 4️⃣ UI 解耦设计

将客户端拆分为：

* client（逻辑）
* main_window（UI）
* socket_service（通信）

降低耦合度

---

## 📸 界面展示

* 登录页
* ![fig_login.png](figs/fig_login.png)
* 注册页
* ![fig_register.png](figs/fig_register.png)
* 主界面
* ![fig_main.png](figs/fig_main.png)



---

## 📸 运行流程

* 数据库--提前创建对应数据库
* 服务端--开启http_server  socket_server
* 客户端--多应用开启client


---
## 🚧 后续可优化方向

* ⏳ 离线消息（未实现）
* 📦 添加好友需确认
* 🔔 消息通知系统
* 🧾 聊天记录持久化（数据库）
* 🎨 UI 和交互动画优化（更接近微信）
* 📦 代码逻辑进一步解耦，面向工程化
---

