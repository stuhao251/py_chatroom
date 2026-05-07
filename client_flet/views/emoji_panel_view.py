import flet as ft


class EmojiPanelView:
    DEFAULT_EMOJIS = [
        "😀", "😁", "😂", "🤣", "😊", "😍", "😘", "😎",
        "😭", "😡", "👍", "👎", "👏", "🙏", "🎉", "🔥",
        "❤️", "💔", "🌹", "🍉", "☕", "⭐",
    ]

    def __init__(self, page: ft.Page, on_confirm, emojis=None):
        self.page = page
        self.on_confirm = on_confirm
        self.emojis = emojis or self.DEFAULT_EMOJIS

        self.dialog = None
        self.selected_emoji = None
        self.preview_text = None
        self.confirm_btn = None

    def open(self, e=None):
        # 如果之前有残留，先关闭
        if self.dialog:
            self.dialog.open = False

        self.selected_emoji = None

        self.preview_text = ft.Text("请选择一个表情", size=12, color="#888888")

        self.confirm_btn = ft.ElevatedButton(
            text="确认",
            bgcolor="#07c160",
            color="white",
            disabled=True,
            on_click=self.confirm,
        )

        grid = ft.GridView(
            runs_count=6,
            spacing=10,
            run_spacing=10,
            expand=True,
            controls=[
                ft.TextButton(
                    text=emoji,
                    data=emoji,
                    on_click=self.select_emoji,
                )
                for emoji in self.emojis
            ],
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("选择表情"),
            content=ft.Container(
                width=320,
                height=260,
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Container(
                            width=320,
                            height=220,
                            content=grid,
                        ),
                        self.preview_text,
                    ],
                ),
            ),
            actions=[
                ft.TextButton(text="取消", on_click=self.cancel),
                self.confirm_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def select_emoji(self, e):
        self.selected_emoji = e.control.data
        self.preview_text.value = f"已选择：{self.selected_emoji}"
        self.confirm_btn.disabled = False
        self.page.update()

    def confirm(self, e=None):
        if self.selected_emoji:
            self.on_confirm(self.selected_emoji)
        self.close_emoji()

    def cancel(self, e=None):
        self.close_emoji()

    def close_emoji(self):
        if not self.dialog:
            return

        self.dialog.open = False
        self.page.update()