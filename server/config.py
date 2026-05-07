import os
from dotenv import load_dotenv
# MySQL数据配置
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "1204",
    "database": "python_chatroom",
    "charset": "utf8mb4"
}

# HTTP数据配置
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 5000
HTTP_BASE = "http://127.0.0.1:5000"

# Socket数据配置
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 9001

# 阿里云 OSS
load_dotenv()

OSS_ENDPOINT = os.getenv("https://oss-cn-chengdu.aliyuncs.com")
OSS_BUCKET_NAME = os.getenv("python-chatroom")
OSS_ACCESS_KEY_ID = os.getenv("LTAI5tK4MTSWfsUJdY9yssvM")
OSS_ACCESS_KEY_SECRET = os.getenv("mUwrWSAL8pnjbkTvOhZ1dhTsnUpowb")
OSS_BUCKET_DOMAIN = os.getenv("https://python-chatroom.oss-cn-chengdu.aliyuncs.com")