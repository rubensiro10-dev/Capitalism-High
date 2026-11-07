"""Tkinter UI for the login and registration portal."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from PIL import Image, ImageTk

from login_app.config import THEME, WINDOW, resolve_background_image
from login_app.dashboard import ManagementDashboard
from login_app.db import DatabaseError, ensure_schema, ping
from login_app.storage import authenticate, register_user
from login_app.ui import configure_styles
from login_app.validators import SignInData, SignUpData, validate_sign_in, validate_sign_up


class LoginBoardApplication:
    """Main window: sign-in and sign-up with shared validation."""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._photo_ref: ImageTk.PhotoImage | None = None

        self._username = tk.StringVar()
        self._password = tk.StringVar()
        self._confirm = tk.StringVar()
        self._email = tk.StringVar()
        self._phone = tk.StringVar()

        self._configure_window()
        self._build_layout()

    def _configure_window(self) -> None:
        w, h = WINDOW.width, WINDOW.height
        self._root.title(WINDOW.title)
        self._root.geometry(f"{w}x{h}")
        self._root.minsize(WINDOW.min_width, WINDOW.min_height)
        self._root.configure(bg=THEME.primary_bg)
        configure_styles(self._root)

    def _build_layout(self) -> None:
        container = tk.Frame(self._root, bg=THEME.primary_bg)
        container.pack(fill=tk.BOTH, expand=True)

        hero = tk.Frame(container, bg=THEME.primary_bg)
        hero.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._load_hero_image(hero)

        panel = ttk.Frame(container, padding=28)
        panel.pack(side=tk.RIGHT, fill=tk.BOTH)

        ttk.Label(panel, text="Portal Access", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(
            panel,
            text=WINDOW.subtitle,
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(4, 4))
        ttk.Label(
            panel,
            text="Sign in to access school administration modules.",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(0, 16))

        notebook = ttk.Notebook(panel)
        notebook.pack(fill=tk.BOTH, expand=True)

        signin_tab = ttk.Frame(notebook, padding=(0, 12))
        signup_tab = ttk.Frame(notebook, padding=(0, 12))
        notebook.add(signin_tab, text="Sign in")
        notebook.add(signup_tab, text="Register")

        self._build_sign_in_form(signin_tab)
        self._build_sign_up_form(signup_tab)

    def _load_hero_image(self, parent: tk.Frame) -> None:
        path = resolve_background_image()
        if path is None:
            tk.Label(
                parent,
                text="CAPITALISM\nHIGH SCHOOL",
                font=(THEME.font_family, 22, "bold"),
                fg=THEME.text,
                bg=THEME.primary_bg,
                justify=tk.CENTER,
            ).place(relx=0.5, rely=0.45, anchor=tk.CENTER)
            tk.Label(
                parent,
                text="Students · Faculty · Academics · Finance · SQL Server",
                font=(THEME.font_family, 10),
                fg=THEME.text_muted,
                bg=THEME.primary_bg,
            ).place(relx=0.5, rely=0.58, anchor=tk.CENTER)
            return

        try:
            img = Image.open(path)
            img = img.resize((WINDOW.width // 2, WINDOW.height), Image.Resampling.LANCZOS)
            self._photo_ref = ImageTk.PhotoImage(img)
            tk.Label(parent, image=self._photo_ref, bg=THEME.primary_bg).pack(fill=tk.BOTH, expand=True)
        except OSError:
            tk.Label(
                parent,
                text="Capitalism High School",
                font=(THEME.font_family, 18, "bold"),
                fg=THEME.text_muted,
                bg=THEME.primary_bg,
            ).pack(expand=True)

    def _field(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        *,
        show: str | None = None,
    ) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.E, padx=(0, 12), pady=6)
        entry = ttk.Entry(parent, textvariable=variable, width=30, show=show or "")
        entry.grid(row=row, column=1, sticky=tk.EW, pady=6)
        parent.columnconfigure(1, weight=1)
        return entry

    def _build_sign_in_form(self, parent: ttk.Frame) -> None:
        form = ttk.Frame(parent)
        form.pack(fill=tk.BOTH, expand=True)

        self._field(form, 0, "Username", self._username)
        pass_entry = self._field(form, 1, "Password", self._password, show="•")
        pass_entry.bind("<Return>", lambda _e: self._on_sign_in())

        ttk.Button(form, text="Sign In", style="Primary.TButton", command=self._on_sign_in).grid(
            row=2, column=0, columnspan=2, pady=(18, 0), sticky=tk.EW
        )

    def _build_sign_up_form(self, parent: ttk.Frame) -> None:
        form = ttk.Frame(parent)
        form.pack(fill=tk.BOTH, expand=True)

        self._field(form, 0, "Username", self._username)
        self._field(form, 1, "Password", self._password, show="•")
        self._field(form, 2, "Confirm password", self._confirm, show="•")
        self._field(form, 3, "Email", self._email)
        phone_entry = self._field(form, 4, "Phone", self._phone)
        phone_entry.bind("<Return>", lambda _e: self._on_sign_up())

        ttk.Label(
            form,
            text="Phone: 10 digits (07... or 01...)",
            style="Muted.TLabel",
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))

        ttk.Button(form, text="Create Account", style="Primary.TButton", command=self._on_sign_up).grid(
            row=6, column=0, columnspan=2, pady=(10, 0), sticky=tk.EW
        )

    def _run_validated(
        self,
        result_ok: bool,
        error_message: str,
        on_success: Callable[[], None],
    ) -> None:
        if not result_ok:
            messagebox.showerror("Validation error", error_message)
            return
        on_success()

    def _on_sign_in(self) -> None:
        data = SignInData(username=self._username.get(), password=self._password.get())
        result = validate_sign_in(data)
        if not result.ok:
            messagebox.showerror("Validation error", result.message)
            return
        auth = authenticate(data)
        if not auth.ok:
            messagebox.showerror("Sign in failed", auth.message)
            return

        try:
            ping()
            ensure_schema()
        except DatabaseError as exc:
            messagebox.showerror(
                "Database unavailable",
                f"{exc}\n\nYou cannot open the dashboard until SQL Server is reachable.",
            )
            return

        username = data.username.strip()
        self._root.withdraw()
        dash_win = tk.Toplevel(self._root)
        dashboard = ManagementDashboard(username, root=dash_win, on_sign_out=self._return_to_login)
        dashboard.run()

    def _return_to_login(self) -> None:
        self._password.set("")
        if self._root.winfo_exists():
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()

    def _on_sign_up(self) -> None:
        data = SignUpData(
            username=self._username.get(),
            password=self._password.get(),
            confirm_password=self._confirm.get(),
            email=self._email.get(),
            phone=self._phone.get(),
        )
        result = validate_sign_up(data)
        if not result.ok:
            messagebox.showerror("Validation error", result.message)
            return
        saved = register_user(data)
        self._run_validated(
            saved.ok,
            saved.message,
            lambda: messagebox.showinfo(
                "Account created",
                f"Your account is ready.\nSign in as {data.username.strip()}.",
            ),
        )

    def run(self) -> None:
        self._root.mainloop()
