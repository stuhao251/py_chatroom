import flet as ft
import os

from views.login_view import LoginView
from views.register_view import RegisterView
from views.main_view import MainView
from views.update_info_view import UpdateInfoView
from services_flet.socket_service_v2 import SocketService
from services_flet.message_service_v2 import MessageService
from controller import ChatController

class ChatApp:
    def __init__(self, page: ft.Page):
        self.page = page

        self.user_id = None
        self.user_name = None
        self.nick_name = None
        self.head_url = None
        self.current_chat_type = None
        self.current_target_id = None
        self.current_target_name = None
        self.file_save_dir = os.path.join(os.getcwd(), "received_files")

        self.message_service = MessageService()
        self.controller = ChatController(self)
        self.socket_service = SocketService(self.controller.handle_message)


    def run(self):
        self.show_login_view()

    def clear_page(self):
        self.page.controls.clear()

    def show_login_view(self):
        self.clear_page()
        self.page.add( LoginView(self.page, self).build() )
        self.page.update()

    def show_register_view(self):
        self.clear_page()
        self.page.add( RegisterView(self.page, self).build() )
        self.page.update()

    def show_main_view(self):
        self.clear_page()
        self.main_view = MainView(self.page, self)
        self.controller.bind_view( self.main_view )
        self.page.add( self.main_view.build() )
        self.main_view.switch_nav("")
        self.page.update()

    def update_chat_ui(self):
        self.main_view.load_current_chat()
        self.page.update()

    def open_updateinfo_window(self):
        self.clear_page()
        self.page.add( UpdateInfoView(self.page, self).build() )
        self.page.update()

    def log_out(self):
        try:
            if self.socket_service:
                self.socket_service.send_json({
                    "type": "logout_socket",
                    "user_id": self.user_id
                })
                self.socket_service.close()
        except Exception:
            pass
        self.user_id = None
        self.user_name = None
        self.nick_name = None
        self.head_url = None
        self.current_chat_type = None
        self.current_target_id = None
        self.current_target_name = None
        self.main_view = None

        self.show_login_view()

    def add_friend(self):
        self.controller.add_friend()

    def delete_friend(self):
        self.controller.delete_friend()

    def create_group(self):
        self.controller.create_group()

    def join_group(self):
        self.controller.join_group()

    def delete_group(self):
        self.controller.delete_group()

    def quit_group(self):
        self.controller.quit_group()

    def open_file_save_path_dialog(self):
        self.controller.open_file_save_path_dialog()


def main(page: ft.Page):
    page.title = "Python 聊天室"
    try:
        page.window.width = 1000
        page.window.height = 730
        page.window.center()
    except Exception:
        page.window_width = 1000
        page.window_height = 730
    page.padding = 0
    page.bgcolor = "#f5f5f5"

    app = ChatApp(page)
    app.run()


if __name__ == "__main__":
    ft.app(target=main)