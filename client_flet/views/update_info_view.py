import os
import flet as ft

from client_flet.services_flet.client_http_services import (
    http_requests_get_user_info,
    http_requests_update_user_info,
)


class UpdateInfoView:
    def __init__(self, page: ft.Page, app):
        self.page = page
        self.app = app
        self.avatar_path = None

        self.avatar_picker = ft.FilePicker(on_result=self.on_avatar_picked)
        self.page.overlay.append(self.avatar_picker)

        self.avatar_preview = ft.Container(
            width=96,
            height=96,
            border_radius=48,
            bgcolor="#07c160",
            alignment=ft.alignment.center,
            content=ft.Text("头像", color="white", size=14),
        )

        self.login_name = ft.TextField(label="账号", read_only=True)
        self.nickname = ft.TextField(label="昵称")

        self.gender = ft.RadioGroup(
            value="男",
            content=ft.Row(
                controls=[
                    ft.Radio(value="男", label="男"),
                    ft.Radio(value="女", label="女"),
                ]
            )
        )

        self.password = ft.TextField(
            label="新密码（不填表示不修改）",
            password=True,
            can_reveal_password=True,
        )

        self.confirm_password = ft.TextField(
            label="重复新密码",
            password=True,
            can_reveal_password=True,
        )

    def build(self):
        self.load_user_info()

        return ft.Container(
            expand=True,
            bgcolor="#f5f5f5",
            alignment=ft.alignment.center,
            content=ft.Container(
                width=460,
                padding=28,
                bgcolor="white",
                border_radius=16,
                content=ft.Column(
                    spacing=14,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("修改个人信息", size=24, weight=ft.FontWeight.BOLD),
                        self.avatar_preview,
                        ft.TextButton("选择新头像", on_click=self.choose_avatar),
                        self.login_name,
                        self.nickname,
                        ft.Container(
                            alignment=ft.alignment.center_left,
                            content=ft.Column([
                                ft.Text("性别", size=13, color="#666666"),
                                self.gender,
                            ]),
                        ),
                        self.password,
                        self.confirm_password,
                        ft.ElevatedButton(
                            text="保存修改",
                            width=320,
                            height=44,
                            bgcolor="#07c160",
                            color="white",
                            on_click=self.submit_update,
                        ),
                        ft.TextButton(
                            text="返回主界面",
                            on_click=lambda e: self.app.show_main_view(),
                        ),
                    ],
                ),
            ),
        )

    def load_user_info(self):
        try:
            resp = http_requests_get_user_info(self.app.user_id)

            if resp["code"] != 0:
                self.show_msg(resp["msg"], "加载失败")
                return

            data = resp["data"]

            self.login_name.value = data["login_name"]
            self.nickname.value = data["nickname"]
            self.gender.value = data["gender"]

            avatar_url = data.get("avatar_url")
            if avatar_url:
                self.avatar_preview.content = ft.Image(
                    src=avatar_url,
                    width=96,
                    height=96,
                    fit=ft.ImageFit.COVER,
                    border_radius=48,
                )

        except Exception as e:
            self.show_msg(str(e), "加载失败")

    def choose_avatar(self, e):
        self.avatar_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
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

    def submit_update(self, e):
        nickname = self.nickname.value.strip()
        gender = self.gender.value
        password = self.password.value.strip()
        confirm_password = self.confirm_password.value.strip()

        if not nickname:
            self.show_msg("昵称不能为空", "修改失败")
            return

        if gender not in ("男", "女"):
            self.show_msg("请选择性别", "修改失败")
            return

        if password or confirm_password:
            if password != confirm_password:
                self.show_msg("两次输入的新密码不一致", "修改失败")
                return

        files = {}

        try:
            if self.avatar_path:
                files["avatar"] = open(self.avatar_path, "rb")

            resp = http_requests_update_user_info(
                user_id=self.app.user_id,
                nickname=nickname,
                gender=gender,
                password=password,
                confirm_password=confirm_password,
                files=files,
            )

            if resp["code"] != 0:
                self.show_msg(resp["msg"], "修改失败")
                return

            self.app.nick_name = resp["data"]["nickname"]
            self.app.head_url = resp["data"]["avatar_url"]

            self.show_msg("个人信息修改成功", "修改成功")

        except Exception as ex:
            self.show_msg(str(ex), "错误")

        finally:
            if "avatar" in files:
                files["avatar"].close()

    def show_msg(self, msg, title="提示"):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(msg),
            actions=[
                ft.TextButton(
                    text="确定",
                    on_click=lambda e: self.close_dialog(dialog),
                )
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()