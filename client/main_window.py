import requests
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import io
from services.client_http_services import http_requests_get_friends, http_requests_get_groups


class MainWindow:
    NAV_BG = "#2e2e2e"
    LIST_BG = "#f7f7f7"
    CHAT_BG = "#ffffff"
    PRIMARY = "#07c160"
    BORDER = "#e5e5e5"
    TEXT = "#222222"
    SUB_TEXT = "#888888"

    def __init__(self, app):
        self.app = app
        self.chat_title_label = None    #聊天区域的大标签显示
        self.session_list_frame = None
        self.current_nav = "friend"

    def build(self):
        self.app.clear_window()
        self.app.root.configure(bg="#f5f5f5")
        self.app.root.title("Python聊天室软件")
        self.app.root.geometry("1200x760")
        self.app.root.resizable(True, True)

        root_frame = Frame(self.app.root, bg="#f5f5f5")
        root_frame.pack(fill=BOTH, expand=True)

        # 左侧导航栏-初始化
        nav_frame = Frame(root_frame, bg=self.NAV_BG, width=72)
        nav_frame.pack(side=LEFT, fill=Y)
        nav_frame.pack_propagate(False)

        # 中间会话列表栏-初始化
        list_frame = Frame(root_frame, bg=self.LIST_BG, width=280)
        list_frame.pack(side=LEFT, fill=Y)
        list_frame.pack_propagate(False)

        # 右侧聊天栏-初始化
        chat_frame = Frame(root_frame, bg=self.CHAT_BG)
        chat_frame.pack(side=LEFT, fill=BOTH, expand=True)

        #三个的构建
        self.build_nav_panel(nav_frame)
        self.build_session_panel(list_frame)
        self.build_chat_panel(chat_frame)

        self.switch_nav( self.current_nav )  #默认


    #ui1-导航栏的构造
    def build_nav_panel(self, parent):
        top_user = Frame(parent, bg=self.NAV_BG)
        top_user.pack(fill=X, pady=(16, 20))

        # 加载头像
        self.nav_head_photo = self.load_nav_avatar_from_url(self.app.head_url, size=56)
        self.nav_head_label = Label(top_user, image = self.nav_head_photo, bg=self.NAV_BG, bd=0)
        self.nav_head_label.pack(pady=(0, 8))

        # 昵称和账号显示
        self.nick_label = Label(top_user, text=self.app.nick_name, bg=self.NAV_BG, fg="white", font=("微软雅黑", 9)).pack()
        self.user_label = Label(top_user, text=self.app.user_name, bg=self.NAV_BG, fg="white", font=("微软雅黑", 9)).pack()

        #导航栏下方的几大功能按钮
        self.icon_friend_btn = ImageTk.PhotoImage(Image.open("figures/persons.png").resize((35, 35)))
        self.icon_group_btn = ImageTk.PhotoImage(Image.open("figures/groups.png").resize((35, 35)))
        self.icon_action_btn = ImageTk.PhotoImage(Image.open("figures/set.png").resize((35, 35)))
        btn_friend = Button(
            parent, image = self.icon_friend_btn,
            bg=self.NAV_BG, fg="white", relief=FLAT, bd=0,
            activebackground="#3a3a3a", activeforeground="white",
            command = lambda: self.switch_nav("friend"), cursor="hand2")
        btn_friend.pack(fill=X, pady=(20, 18))

        btn_group = Button(
            parent, image = self.icon_group_btn,
            bg=self.NAV_BG, fg="white", relief=FLAT, bd=0,
            activebackground="#3a3a3a", activeforeground="white",
            command = lambda: self.switch_nav("group"), cursor="hand2")
        btn_group.pack(fill=X, pady=18)

        btn_action = Button(
            parent, image = self.icon_action_btn,
            bg=self.NAV_BG, fg="white", relief=FLAT, bd=0,
            activebackground="#3a3a3a", activeforeground="white",
            command = lambda: self.switch_nav("action"), cursor="hand2")
        btn_action.pack(fill=X, pady=18)


    #ui2-中间会话表栏的构造
    def build_session_panel(self, parent):
        header = Frame(parent, bg=self.LIST_BG, height=86, highlightbackground=self.BORDER, highlightthickness=1)
        header.pack(fill=X)
        header.pack_propagate(False)

        self.session_title_label = Label( header, text = "选择好友或群进行聊天",
            bg = self.LIST_BG, fg = self.TEXT, font = ("微软雅黑", 18, "bold"))
        self.session_title_label.pack(anchor="w", padx=16, pady=(12, 2))

        Label(header, text=f"{self.app.nick_name}（{self.app.user_name}）",
            bg = self.LIST_BG,fg = self.SUB_TEXT, font=("微软雅黑", 11)
        ).pack(anchor="w", padx=16)

        # ===== 列表区域容器 =====
        list_container = Frame(parent, bg=self.LIST_BG)
        list_container.pack(fill=BOTH, expand=True)

        # 纵向滚动条
        self.session_scrollbar = Scrollbar(list_container, orient=VERTICAL)
        self.session_scrollbar.pack(side=RIGHT, fill=Y)

        # Canvas
        self.session_list_canvas = Canvas(
            list_container, bg=self.LIST_BG,
            highlightthickness=0, bd=0,
            yscrollcommand=self.session_scrollbar.set)
        self.session_list_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # 滚动条和 canvas 互相绑定
        self.session_scrollbar.config(command = self.session_list_canvas.yview)

        # 真正放列表项的 frame
        self.session_list_frame = Frame(self.session_list_canvas, bg=self.LIST_BG)

        self.session_window_id = self.session_list_canvas.create_window(
            (0, 0), window=self.session_list_frame, anchor="nw")

        # 内容变化时更新滚动区域
        self.session_list_frame.bind(
            "<Configure>",
            lambda e: self.session_list_canvas.configure(scrollregion=self.session_list_canvas.bbox("all")) )

        # Canvas 大小变化时，让内部 frame 跟着变宽
        self.session_list_canvas.bind(
            "<Configure>",
            lambda e: self.session_list_canvas.itemconfigure(self.session_window_id, width=e.width) )

        # 鼠标滚轮支持
        self.session_list_canvas.bind("<Enter>",
                                      lambda e: self.session_list_canvas.bind_all("<MouseWheel>",
                                     self.on_session_mousewheel))
        self.session_list_canvas.bind("<Leave>",
                                      lambda e: self.session_list_canvas.unbind_all("<MouseWheel>"))
    #鼠标滚轮函数
    def on_session_mousewheel(self, event):
        if self.session_list_canvas.winfo_exists():
            self.session_list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    #ui3-聊天栏的会话
    def build_chat_panel(self, parent):
        # 顶部标题栏
        top = Frame(parent, bg=self.CHAT_BG, height=64, highlightbackground=self.BORDER, highlightthickness=1)
        top.pack(fill=X)
        top.pack_propagate(False)

        self.chat_title_label = Label(top, text="请选择一个会话", bg=self.CHAT_BG, fg=self.TEXT, font=("微软雅黑", 14, "bold"))
        self.chat_title_label.pack(anchor="w", padx=20, pady=(16, 0))

        # 聊天记录区
        msg_frame = Frame(parent, bg=self.CHAT_BG, highlightbackground=self.BORDER, highlightthickness=1)
        msg_frame.pack(fill=BOTH, expand=True)

        self.app.text_area = Text(msg_frame, state=DISABLED, font=("微软雅黑", 11),
            bg=self.CHAT_BG, fg=self.TEXT, bd=0, wrap="word", padx=4, pady=4)
        self.app.text_area.pack(fill=BOTH, expand=True, padx=16, pady=12)

        # 底部输入区：
        input_wrap = Frame(parent, bg = "#f5f5f5", height = 190,
            highlightbackground = self.BORDER, highlightthickness = 1)
        input_wrap.pack(fill=X)
        input_wrap.pack_propagate(False)

        input_wrap.grid_rowconfigure(0, weight=0)  # 工具栏
        input_wrap.grid_rowconfigure(1, weight=1)  # 输入框
        input_wrap.grid_rowconfigure(2, weight=0)  # 发送栏
        input_wrap.grid_columnconfigure(0, weight=1)

        # 工具栏
        tool_bar = Frame(input_wrap, bg="#f5f5f5", height=32)
        tool_bar.grid(row=0, column=0, sticky="ew", padx=14, pady=(8, 2))
        tool_bar.grid_propagate(False)

        self.icon_emoj_btn = ImageTk.PhotoImage(Image.open("figures/emoji.png").resize((20, 20)))
        self.icon_pics_btn = ImageTk.PhotoImage(Image.open("figures/pictures.png").resize((20, 20)))
        self.icon_links_btn = ImageTk.PhotoImage(Image.open("figures/links.png").resize((20, 20)))
        self.btn_emoji = Button(tool_bar, image = self.icon_emoj_btn, relief=FLAT,
            bd=0, bg="#f5f5f5", activebackground="#ebebeb",
            cursor="hand2", command = self.app.send_emoji).pack(side=LEFT, padx=(0, 8))
        self.btn_pics = Button( tool_bar, image = self.icon_pics_btn, relief=FLAT,
            bd=0, bg="#f5f5f5", activebackground="#ebebeb",
            cursor="hand2", command = self.app.send_image).pack(side=LEFT, padx=8)
        self.btn_links = Button(tool_bar, image = self.icon_links_btn,relief=FLAT,
            bd=0,bg="#f5f5f5",activebackground="#ebebeb",
               cursor="hand2",command = self.app.send_file).pack(side=LEFT, padx=8)

        # 输入框白色面板
        editor_panel = Frame(input_wrap, bg="white", highlightbackground="#e7e7e7", highlightthickness=1)
        editor_panel.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 4))

        self.app.entry_msg = Text(editor_panel, font=("微软雅黑", 11),
            bd=0, bg="white", fg=self.TEXT, insertbackground = self.TEXT, wrap="word")
        self.app.entry_msg.pack(fill=BOTH, expand=True, padx=12, pady=10)

        # 发送栏：单独一整行
        send_bar = Frame(input_wrap, bg="#f5f5f5", height=44)
        send_bar.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))
        send_bar.grid_propagate(False)

        # 右对齐格式-发送按钮
        send_bar.grid_columnconfigure(0, weight=1)
        send_bar.grid_columnconfigure(1, weight=0)
        self.send_btn = Button(send_bar, text="发送",
            command = self.app.send_text,
            font=("微软雅黑", 10), bg=self.PRIMARY,
            fg="white", activebackground="#06ad56",
            activeforeground="white", relief=FLAT, bd=0,
            cursor="hand2", width=10, height=1)
        self.send_btn.grid(row=0, column=1, sticky="e", padx=(0, 16), pady=(4, 4))


    #d-导航栏功能的选择
    def switch_nav(self, mode):
        self.current_nav = mode
        for widget in self.session_list_frame.winfo_children():
            widget.destroy()
        if mode == "friend":
            self.session_title_label.config(text = "好友列表" )
            self.chat_title_label.config(text='')
            self.load_friend_sessions()

            self.disable_chat_area( self.current_nav )
        elif mode == "group":
            self.session_title_label.config(text = "群聊列表" )
            self.chat_title_label.config(text='')
            self.load_group_sessions()

            self.disable_chat_area( self.current_nav )
        elif mode == "action":
            self.session_title_label.config(text = "功能菜单" )
            self.chat_title_label.config(text='')
            self.load_action_sessions()

            self.disable_chat_area( self.current_nav )
    #d1-加载好友列表的逻辑
    def load_friend_sessions(self):
        self.app.friend_map.clear()
        try:
            resp = http_requests_get_friends(self.app.user_id)
            friends = resp["data"]

            for item in friends:
                key = f'{item["nickname"]}（{item["login_name"]}）'
                self.app.friend_map[key] = item
                self.create_session_item(
                    self.session_list_frame, item = item,
                    command=lambda i = item: self.select_friend(i), is_group=False )
        except Exception as e:
            messagebox.showerror("错误", str(e))
    #d2-加载群聊列表的逻辑
    def load_group_sessions(self):
        self.app.group_map.clear()
        try:
            resp = http_requests_get_groups(self.app.user_id)
            groups = resp["data"]
            for item in groups:
                key = f'{item["group_name"]}（{item["member_count"]}人）'
                self.app.group_map[key] = item
                self.create_session_item(
                    self.session_list_frame, item=item,
                    command = lambda i = item: self.select_group(i), is_group=True )
        except Exception as e:
            messagebox.showerror("错误", str(e))
    #d3-加载功能菜单列表逻辑
    def load_action_sessions(self):
        actions = [
            ("添加好友", self.app.add_friend),
            ("删除好友", self.app.delete_friend),
            ("创建群聊", self.app.create_group),
            ("加入群聊", self.app.join_group),
            ("删除群聊", self.app.delete_group),
            ("退出群聊", self.app.quit_group),
            ("修改信息", self.app.open_updateinfo_window),
        ]
        for text, cmd in actions:
            self.create_setting_item(self.session_list_frame, text, cmd)

    #单个聊天元素的创建（单个好友或群聊框）
    def create_session_item(self, parent, item, command, is_group=False):
        if is_group:
            title = item["group_name"]
            subtitle = f'群成员：{item["member_count"]}人'
            unread = self.app.message_service.get_unread("group", item["id"])   #获取未读数量
        else:
            title = item["nickname"]
            subtitle = f'账号：{item["login_name"]}'
            unread = self.app.message_service.get_unread("private", item["id"]) #获取未读数量

        box = Frame( parent, bg="white", highlightbackground = self.BORDER,
            highlightthickness = 1, cursor = "hand2")
        box.pack(fill=X, expand = True, padx = 8, pady = 6)

        avatar = Label(box, text = "头像", bg= "#dddddd",
                       fg = "#666666", width = 6,height= 3, cursor= "hand2")
        avatar.pack(side=LEFT, padx=12, pady=12)

        info = Frame(box, bg="white", cursor="hand2")
        info.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 12), pady=10)

        title_label = Label(info, text=title, bg="white", fg=self.TEXT,
            font=("微软雅黑", 12, "bold"), anchor="w", justify=LEFT, cursor="hand2")
        title_label.pack(fill=X)

        subtitle_label = Label(info, text=subtitle, bg="white", fg=self.SUB_TEXT,
            font=("微软雅黑", 10), anchor="w", justify=LEFT, cursor="hand2")
        subtitle_label.pack(fill=X, pady=(4, 0))

        # 红点,未读数字的构建
        if unread > 0:
            unread_text = str(unread) if unread < 100 else "99+"

            unread_label = Label(box, text = unread_text, bg="#fa5151", fg="white",
                font=("微软雅黑", 9, "bold"),padx=6, pady=1 )
            unread_label.pack(side=RIGHT, padx=10)

        def on_click(event=None):
            command()

        #self.bind_click_recursive(box, on_click)
        box.bind("<Button-1>", on_click)
        avatar.bind("<Button-1>", on_click)
        info.bind("<Button-1>", on_click)
        title_label.bind("<Button-1>", on_click)
        subtitle_label.bind("<Button-1>", on_click)

    #单个设置功能框的构建
    def create_setting_item(self, parent, title, command):
        item = Button(parent, text=title, command = command,
            font=("微软雅黑", 11), bg="white", fg=self.TEXT,
            activebackground="#f0f0f0", relief=FLAT, bd=0, pady=14, cursor = "hand2")
        item.pack(fill=X, padx=10, pady=6)


    # 选中好友时的逻辑
    def select_friend(self, item):
        self.enable_chat_area()

        self.app.current_chat_type = "private"
        self.app.current_target_id = item["id"]
        self.app.current_target_name = item["nickname"]
        self.chat_title_label.config( text = f'{item["nickname"]}  ({item["login_name"]})' )

        self.app.message_service.clear_unread("private", item["id"]) #清除未读数和内容
        self.app.load_current_chat()                                 #加载当前的对话
        self.refresh_current_session_list()                          #更新列表，把显示框未读数更新掉

    # 选中群聊时的逻辑
    def select_group(self, item):
        self.enable_chat_area()

        self.app.current_chat_type = "group"
        self.app.current_target_id = item["id"]
        self.app.current_target_name = item["group_name"]

        members = item.get("member_names", "")
        if len(members) > 30:
            members = members[:30] + "..."
        self.chat_title_label.config(text= f'{item["group_name"]}({item["member_count"]}人)：{members}')

        self.app.message_service.clear_unread("group", item["id"])  #清除未读数和内容
        self.app.load_current_chat()                                #加载当前的对话
        self.refresh_current_session_list()                         #更新列表，把显示框未读数更新掉

    #禁用当前聊天区按钮
    def disable_chat_area(self, current_nav):
        # 清空当前会话状态
        self.app.current_chat_type = None
        self.app.current_target_id = None
        self.app.current_target_name = None

        # 标题改掉
        # if hasattr(self, "chat_title_label") and self.chat_title_label:
        #     self.chat_title_label.config(text="当前为功能面板")
        if current_nav == "friend":
            self.chat_title_label.config(text="进入私聊对象区")
        if current_nav == "group":
            self.chat_title_label.config(text="进入群聊对象区")
        if current_nav == "action":
            self.chat_title_label.config(text="进入功能面板区")

        # 清空聊天内容
        if self.app.text_area:
            self.app.text_area.config(state=NORMAL)
            self.app.text_area.delete("1.0", END)
            self.app.text_area.config(state=DISABLED)

        # 输入框禁用
        if self.app.entry_msg:
            self.app.entry_msg.delete("1.0", END)
            self.app.entry_msg.config(state=DISABLED)

        # 发送区的工具按钮禁用
        if hasattr(self, "btn_emoji") and self.btn_emoji:
            self.btn_emoji.config(state=DISABLED)
        if hasattr(self, "btn_pics") and self.btn_pics:
            self.btn_pics.config(state=DISABLED)
        if hasattr(self, "btn_links") and self.btn_links:
            self.btn_links.config(state=DISABLED)
        # 发送区的发送按钮禁用
        if hasattr(self, "send_btn") and self.send_btn:
            self.send_btn.config(state=DISABLED)

    #允许聊天区按钮可用
    def enable_chat_area(self):
        if hasattr(self, "btn_emoji") and self.btn_emoji:
            self.btn_emoji.config(state=NORMAL)
        if hasattr(self, "btn_pics") and self.btn_pics:
            self.btn_pics.config(state=NORMAL)
        if hasattr(self, "btn_links") and self.btn_links:
            self.btn_links.config(state=NORMAL)
        if hasattr(self, "send_btn") and self.send_btn:
            self.send_btn.config(state=NORMAL)

        if self.app.entry_msg:
            self.app.entry_msg.config(state=NORMAL)

    #制作导航栏-默认头像
    def make_nav_default_avatar(self, size=64):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 外层圆背景
        draw.ellipse((0, 0, size - 1, size - 1), fill=(90, 90, 90, 255))

        # 头部
        head_r = int(size * 0.18)
        head_x1 = size // 2 - head_r
        head_y1 = int(size * 0.20)
        head_x2 = size // 2 + head_r
        head_y2 = head_y1 + head_r * 2
        draw.ellipse((head_x1, head_y1, head_x2, head_y2), fill=(220, 220, 220, 255))

        # 身体
        body_w = int(size * 0.52)
        body_h = int(size * 0.28)
        body_x1 = size // 2 - body_w // 2
        body_y1 = int(size * 0.55)
        body_x2 = body_x1 + body_w
        body_y2 = body_y1 + body_h
        draw.rounded_rectangle((body_x1, body_y1, body_x2, body_y2), radius=body_h // 2, fill=(220, 220, 220, 255))

        return ImageTk.PhotoImage(img)

    #加载导航栏显示头像
    def load_nav_avatar_from_url(self, url, size=64):
        try:
            if not url:
                return self.make_nav_default_avatar(size)

            resp = requests.get(url, timeout=8)
            resp.raise_for_status()

            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")

            # 强制裁剪成正方形（避免变形）
            w, h = img.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))

            # 强制拉伸到指定尺寸（关键！）
            img = img.resize((size, size), Image.LANCZOS)

            # 圆形遮罩
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)

            result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            result.paste(img, (0, 0), mask)

            return ImageTk.PhotoImage(result)
        except Exception as e:
            print("头像加载失败:", e)
            return self.make_nav_default_avatar(size)



    #更新当前列表内容
    def refresh_current_session_list(self):
        for widget in self.session_list_frame.winfo_children():
            widget.destroy()

        if self.current_nav == "friend":
            self.redraw_friend_sessions()
        elif self.current_nav == "group":
            self.redraw_group_sessions()
        elif self.current_nav == "action":
            self.load_action_sessions()
    #更新好友列表
    def redraw_friend_sessions(self):
        for widget in self.session_list_frame.winfo_children():
            widget.destroy()

        for _, item in self.app.friend_map.items():
            self.create_session_item( self.session_list_frame, item = item,
                command=lambda i=item: self.select_friend(i),  is_group=False)
    #更新群聊列表
    def redraw_group_sessions(self):
        for widget in self.session_list_frame.winfo_children():
            widget.destroy()

        for _, item in self.app.group_map.items():
            self.create_session_item(self.session_list_frame,  item=item,
                command=lambda i=item: self.select_group(i),  is_group=True)


    #刷新导航栏界面的用户头像、昵称
    def refresh_user_info(self):
        print("refresh_user_info 被调用了")
        print("最新昵称:", self.app.nick_name)
        print("最新头像:", self.app.head_url)
        # 刷新昵称
        if hasattr(self, "nick_label") and self.nick_label:
            self.nick_label.config(text = self.app.nick_name)

        # 账号一般不变，但也可以顺手刷新
        # if hasattr(self, "user_label") and self.user_label:
        #     self.user_label.config(text = self.app.user_name)

        # 刷新头像
        if hasattr(self, "avatar_label") and self.nav_head_label:
            self.nav_head_photo = self.load_nav_avatar_from_url(self.app.head_url, size=64)
            self.nav_head_label.config(image=self.nav_head_photo)

