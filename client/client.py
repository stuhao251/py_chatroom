import os
import io
import base64
from datetime import datetime
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
try:
    import pygame
    pygame.mixer.init()
except Exception:
    pygame = None

from login_window import LoginWindow
from main_window import MainWindow
from update_info_window import UpdateInfoWindow
from services.client_http_services import (http_requests_add_friend,
                                           http_requests_delete_friend,
                                           http_requests_create_groups,
                                           http_requests_join_groups, http_requests_delete_group,
                                           http_requests_quit_group)
from services.message_service import MessageService
from services.socket_service import SocketService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "chat_logs")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
SOUND_FILE = os.path.join(BASE_DIR, "sounds", "notify.mp3")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class ChatClient:
    def __init__(self, root):
        self.root = root

        self.user_id = None        # id
        self.user_name = None      # 登录名
        self.nick_name = None      # 昵称
        self.head_url = None       # 用户头像地址

        self.friend_map = {}    #好友池
        self.group_map = {}     #群聊池

        #self.chat_cache = {}    #聊天的缓存
        #self.unread_count = {}  #未读内容
        self.main_window = None

        self.current_chat_type =   None  # private / group
        self.current_target_id =   None
        self.current_target_name = None

        self.text_area = None
        self.entry_msg = None

        self.message_service = MessageService()  # 消息缓存与未读消息逻辑,不同用户聊天显示不同内容
        self.socket_service = SocketService(self.handle_message)  # socket连接服务器，接受发送消息

        self.show_login_ui()



    # 0 ui部分
    # 打开登录ui
    def show_login_ui(self):
        self.login_window = LoginWindow(self)
        self.login_window.build()

    # 打开主窗口ui
    def show_main_ui(self):
        self.main_window = MainWindow(self)
        self.main_window.build()

    # 打开更新个人信息窗口ui
    def open_updateinfo_window(self):
        UpdateInfoWindow(self.root, self)

    # 清除窗口
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()



    #1 接收消息
    #收到消息时的处理逻辑
    def handle_message(self, data):
        msg_type = data.get("type")

        if msg_type == "system":
            msg = data.get("message","")
            if msg:
                if "不是好友" in msg:
                    # self.message_service.save_message("private",
                    #                                   self.current_target_id,
                    #                                   f"[系统] {msg}\n\n") #聊天框中提示
                    self.save_message_to_cache("private", self.current_target_id, f"[系统] {msg}\n\n")
                    self.load_current_chat()
                elif "群聊已被删除" in msg:
                    # self.message_service.save_message("group",
                    #                                   self.current_target_id,
                    #                                   f"[系统] {msg}\n\n") #聊天框中提示
                    self.save_message_to_cache("group", self.current_target_id, f"[系统] {msg}\n\n")
                    self.load_current_chat()
                # elif "已在线" in msg:
                #     messagebox.showwarning("提示",msg)
            return

        if msg_type == "private_message":
            sender = data["from_username"]
            from_user_id = data["from_user_id"]
            content_type = data["content_type"]
            content = data["content"]
            file_name = data.get("file_name", "")

            show_text = self.decode_content_for_display(content_type, content, file_name)
            # msg = f"[私聊] {sender} {data['time']}\n{show_text}\n\n"

            if content_type == "image":
                msg = {
                    "kind": "image",
                    "header": f"[私聊] {sender} {data['time']}\n",
                    "content": content,
                    "file_name": file_name
                }
            else:
                #show_text = self.decode_content_for_display(content_type, content, file_name)
                msg = {
                    "kind": "text",
                    "text": f"[私聊] {sender} {data['time']}\n{show_text}\n\n"
                }

            # 保存到对应私聊缓存
            self.save_message_to_cache("private", from_user_id, msg)

            # 如果当前正在和这个人聊天，刷新当前窗口
            if self.current_chat_type == "private" and self.current_target_id == from_user_id:
                self.load_current_chat()
                print(f"接收测试 {self.nick_name}的当前聊天类型:{self.current_chat_type}" +
                      f"正在和聊天对象：{self.current_target_name}（{self.current_target_id}）聊天")
            else:
                self.message_service.increase_unread("private", from_user_id)  #未读消息增加
                self.main_window.refresh_current_session_list()  #刷新会话列表，可以增加未读红点


            self.save_local_logs2("private",
                                  self.user_id, self.nick_name,
                                  str(from_user_id), str(sender),
                                  f"{sender}: {show_text}")
            self.play_notify()

        elif msg_type == "group_message":
            sender = data["from_username"]
            group_id = data["group_id"]
            content_type = data["content_type"]
            content = data["content"]
            file_name = data.get("file_name", "")

            show_text = self.decode_content_for_display(content_type, content, file_name)
            # msg = f"[群聊 {group_id}] {sender} {data['time']}\n{show_text}\n\n"
            if content_type == "image":
                msg = {
                    "kind": "image",
                    "header": f"[群聊] {sender} {data['time']}\n",
                    "content": content,
                    "file_name": file_name
                }
            else:
                #show_text = self.decode_content_for_display(content_type, content, file_name)
                msg = {
                    "kind": "text",
                    "text": f"[群聊] {sender} {data['time']}\n{show_text}\n\n"
                }

            self.save_message_to_cache("group", group_id, msg)

            if self.current_chat_type == "group" and self.current_target_id == group_id:
                self.load_current_chat()
                print(f"接收测试 {self.nick_name}的当前聊天类型:{self.current_chat_type}" +
                      f"正在和聊天对象：{self.current_target_name}（{self.current_target_id}）聊天")
            else:
                self.message_service.increase_unread("group", group_id)
                self.main_window.refresh_current_session_list() #刷新会话列表，可以增加未读红点

            self.save_local_logs2("group",
                                  self.user_id, self.nick_name,
                                  str(group_id), str(sender),
                                  f"{sender}: {show_text}")
            self.play_notify()

    #解码处理不同的聊天内容类型
    def decode_content_for_display(self, content_type, content, file_name=""):
        if content_type == "text":
            return content
        elif content_type == "emoji":
            return f"[表情] {content}"
        elif content_type == "image":
            path = self.save_base64_file(content, file_name or f"image_{datetime.now().timestamp()}.png")
            return f"[图片] 已保存到: {path}"
        elif content_type == "file":
            path = self.save_base64_file(content, file_name or f"file_{datetime.now().timestamp()}")
            return f"[文件] 已保存到: {path}"
        return "[未知消息]"

    #图片渲染函数
    def render_image_to_text(self, b64_text, max_size=(180, 180)):
        try:
            image_data = base64.b64decode(b64_text)
            img = Image.open(io.BytesIO(image_data)).convert("RGBA")
            img.thumbnail(max_size, Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)

            # 必须保存引用，否则图片会消失
            if not hasattr(self, "chat_image_refs"):
                self.chat_image_refs = []
            self.chat_image_refs.append(photo)

            self.text_area.image_create(END, image=photo)
            self.text_area.insert(END, "\n\n")
        except Exception as e:
            self.text_area.insert(END, f"[图片显示失败] {e}\n\n")

    #收到文件信息时的逻辑
    def save_base64_file(self, b64_text, filename):
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(b64_text))
        return file_path

    #收到消息响铃
    def play_notify(self):
        if pygame and os.path.exists(SOUND_FILE):
            try:
                pygame.mixer.music.load(SOUND_FILE)
                pygame.mixer.music.play()
            except Exception as e:
                print("声音问题：", e)

    #保存聊天的内容日志
    # def save_local_logs(self, chat_type, target_id, message):
    #     file_path = os.path.join(LOG_DIR, f"{chat_type}_{target_id}.txt")
    #     with open(file_path, "a", encoding="utf-8") as f:
    #         f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    def save_local_logs2(self, chat_type, user_id, nick_name, target_id, target_name, message):
        file_path = os.path.join(LOG_DIR, f"{chat_type}_{nick_name}({user_id})&{target_name}({target_id}).txt")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}\n")

    #2 发送和接收消息时的展示处理方法
    #保存消息到对应会话key的缓存中
    def save_message_to_cache(self, chat_type, target_id, message):
        key = self.message_service.get_chat_key(chat_type, target_id)

        if key not in self.message_service.chat_cache:
            self.message_service.chat_cache[key] = []
        self.message_service.chat_cache[key].append(message)

    #加载当前会话-显示当前聊天内容
    def load_current_chat(self):
        if not self.text_area:
            return

        self.text_area.config(state=NORMAL)
        self.text_area.delete("1.0", END)

        self.chat_image_refs = []

        if not self.current_chat_type or not self.current_target_id:
            self.text_area.config(state=DISABLED)
            return

        key = self.message_service.get_chat_key(self.current_chat_type, self.current_target_id)
        messages = self.message_service.chat_cache.get(key, [])

        for msg in messages:
            # self.text_area.insert(END, msg)
            if isinstance(msg, str):
                self.text_area.insert(END, msg)
            elif isinstance(msg, dict):
                kind = msg.get("kind")

                if kind == "text":
                    self.text_area.insert(END, msg["text"])
                elif kind == "image":
                    self.text_area.insert(END, msg["header"])
                    self.render_image_to_text(msg["content"])
                elif kind == "system":
                    self.text_area.insert(END, msg["text"])

        self.text_area.see(END)
        self.text_area.config(state=DISABLED)



    def delete_friend(self):
        dialog = Toplevel(self.root)
        dialog.transient(self.root)
        dialog.title("删除好友")
        dialog.geometry("300x120")
        Label(dialog, text="输入好友账号").pack(pady=10)
        entry = Entry(dialog)
        entry.pack()

        def submit():
            try:
                friend_name = entry.get().strip()
                resp = http_requests_delete_friend(self.user_id, friend_name)
                messagebox.showinfo("提示", resp["msg"])
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        Button(dialog, text="确定", command=submit).pack(pady=10)

    def add_friend(self):
        dialog = Toplevel(self.root)
        dialog.transient(self.root)
        dialog.title("添加好友")
        dialog.geometry("300x120")
        Label(dialog, text="输入好友账号").pack(pady=10)
        entry = Entry(dialog)
        entry.pack()

        def submit():
            try:
                friend_name = entry.get().strip()
                resp = http_requests_add_friend(self.user_id, friend_name)
                messagebox.showinfo("提示", resp["msg"])
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        Button(dialog, text="确定", command=submit).pack(pady=10)

    def create_group(self):
        dialog = Toplevel(self.root)
        dialog.transient(self.root)
        dialog.title("创建群聊")
        dialog.geometry("300x120")

        Label(dialog, text="群聊名称").pack(pady=10)
        entry = Entry(dialog)
        entry.pack()

        def submit():
            group_name = entry.get().strip()
            try:
                resp = http_requests_create_groups(self.user_id, group_name)
                messagebox.showinfo("提示", resp["msg"])
                dialog.destroy()
                self.refresh_current_lists()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        Button(dialog, text="确定", command=submit).pack(pady=10)

    def delete_group(self):
        dialog = Toplevel(self.root)
        dialog.title("删除群聊")
        dialog.geometry("300x120")
        dialog.resizable(False, False)

        Label(dialog, text="群聊名称").pack(pady=10)
        entry = Entry(dialog)
        entry.pack()

        def submit():
            group_name = entry.get().strip()
            try:
                resp = http_requests_delete_group(self.user_id, group_name)
                messagebox.showinfo("提示", resp["msg"])

                if resp["code"] == 0:
                    # 如果当前正在这个群聊界面，清空当前聊天对象
                    if (self.current_chat_type == "group"
                        and self.current_target_name == group_name):
                        self.current_chat_type = None
                        self.current_target_id = None
                        self.current_target_name = None

                        if self.text_area:
                            self.text_area.config(state=NORMAL)
                            self.text_area.delete("1.0", END)
                            self.text_area.config(state=DISABLED)

                        if self.main_window and hasattr(self.main_window, "chat_title_label"):
                            self.main_window.chat_title_label.config(text="请选择一个会话")

                    dialog.destroy()

                    # 刷新列表
                    if self.main_window:
                        self.main_window.load_group_sessions()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        Button(dialog, text="确定", command=submit).pack(pady=10)

    def quit_group(self):
        dialog = Toplevel(self.root)
        dialog.title("退出群聊")
        dialog.geometry("300x120")
        dialog.resizable(False, False)

        Label(dialog, text="群聊名称").pack(pady=10)
        entry = Entry(dialog)
        entry.pack()

        def submit():
            group_name = entry.get().strip()
            try:
                resp = http_requests_quit_group(self.user_id, group_name)
                messagebox.showinfo("提示", resp["msg"])

                if resp["code"] == 0:
                    # 如果当前就在这个群聊天，清空当前会话
                    if (
                            self.current_chat_type == "group"
                            and self.current_target_name == group_name
                    ):
                        self.current_chat_type = None
                        self.current_target_id = None
                        self.current_target_name = None

                        if self.text_area:
                            self.text_area.config(state=NORMAL)
                            self.text_area.delete("1.0", END)
                            self.text_area.config(state=DISABLED)

                        if self.main_window and hasattr(self.main_window, "chat_title_label"):
                            self.main_window.chat_title_label.config(text="请选择一个会话")

                    dialog.destroy()

                    # 刷新群列表
                    if self.main_window:
                        self.main_window.load_group_sessions()

            except Exception as e:
                messagebox.showerror("错误", str(e))

        Button(dialog, text="确定", command=submit).pack(pady=10)

    def join_group(self):
        dialog = Toplevel(self.root)
        dialog.transient(self.root)
        dialog.title("加入群聊")
        dialog.geometry("300x120")

        Label(dialog, text="群聊名称").pack(pady=10)
        entry = Entry(dialog)
        entry.pack()

        def submit():
            group_name = entry.get().strip()
            try:
                resp = http_requests_join_groups(self.user_id, group_name)
                messagebox.showinfo("提示", resp["msg"])
                dialog.destroy()
                self.refresh_current_lists()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        Button(dialog, text="确定", command=submit).pack(pady=10)

    def refresh_current_lists(self):
        self.show_main_ui()



    #3 发送消息
    #发送消息-本地封装格式
    def local_show_text(self, content_type, content, file_name):
        if content_type == "text":
            return content
        elif content_type == "emoji":
            return content  # f"[表情] {content}"
        elif content_type == "image":
            return f"[图片] {file_name}"
        elif content_type == "file":
            return f"[文件] {file_name}"
        return "[未知内容]"

    # 发送文本信息
    def send_text(self):
        msg = self.entry_msg.get("1.0", END).strip()
        if not msg:
            return
        self.send_message("text", msg)
        self.entry_msg.delete("1.0", END)

    # 发送emoj信息
    def open_emoji_panel(self):
        emojis = [
            "😀", "😁", "😂", "🤣", "😊", "😍", "😘", "😎",
            "😢", "😭", "😡", "👍", "👎", "🙏", "👏", "🎉",
            "❤️", "💔", "🔥", "🌹", "🍀", "🍉", "☕", "⭐"
        ]

        panel = Toplevel(self.root)
        panel.title("选择表情")
        panel.geometry("320x220")
        panel.resizable(False, False)
        panel.transient(self.root)
        panel.grab_set()

        frame = Frame(panel, bg="white")
        frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        cols = 6
        for i, emoji in enumerate(emojis):
            def on_click(e=emoji):
                self.send_message("emoji", e)
                panel.destroy()

            btn = Button(frame, text=emoji, font=("Segoe UI Emoji", 16),
                width=3, height=1, relief=FLAT, bd=0, bg="white",
                activebackground="#f0f0f0", cursor="hand2", command=on_click)
            btn.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")
    def send_emoji(self):
        self.open_emoji_panel()

    # 发送图片信息
    def send_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if not file_path:
            return
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        self.send_message("image", content, os.path.basename(file_path))

    # 发送文件信息
    def send_file(self):
        file_path = filedialog.askopenfilename(title="选择文件")
        if not file_path:
            return
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        self.send_message("file", content, os.path.basename(file_path))

    #发送信息的处理逻辑
    def send_message(self, content_type, content, file_name = ""):
        if not self.current_chat_type or not self.current_target_id:
            messagebox.showwarning("提示", "请先选择聊天对象")
            return
        print(f"发送测试 {self.nick_name}的当前聊天类型:{self.current_chat_type}"+
              f" 聊天对象：{self.current_target_name}（{self.current_target_id}）")
        if self.current_chat_type == "private":
            data = {
                "type": "private_message",
                "from_user_id": self.user_id,
                "from_username": self.nick_name,
                "to_user_id": self.current_target_id,
                "content_type": content_type,
                "content": content,
                "file_name": file_name
            }
            self.socket_service.send_json(data)

            # show = self.local_show_text(content_type, content, file_name)
            # msg = f"[我 -> {self.current_target_name}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{show}\n\n"

            if content_type == "image":
                msg = {
                    "kind": "image",
                    "header": f"[我 -> {self.current_target_name}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                    "content": content,
                    "file_name": file_name
                }
            else:
                show = self.local_show_text(content_type, content, file_name)
                msg = {
                    "kind": "text",
                    "text": f"[我 -> {self.current_target_name}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{show}\n\n"
                }

            self.save_message_to_cache("private", self.current_target_id, msg)
            self.load_current_chat()

            #self.save_local_logs("private", str(self.current_target_id), f"我: {show}")
            self.save_local_logs2("private",
                                  self.user_id, self.nick_name,
                                  self.current_target_id, self.current_target_name,
                                  f"我: {show}")
        elif self.current_chat_type == "group":
            data = {
                "type": "group_message",
                "group_id": self.current_target_id,
                "from_user_id": self.user_id,
                "from_username": self.nick_name,
                "content_type": content_type,
                "content": content,
                "file_name": file_name
            }
            self.socket_service.send_json(data)

            # show = self.local_show_text(content_type, content, file_name)
            # msg = f"[我 -> 群 {self.current_target_name}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{show}\n\n"

            if content_type == "image":
                msg = {
                    "kind": "image",
                    "header": f"[我 -> 群 {self.current_target_name}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                    "content": content,
                    "file_name": file_name
                }
            else:
                show = self.local_show_text(content_type, content, file_name)
                msg = {
                    "kind": "text",
                    "text": f"[我 -> {self.current_target_name}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{show}\n\n"
                }
            self.save_message_to_cache("group", self.current_target_id, msg)

            self.load_current_chat()
            self.save_local_logs2("group",
                                  self.user_id, self.nick_name,
                                  self.current_target_id, self.current_target_name,
                                  f"我: {show}")






if __name__ == "__main__":
    root = Tk()
    app = ChatClient(root)
    root.mainloop()