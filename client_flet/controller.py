import os
import base64
import flet as ft

from client_flet.services_flet.client_http_services_v2 import (
    http_requests_add_friend,
    http_requests_delete_friend,
    http_requests_create_groups,
    http_requests_join_groups,
    http_requests_delete_group,
    http_requests_quit_group,
)


class ChatController:
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.view = None

    def bind_view(self, view):
        self.view = view

    def show_input_dialog(self, title, label, on_submit):
        input_field = ft.TextField(label=label, autofocus=True)

        def close_dialog(e=None):
            dialog.open = False
            self.page.update()

        def submit(e=None):
            value = input_field.value.strip()
            if not value:
                self.show_alert("提示", f"{label}不能为空")
                return
            close_dialog()
            on_submit(value)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=input_field,
            actions=[
                ft.TextButton("取消", on_click = close_dialog),
                ft.ElevatedButton("确定", on_click= submit),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


    def show_alert(self, title, msg):
        def close_dialog(e=None):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(msg),
            actions=[ft.TextButton("确定", on_click=close_dialog)],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


    def add_friend(self):
        def submit(friend_login_name):
            try:
                resp = http_requests_add_friend(self.app.user_id, friend_login_name)
                self.show_alert("提示", resp["msg"])

                if resp["code"] == 0 and self.app.main_view:
                    self.app.main_view.load_friend_sessions()
                    self.app.main_view.current_nav = "friend"
            except Exception as e:
                self.show_alert("错误", str(e))

        self.show_input_dialog("添加好友", "好友登录名", submit)


    def delete_friend(self):
        def submit(friend_login_name):
            try:
                resp = http_requests_delete_friend(self.app.user_id, friend_login_name)
                self.show_alert("提示", resp["msg"])

                if resp["code"] == 0 and self.app.main_view:
                    if self.app.current_chat_type == "private":
                        self.app.current_chat_type = None
                        self.app.current_target_id = None
                        self.app.current_target_name = None
                        self.app.main_view.disable_chat_area()

                    self.app.main_view.load_friend_sessions()
            except Exception as e:
                self.show_alert("错误", str(e))

        self.show_input_dialog("删除好友", "好友登录名", submit)


    def create_group(self):
        def submit(group_name):
            try:
                resp = http_requests_create_groups(self.app.user_id, group_name)
                self.show_alert("提示", resp["msg"])
                if resp["code"] == 0 and self.app.main_view:
                    self.app.main_view.load_group_sessions()
            except Exception as e:
                self.show_alert("错误", str(e))

        self.show_input_dialog("创建群聊", "群聊名称", submit)


    def join_group(self):
        def submit(group_name):
            try:
                resp = http_requests_join_groups(self.app.user_id, group_name)
                self.show_alert("提示", resp["msg"])
                if resp["code"] == 0 and self.app.main_view:
                    self.app.main_view.load_group_sessions()
            except Exception as e:
                self.show_alert("错误", str(e))

        self.show_input_dialog("加入群聊", "群聊名称", submit)


    def delete_group(self):
        def submit(group_name):
            try:
                resp = http_requests_delete_group(self.app.user_id, group_name)
                self.show_alert("提示", resp["msg"])

                if resp["code"] == 0 and self.app.main_view:
                    if self.app.current_chat_type == "group" and self.app.current_target_name == group_name:
                        self.app.current_chat_type = None
                        self.app.current_target_id = None
                        self.app.current_target_name = None
                        self.app.main_view.disable_chat_area()

                    self.app.main_view.load_group_sessions()
            except Exception as e:
                self.show_alert("错误", str(e))

        self.show_input_dialog("删除群聊", "群聊名称", submit)


    def quit_group(self):
        def submit(group_name):
            try:
                resp = http_requests_quit_group(self.app.user_id, group_name)
                self.show_alert("提示", resp["msg"])

                if resp["code"] == 0 and self.app.main_view:
                    if self.app.current_chat_type == "group" and self.app.current_target_name == group_name:
                        self.app.current_chat_type = None
                        self.app.current_target_id = None
                        self.app.current_target_name = None
                        self.app.main_view.disable_chat_area()

                    self.app.main_view.load_group_sessions()
            except Exception as e:
                self.show_alert("错误", str(e))

        self.show_input_dialog("退出群聊", "群聊名称", submit)

    def open_file_save_path_dialog(self):
        path_field = ft.TextField(
            label="文件保存路径",
            value=self.app.file_save_dir,
            autofocus=True,
            width=420,
        )

        def close_dialog(e=None):
            dialog.open = False
            self.page.update()

        def save_path(e=None):
            new_path = path_field.value.strip()

            if not new_path:
                self.show_alert("提示", "文件保存路径不能为空")
                return

            try:
                os.makedirs(new_path, exist_ok=True)
                self.app.file_save_dir = new_path

                close_dialog()
                self.show_alert("成功", f"文件保存路径已修改为：\n{new_path}")

            except Exception as ex:
                self.show_alert("错误", f"路径设置失败：{ex}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("设置文件保存路径"),
            content=path_field,
            actions=[
                ft.TextButton("取消", on_click=close_dialog),
                ft.ElevatedButton("保存", on_click=save_path),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def save_received_file(self, file_base64, file_name):
        save_dir = self.app.file_save_dir
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, file_name)

        with open(save_path, "wb") as f:
            f.write(base64.b64decode(file_base64))

        return save_path


    #接受消息
    def handle_message(self, data):
        msg_type = data.get("type")
        if msg_type == "system":
            self._handle_system_message(data)
        elif msg_type == "private_message":
            self._handle_private_message(data)
        elif msg_type == "group_message":
            self._handle_group_message(data)

    def _handle_system_message(self, data):
        msg = data.get("message", "")
        if not msg:
            return

        if "不是好友" in msg:
            if self.app.current_chat_type == "private" and self.app.current_target_id:
                self.app.message_service.save_message(
                    "private",
                    self.app.current_target_id,
                    f"[系统]: {msg}"
                )
                self.app.update_chat_ui()
            return
        if "群聊已被删除" in msg or "不在该群聊" in msg or "不在该群聊中" in msg:
            if self.app.current_chat_type == "group" and self.app.current_target_id:
                self.app.message_service.save_message(
                    "group",
                    self.app.current_target_id,
                    f"[系统]: {msg}"
                )
                self.app.update_chat_ui()
            return

    def _handle_private_message(self, data):
        sender = data["from_username"]
        from_user_id = data["from_user_id"]
        content_type = data["content_type"]
        content = data["content"]
        file_name = data.get("file_name", "")

        if content_type == "image":
            msg = {
                "kind": "image",
                "sender": sender,
                "content": content,
                "file_name": file_name,
            }
        elif content_type == "file":
            save_path = self.save_received_file(content, file_name)
            msg = {
                "kind": "file",
                "sender": sender,
                "content": content,
                "file_name": file_name,
                "save_path": save_path,
            }
        else:
            msg = f"[{sender}]: {content}"

        self.app.message_service.save_message("private", from_user_id, msg)

        if self.app.current_chat_type == "private" and self.app.current_target_id == from_user_id:
            self.app.update_chat_ui()
        else:
            self.app.message_service.increase_unread("private", from_user_id)
            if self.app.main_view:
                self.app.main_view.refresh_current_session_list()


    def _handle_group_message(self, data):
        sender = data["from_username"]
        group_id = data["group_id"]
        content_type = data["content_type"]
        content = data["content"]
        file_name = data.get("file_name", "")

        if content_type == "image":
            msg = {
                "kind": "image",
                "sender": sender,
                "content": content,
                "file_name": file_name,
            }
        elif content_type == "file":
            save_path = self.save_received_file(content, file_name)
            msg = {
                "kind": "file",
                "sender": sender,
                "content": content,
                "file_name": file_name,
                "save_path": save_path,
            }
        else:
            msg = f"[{sender}]: {content}"

        self.app.message_service.save_message("group", group_id, msg)

        if self.app.current_chat_type == "group" and self.app.current_target_id == group_id:
            self.app.update_chat_ui()
        else:
            self.app.message_service.increase_unread("group", group_id)
            if self.app.main_view:
                self.app.main_view.refresh_current_session_list()

    #发送消息（文件和文本）
    def send_text(self, e = None):
        view = self.view

        if view.pending_file_path: #发送文件
            self.send_file()
            return

        text = view.input_box.value.strip()
        if not text:
            return

        if not self.app.current_chat_type or not self.app.current_target_id:
            view.show_msg("请先选择聊天对象")
            return

        if self.app.current_chat_type == "private":
            data = {
                "type": "private_message",
                "from_user_id": self.app.user_id,
                "from_username": self.app.nick_name,
                "to_user_id": self.app.current_target_id,
                "content_type": "text",
                "content": text,
                "file_name": ""
            }
        else:
            data = {
                "type": "group_message",
                "group_id": self.app.current_target_id,
                "from_user_id": self.app.user_id,
                "from_username": self.app.nick_name,
                "content_type": "text",
                "content": text,
                "file_name": ""
            }

        self.app.socket_service.send_json(data)

        self.app.message_service.save_message(
            self.app.current_chat_type,
            self.app.current_target_id,
            f"[我]: {text}",
        )

        view.input_box.value = ""
        view.load_current_chat()
        self.page.update()


    #点击图片按钮
    def pick_image(self, e=None):
        view = self.view

        if not self.app.current_chat_type or not self.app.current_target_id:
            view.show_msg("请先选择聊天对象")
            return

        view.file_picker_image.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)
    #图片点击后
    def on_image_picked(self, e):
        view = self.view
        if not e.files:
            return
        file_path = e.files[0].path
        file_name = os.path.basename(file_path)

        try:
            with open(file_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode("utf-8")
            self.send_image(img_base64, file_name)
        except Exception as ex:
            view.show_msg(f"图片发送失败：{ex}")
    #发送图片信息
    def send_image(self, img_base64, file_name):
        view = self.view

        if self.app.current_chat_type == "private":
            data = {
                "type": "private_message",
                "from_user_id": self.app.user_id,
                "from_username": self.app.nick_name,
                "to_user_id": self.app.current_target_id,
                "content_type": "image",
                "content": img_base64,
                "file_name": file_name
            }
        else:
            data = {
                "type": "group_message",
                "group_id": self.app.current_target_id,
                "from_user_id": self.app.user_id,
                "from_username": self.app.nick_name,
                "content_type": "image",
                "content": img_base64,
                "file_name": file_name
            }

        self.app.socket_service.send_json(data)

        msg = {
            "kind": "image",
            "sender": "我",
            "content": img_base64,
            "file_name": file_name
        }

        self.app.message_service.save_message(
            self.app.current_chat_type,
            self.app.current_target_id,
            msg
        )

        view.load_current_chat()
        self.page.update()


    # 点击文件
    def pick_file(self, e=None):
        view = self.view
        if not self.app.current_chat_type or not self.app.current_target_id:
            view.show_msg("请先选择聊天对象")
            return
        view.file_picker_file.pick_files(allow_multiple=False)
    # 文件点击后
    def on_file_picked(self, e):
        view = self.view
        if not e.files:
            return
        view.pending_file_path = e.files[0].path
        view.pending_file_name = os.path.basename(view.pending_file_path)
        view.input_box.value = f"[文件] {view.pending_file_name}"
        self.page.update()
    #发送文件信息
    def send_file(self):
        view = self.view

        try:
            with open(view.pending_file_path, "rb") as f:
                file_base64 = base64.b64encode(f.read()).decode("utf-8")

            file_name = view.pending_file_name

            if self.app.current_chat_type == "private":
                data = {
                    "type": "private_message",
                    "from_user_id": self.app.user_id,
                    "from_username": self.app.nick_name,
                    "to_user_id": self.app.current_target_id,
                    "content_type": "file",
                    "content": file_base64,
                    "file_name": file_name,
                }
            else:
                data = {
                    "type": "group_message",
                    "group_id": self.app.current_target_id,
                    "from_user_id": self.app.user_id,
                    "from_username": self.app.nick_name,
                    "content_type": "file",
                    "content": file_base64,
                    "file_name": file_name,
                }

            self.app.socket_service.send_json(data)

            msg = {
                "kind": "file",
                "sender": "我",
                "content": file_base64,
                "file_name": file_name,
            }

            self.app.message_service.save_message(
                self.app.current_chat_type,
                self.app.current_target_id,
                msg,
            )

            view.pending_file_path = None
            view.pending_file_name = None
            view.input_box.value = ""

            view.load_current_chat()
            self.page.update()

        except Exception as ex:
            view.show_msg(f"文件发送失败：{ex}")