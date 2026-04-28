import os
import sys
import json
import base64
import socket
import threading
from datetime import datetime

from config import SOCKET_HOST, SOCKET_PORT
from databsase import query_all, query_one,execute

online_users = {}  # user_id -> conn
ui_event_handler = None


def set_ui_event_handler(handler):
    global ui_event_handler
    ui_event_handler = handler


def emit_ui_event(event):  #event是一个字典格式
    if ui_event_handler:
        try:
            ui_event_handler(event)
        except Exception as e:
            print("推送UI事件失败:", e)


def get_user_name_by_id(user_id):
    row = query_one(
        "SELECT login_name, nickname FROM users WHERE id=%s",
        (user_id,)
    )
    if row:
        return f"{row[1]}({row[0]})"
    return f"用户{user_id}"


def get_group_name_by_id(group_id):
    row = query_one(
        "SELECT group_name FROM chat_groups WHERE id=%s",
        (group_id,)
    )
    if row:
        return row[0]
    return f"群聊{group_id}"


def get_message_preview(data):
    content_type = data.get("content_type", "text")
    content = data.get("content", "")
    file_name = data.get("file_name", "")

    if content_type == "text":
        return content

    if file_name:
        return file_name

    if content_type == "image":
        return "[图片]"

    if content_type == "file":
        return "[文件]"

    if content_type == "emoji":
        return "[表情]"

    return "[消息]"



#判断是不是朋友
def is_friend(user_id, target_id):
    row = query_one(
        "SELECT 1 FROM friends WHERE user_id=%s AND friend_id=%s",
        (user_id, target_id)
    )
    return row is not None
#判断群聊是否存在
def group_exists(group_id):
    row = query_one(
        "SELECT 1 FROM chat_groups WHERE id=%s",
        (group_id,)
    )
    return row is not None

def sever_send_json(conn, data):
    try:
        msg = json.dumps(data, ensure_ascii=False) + "\n"
        conn.sendall(msg.encode("utf-8"))
    except Exception as e:
        print(e)

def server_recv_json(conn_file):
    try:
        line = conn_file.readline()
        if not line:
            return None
        return json.loads(line.strip())
    # 捕获客户端正常断开的常见异常，不打印错误
    except Exception:
        return None


def broadcast_to_group(group_id, message, exclude_user_id=None):
    try:
        rows = query_all("SELECT user_id FROM group_members WHERE group_id=%s", (group_id,))
        for row in rows:
            uid = row[0]
            if exclude_user_id is not None and uid == exclude_user_id:
                continue
            target_conn = online_users.get(uid)
            if target_conn:
                try:
                    sever_send_json(target_conn, message)
                except Exception:
                    pass
    except Exception as e:
        print(e)

def handle_client(conn, addr):
    print(f"客户端连接: {addr}")
    conn_file = conn.makefile("r", encoding="utf-8")
    current_user_id = None
    current_user_name = None

    try:
        while True:
            data = server_recv_json(conn_file)
            if not data:
                break
            msg_type = data.get("type")

            if msg_type == "login_socket":
                user_id = int(data["user_id"])
                user_name = str(data["user_name"])
                user_nickname = str(data["user_nick_name"])

                # 防重复登录
                if user_id in online_users:
                    sever_send_json(conn, {
                        "type": "system",
                        "message": "该账号已在线，禁止重复登录"
                    })
                    conn.close()
                    return

                current_user_id = user_id
                current_user_name = user_name
                online_users[user_id] = conn

                #向数据库更新用户登录状态
                execute("UPDATE users SET is_online=1 WHERE id=%s", (user_id,))
                sever_send_json(conn, {"type": "system", "message": "socket连接成功"})
                print(f"用户上线: {user_id}, 账号: {user_name}, 用户昵称: {user_nickname}")

                emit_ui_event({
                    "type": "login",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "text": f"用户上线：{user_nickname}，账号：{user_name}，用户ID：{user_id}",
                    "online_count": len(online_users)
                })

            elif msg_type == "private_message":
                from_user_id = int(data["from_user_id"])
                target_id = int(data["to_user_id"])

                # 发送消息前-校验好友关系
                if not is_friend(from_user_id, target_id):
                    sever_send_json(conn, {
                        "type": "system",
                        "message": "和对方不是好友，无法发送消息"
                    })
                    continue

                payload = {
                    "type": "private_message",
                    "from_user_id": data["from_user_id"],
                    "from_username": data["from_username"],
                    "content_type": data["content_type"],    # text/image/file/emoji
                    "content": data["content"],
                    "file_name": data.get("file_name", ""),
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                target_conn = online_users.get(target_id)

                emit_ui_event({
                    "type": "private",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "text": (
                        f"私聊：{get_user_name_by_id(from_user_id)} "
                        f"发送给 {get_user_name_by_id(target_id)}，"
                        f"内容：{get_message_preview(data)}，"
                        f"状态：{'已发送' if target_conn else '对方离线'}"
                    ),
                    "online_count": len(online_users)
                })

                if target_conn:
                    sever_send_json(target_conn, payload)

            elif msg_type == "group_message":
                group_id = int(data["group_id"])
                from_user_id = int(data["from_user_id"])

                #群聊天时判断
                if not group_exists(group_id):
                    sever_send_json(conn, {
                        "type": "system",
                        "message": "该群聊已被删除，无法发送消息",
                        "chat_type": "group",
                        "target_id": group_id})
                    continue

                #封装格式
                payload = {
                    "type": "group_message",
                    "group_id": group_id,
                    "from_user_id": data["from_user_id"],
                    "from_username": data["from_username"],
                    "content_type": data["content_type"],
                    "content": data["content"],
                    "file_name": data.get("file_name", ""),
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                emit_ui_event({
                    "type": "group",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "text": (
                        f"群聊：{get_group_name_by_id(group_id)}，"
                        f"发送人：{get_user_name_by_id(from_user_id)}，"
                        f"内容：{get_message_preview(data)}"
                    ),
                    "online_count": len(online_users)
                })

                broadcast_to_group(group_id, payload, exclude_user_id=from_user_id)

            elif msg_type == "logout_socket":
                user_id = int(data["user_id"])

                if user_id in online_users:
                    del online_users[user_id]

                emit_ui_event({
                    "type": "logout",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "text": f"用户退出登录：{get_user_name_by_id(user_id)}",
                    "online_count": len(online_users)
                })

                print(f"用户 {user_id} 已退出登录")
                break

    except Exception as e:
        print("连接异常:", e)

    finally:
        if current_user_id and current_user_id in online_users:
            del online_users[current_user_id]

            emit_ui_event({
                "type": "logout",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": f"用户下线：{get_user_name_by_id(current_user_id)}",
                "online_count": len(online_users)
            })

            print(f"用户下线: {current_user_id}, 账号: {current_user_name}")

        # 更新数据库-用户离线
        if current_user_id:
            try:
                execute("UPDATE users SET is_online=0 WHERE id=%s", (current_user_id,))
            except Exception as e:
                print("更新离线状态失败:", e)
        conn.close()


def start_server():
    try:
        execute("UPDATE users SET is_online=0")  # 启动时清空在线状态
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 允许端口快速复用，避免刚关闭又启动时报端口占用
        server.bind((SOCKET_HOST, SOCKET_PORT))
        server.listen(100)
        print(f"Socket server running at {SOCKET_HOST}:{SOCKET_PORT}")

        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

    except Exception as e:
        print(e)




if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("服务器手动关闭")
        sys.exit(0)
    except Exception as e:
        print("服务器异常退出:", e)
        sys.exit(1)