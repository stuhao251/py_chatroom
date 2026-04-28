import flet as ft
import base64
import os
from client_flet.services_flet.client_http_services import (
    http_requests_get_friends,
    http_requests_get_groups,
)


class MainView:
    def __init__(self, page: ft.Page, app):
        self.page = page
        self.app = app

        self.nav_buttons = {}
        self.current_nav = "friend"
        self.pending_file_path = None
        self.pending_file_name = None

        self.session_title = ft.Text("好友列表", size=18, weight=ft.FontWeight.BOLD)
        self.session_list = ft.ListView(expand=True, spacing=6, padding=10)

        self.chat_title = ft.Text("请选择一个会话", size=18, weight=ft.FontWeight.BOLD)
        self.chat_list = ft.ListView(expand=True, spacing=8, padding=16)

        self.input_box = ft.TextField(
            hint_text="请输入消息...",
            multiline=True, min_lines=2, max_lines=4, expand=True, disabled=True,)

        self.send_btn = ft.ElevatedButton(
            text="发送", bgcolor="#07c160", color="white", disabled=True,
            on_click = lambda e: self.app.controller.send_text(e), )

        self.file_picker_image = ft.FilePicker(
            on_result=lambda e: self.app.controller.on_image_picked(e)
        )

        self.file_picker_file = ft.FilePicker(
            on_result=lambda e: self.app.controller.on_file_picked(e)
        )

        self.page.overlay.append(self.file_picker_image)
        self.page.overlay.append(self.file_picker_file)

    def build(self):
        return ft.Row(
            expand=True, spacing=0,
            controls=[
                self.build_nav_bar(),
                self.build_session_panel(),
                self.build_chat_panel(),
            ], )

    def build_nav_bar(self):
        return ft.Container(
            width=72,
            bgcolor="#2e2e2e",
            padding=ft.padding.only(top=20, bottom=16),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.build_avatar(
                        name=self.app.nick_name,
                        avatar_url=self.app.head_url,
                        size=48
                    ),
                    ft.Text(self.app.nick_name or "", color="white", size=11),
                    ft.Divider(height=20, color="transparent"),

                    self.nav_button(ft.Icons.CHAT_BUBBLE_OUTLINE, "friend"),
                    self.nav_button(ft.Icons.GROUP_OUTLINED, "group"),
                    self.nav_button(ft.Icons.APPS_OUTLINED, "action"),

                    ft.Container(expand=True),

                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color="#d8d8d8",
                        tooltip="退出登录",
                        on_click=lambda e: self.app.logout()
                    ),
                ],
            ),
        )

    def nav_button(self, icon, mode):
        btn = ft.Container(
            width=56,
            height=48,
            alignment=ft.alignment.center,
            border_radius=10,
            bgcolor="#3a3a3a" if self.current_nav == mode else "#2e2e2e",
            on_click=lambda e: self.switch_nav(mode),
            content=ft.Icon(
                icon,
                size=26,
                color="#07c160" if self.current_nav == mode else "#d8d8d8",
            ),
        )
        self.nav_buttons[mode] = btn
        return btn

    def refresh_nav_buttons(self):
        for mode, btn in self.nav_buttons.items():
            selected = self.current_nav == mode
            btn.bgcolor = "#3a3a3a" if selected else "#2e2e2e"
            btn.content.color = "#07c160" if selected else "#d8d8d8"

    def build_session_panel(self):
        return ft.Container(
            width=300,
            bgcolor="#f7f7f7",
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=76,
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                        border=ft.border.only(right=ft.BorderSide(1, "#e5e5e5")),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                self.session_title,
                                ft.Text(
                                    f"{self.app.nick_name}（{self.app.user_name}）",
                                    size=12,
                                    color="#888888",
                                ),
                            ],
                        ),
                    ),
                    self.session_list,
                ],
            ),
        )

    def build_chat_panel(self):
        return ft.Container(
            expand=True,
            bgcolor="white",
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=70,
                        padding=ft.padding.only(left=20, top=18),
                        border=ft.border.only(bottom=ft.BorderSide(1, "#e5e5e5")),
                        content=self.chat_title,
                    ),
                    self.chat_list,
                    ft.Container(
                        height=170,
                        bgcolor="#f5f5f5",
                        padding=12,
                        border=ft.border.only(top=ft.BorderSide(1, "#e5e5e5")),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.EMOJI_EMOTIONS_OUTLINED,
                                            on_click = self.open_emoji_panel,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.IMAGE_OUTLINED,
                                            on_click = lambda e: self.app.controller.pick_image(e) ,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.ATTACH_FILE,
                                            on_click = lambda e: self.app.controller.pick_file(e),
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    expand=True,
                                    controls=[
                                        self.input_box,
                                        self.send_btn,
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def switch_nav(self, mode):
        self.current_nav = mode
        self.refresh_nav_buttons()

        self.app.current_chat_type = None
        self.app.current_target_id = None
        self.app.current_target_name = None

        self.disable_chat_area()

        if mode == "friend":
            self.session_title.value = "好友列表"
            self.load_friend_sessions()

        elif mode == "group":
            self.session_title.value = "群聊列表"
            self.load_group_sessions()

        elif mode == "action":
            self.session_title.value = "功能菜单"
            self.load_action_sessions()

        self.page.update()

    def open_emoji_panel(self, e=None):
        emojis = [
            "😀", "😁", "😂", "🤣", "😊", "😍", "😘", "😎",
            "😭", "😡", "👍", "👎", "👏", "🙏", "🎉", "🔥",
            "❤️", "💔", "🌹", "🍉", "☕", "⭐"
        ]

        def select_emoji(ev):
            emoji = ev.control.data
            self.input_box.value = (self.input_box.value or "") + emoji

            dialog.open = False
            self.page.update()

        grid = ft.GridView(
            runs_count=6,
            spacing=10,
            run_spacing=10,
            controls=[ ft.TextButton(text=emo, data=emo, on_click = select_emoji) for emo in emojis ]
        )

        dialog = ft.AlertDialog( modal=True, title=ft.Text("选择表情"),
            content=ft.Container(width=300, height=220, content=grid ), )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


    def load_friend_sessions(self):
        self.session_list.controls.clear()

        try:
            resp = http_requests_get_friends(self.app.user_id)
            friends = resp.get("data", [])

            self.app.friend_map = {}

            for item in friends:
                self.app.friend_map[item["id"]] = item
                self.session_list.controls.append(
                    # self.create_session_item(
                    #     title=item["nickname"],
                    #     subtitle=f"账号：{item['login_name']}",
                    #     on_click=lambda e, i=item: self.select_friend(i),
                    # )
                    self.create_session_item(
                        title=item["nickname"],
                        subtitle=f"账号：{item['login_name']}",
                        on_click=lambda e, i=item: self.select_friend(i),
                        chat_type="private",
                        target_id=item["id"],
                        avatar_url=item.get("avatar_url"),
                    )
                )

        except Exception as e:
            self.show_msg(f"加载好友失败：{e}")

    def load_group_sessions(self):
        self.session_list.controls.clear()

        try:
            resp = http_requests_get_groups(self.app.user_id)
            groups = resp.get("data", [])

            self.app.group_map = {}

            for item in groups:
                self.app.group_map[item["id"]] = item
                self.session_list.controls.append(
                    # self.create_session_item(
                    #     title=item["group_name"],
                    #     subtitle=f"群成员：{item.get('member_count', 0)}人",
                    #     on_click=lambda e, i=item: self.select_group(i),
                    # )
                    self.create_session_item(
                        title=item["group_name"],
                        subtitle=f"群成员：{item.get('member_count', 0)}人",
                        on_click=lambda e, i=item: self.select_group(i),
                        chat_type="group",
                        target_id=item["id"],
                    )
                )

        except Exception as e:
            self.show_msg(f"加载群聊失败：{e}")

    def load_action_sessions(self):
        self.session_list.controls.clear()

        actions = [
            ("添加好友", getattr(self.app, "add_friend", None)),
            ("删除好友", getattr(self.app, "delete_friend", None)),
            ("创建群聊", getattr(self.app, "create_group", None)),
            ("加入群聊", getattr(self.app, "join_group", None)),
            ("删除群聊", getattr(self.app, "delete_group", None)),
            ("退出群聊", getattr(self.app, "quit_group", None)),
            ("文件保存路径", getattr(self.app, "open_file_save_path_dialog", None)),
            ("修改个人信息", getattr(self.app, "open_updateinfo_window", None)),
        ]

        for title, callback in actions:
            self.session_list.controls.append(
                ft.Container(
                    height=52,
                    bgcolor="white",
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=16),
                    alignment=ft.alignment.center_left,
                    on_click=lambda e, cb=callback: cb() if cb else self.show_msg("该功能还未迁移"),
                    content=ft.Text(title, size=15, color="#222222"),
                )
            )

    def create_session_item(self, title, subtitle, on_click, chat_type=None, target_id=None, avatar_url=None):
        unread = 0
        if chat_type and target_id:
            unread = self.app.message_service.get_unread(chat_type, target_id)

        badge = ft.Container(
            visible=unread > 0,
            bgcolor="#fa5151",
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            content=ft.Text(
                str(unread) if unread < 100 else "99+",
                size=10,
                color="white",
                weight=ft.FontWeight.BOLD,
            ),
        )

        return ft.Container(
            bgcolor="white",
            border_radius=10,
            padding=12,
            on_click=on_click,
            content=ft.Row(
                spacing=12,
                controls=[
                    # ft.CircleAvatar(
                    #     content=ft.Text(title[:1], color="white"),
                    #     bgcolor="#07c160",
                    #     radius=24,
                    # ),
                    self.build_avatar(
                        name=title,
                        avatar_url=avatar_url,
                        size=48
                    ),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(title, size=15, weight=ft.FontWeight.BOLD),
                            ft.Text(subtitle, size=12, color="#888888"),
                        ],
                    ),
                    badge,
                ],
            ),
        )

    def select_friend(self, item):
        self.app.current_chat_type = "private"
        self.app.current_target_id = item["id"]
        self.app.current_target_name = item["nickname"]

        self.chat_title.value = f"{item['nickname']}（{item['login_name']}）"

        self.enable_chat_area()
        self.load_current_chat()
        # self.app.message_service.clear_unread("private", item["id"])
        # self.page.update()
        self.app.message_service.clear_unread("private", item["id"])
        self.refresh_current_session_list()

    def select_group(self, item):
        self.app.current_chat_type = "group"
        self.app.current_target_id = item["id"]
        self.app.current_target_name = item["group_name"]

        members = item.get("member_names", "")
        if len(members) > 30:
            members = members[:30] + "..."

        self.chat_title.value = f"{item['group_name']}（{item.get('member_count', 0)}人） 成员：{members}"

        self.enable_chat_area()
        self.load_current_chat()
        self.app.message_service.clear_unread("group", item["id"])
        self.refresh_current_session_list()

    def enable_chat_area(self):
        self.input_box.disabled = False
        self.send_btn.disabled = False

    def disable_chat_area(self):
        self.chat_title.value = "请选择一个会话"
        self.chat_list.controls.clear()
        self.input_box.value = ""
        self.input_box.disabled = True
        self.send_btn.disabled = True

    def load_current_chat(self):
        self.chat_list.controls.clear()

        if not self.app.current_chat_type or not self.app.current_target_id:
            return

        messages = self.app.message_service.get_messages(
            self.app.current_chat_type,
            self.app.current_target_id,
        )


        for msg in messages:
            self.chat_list.controls.append( self.render_message(msg) )

    def show_msg(self, msg):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()

    def build_avatar(self, name="", avatar_url=None, size=48):
        if avatar_url:
            return ft.Container(
                width=size,
                height=size,
                border_radius=size // 2,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Image(
                    src=avatar_url,
                    width=size,
                    height=size,
                    fit=ft.ImageFit.COVER,
                )
            )

        return ft.CircleAvatar(
            content=ft.Text(
                name[:1] if name else "我",
                color="white",
            ),
            bgcolor="#07c160",
            radius=size // 2,
        )

    def refresh_current_session_list(self):
        if self.current_nav == "friend":
            self.redraw_friend_sessions()
        elif self.current_nav == "group":
            self.redraw_group_sessions()

        self.page.update()

    def redraw_friend_sessions(self):
        self.session_list.controls.clear()
        for item in self.app.friend_map.values():
            self.session_list.controls.append(
                self.create_session_item(
                    title=item["nickname"],
                    subtitle=f"账号：{item['login_name']}",
                    on_click=lambda e, i=item: self.select_friend(i),
                    chat_type="private",
                    target_id=item["id"],
                    avatar_url=item.get("avatar_url"),
                )
            )
    def redraw_group_sessions(self):
        self.session_list.controls.clear()
        for item in self.app.group_map.values():
            self.session_list.controls.append(
                self.create_session_item(
                    title=item["group_name"],
                    subtitle=f"群成员：{item.get('member_count', 0)}人",
                    on_click=lambda e, i=item: self.select_group(i),
                    chat_type="group",
                    target_id=item["id"],
                )
            )

    def render_message(self, msg):
        if isinstance(msg, dict) and msg.get("kind") == "image":
            sender = msg.get("sender", "")
            sender_text = f"[{sender}]: " if sender else ""

            return ft.Column(
                spacing=4,
                controls=[
                    ft.Text(sender_text, size=14, color="#666666"),
                    ft.Image(src_base64 = msg["content"], width=220, height=160,
                        fit=ft.ImageFit.CONTAIN,border_radius=8,),
                    ft.Text(msg.get("file_name", ""), size=14, color="#999999"),
                ],
            )
        if isinstance(msg, dict) and msg.get("kind") == "file":
            sender = msg.get("sender", "")
            sender_text = f"[{sender}]: " if sender else ""
            file_name = msg.get("file_name", "未知文件")
            save_path = msg.get("save_path", "")

            return ft.Container(
                bgcolor="#f5f5f5",
                border_radius=8,
                padding=10,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(sender_text, size=14, color="#666666"),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color="#576b95"),
                                ft.Text(file_name, size=14, color="#222222", expand=True),
                            ]
                        ),
                        ft.Text(
                            f"已保存到：{save_path}" if save_path else "",
                            size=11,
                            color="#999999",
                        ),
                    ],
                ),
            )
        return ft.Text(str(msg), size=14)

