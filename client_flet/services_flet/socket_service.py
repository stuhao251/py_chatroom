import json
import socket
import threading
from server.config import SOCKET_HOST, SOCKET_PORT

#客户端的socket服务

class SocketService:
    def __init__(self, on_message_handling):
        self.sock = None
        self.sock_file = None
        self.on_message_handling = on_message_handling

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass

        try:
            if self.sock_file:
                self.sock_file.close()
        except Exception:
            pass

        self.sock = None
        self.sock_file = None

    def connect(self, user_id, user_name, nick_name):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SOCKET_HOST, SOCKET_PORT))
            self.sock_file = self.sock.makefile("r", encoding="utf-8")

            #1 发送登录的json信息
            self.send_json({
                "type": "login_socket",
                "user_id": user_id,
                "user_name": user_name,
                "user_nick_name": nick_name
            })

            #2 等待服务器
            resp = self.recv_json()
            if not resp:
                return False, "服务器无响应"
            if resp.get("type") == "system":
                msg = resp.get("message", "")
                if "成功" not in msg:
                    return False, msg

            #3 启动接收线程
            threading.Thread(target=self.receive_loop, daemon=True).start()
            return True, "连接成功"

        except Exception as e:
            return False, str(e)

    def send_json(self, data):
        msg = json.dumps(data, ensure_ascii=False) + "\n"
        self.sock.sendall(msg.encode("utf-8"))

    def recv_json(self):
        try:
            line = self.sock_file.readline()
            if not line:
                return None
            return json.loads(line.strip())
        except Exception:
            return None

    def receive_loop(self):
        while True:
            try:
                line = self.sock_file.readline()
                if not line:
                    break
                data = json.loads(line.strip())
                self.on_message_handling(data)
            except Exception:
                break