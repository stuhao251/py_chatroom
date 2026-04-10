from tkinter import *
from tkinter import messagebox

from register_window import RegisterWindow
from services.client_http_services import http_requests_login


class LoginWindow:
    def __init__(self, app):
        self.app = app
        self.root = app.root

        self.entry_username = None
        self.entry_password = None

    def build(self):
        self.app.clear_window()

        self.root.title("登录")

        # 整体窗口风格
        self.root.configure(bg="#f5f5f5")
        self.root.geometry("460x440")
        self.root.resizable(False, False)

        # 最外层框架
        outer = Frame(self.root, bg="#f5f5f5")
        outer.pack(fill=BOTH, expand=True)

        # 中间大卡片容器
        card = Frame(outer, bg="white", highlightbackground="#e8e8e8", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=400)

        # 1-标题区
        Label(card, text="欢迎使用Python版本聊天室", font=("微软雅黑", 18, "bold")
              , bg="white", fg="#222222").pack( pady=(28, 6) )
        Label(card, text="登录你的聊天账号", font=("微软雅黑", 10), bg="white", fg="#888888").pack(pady=(0, 20))

        # 输入区域容器
        form = Frame(card, bg="white")
        form.pack(fill=X, padx=32)

        # 2-登录名-标签
        Label(form, text="登录名", font=("微软雅黑", 10), bg="white", fg="#222222").pack(anchor="w", pady=(0, 6))

        # 3-登录名-输入框
        username_box = Frame(form, bg="#fafafa", highlightbackground="#e8e8e8", highlightthickness=1)
        username_box.pack(fill=X, pady=(0, 14))
        self.entry_username = Entry(username_box, font=("微软雅黑", 11), bd=0,
                                    bg="#fafafa", fg="#222222", insertbackground="#222222")
        self.entry_username.pack(fill=X, padx=12, pady=10)

        # 4-密码-标签
        Label(form, text="密码", font=("微软雅黑", 10), bg="white", fg="#222222").pack(anchor="w", pady=(0, 6))

        # 5-密码-输入框
        password_box = Frame(form, bg="#fafafa", highlightbackground="#e8e8e8", highlightthickness=1)
        password_box.pack(fill=X, pady=(0, 18))
        self.entry_password = Entry(password_box, font=("微软雅黑", 11), bd=0, bg="#fafafa",
                                    fg="#222222", insertbackground="#222222", show="*")
        self.entry_password.pack(fill=X, padx=12, pady=10)

        # 6-主按钮：登录
        Button(card, text="登录", width=28, command = self.login, font=("微软雅黑", 11),
               bg="#07c160", fg="white", activebackground="#06ad56", activeforeground="white",
               relief=FLAT, bd=0, pady=9, cursor="hand2").pack(pady=(0, 12))

        # 7-次按钮区域(注册)
        bottom_frame = Frame(card, bg="white")
        bottom_frame.pack()
        Button(bottom_frame, text="注册账号", command=self.open_register_window,
               font=("微软雅黑", 10), bg="white", fg="#576b95", activebackground="white",
               activeforeground="#445a88", relief=FLAT, bd=0, cursor="hand2").pack(side=LEFT, padx=10)

        self.root.bind("<Return>", self.on_enter_login) #给登录按钮绑定回车键

    def on_enter_login(self, event):
        self.login()

    def open_register_window(self):
        RegisterWindow(self.root)

    def login(self):
        login_name = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        try:
            #1 发送http登录请求
            resp = http_requests_login(login_name, password)

            if resp["code"] != 0:
                messagebox.showerror("登录失败", resp["msg"])
                return

            # 把响应值付给本主窗口的属性
            self.app.user_id = resp["data"]["user_id"]
            self.app.nick_name = resp["data"]["nickname"]
            self.app.user_name = resp["data"]["login_name"]
            self.app.head_url = resp["data"]["avatar_url"]

            # 2 调用socket，发起socket连接
            ok, msg = self.app.socket_service.connect(
                self.app.user_id,
                self.app.user_name,
                self.app.nick_name
            )
            if not ok:
                messagebox.showerror("登录失败", msg)
                return

            # 3 登录成功显示聊天界面
            self.root.unbind("<Return>")
            self.app.show_main_ui()

        except Exception as e:
            messagebox.showerror("错误", str(e))