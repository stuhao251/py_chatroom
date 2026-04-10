import os
import requests
from tkinter import *
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk, ImageDraw, ImageOps

from server.config import HTTP_BASE


class RegisterWindow:
    BG_COLOR = "#f5f5f5"
    CARD_COLOR = "#ffffff"
    PRIMARY_COLOR = "#07c160"
    PRIMARY_ACTIVE = "#06ad56"
    TEXT_COLOR = "#222222"
    SUB_TEXT_COLOR = "#888888"
    BORDER_COLOR = "#e8e8e8"
    INPUT_BG = "#fafafa"

    def __init__(self, parent):
        self.parent = parent
        self.top = Toplevel(parent)
        self.top.title("用户注册")
        self.top.geometry("500x950+420+20")
        self.top.resizable(False, False)
        self.top.configure(bg=self.BG_COLOR)


        self.top.grab_set()
        self.top.focus_force()
        self.top.lift()
        self.top.protocol("WM_DELETE_WINDOW", self.go_back)

        self.avatar_path = ""
        self.avatar_photo = None

        self.build_ui()

    def build_ui(self):
        # 最外层
        container = Frame(self.top, bg=self.BG_COLOR)
        container.pack(fill=BOTH, expand=True)

        # 画布 + 滚动条
        self.canvas = Canvas(
            container,
            bg=self.BG_COLOR,
            highlightthickness=0,
            bd=0
        )
        self.v_scroll = Scrollbar(container, orient=VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set)

        self.v_scroll.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # 真正放内容的 frame
        self.scroll_frame = Frame(self.canvas, bg=self.BG_COLOR)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        # 绑定尺寸更新
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # 鼠标滚轮
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        # 把原来所有内容放到 scroll_frame 里
        self.build_form_content(self.scroll_frame)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def build_form_content(self, parent):
        outer = Frame(parent, bg=self.BG_COLOR)
        outer.pack(fill=BOTH, expand=True, padx=15, pady=20)

        # 标题区域
        title_frame = Frame(outer, bg=self.BG_COLOR)
        title_frame.pack(fill=X, pady=(0, 10))

        Label(title_frame, text="注册", font=("微软雅黑", 20, "bold"),
              bg=self.BG_COLOR,fg=self.TEXT_COLOR).pack(anchor="center")

        Label(title_frame,text="创建你的聊天账号",font=("微软雅黑", 10),
            bg=self.BG_COLOR,fg=self.SUB_TEXT_COLOR).pack(anchor="center", pady=(1, 0))

        # 卡片区域
        card = Frame(outer,bg=self.CARD_COLOR,
            highlightbackground=self.BORDER_COLOR,highlightthickness=1)
        card.pack(fill=BOTH, expand=True)

        # 卡片-头像区域
        avatar_section = Frame(card, bg=self.CARD_COLOR)
        avatar_section.pack(fill=X, pady=(20, 10))

        self.avatar_preview = Label(avatar_section, bg=self.CARD_COLOR, bd=0)
        self.avatar_preview.pack()

        self.show_default_avatar()

        Button(avatar_section, text="选择头像", command=self.choose_avatar, font=("微软雅黑", 10),
            bg="#f2f2f2", fg=self.TEXT_COLOR, activebackground="#eaeaea", relief=FLAT,
            bd=0, padx=18, pady=6, cursor="hand2").pack(pady=(10, 0))

        self.avatar_path_label = Label(
            avatar_section,
            text="未选择图片",
            font=("微软雅黑", 9),
            bg=self.CARD_COLOR,
            fg=self.SUB_TEXT_COLOR
        )
        self.avatar_path_label.pack(pady=(3, 0))

        # 卡片-表单区域
        form = Frame(card, bg=self.CARD_COLOR)
        form.pack(fill=BOTH, expand=True, padx=23, pady=(20, 10))
        form.grid_columnconfigure(0, weight=1)

        self.entry_login_name = self.create_input_row(
            form,
            row=0,
            label_text="登录名",
            validate_digits=True,
            trailing_button=("检查", self.check_login_name)
        )

        self.login_hint = Label(
            form,
            text="1-10位数字",
            font=("微软雅黑", 9),
            bg=self.CARD_COLOR,
            fg="#fa5151"
        )
        self.login_hint.grid(row=2, column=0, sticky="w", pady=(0, 10))

        self.entry_nickname = self.create_input_row(
            form,
            row=3,
            label_text="昵称"
        )

        self.create_gender_row(form, row=5)

        self.entry_password = self.create_input_row(
            form,
            row=7,
            label_text="密码",
            show="*"
        )

        self.entry_confirm_password = self.create_input_row(
            form,
            row=9,
            label_text="重复密码",
            show="*"
        )

        # 底部按钮
        btn_frame = Frame(card, bg=self.CARD_COLOR)
        btn_frame.pack(fill=X, padx=20, pady=(8, 22))

        Button(
            btn_frame,
            text="注册",
            command=self.submit_register,
            font=("微软雅黑", 11),
            bg=self.PRIMARY_COLOR,
            fg="white",
            activebackground=self.PRIMARY_ACTIVE,
            activeforeground="white",
            relief=FLAT,
            bd=0,
            pady=5,
            cursor="hand2"
        ).pack(fill=X)

        Button(
            btn_frame,
            text="返回",
            command=self.go_back,
            font=("微软雅黑", 10),
            bg=self.CARD_COLOR,
            fg=self.SUB_TEXT_COLOR,
            activebackground=self.CARD_COLOR,
            activeforeground=self.TEXT_COLOR,
            relief=FLAT,
            bd=0,
            pady=5,
            cursor="hand2"
        ).pack(fill=X, pady=(10, 0))

    def create_input_row(self, parent, row, label_text, show=None, validate_digits=False, trailing_button=None):
        Label(
            parent,
            text=label_text,
            font=("微软雅黑", 10),
            bg=self.CARD_COLOR,
            fg=self.TEXT_COLOR
        ).grid(row=row, column=0, sticky="w", pady=(0, 6))

        row_frame = Frame(parent, bg=self.CARD_COLOR)
        row_frame.grid(row=row + 1, column=0, columnspan=3, sticky="ew", pady=(0, 14))

        input_box = Frame(
            row_frame,
            bg=self.INPUT_BG,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1
        )
        input_box.pack(side=LEFT, fill=X, expand=True)

        entry_opts = {
            "font": ("微软雅黑", 11),
            "bd": 0,
            "bg": self.INPUT_BG,
            "fg": self.TEXT_COLOR,
            "insertbackground": self.TEXT_COLOR
        }

        if show:
            entry_opts["show"] = show

        if validate_digits:
            vcmd = (self.top.register(self.validate_login_name_input), "%P")
            entry_opts["validate"] = "key"
            entry_opts["validatecommand"] = vcmd

        entry = Entry(input_box, **entry_opts)
        entry.pack(fill=X, padx=12, pady=10)

        if trailing_button:
            btn_text, btn_cmd = trailing_button
            Button(
                row_frame,
                text=btn_text,
                command=btn_cmd,
                font=("微软雅黑", 9),
                bg="#f2f2f2",
                fg=self.TEXT_COLOR,
                activebackground="#eaeaea",
                relief=FLAT,
                bd=0,
                padx=14,
                pady=9,
                cursor="hand2"
            ).pack(side=LEFT, padx=(10, 0))

        return entry

    def create_gender_row(self, parent, row):
        Label(
            parent,
            text="性别",
            font=("微软雅黑", 10),
            bg=self.CARD_COLOR,
            fg=self.TEXT_COLOR
        ).grid(row=row, column=0, sticky="w", pady=(0, 6))

        gender_wrap = Frame(
            parent,
            bg=self.INPUT_BG,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1
        )
        gender_wrap.grid(row=row + 1, column=0, columnspan=3, sticky="ew", pady=(0, 14))

        self.gender_var = StringVar(value="男")

        inner = Frame(gender_wrap, bg=self.INPUT_BG)
        inner.pack(anchor="w", padx=10, pady=8)

        Radiobutton(
            inner,
            text="男",
            variable=self.gender_var,
            value="男",
            font=("微软雅黑", 10),
            bg=self.INPUT_BG,
            fg=self.TEXT_COLOR,
            activebackground=self.INPUT_BG,
            selectcolor=self.CARD_COLOR,
            bd=0
        ).pack(side=LEFT, padx=(0, 24))

        Radiobutton(
            inner,
            text="女",
            variable=self.gender_var,
            value="女",
            font=("微软雅黑", 10),
            bg=self.INPUT_BG,
            fg=self.TEXT_COLOR,
            activebackground=self.INPUT_BG,
            selectcolor=self.CARD_COLOR,
            bd=0
        ).pack(side=LEFT)

    def validate_login_name_input(self, value):
        return value.isdigit() or value == ""

    #默认空白头像
    def show_default_avatar(self):
        size = 120
        img = Image.new("RGBA", (size, size), (230, 230, 230, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, size - 1, size - 1), fill=(230, 230, 230, 255))
        draw.ellipse((35, 22, 85, 72), fill=(200, 200, 200, 255))
        draw.rounded_rectangle((28, 72, 92, 110), radius=18, fill=(200, 200, 200, 255))
        self.avatar_photo = ImageTk.PhotoImage(img)
        self.avatar_preview.config(image=self.avatar_photo)

    def choose_avatar(self):
        path = filedialog.askopenfilename(
            parent=self.top,
            title="选择头像",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp")]
        )
        if not path:
            self.top.lift()
            self.top.focus_force()
            return

        self.avatar_path = path
        self.avatar_path_label.config(text=os.path.basename(path))
        self.show_avatar_preview(path)

        self.top.lift()
        self.top.focus_force()

    #显示预览头像
    def show_avatar_preview(self, path):
        try:
            img = Image.open(path).convert("RGBA")

            # 居中裁剪成正方形
            w, h = img.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))

            # 缩放
            size = 120
            img = img.resize((size, size), Image.LANCZOS)

            # 圆形遮罩
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)

            circular = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            circular.paste(img, (0, 0), mask=mask)

            # 外圈白边，接近微信头像感觉
            bordered = ImageOps.expand(circular, border=3, fill="white")

            self.avatar_photo = ImageTk.PhotoImage(bordered)
            self.avatar_preview.config(image=self.avatar_photo)
        except Exception as e:
            print("头像预览失败：", e)
            self.show_default_avatar()

    def check_login_name(self):
        login_name = self.entry_login_name.get().strip()
        if not login_name:
            messagebox.showwarning("提示", "请输入登录名", parent=self.top)
            return

        if len(login_name) < 1 or len(login_name) > 10:
            messagebox.showwarning("提示", "登录名长度必须为1到10位", parent=self.top)
            return

        try:
            resp = requests.get(
                f"{HTTP_BASE}/check_login_name",
                params={"login_name": login_name}
            ).json()

            if resp["code"] == 0:
                messagebox.showinfo("提示", "该登录名可用", parent=self.top)
            else:
                messagebox.showwarning("提示", resp["msg"], parent=self.top)
        except Exception as e:
            messagebox.showerror("错误", str(e), parent=self.top)

        self.top.lift()
        self.top.focus_force()

    def submit_register(self):
        login_name = self.entry_login_name.get().strip()
        nickname = self.entry_nickname.get().strip()
        gender = self.gender_var.get()
        password = self.entry_password.get().strip()
        confirm_password = self.entry_confirm_password.get().strip()

        if not login_name or not nickname or not password or not confirm_password:
            messagebox.showwarning("提示", "请完整填写注册信息", parent=self.top)
            return

        if not login_name.isdigit():
            messagebox.showwarning("提示", "登录名只能输入数字", parent=self.top)
            return

        if len(login_name) < 1 or len(login_name) > 10:
            messagebox.showwarning("提示", "登录名长度必须为1到10位", parent=self.top)
            return

        if password != confirm_password:
            messagebox.showwarning("提示", "两次输入的密码不一致", parent=self.top)
            return

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

        try:
            resp = requests.post(f"{HTTP_BASE}/register", data=data, files=files).json()
            if resp["code"] == 0:
                messagebox.showinfo("提示", "注册成功", parent=self.top)
                self.go_back() #回到登录页面
            else:
                messagebox.showwarning("提示", resp["msg"], parent=self.top)
        except Exception as e:
            messagebox.showerror("错误", str(e), parent=self.top)
        finally:
            if "avatar" in files:
                files["avatar"].close()

        if self.top.winfo_exists():
            self.top.lift()
            self.top.focus_force()


    def go_back(self):
        try:
            self.top.grab_release()
        except Exception:
            pass
        self.top.destroy()