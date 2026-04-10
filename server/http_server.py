from flask import Flask, request, jsonify
import hashlib

from databsase import query_one, query_all, execute, insert_and_get_id
from config import HTTP_HOST, HTTP_PORT, OSS_BUCKET_DOMAIN
from oss_utils import upload_avatar_to_oss

app = Flask(__name__)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def build_avatar_url(avatar_object_key: str):
    if not avatar_object_key:
        return None
    return f"{OSS_BUCKET_DOMAIN}/{avatar_object_key}"

#检查用户名是否存在接口
@app.route("/check_login_name", methods=["GET"])
def check_login_name():
    login_name = request.args.get("login_name", "").strip()

    if not login_name:
        return jsonify({"code": 1, "msg": "登录名不能为空"})

    if not login_name.isdigit():
        return jsonify({"code": 1, "msg": "登录名只能是数字"})

    user = query_one("SELECT id FROM users WHERE login_name=%s", (login_name,))
    if user:
        return jsonify({"code": 1, "msg": "该登录名已存在", "available": False})

    return jsonify({"code": 0, "msg": "该登录名可用", "available": True})

#注册用户的接口
@app.route("/register", methods=["POST"])
def register():
    login_name = request.form.get("login_name", "").strip()
    nickname = request.form.get("nickname", "").strip()
    gender = request.form.get("gender", "男").strip()
    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    avatar = request.files.get("avatar")

    if not login_name or not nickname or not password or not confirm_password:
        return jsonify({"code": 1, "msg": "请完整填写注册信息"})

    if not login_name.isdigit():
        return jsonify({"code": 1, "msg": "登录名只能输入数字"})

    if len(login_name) < 1 or len(login_name) > 10:
        return jsonify({"code": 1, "msg": "登录名长度必须为1到10位"})

    if gender not in ("男", "女"):
        return jsonify({"code": 1, "msg": "性别参数错误"})

    if password != confirm_password:
        return jsonify({"code": 1, "msg": "两次输入的密码不一致"})

    exists = query_one("SELECT id FROM users WHERE login_name=%s", (login_name,))
    if exists:
        return jsonify({"code": 1, "msg": "该登录名已存在"})

    avatar_object_key = None
    if avatar and avatar.filename:
        try:
            avatar_object_key = upload_avatar_to_oss(avatar)
        except Exception as e:
            return jsonify({"code": 1, "msg": f"头像上传失败: {str(e)}"})

    password_hash = hash_password(password)

    user_id = insert_and_get_id(
        """
        INSERT INTO users(login_name, nickname, gender, password_hash, avatar_object_key)
        VALUES(%s, %s, %s, %s, %s)
        """,
        (login_name, nickname, gender, password_hash, avatar_object_key)
    )

    return jsonify({
        "code": 0,
        "msg": "注册成功",
        "data": {
            "user_id": user_id,
            "login_name": login_name,
            "avatar_object_key": avatar_object_key,
            "avatar_url": build_avatar_url(avatar_object_key)
        }
    })

#查看个人用户的接口
@app.route("/user_info/<int:user_id>", methods=["GET"])
def get_user_info(user_id):
    user = query_one(
        """
        SELECT id, login_name, nickname, gender, avatar_object_key
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    if not user:
        return jsonify({"code": 1, "msg": "用户不存在"})

    return jsonify({
        "code": 0,
        "msg": "获取用户信息成功",
        "data": {
            "user_id": user[0],
            "login_name": user[1],
            "nickname": user[2],
            "gender": user[3],
            "avatar_object_key": user[4],
            "avatar_url": build_avatar_url(user[4])
        }
    })

#更新个人信息的接口
@app.route("/update_user_info", methods=["POST"])
def update_user_info():
    user_id = request.form.get("user_id", "").strip()
    nickname = request.form.get("nickname", "").strip()
    gender = request.form.get("gender", "").strip()
    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    avatar = request.files.get("avatar")

    if not user_id:
        return jsonify({"code": 1, "msg": "用户ID不能为空"})

    user = query_one(
        """
        SELECT id, login_name, nickname, gender, avatar_object_key
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )
    if not user:
        return jsonify({"code": 1, "msg": "用户不存在"})

    old_login_name = user[1]
    old_nickname = user[2]
    old_gender = user[3]
    old_avatar_object_key = user[4]

    # 昵称为空则保持原值
    if not nickname:
        nickname = old_nickname

    # 性别为空则保持原值
    if not gender:
        gender = old_gender

    if gender not in ("男", "女"):
        return jsonify({"code": 1, "msg": "性别参数错误"})

    password_hash = None
    if password or confirm_password:
        if password != confirm_password:
            return jsonify({"code": 1, "msg": "两次输入的密码不一致"})
        if not password:
            return jsonify({"code": 1, "msg": "密码不能为空"})
        password_hash = hash_password(password)

    avatar_object_key = old_avatar_object_key
    if avatar and avatar.filename:
        try:
            avatar_object_key = upload_avatar_to_oss(avatar)
        except Exception as e:
            return jsonify({"code": 1, "msg": f"头像上传失败: {str(e)}"})

    if password_hash is not None:
        execute(
            """
            UPDATE users
            SET nickname=%s, gender=%s, password_hash=%s, avatar_object_key=%s
            WHERE id=%s
            """,
            (nickname, gender, password_hash, avatar_object_key, user_id)
        )
    else:
        execute(
            """
            UPDATE users
            SET nickname=%s, gender=%s, avatar_object_key=%s
            WHERE id=%s
            """,
            (nickname, gender, avatar_object_key, user_id)
        )

    return jsonify({
        "code": 0,
        "msg": "个人信息修改成功",
        "data": {
            "user_id": int(user_id),
            "login_name": old_login_name,
            "nickname": nickname,
            "gender": gender,
            "avatar_object_key": avatar_object_key,
            "avatar_url": build_avatar_url(avatar_object_key)
        }
    })

#用户登录的接口
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    login_name = data.get("login_name", "").strip()
    password = data.get("password", "").strip()

    password_hash = hash_password(password)

    user = query_one(
        """
        SELECT id, login_name, nickname, gender, avatar_object_key,is_online
        FROM users
        WHERE login_name=%s AND password_hash=%s
        """,
        (login_name, password_hash)
    )

    if not user:
        return jsonify({"code": 1, "msg": "登录名或密码错误"})
    if user[5] == 1:
        return jsonify({"code": 1, "msg": "该用户已经在线"})

    avatar_object_key = user[4]

    return jsonify({
        "code": 0,
        "msg": "登录成功",
        "data": {
            "user_id": user[0],
            "login_name": user[1],
            "nickname": user[2],
            "gender": user[3],
            "avatar_object_key": avatar_object_key,
            "avatar_url": build_avatar_url(avatar_object_key)
        }
    })


#添加朋友的接口
@app.route("/add_friend", methods=["POST"])
def add_friend():
    data = request.json

    user_id = data.get("user_id")
    friend_login_name = data.get("friend_login_name", "").strip()

    if not user_id or not friend_login_name:
        return jsonify({"code": 1, "msg": "参数不完整"})
    if not friend_login_name.isdigit():
        return jsonify({"code": 1, "msg": "好友登录用户名只能是数字"})

    #1 先查出要添加的好友用户信息
    friend = query_one(
        "SELECT id, login_name, nickname, gender, avatar_object_key FROM users WHERE login_name=%s",
        (friend_login_name,)
    )
    if not friend:
        return jsonify({"code": 1, "msg": "该用户不存在"})

    friend_id = friend[0]

    #2 不能添加自己
    if int(user_id) == int(friend_id):
        return jsonify({"code": 1, "msg": "不能添加自己"})

    #3 查询是否已经是好友（判断 friends 表是否存在关系）
    is_friend = query_one(
        "SELECT 1 FROM friends WHERE user_id = %s AND friend_id = %s",
        (user_id, friend_id)
    )
    if is_friend:
        return jsonify({"code": 1, "msg": "已经添加过该好友"})

    #4 双向添加好友
    execute("INSERT IGNORE INTO friends(user_id, friend_id) VALUES(%s, %s)", (user_id, friend_id))
    execute("INSERT IGNORE INTO friends(user_id, friend_id) VALUES(%s, %s)", (friend_id, user_id))

    return jsonify({
        "code": 0,
        "msg": "添加好友成功",
        "data": {
            "friend_id": friend[0],
            "login_name": friend[1],
            "nickname": friend[2],
            "gender": friend[3],
            "avatar_object_key": friend[4],
            "avatar_url": build_avatar_url(friend[4])
        }
    })

#删除朋友的接口
@app.route("/delete_friend", methods=["POST"])
def delete_friend():
    data = request.json

    user_id = data.get("user_id")
    friend_login_name = data.get("friend_login_name", "").strip()

    if not user_id or not friend_login_name:
        return jsonify({"code": 1, "msg": "参数不完整"})
    if not friend_login_name.isdigit():
        return jsonify({"code": 1, "msg": "好友登录用户名只能是数字"})

    # 1. 查询要删除的好友是否存在
    friend = query_one(
        "SELECT id, login_name FROM users WHERE login_name=%s",
        (friend_login_name,)
    )
    if not friend:
        return jsonify({"code": 1, "msg": "该用户不存在"})

    friend_id = friend[0]

    # 2. 不能删除自己
    if int(user_id) == int(friend_id):
        return jsonify({"code": 1, "msg": "不能删除自己"})

    # 3. 检查是否是好友（不是好友不能删）
    is_friend = query_one(
        "SELECT 1 FROM friends WHERE user_id = %s AND friend_id = %s",
        (user_id, friend_id)
    )
    if not is_friend:
        return jsonify({"code": 1, "msg": "你们还不是好友，无法删除"})

    # 4. 核心：双向删除好友关系（和你添加时的双向插入对应）
    execute("DELETE FROM friends WHERE user_id = %s AND friend_id = %s", (user_id, friend_id))
    execute("DELETE FROM friends WHERE user_id = %s AND friend_id = %s", (friend_id, user_id))

    return jsonify({
        "code": 0,
        "msg": "删除好友成功"
    })

#查询朋友的接口
@app.route("/friends/<int:user_id>", methods=["GET"])
def get_friends(user_id):
    rows = query_all(
        """
        SELECT u.id, u.login_name, u.nickname, u.gender, u.avatar_object_key
        FROM friends f
        JOIN users u ON f.friend_id = u.id
        WHERE f.user_id = %s
        ORDER BY u.id ASC
        """,
        (user_id,)
    )

    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "login_name": r[1],
            "nickname": r[2],
            "gender": r[3],
            "avatar_object_key": r[4],
            "avatar_url": build_avatar_url(r[4])
        })

    return jsonify({"code": 0, "data": data})


#创建群聊的方法接口
@app.route("/create_group", methods=["POST"])
def create_group():
    data = request.json
    user_id = data.get("user_id")
    group_name = data.get("group_name", "").strip()

    if not user_id or not group_name:
        return jsonify({"code": 1, "msg": "参数不完整"})

    exists = query_one("SELECT id FROM chat_groups WHERE group_name=%s", (group_name,))
    if exists:
        return jsonify({"code": 1, "msg": "群名已存在"})

    group_id = insert_and_get_id(
        "INSERT INTO chat_groups(group_name, owner_id) VALUES(%s, %s)",
        (group_name, user_id)
    )

    execute(
        "INSERT IGNORE INTO group_members(group_id, user_id) VALUES(%s, %s)",
        (group_id, user_id)
    )

    return jsonify({
        "code": 0,
        "msg": "创建群聊成功",
        "data": {
            "group_id": group_id,
            "group_name": group_name
        }
    })

#加入群聊的方法接口
@app.route("/join_group", methods=["POST"])
def join_group():
    data = request.json
    user_id = data.get("user_id")
    group_name = data.get("group_name", "").strip()

    if not user_id or not group_name:
        return jsonify({"code": 1, "msg": "参数不完整"})

    group = query_one("SELECT id FROM chat_groups WHERE group_name=%s", (group_name,))
    if not group:
        return jsonify({"code": 1, "msg": "群聊不存在"})

    group_id = group[0]
    execute("INSERT IGNORE INTO group_members(group_id, user_id) VALUES(%s, %s)", (group_id, user_id))
    return jsonify({"code": 0, "msg": "加入群聊成功"})

#删除群聊的方法接口
@app.route("/delete_group", methods=["POST"])
def delete_group():
    data = request.json
    user_id = data.get("user_id")
    group_name = data.get("group_name", "").strip()

    if not user_id or not group_name:
        return jsonify({"code": 1, "msg": "参数不完整"})

    #1 查群是否存在，以及群主是谁
    group = query_one(
        "SELECT id, owner_id FROM chat_groups WHERE group_name=%s",
        (group_name,)
    )
    if not group:
        return jsonify({"code": 1, "msg": "群聊不存在"})
    group_id, owner_id = group

    #2 只有群主可以删除
    if int(owner_id) != int(user_id):
        return jsonify({"code": 1, "msg": "只有群主才能删除群聊"})

    #3 删除群成员关系
    execute("DELETE FROM group_members WHERE group_id=%s", (group_id,))
    # 如果有群消息表，可以顺手删
    # execute("DELETE FROM messages WHERE chat_type='group' AND group_id=%s", (group_id,))
    # 删除群
    execute("DELETE FROM chat_groups WHERE id=%s", (group_id,))

    #4 返回响应数据
    return jsonify({
        "code": 0,
        "msg": "删除群聊成功",
        "data": {
            "group_id": group_id,
            "group_name": group_name
        }
    })

#退出群聊的方法接口
@app.route("/quit_group", methods=["POST"])
def quit_group():
    data = request.json
    user_id = data.get("user_id")
    group_name = data.get("group_name", "").strip()
    if not user_id or not group_name:
        return jsonify({"code": 1, "msg": "参数不完整"})

    #1 查询群是否存在
    group = query_one(
        "SELECT id, owner_id FROM chat_groups WHERE group_name=%s",
        (group_name,)
    )
    if not group:
        return jsonify({"code": 1, "msg": "群聊不存在"})
    group_id, owner_id = group

    #2 判断是否群主，群主不能直接退出
    if int(owner_id) == int(user_id):
        return jsonify({"code": 1, "msg": "群主不能直接退出群聊，请先删除群聊"})

    #3 判断是否在该群聊里面
    member = query_one(
        "SELECT 1 FROM group_members WHERE group_id=%s AND user_id=%s",
        (group_id, user_id)
    )
    if not member:
        return jsonify({"code": 1, "msg": "你不在该群聊中"})

    #4 执行退出群聊，即删除群的某个成员
    execute(
        "DELETE FROM group_members WHERE group_id=%s AND user_id=%s",
        (group_id, user_id)
    )

    #5 返回响应数值
    return jsonify({
        "code": 0,
        "msg": "退出群聊成功",
        "data": {
            "group_id": group_id,
            "group_name": group_name
        }
    })

#查看已加入群聊的方法接口
@app.route("/groups/<int:user_id>", methods=["GET"])
def get_groups(user_id):
    rows = query_all("""
        SELECT
            g.id,
            g.group_name,
            COUNT(gm2.user_id) AS member_count,
            GROUP_CONCAT(u.nickname ORDER BY u.id SEPARATOR '、') AS member_names
        FROM group_members gm
        JOIN chat_groups g ON gm.group_id = g.id
        JOIN group_members gm2 ON g.id = gm2.group_id
        JOIN users u ON gm2.user_id = u.id
        WHERE gm.user_id = %s
        GROUP BY g.id, g.group_name
        ORDER BY g.id ASC
    """, (user_id,))

    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "group_name": r[1],
            "member_count": r[2],
            "member_names": r[3] or ""
        })

    return jsonify({"code": 0, "data": data})

if __name__ == "__main__":
    app.run(host=HTTP_HOST, port=HTTP_PORT, debug=True)