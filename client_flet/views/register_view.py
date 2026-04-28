import flet as ft
import os

from client_flet.services_flet.client_http_services_v2 import http_requests_register


class RegisterView:
    def __init__(self, page: ft.Page, app):
        self.page = page
        self.app = app
        self.avatar_path = None

        self.avatar_picker = ft.FilePicker(on_result=self.on_avatar_picked)
        self.page.overlay.append(self.avatar_picker)

        # self.avatar_preview = ft.CircleAvatar(
        #     content=ft.Text("头像", size=12, color="white"),
        #     bgcolor="#07c160",
        #     radius=42,
        # )
        self.avatar_preview = ft.Container(
            width=96,
            height=96,
            border_radius=48,
            bgcolor="#07c160",
            alignment=ft.alignment.center,
            content=ft.Text("头像", color="white", size=14),
        )

        self.login_name = ft.TextField(label="登录名", hint_text="只能输入数字")
        self.nickname = ft.TextField(label="昵称")
        self.gender = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="男", label="男"),
                ft.Radio(value="女", label="女"),
            ]),
            value="男",
        )
        self.password = ft.TextField(label="密码", password=True, can_reveal_password=True)
        self.confirm_password = ft.TextField(label="重复密码", password=True, can_reveal_password=True)

    def build(self):
        return ft.Container(
            expand=True,
            bgcolor="#f5f5f5",
            alignment=ft.alignment.center,
            content=ft.Container(
                width=460,
                padding=28,
                bgcolor="white",
                border_radius=16,
                shadow=ft.BoxShadow(
                    blur_radius=18,
                    spread_radius=1,
                    color="#22000000",
                    offset=ft.Offset(0, 6),
                ),
                content=ft.Column(
                    spacing=14,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("注册账号", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("创建你的聊天账号", size=13, color="#888888"),

                        self.avatar_preview,
                        ft.TextButton("选择头像", on_click=self.choose_avatar),

                        self.login_name,
                        self.nickname,

                        ft.Container(
                            alignment=ft.alignment.center_left,
                            content=ft.Column([
                                ft.Text("性别", size=13, color="#666666"),
                                self.gender,
                            ])
                        ),

                        self.password,
                        self.confirm_password,

                        ft.ElevatedButton(
                            text="注册",
                            width=320,
                            height=44,
                            bgcolor="#07c160",
                            color="white",
                            on_click=self.submit_register,
                        ),

                        ft.TextButton(
                            text="返回登录",
                            on_click=lambda e: self.app.show_login_view(),
                        ),
                    ],
                ),
            ),
        )

    def choose_avatar(self, e):
        self.avatar_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE
        )


    def on_avatar_picked(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        self.avatar_path = e.files[0].path

        self.avatar_preview.content = ft.Image(
            src=self.avatar_path,
            width=96,
            height=96,
            fit=ft.ImageFit.COVER,
            border_radius=48,
        )

        self.page.update()

    def submit_register(self, e):
        login_name = self.login_name.value.strip()
        nickname = self.nickname.value.strip()
        gender = self.gender.value
        password = self.password.value.strip()
        confirm_password = self.confirm_password.value.strip()

        if not login_name or not login_name.isdigit():
            self.show_msg("登录名不能为空，且只能是数字")
            return

        if not nickname:
            self.show_msg("昵称不能为空")
            return

        if not password or not confirm_password:
            self.show_msg("密码不能为空")
            return

        if password != confirm_password:
            self.show_msg("两次输入的密码不一致")
            return

        try:
            files = {}
            if self.avatar_path:
                files["avatar"] = open(self.avatar_path, "rb")

            data = {
                "login_name": login_name,
                "nickname": nickname,
                "gender": gender,
                "password": password,
                "confirm_password": confirm_password
            }

            resp = http_requests_register(data=data, files=files)

            if "avatar" in files:
                files["avatar"].close()

            if resp["code"] == 0:
                self.show_msg("注册成功，请返回登录", "注册成功")
            else:
                self.show_msg(resp["msg"], "注册失败")

        except Exception as ex:
            self.show_msg(f"注册失败：{ex}")



    def show_msg(self, msg, title="提示"):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(msg),
            actions=[
                ft.TextButton(
                    text="确定",
                    on_click=lambda e: self.close_dialog(dialog)
                )
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()