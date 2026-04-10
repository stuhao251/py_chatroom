import os
import json
import base64
import socket
import threading
import requests
from datetime import datetime
from server.config import HTTP_BASE, SOCKET_HOST, SOCKET_PORT

#客户端的登录请求
def http_requests_login(login_name, password):
    resp = requests.post(
        f"{HTTP_BASE}/login",
        json={"login_name": login_name, "password": password}
    ).json()
    print("客户端登录请求：", resp)

    return resp

# 客户端的添加好友请求
def http_requests_add_friend(user_id, friend_name):
    resp = requests.post(
        f"{HTTP_BASE}/add_friend",
        json={"user_id": user_id, "friend_login_name": friend_name}
    ).json()
    print("客户端添加好友请求：", resp)

    return resp

# 客户端的删除好友请求
def http_requests_delete_friend(user_id, friend_name):
    resp = requests.post(
        f"{HTTP_BASE}/delete_friend",
        json={"user_id": user_id, "friend_login_name": friend_name}
    ).json()
    print("客户端删除好友请求：", resp)

    return resp

# 客户端的获取好友列表请求
def http_requests_get_friends(user_id):
    resp = requests.get(f"{HTTP_BASE}/friends/{user_id}").json()
    print("客户端获取好友列表请求：", resp)

    return resp

# 客户端的获取群聊列表请求
def http_requests_get_groups(user_id):
    resp = requests.get(f"{HTTP_BASE}/groups/{user_id}").json()
    print("客户端获取群聊列表请求：", resp)

    return resp

# 客户端的创建群聊列表请求
def http_requests_create_groups(user_id, group_name):

    resp = requests.post(
        f"{HTTP_BASE}/create_group",
        json={"user_id": user_id, "group_name": group_name}
    ).json()
    print("客户端创建群聊列表请求：", resp)

    return resp


# 客户端的加入群聊列表请求
def http_requests_join_groups(user_id, group_name):
    resp = requests.post(
        f"{HTTP_BASE}/join_group",
        json={"user_id": user_id, "group_name": group_name}
    ).json()
    print("客户端加入群聊列表请求：", resp)

    return resp

# 客户端的删除群聊列表请求
def http_requests_delete_group(user_id, group_name):
    return requests.post(
        f"{HTTP_BASE}/delete_group",
        json={"user_id": user_id, "group_name": group_name}
    ).json()

# 客户端的退出群聊列表请求
def http_requests_quit_group(user_id, group_name):
    return requests.post(
        f"{HTTP_BASE}/quit_group",
        json={"user_id": user_id, "group_name": group_name}
    ).json()