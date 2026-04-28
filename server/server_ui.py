import os
import threading
import queue
import time
from datetime import datetime
import flet as ft

import http_server
import socket_server


class ServerUI:

    def __init__(self, page: ft.Page):
        self.event_queue = queue.Queue()            #事件队列，全都poll到里
        self.server_started = False                 #服务器启动标志
        self.closing_event = threading.Event()      #关闭事件的线程

        self.page = page
        self.current_filter = "全部"
        self.all_events = []

        self.title = None                   #页面布局大标题
        self.status_text = None             #服务器状态文本（正在启动、已启动.....）
        self.online_text = None
        self.count_text = None
        self.private_count_text = None
        self.group_count_text = None
        self.message_list = None
        self.close_button = None
        self.clear_button = None

        self.init_page()              #初始化配置
        self.create_controls()        #控件创建
        self.bind_window_event()      #窗口事件绑定
        self.build_layout()           #布局创建
        self.start_backend_servers()  #开启后端服务器http和socket
        self.status_text.value = "服务状态：已启动"
        self.page.update()
        self.page.run_thread( self.poll_events )

    # -----------------------------
    # 基础配置
    # -----------------------------

    def init_page(self):
        self.page.title = "聊天室服务端"
        self.page.padding = 20
        self.page.bgcolor = "#F5F7FB"

        try:
            self.page.window.width = 1000
            self.page.window.height = 800
            self.page.window.min_width = 1000
            self.page.window.min_height = 800
            self.page.window.center()
        except Exception:
            self.page.window_width = 1000
            self.page.window_height = 800
            self.page.window_min_width = 1000
            self.page.window_min_height = 800

    def bind_window_event(self):
        try:
            self.page.window.prevent_close = True
            self.page.window.on_event = self.window_event
        except Exception:
            self.page.window_prevent_close = True
            self.page.on_window_event = self.window_event

    # -----------------------------
    # 后台服务
    # -----------------------------

    def start_http_server_thread(self):
        http_server.app.run(
            host=http_server.HTTP_HOST,
            port=http_server.HTTP_PORT,
            debug=False,
            use_reloader=False
        )

    def push_event_to_ui(cls, event):
        cls.event_queue.put(event)

    def start_backend_servers(self):
        if self.server_started:
            return
        self.server_started = True

        if hasattr(socket_server, "set_ui_event_handler"):
            socket_server.set_ui_event_handler(self.push_event_to_ui)
        else:
            self.event_queue.put({
                "type": "system",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": "警告：socket_server.py 中没有 set_ui_event_handler，聊天事件不会显示到 UI",
                "online_count": 0
            })

        threading.Thread(target = self.start_http_server_thread, daemon=True).start()
        threading.Thread(target = socket_server.start_server, daemon=True).start()

        self.event_queue.put({
            "type": "system",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": "服务端已启动，HTTP 服务和 Socket 服务正在运行",
            "online_count": 0
        })


    # -----------------------------
    # 控件创建
    # -----------------------------
    def create_controls(self):
        self.title = ft.Text(
            "聊天室服务端监控界面",
            size=28,
            weight=ft.FontWeight.BOLD,
            color="#0F172A"
        )

        self.status_text = ft.Text(
            "服务状态：启动中...",
            size=14,
            color="#475569"
        )

        self.online_text = ft.Text(
            "在线人数：0",
            size=18,
            weight=ft.FontWeight.BOLD,
            color="#0F172A"
        )

        self.count_text = ft.Text(
            "事件数量：0",
            size=18,
            weight=ft.FontWeight.BOLD,
            color="#0F172A"
        )

        self.private_count_text = ft.Text(
            "私聊：0",
            size=18,
            weight=ft.FontWeight.BOLD,
            color="#16A34A"
        )

        self.group_count_text = ft.Text(
            "群聊：0",
            size=18,
            weight=ft.FontWeight.BOLD,
            color="#D97706"
        )

        self.message_list = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True
        )

        self.close_button = ft.ElevatedButton(
            "关闭服务端",
            on_click=self.close_app,
            bgcolor="#DC2626",
            color="white"
        )

        self.clear_button = ft.ElevatedButton(
            "清空当前记录",
            on_click=self.clear_events
        )

    def build_stat_card(self, title_text, value_control, bg_color="#FFFFFF"):
        return ft.Container(
            expand=True,
            bgcolor=bg_color,
            border_radius=14,
            padding=16,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(title_text, size=13, color="#64748B"),
                    value_control,
                ]
            )
        )

    def build_event_item(self, event):
        event_type = event.get("type", "system")
        event_time = event.get("time", "")
        text = event.get("text", "")

        style_map = {
            "private": ("私聊", "#16A34A", "#DCFCE7"),
            "group": ("群聊", "#D97706", "#FEF3C7"),
            "login": ("上线", "#2563EB", "#DBEAFE"),
            "logout": ("下线", "#DC2626", "#FEE2E2"),
        }

        tag, tag_color, tag_bg = style_map.get(
            event_type,
            ("系统", "#475569", "#E2E8F0")
        )

        return ft.Container(
            bgcolor="#FFFFFF",
            border_radius=12,
            padding=14,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Container(
                                bgcolor=tag_bg,
                                border_radius=20,
                                padding=ft.padding.symmetric(
                                    horizontal=10,
                                    vertical=4
                                ),
                                content=ft.Text(
                                    tag,
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=tag_color
                                )
                            ),
                            ft.Text(
                                event_time,
                                size=12,
                                color="#64748B"
                            ),
                        ]
                    ),
                    ft.Text(
                        text,
                        size=15,
                        color="#0F172A",
                        selectable=True
                    )
                ]
            )
        )

    def build_filter_row(self):
        return ft.Row(
            spacing=10,
            controls=[
                ft.ElevatedButton("全部", data="全部", on_click=self.change_filter),
                ft.ElevatedButton("只看私聊", data="私聊", on_click=self.change_filter),
                ft.ElevatedButton("只看群聊", data="群聊", on_click=self.change_filter),
                ft.ElevatedButton("系统事件", data="系统", on_click=self.change_filter),
            ]
        )


    # -----------------------------
    # 页面布局
    # -----------------------------
    def build_layout(self):
        self.page.add(
            ft.Column(
                expand=True,
                spacing=16,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    self.title,
                                    self.status_text,
                                ]
                            ),
                            ft.Row(
                                spacing=10,
                                controls=[
                                    self.clear_button,
                                    self.close_button,
                                ]
                            )
                        ]
                    ),

                    ft.Row(
                        spacing=12,
                        controls=[
                            self.build_stat_card("在线状态", self.online_text),
                            self.build_stat_card("全部事件", self.count_text),
                            self.build_stat_card("私聊统计", self.private_count_text),
                            self.build_stat_card("群聊统计", self.group_count_text),
                        ]
                    ),

                    ft.Container(
                        bgcolor="#FFFFFF",
                        border_radius=14,
                        padding=12,
                        border=ft.border.all(1, "#E2E8F0"),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "消息监控信息页",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color="#0F172A"
                                ),
                                self.build_filter_row()
                            ]
                        )
                    ),

                    ft.Container(
                        expand=True,
                        bgcolor="#FFFFFF",
                        border_radius=16,
                        padding=12,
                        border=ft.border.all(1, "#E2E8F0"),
                        content=self.message_list
                    )
                ]
            )
        )


    # -----------------------------
    # 刷新与筛选
    # -----------------------------
    def is_event_visible(self, event):
        event_type = event.get("type", "system")
        if self.current_filter == "私聊":
            return event_type == "private"
        if self.current_filter == "群聊":
            return event_type == "group"
        if self.current_filter == "系统":
            return event_type in ("login", "logout", "system")
        return True

    def refresh_list(self):
        if self.closing_event.is_set():
            return

        self.message_list.controls.clear()

        for event in self.all_events:
            if self.is_event_visible(event):
                self.message_list.controls.append(self.build_event_item(event))

        private_count = sum(
            1 for e in self.all_events
            if e.get("type") == "private"
        )

        group_count = sum(
            1 for e in self.all_events
            if e.get("type") == "group"
        )

        self.count_text.value = f"事件数量：{len(self.all_events)}"
        self.private_count_text.value = f"私聊：{private_count}"
        self.group_count_text.value = f"群聊：{group_count}"

        if self.all_events:
            online_count = self.all_events[-1].get("online_count", 0)
            self.online_text.value = f"在线人数：{online_count}"

        try:
            self.page.update()
        except Exception:
            pass

    def change_filter(self, e):
        self.current_filter = e.control.data
        self.refresh_list()

    def clear_events(self, e):
        self.all_events.clear()

        self.event_queue.put({
            "type": "system",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": "当前界面记录已清空",
            "online_count": 0
        })

    # -----------------------------
    # 关闭逻辑
    # -----------------------------
    def close_app(self, e=None):
        if self.closing_event.is_set():
            return
        self.closing_event.set()
        print("正在关闭服务端程序...")

        try:
            self.status_text.value = "服务状态：正在关闭..."
            self.close_button.disabled = True
            self.close_button.text = "正在关闭..."
            self.page.update()
        except Exception:
            pass

        threading.Thread(target=self.exit_later,daemon=True).start()
        print("已关闭服务端程序。")

    def exit_later(self):
        time.sleep(0.02)

        try:
            self.page.window.prevent_close = False
        except Exception:
            try:
                self.page.window_prevent_close = False
            except Exception:
                pass

        try:
            self.page.window.destroy()
        except Exception:
            try:
                self.page.window.close()
            except Exception:
                pass

        time.sleep(0.02)
        os._exit(0)

    def window_event(self, e):
        if e.data == "close":
            self.close_app(e)


    # -----------------------------
    # 事件轮询
    # -----------------------------
    def poll_events(self):
        while not self.closing_event.is_set():
            changed = False

            while not self.event_queue.empty():
                try:
                    event = self.event_queue.get_nowait()
                except queue.Empty:
                    break

                self.all_events.append(event)

                if len(self.all_events) > 300:
                    self.all_events.pop(0)

                changed = True

            if changed:
                self.refresh_list()

            time.sleep(0.2)


def main(page: ft.Page):
    ServerUI(page)


if __name__ == "__main__":
    ft.app(target=main)