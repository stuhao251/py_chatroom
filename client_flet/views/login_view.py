import flet as ft
from client_flet.services_flet.client_http_services_v2 import http_requests_login


class LoginView:
    def __init__(self, page: ft.Page, app):
        self.page = page
        self.app = app

        self.username = ft.TextField(label="登录名", border_radius=8, height=48, text_size=14,)
        self.password = ft.TextField(label="密码", password=True, can_reveal_password=True,
            border_radius=8, height=48, text_size=14,)

    def build(self):
        return ft.Container(
            expand=True, bgcolor="#f5f5f5", alignment=ft.alignment.center,
            content = ft.Container(
                width=400,
                padding=32,
                bgcolor="white",
                border_radius=16,
                shadow=ft.BoxShadow(
                    blur_radius=18,
                    spread_radius=1,
                    color="#22000000",
                    offset=ft.Offset(0, 6),
                ),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=18,
                    controls=[
                        ft.Text(
                            "欢迎使用 Python 聊天室",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color="#222222",
                        ),
                        ft.Text(
                            "登录你的聊天账号",
                            size=13,
                            color="#888888",
                        ),
                        self.username,
                        self.password,
                        ft.Button(
                            content = ft.Text("登录"),
                            bgcolor="#07c160",
                            color="white",
                            height=44,
                            width=320,
                            on_click = self.login,
                        ),
                        ft.TextButton(
                            text="注册账号",
                            on_click = self.open_register,
                            style=ft.ButtonStyle(color="#576b95"),
                        ),
                    ],
                ),
            ),
        )

    def login(self, e):
        login_name = self.username.value.strip()
        password = self.password.value.strip()

        if not login_name or not password:
            self.show_msg("请输入登录名和密码")
            return

        try:
            resp = http_requests_login(login_name, password)

            if resp["code"] != 0:
                self.show_msg(resp["msg"])
                return

            self.app.user_id = resp["data"]["user_id"]
            self.app.user_name = resp["data"]["login_name"]
            self.app.nick_name = resp["data"]["nickname"]
            self.app.head_url = resp["data"].get("avatar_url")

            ok, msg = self.app.socket_service.connect(
                self.app.user_id,
                self.app.user_name,
                self.app.nick_name,
            )

            if not ok:
                self.show_msg(msg)
                return

            self.app.show_main_view()

        except Exception as ex:
            self.show_msg(f"登录失败：{ex}")

    def open_register(self, e):
        self.app.show_register_view()

    def show_msg(self, msg, title="提示"):
        dialog = ft.AlertDialog(
            modal=True,
            title= ft.Text(title),
            content= ft.Text(msg),
            actions=[
                ft.TextButton( text="确定",  on_click=lambda e: self.close_dialog(dialog) )
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()