"""Enterprise Management Dashboard for Capitalism High School.

Provides full operations for:
- Executive Overview & Real-time KPIs with Direct Item Creation Actions
- Student Directory & Admissions
- Teaching Staff & Faculty
- Academics (Curriculum Subjects & Exam Grading)
- Fees & Bursaries Administration
- Boarding & Dormitory Allocation
- Clubs & Societies Memberships
- Support & Administrative Workforce (Employees)
- Inventory Control & School Supplies
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Sequence

from login_app.config import DASHBOARD_THEME, DASHBOARD_WINDOW
from login_app.db import (
    BoardingRecord,
    BursaryRecord,
    ClubMemberRecord,
    ClubRecord,
    DatabaseError,
    EmployeeRecord,
    FeeRecord,
    InventoryRecord,
    ResultRecord,
    StudentRecord,
    SubjectRecord,
    TeacherRecord,
    add_club_member,
    assign_boarding,
    calculate_grade,
    dashboard_stats,
    delete_boarding,
    delete_bursary,
    delete_club,
    delete_employee,
    delete_fee,
    delete_inventory_item,
    delete_result,
    delete_student,
    delete_subject,
    delete_teacher,
    ensure_schema,
    get_student_choices,
    insert_bursary,
    insert_club,
    insert_employee,
    insert_inventory_item,
    insert_result,
    insert_student,
    insert_subject,
    insert_teacher,
    list_boarding,
    list_bursaries,
    list_club_members,
    list_clubs,
    list_employees,
    list_fees,
    list_inventory,
    list_results,
    list_students,
    list_subjects,
    list_teachers,
    ping,
    remove_club_member,
    update_boarding,
    update_bursary,
    update_club,
    update_employee,
    update_inventory_item,
    update_result,
    update_student,
    update_teacher,
    upsert_fee,
)
from login_app.ui import configure_dashboard_styles
from login_app.validators import (
    validate_boarding_fields,
    validate_bursary_fields,
    validate_club_fields,
    validate_employee_fields,
    validate_fee_fields,
    validate_inventory_fields,
    validate_result_fields,
    validate_student_fields,
    validate_subject_fields,
    validate_teacher_fields,
)

_NAV_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("overview", "Overview", "📊"),
    ("students", "Students", "🎓"),
    ("teachers", "Teaching Staff", "👨‍🏫"),
    ("academics", "Academics", "📚"),
    ("fees", "Fees & Bursaries", "💳"),
    ("boarding", "Boarding", "🛏️"),
    ("clubs", "Clubs & Societies", "👥"),
    ("employees", "Support Staff", "💼"),
    ("inventory", "Inventory", "📦"),
)

_PAGE_TITLES: dict[str, tuple[str, str, str]] = {
    "overview": (
        "Executive Dashboard",
        "Real-time operational metrics and live database synchronized records.",
        "Workspace / Executive Overview",
    ),
    "students": (
        "Student Directory & Admissions",
        "Register, manage student biodata, class assignments, and guardian contacts.",
        "Workspace / Student Management",
    ),
    "teachers": (
        "Teaching Staff & Faculty",
        "Maintain teacher records, TSC registration numbers, and subject assignments.",
        "Workspace / Teaching Staff",
    ),
    "academics": (
        "Academics, Subjects & Exams",
        "Manage curriculum subjects, record continuous assessments and terminal exam grades.",
        "Workspace / Academic Records",
    ),
    "fees": (
        "Fees Management & Bursaries",
        "Track fee invoices, receipt payments, outstanding balances, and sponsor bursary awards.",
        "Workspace / Fees & Bursaries",
    ),
    "boarding": (
        "Boarding & Dormitory Allocation",
        "Assign and monitor dormitory occupancy, cubicles, and student bed allocations.",
        "Workspace / Boarding Management",
    ),
    "clubs": (
        "Clubs & Co-Curricular Societies",
        "Register school clubs, teacher patrons, meeting schedules, and student memberships.",
        "Workspace / Clubs & Societies",
    ),
    "employees": (
        "Support Staff & Workforce",
        "Maintain non-teaching administration and support staff payroll records.",
        "Workspace / Support Staff",
    ),
    "inventory": (
        "Inventory Control & Supplies",
        "Track stock levels, valuations, vendor supplies, and low-stock replenishment alerts.",
        "Workspace / Inventory Control",
    ),
}

DORMITORIES = (
    "All Dormitories",
    "Mount Kenya House",
    "Kilimanjaro House",
    "Aberdare House",
    "Elgon House",
    "Ruwenzori House",
    "Mara House",
)

CLASSES = (
    "All Classes",
    "Form 1 East",
    "Form 1 West",
    "Form 2 East",
    "Form 2 West",
    "Form 3 Alpha",
    "Form 3 Beta",
    "Form 4 East",
    "Form 4 West",
)

DEPARTMENTS = (
    "All Departments",
    "Mathematics",
    "Sciences",
    "Languages",
    "Humanities",
    "Technical & Applied",
    "Physical Education",
)


class ManagementDashboard:
    """Main application workspace supporting all school management modules."""

    def __init__(
        self,
        username: str,
        root: tk.Tk | tk.Toplevel | None = None,
        on_sign_out: Callable[[], None] | None = None,
    ) -> None:
        self._username = username.strip()
        self._on_sign_out = on_sign_out
        self._owns_root = root is None
        self._root = root if root is not None else tk.Tk()
        self._field_widgets: dict[tk.StringVar, ttk.Widget] = {}

        self._status = self._str_var("Connected to SQL Server — Ready")
        self._breadcrumb = self._str_var(_PAGE_TITLES["overview"][2])
        self._page_title = self._str_var(_PAGE_TITLES["overview"][0])
        self._page_lead = self._str_var(_PAGE_TITLES["overview"][1])
        self._active_page = "overview"
        self._nav_buttons: dict[str, tk.Button] = {}
        self._pages: dict[str, tk.Frame] = {}

        # Cached dropdown choices
        self._student_choices: list[tuple[int, str, str, str]] = []
        self._subject_choices: list[SubjectRecord] = []
        self._club_choices: list[ClubRecord] = []

        # Overview KPI variables
        self._stat_students = self._str_var("0")
        self._stat_teachers = self._str_var("0")
        self._stat_fees_collected = self._str_var("0.00")
        self._stat_fees_balance = self._str_var("0.00")
        self._stat_boarders = self._str_var("0")
        self._stat_employees = self._str_var("0")
        self._stat_inventory = self._str_var("0")
        self._stat_inv_value = self._str_var("0.00")
        self._stat_low_stock = self._str_var("0")
        self._stat_clubs = self._str_var("0")
        self._stat_exams = self._str_var("0")
        self._stat_avg_score = self._str_var("0.0")

        # ----------------- Student Module Variables -----------------
        self._selected_student_id: int | None = None
        self._stu_search = self._str_var()
        self._stu_class_filter = self._str_var("All Classes")
        self._stu_adm = self._str_var()
        self._stu_name = self._str_var()
        self._stu_gender = self._str_var("Male")
        self._stu_dob = self._str_var()
        self._stu_class = self._str_var("Form 1 East")
        self._stu_parent = self._str_var()
        self._stu_parent_phone = self._str_var()
        self._stu_email = self._str_var()
        self._stu_address = self._str_var()

        # ----------------- Teacher Module Variables -----------------
        self._selected_teacher_id: int | None = None
        self._tea_search = self._str_var()
        self._tea_dept_filter = self._str_var("All Departments")
        self._tea_name = self._str_var()
        self._tea_tsc = self._str_var()
        self._tea_email = self._str_var()
        self._tea_phone = self._str_var()
        self._tea_dept = self._str_var("Sciences")
        self._tea_sub1 = self._str_var("Mathematics")
        self._tea_sub2 = self._str_var("Physics")
        self._tea_salary = self._str_var()

        # ----------------- Academics Variables -----------------
        self._selected_result_id: int | None = None
        self._selected_subject_id: int | None = None
        self._res_search = self._str_var()
        self._res_student_pick = self._str_var()
        self._res_subject_pick = self._str_var()
        self._res_cat = self._str_var()
        self._res_exam = self._str_var()
        self._res_preview = self._str_var("Total: — | Grade: —")
        self._new_subject_name = self._str_var()

        # ----------------- Fees Module Variables -----------------
        self._selected_fee_id: int | None = None
        self._selected_bursary_id: int | None = None
        self._fee_search = self._str_var()
        self._fee_status_filter = self._str_var("All")
        self._fee_student_pick = self._str_var()
        self._fee_required = self._str_var("45000.00")
        self._fee_paid = self._str_var("0.00")
        self._fee_preview = self._str_var("Balance: KSh 45,000.00")

        self._bur_search = self._str_var()
        self._bur_student_pick = self._str_var()
        self._bur_sponsor = self._str_var()
        self._bur_amount = self._str_var()
        self._bur_date = self._str_var()

        # ----------------- Boarding Module Variables -----------------
        self._selected_boarding_id: int | None = None
        self._bd_search = self._str_var()
        self._bd_dorm_filter = self._str_var("All Dormitories")
        self._bd_student_pick = self._str_var()
        self._bd_dorm = self._str_var("Mount Kenya House")
        self._bd_bed = self._str_var()

        # ----------------- Clubs Module Variables -----------------
        self._selected_club_id: int | None = None
        self._selected_membership_id: int | None = None
        self._club_name = self._str_var()
        self._club_patron = self._str_var()
        self._club_day = self._str_var("Wednesday 4:00 PM")
        self._mem_club_filter = self._str_var("All Clubs")
        self._mem_student_pick = self._str_var()
        self._mem_club_pick = self._str_var()

        # ----------------- Support Staff Variables -----------------
        self._selected_employee_id: int | None = None
        self._emp_search = self._str_var()
        self._emp_name = self._str_var()
        self._emp_email = self._str_var()
        self._emp_phone = self._str_var()
        self._emp_role = self._str_var()
        self._emp_salary = self._str_var()

        # ----------------- Inventory Variables -----------------
        self._selected_inventory_id: int | None = None
        self._inv_search = self._str_var()
        self._inv_name = self._str_var()
        self._inv_category = self._str_var("Stationery")
        self._inv_quantity = self._str_var()
        self._inv_price = self._str_var()
        self._inv_supplier = self._str_var()

        self._configure_window()
        self._build_layout()
        self._show_page("overview")
        self._refresh_all()

    def _str_var(self, value: str = "") -> tk.StringVar:
        return tk.StringVar(master=self._root, value=str(value) if value is not None else "")

    def _configure_window(self) -> None:
        cfg = DASHBOARD_WINDOW
        self._root.title(cfg.title)
        self._root.geometry(f"{cfg.width}x{cfg.height}")
        self._root.minsize(cfg.min_width, cfg.min_height)
        d = DASHBOARD_THEME
        self._root.configure(bg=d.canvas_bg)
        self._root.protocol("WM_DELETE_WINDOW", self._close)
        configure_dashboard_styles(self._root)

    def _build_layout(self) -> None:
        d = DASHBOARD_THEME
        cfg = DASHBOARD_WINDOW

        body = tk.Frame(self._root, bg=d.canvas_bg)
        body.pack(fill=tk.BOTH, expand=True)

        self._build_sidebar(body, cfg.product_name)

        main = tk.Frame(body, bg=d.canvas_bg)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Header bar
        header = tk.Frame(main, bg=d.header_bg, padx=24, pady=12)
        header.pack(fill=tk.X)
        header_inner = tk.Frame(header, bg=d.header_bg)
        header_inner.pack(fill=tk.X)

        left_header = tk.Frame(header_inner, bg=d.header_bg)
        left_header.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(left_header, textvariable=self._breadcrumb, style="Dash.Breadcrumb.TLabel").pack(anchor=tk.W)
        ttk.Label(left_header, textvariable=self._page_title, style="Dash.PageTitle.TLabel").pack(
            anchor=tk.W, pady=(2, 0)
        )
        ttk.Label(left_header, textvariable=self._page_lead, style="Dash.PageHeaderLead.TLabel").pack(
            anchor=tk.W, pady=(2, 0)
        )

        actions = tk.Frame(header_inner, bg=d.header_bg)
        actions.pack(side=tk.RIGHT)
        ttk.Button(
            actions,
            text="+ Add Item",
            style="Dash.Primary.TButton",
            command=self._show_add_inventory_dialog,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text="🔄 Sync data", style="Dash.Secondary.TButton", command=self._refresh_all).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(actions, text="Sign out", style="Dash.Secondary.TButton", command=self._sign_out).pack(side=tk.LEFT)

        # Content host
        self._content_host = tk.Frame(main, bg=d.canvas_bg, padx=20, pady=14)
        self._content_host.pack(fill=tk.BOTH, expand=True)

        # Build all modules
        for page_id, _label, _icon in _NAV_ITEMS:
            frame = tk.Frame(self._content_host, bg=d.canvas_bg)
            self._pages[page_id] = frame

        self._build_overview(self._pages["overview"])
        self._build_students_page(self._pages["students"])
        self._build_teachers_page(self._pages["teachers"])
        self._build_academics_page(self._pages["academics"])
        self._build_fees_page(self._pages["fees"])
        self._build_boarding_page(self._pages["boarding"])
        self._build_clubs_page(self._pages["clubs"])
        self._build_employees_page(self._pages["employees"])
        self._build_inventory_page(self._pages["inventory"])

        # Status Bar
        status_bar = tk.Frame(self._root, bg=d.status_bar, padx=16, pady=6)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status_bar, textvariable=self._status, style="Dash.Status.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            status_bar,
            text="SQL Server · ManagementSystem · Autocommit Active",
            style="Dash.Status.TLabel",
        ).pack(side=tk.RIGHT)

    def _build_sidebar(self, parent: tk.Frame, product_name: str) -> None:
        d = DASHBOARD_THEME
        sidebar = tk.Frame(parent, bg=d.sidebar_bg, width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=d.sidebar_bg, padx=20, pady=20)
        brand.pack(fill=tk.X)
        tk.Label(
            brand,
            text=product_name,
            bg=d.sidebar_bg,
            fg="#ffffff",
            font=(d.font_family, 13, "bold"),
            wraplength=210,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)
        tk.Label(
            brand,
            text="Integrated Administration ERP",
            bg=d.sidebar_bg,
            fg=d.sidebar_muted,
            font=(d.font_family, 9),
        ).pack(anchor=tk.W, pady=(3, 0))

        tk.Label(
            sidebar,
            text="NAVIGATION",
            bg=d.sidebar_bg,
            fg=d.sidebar_muted,
            font=(d.font_family, 8, "bold"),
            padx=20,
        ).pack(anchor=tk.W, pady=(4, 4))

        nav = tk.Frame(sidebar, bg=d.sidebar_bg, padx=10)
        nav.pack(fill=tk.X)

        for page_id, label, icon in _NAV_ITEMS:
            btn = tk.Button(
                nav,
                text=f"  {icon}  {label}",
                anchor=tk.W,
                relief=tk.FLAT,
                borderwidth=0,
                padx=10,
                pady=7,
                cursor="hand2",
                bg=d.sidebar_bg,
                fg=d.sidebar_text,
                activebackground=d.sidebar_active_bg,
                activeforeground=d.sidebar_active_text,
                font=(d.font_family, 10),
                command=lambda pid=page_id: self._show_page(pid),
            )
            btn.pack(fill=tk.X, pady=1)
            self._nav_buttons[page_id] = btn

        # Quick Actions Section
        tk.Label(
            sidebar,
            text="QUICK ACTIONS",
            bg=d.sidebar_bg,
            fg=d.sidebar_muted,
            font=(d.font_family, 8, "bold"),
            padx=20,
        ).pack(anchor=tk.W, pady=(12, 4))

        quick_nav = tk.Frame(sidebar, bg=d.sidebar_bg, padx=10)
        quick_nav.pack(fill=tk.X)

        for qlabel, qcmd in (
            ("+ Add Inventory Item", self._show_add_inventory_dialog),
            ("+ Enroll Student", self._show_add_student_dialog),
            ("+ Add Teacher", self._show_add_teacher_dialog),
            ("+ Add Employee", self._show_add_employee_dialog),
        ):
            qbtn = tk.Button(
                quick_nav,
                text=f"  {qlabel}",
                anchor=tk.W,
                relief=tk.FLAT,
                borderwidth=0,
                padx=10,
                pady=6,
                cursor="hand2",
                bg=d.sidebar_bg,
                fg=d.sidebar_accent_bar,
                activebackground=d.sidebar_active_bg,
                activeforeground="#ffffff",
                font=(d.font_family, 9, "bold"),
                command=qcmd,
            )
            qbtn.pack(fill=tk.X, pady=1)

        user_panel = tk.Frame(sidebar, bg=d.sidebar_active_bg, padx=16, pady=12)
        user_panel.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=14)
        tk.Label(
            user_panel,
            text="Administrator",
            bg=d.sidebar_active_bg,
            fg=d.sidebar_muted,
            font=(d.font_family, 8),
        ).pack(anchor=tk.W)
        tk.Label(
            user_panel,
            text=self._username,
            bg=d.sidebar_active_bg,
            fg="#ffffff",
            font=(d.font_family, 10, "bold"),
        ).pack(anchor=tk.W, pady=(2, 0))

    def _show_page(self, page_id: str) -> None:
        if page_id not in self._pages:
            return
        self._active_page = page_id
        for frame in self._pages.values():
            frame.pack_forget()
        self._pages[page_id].pack(fill=tk.BOTH, expand=True)

        title, lead, breadcrumb = _PAGE_TITLES[page_id]
        self._page_title.set(title)
        self._page_lead.set(lead)
        self._breadcrumb.set(breadcrumb)
        self._update_nav_highlight(page_id)

    def _update_nav_highlight(self, page_id: str) -> None:
        d = DASHBOARD_THEME
        for pid, btn in self._nav_buttons.items():
            if pid == page_id:
                btn.configure(bg=d.sidebar_active_bg, fg=d.sidebar_active_text, font=(d.font_family, 10, "bold"))
            else:
                btn.configure(bg=d.sidebar_bg, fg=d.sidebar_text, font=(d.font_family, 10))

    def _section_card(self, parent: tk.Misc, padx: int = 14, pady: int = 14) -> tk.Frame:
        d = DASHBOARD_THEME
        outer = tk.Frame(parent, bg=d.border, padx=1, pady=1)
        outer.pack(fill=tk.BOTH, expand=True)
        card = tk.Frame(outer, bg=d.surface, padx=padx, pady=pady)
        card.pack(fill=tk.BOTH, expand=True)
        return card

    def _var_key(self, var: tk.StringVar | str) -> str:
        if hasattr(var, "_name"):
            return str(var._name)
        return str(var)

    def _grid_field(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        *,
        widget_type: str = "entry",
        values: Sequence[str] | None = None,
        state: str = "normal",
    ) -> ttk.Widget:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.E, padx=(0, 10), pady=4)
        if widget_type == "combobox":
            w = ttk.Combobox(parent, textvariable=variable, values=values or (), state=state, width=28)
        else:
            w = ttk.Entry(parent, textvariable=variable, width=30)
        w.grid(row=row, column=1, sticky=tk.EW, pady=4)
        parent.columnconfigure(1, weight=1)
        self._field_widgets[self._var_key(variable)] = w
        return w

    def _val(self, var: tk.StringVar) -> str:
        """Safely retrieve the current string from the physical Entry/Combobox widget or StringVar."""
        key = self._var_key(var)
        w = self._field_widgets.get(key)
        if w is not None and hasattr(w, "get"):
            try:
                txt = str(w.get()).strip()
                if txt:
                    return txt
            except Exception:
                pass
        val = var.get() if hasattr(var, "get") else ""
        return val.strip() if val else ""

    def _set_field(self, var: tk.StringVar, val: Any) -> None:
        """Update both the StringVar and the physical widget text."""
        text = "" if val is None or str(val) == "None" else str(val).strip()
        if hasattr(var, "set"):
            var.set(text)
        key = self._var_key(var)
        w = self._field_widgets.get(key)
        if isinstance(w, ttk.Entry):
            try:
                w.delete(0, tk.END)
                w.insert(0, text)
            except Exception:
                pass
        elif isinstance(w, ttk.Combobox):
            try:
                w.set(text)
            except Exception:
                pass

    def _clear_field(self, var: tk.StringVar, default: str = "") -> None:
        """Clear both the StringVar and any associated physical Entry/Combobox widget."""
        self._set_field(var, default)

    # ========================================================================
    # OVERVIEW MODULE
    # ========================================================================

    def _build_overview(self, parent: tk.Frame) -> None:
        d = DASHBOARD_THEME

        # Top row: 4 primary metrics
        top_grid = tk.Frame(parent, bg=d.canvas_bg)
        top_grid.pack(fill=tk.X)
        for col in range(4):
            top_grid.columnconfigure(col, weight=1, uniform="stat_top")

        self._stat_card(top_grid, 0, "Total Students", self._stat_students, "🎓", d.stat_students)
        self._stat_card(top_grid, 1, "Teaching Staff", self._stat_teachers, "👨‍🏫", d.stat_teachers)
        self._stat_card(top_grid, 2, "Fees Collected", self._stat_fees_collected, "💳", d.stat_fees, prefix="KSh ")
        self._stat_card(top_grid, 3, "Fee Balance Due", self._stat_fees_balance, "⚠️", d.stat_low, prefix="KSh ")

        # Second row: 4 secondary metrics
        sec_grid = tk.Frame(parent, bg=d.canvas_bg)
        sec_grid.pack(fill=tk.X, pady=(12, 0))
        for col in range(4):
            sec_grid.columnconfigure(col, weight=1, uniform="stat_sec")

        self._stat_card(sec_grid, 0, "Boarding Students", self._stat_boarders, "🛏️", d.stat_boarding)
        self._stat_card(sec_grid, 1, "Support Workforce", self._stat_employees, "💼", d.stat_employees)
        self._stat_card(sec_grid, 2, "Inventory SKUs", self._stat_inventory, "📦", d.stat_inventory)
        self._stat_card(sec_grid, 3, "Active Clubs", self._stat_clubs, "👥", d.stat_clubs)

        # Quick Actions Toolbar
        action_card = self._section_card(parent, padx=16, pady=12)
        action_bar = tk.Frame(action_card, bg=d.surface)
        action_bar.pack(fill=tk.X)
        ttk.Label(action_bar, text="QUICK RECORD ACTIONS", style="Dash.CardTitle.TLabel").pack(side=tk.LEFT)

        btn_container = tk.Frame(action_bar, bg=d.surface)
        btn_container.pack(side=tk.RIGHT)

        ttk.Button(
            btn_container,
            text="+ Add Inventory Item",
            style="Dash.Primary.TButton",
            command=self._show_add_inventory_dialog,
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_container,
            text="+ Enroll Student",
            style="Dash.Success.TButton",
            command=self._show_add_student_dialog,
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_container,
            text="+ Add Teacher",
            style="Dash.Secondary.TButton",
            command=self._show_add_teacher_dialog,
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_container,
            text="+ Add Employee",
            style="Dash.Secondary.TButton",
            command=self._show_add_employee_dialog,
        ).pack(side=tk.LEFT)

        # Quick access section
        links_card = self._section_card(parent, padx=18, pady=16)
        ttk.Label(links_card, text="MODULE QUICK ACCESS", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        tiles_frame = tk.Frame(links_card, bg=d.surface)
        tiles_frame.pack(fill=tk.X)
        for col in range(3):
            tiles_frame.columnconfigure(col, weight=1, uniform="tile")

        tiles_data = [
            ("🎓 Students", "Admit, update, search, and manage student directory.", "students", d.stat_students),
            ("👨‍🏫 Teaching Faculty", "Manage teachers, TSC numbers, and departments.", "teachers", d.stat_teachers),
            ("📚 Exam Results", "Record CAT/Exam scores and calculate grades.", "academics", d.stat_clubs),
            ("💳 Fee Register", "Process student fee payments and bursary awards.", "fees", d.stat_fees),
            ("🛏️ Boarding Allocation", "Assign dormitories, cubicles, and bed spaces.", "boarding", d.stat_boarding),
            ("📦 Inventory Supplies", "Track school property, stock ledger, and orders.", "inventory", d.stat_inventory),
        ]

        for i, (title, desc, target_pid, color) in enumerate(tiles_data):
            row = i // 3
            col = i % 3
            self._tile_button(tiles_frame, row, col, title, desc, target_pid, color)

    def _stat_card(
        self,
        parent: tk.Frame,
        column: int,
        title: str,
        value_var: tk.StringVar,
        icon: str,
        accent: str,
        prefix: str = "",
    ) -> None:
        d = DASHBOARD_THEME
        outer = tk.Frame(parent, bg=d.border, padx=1, pady=1)
        outer.grid(row=0, column=column, sticky=tk.NSEW, padx=6)
        card = tk.Frame(outer, bg=d.surface, padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True)

        top_row = tk.Frame(card, bg=d.surface)
        top_row.pack(fill=tk.X)
        tk.Label(top_row, text=icon, font=(d.font_family, 14), bg=d.surface).pack(side=tk.LEFT)
        tk.Label(
            top_row,
            text=f"  {title.upper()}",
            bg=d.surface,
            fg=d.text_muted,
            font=(d.font_family, 8, "bold"),
        ).pack(side=tk.LEFT, pady=(2, 0))

        val_frame = tk.Frame(card, bg=d.surface)
        val_frame.pack(anchor=tk.W, pady=(8, 0))
        if prefix:
            tk.Label(val_frame, text=prefix, bg=d.surface, fg=accent, font=(d.font_family, 13, "bold")).pack(
                side=tk.LEFT, pady=(4, 0)
            )
        tk.Label(
            val_frame,
            textvariable=value_var,
            bg=d.surface,
            fg=accent,
            font=(d.font_family, 18, "bold"),
        ).pack(side=tk.LEFT)

    def _tile_button(
        self,
        parent: tk.Frame,
        row: int,
        col: int,
        title: str,
        desc: str,
        page_id: str,
        color: str,
    ) -> None:
        d = DASHBOARD_THEME
        frame = tk.Frame(parent, bg=d.border, padx=1, pady=1)
        frame.grid(row=row, column=col, sticky=tk.NSEW, padx=6, pady=6)
        btn = tk.Frame(frame, bg=d.surface, padx=14, pady=12, cursor="hand2")
        btn.pack(fill=tk.BOTH, expand=True)

        for w in (frame, btn):
            w.bind("<Button-1>", lambda _e, pid=page_id: self._show_page(pid))

        h = tk.Label(btn, text=title, bg=d.surface, fg=color, font=(d.font_family, 11, "bold"), cursor="hand2")
        h.pack(anchor=tk.W)
        h.bind("<Button-1>", lambda _e, pid=page_id: self._show_page(pid))

        b = tk.Label(btn, text=desc, bg=d.surface, fg=d.text_muted, font=(d.font_family, 9), wraplength=260, justify=tk.LEFT, cursor="hand2")
        b.pack(anchor=tk.W, pady=(4, 6))
        b.bind("<Button-1>", lambda _e, pid=page_id: self._show_page(pid))

        f = tk.Label(btn, text="Open module →", bg=d.surface, fg=d.accent, font=(d.font_family, 8, "bold"), cursor="hand2")
        f.pack(anchor=tk.W)
        f.bind("<Button-1>", lambda _e, pid=page_id: self._show_page(pid))

    # ========================================================================
    # MODAL ITEM & RECORD CREATION DIALOGS
    # ========================================================================

    def _show_add_inventory_dialog(self) -> None:
        """Modal dialog to add a new item directly to SQL Server."""
        d = DASHBOARD_THEME
        dialog = tk.Toplevel(self._root)
        dialog.title("Add New Inventory Item")
        dialog.geometry("480x420")
        dialog.minsize(440, 380)
        dialog.transient(self._root)
        dialog.grab_set()
        dialog.configure(bg=d.canvas_bg)

        card = ttk.Frame(dialog, padding=20)
        card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(card, text="New Inventory Supply Item", style="Dash.CardTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(
            card,
            text="Records created here are committed directly to Microsoft SQL Server.",
            style="Dash.PageLead.TLabel",
        ).pack(anchor=tk.W, pady=(2, 14))

        form = ttk.Frame(card)
        form.pack(fill=tk.X)

        item_name_var = tk.StringVar(master=dialog)
        category_var = tk.StringVar(master=dialog, value="Stationery")
        qty_var = tk.StringVar(master=dialog, value="10")
        price_var = tk.StringVar(master=dialog, value="100.00")
        supplier_var = tk.StringVar(master=dialog)

        name_ent = self._grid_field(form, 0, "Item Name *", item_name_var)
        cats = ("Electronics", "Stationery", "Science Lab", "Sports Equipment", "Furniture", "Textbooks", "Food & Kitchen", "Maintenance")
        cat_ent = self._grid_field(form, 1, "Category *", category_var, widget_type="combobox", values=cats)
        qty_ent = self._grid_field(form, 2, "Quantity *", qty_var)
        price_ent = self._grid_field(form, 3, "Unit Price (KSh) *", price_var)
        sup_ent = self._grid_field(form, 4, "Supplier *", supplier_var)

        def save_item() -> None:
            raw_name = (name_ent.get() if hasattr(name_ent, "get") else "").strip() or item_name_var.get().strip()
            raw_cat = (cat_ent.get() if hasattr(cat_ent, "get") else "").strip() or category_var.get().strip()
            raw_qty = (qty_ent.get() if hasattr(qty_ent, "get") else "").strip() or qty_var.get().strip()
            raw_prc = (price_ent.get() if hasattr(price_ent, "get") else "").strip() or price_var.get().strip()
            raw_sup = (sup_ent.get() if hasattr(sup_ent, "get") else "").strip() or supplier_var.get().strip()

            res, qty, prc = validate_inventory_fields(
                raw_name,
                raw_cat,
                raw_qty,
                raw_prc,
                raw_sup,
            )
            if not res.ok or qty is None or prc is None:
                messagebox.showerror("Validation Error", res.message, parent=dialog)
                return

            def action() -> None:
                new_id = insert_inventory_item(raw_name, raw_cat, qty, prc, raw_sup)
                dialog.destroy()
                self._show_page("inventory")
                self._refresh_inventory()
                if self._inv_tree.exists(str(new_id)):
                    self._inv_tree.selection_set(str(new_id))
                    self._inv_tree.see(str(new_id))
                messagebox.showinfo(
                    "Item Saved to Database",
                    f"'{raw_name}' was successfully recorded in the database.\n\nDatabase: ManagementSystem\nTable: dbo.Inventory\nItem ID: #{new_id}",
                    parent=self._root,
                )

            self._run_db(action, f"Inventory item '{raw_name}' committed to database.")

        sup_ent.bind("<Return>", lambda _e: save_item())

        btn_box = ttk.Frame(card)
        btn_box.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(btn_box, text="Save to Database", style="Dash.Success.TButton", command=save_item).pack(side=tk.LEFT)
        ttk.Button(btn_box, text="Cancel", style="Dash.Secondary.TButton", command=dialog.destroy).pack(side=tk.LEFT, padx=(8, 0))

    def _show_add_student_dialog(self) -> None:
        """Modal dialog to enroll a new student directly into SQL Server."""
        d = DASHBOARD_THEME
        dialog = tk.Toplevel(self._root)
        dialog.title("Enroll New Student")
        dialog.geometry("500x520")
        dialog.minsize(460, 480)
        dialog.transient(self._root)
        dialog.grab_set()
        dialog.configure(bg=d.canvas_bg)

        card = ttk.Frame(dialog, padding=20)
        card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(card, text="Student Enrollment Form", style="Dash.CardTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(
            card,
            text="Record new student biodata directly into SQL Server.",
            style="Dash.PageLead.TLabel",
        ).pack(anchor=tk.W, pady=(2, 14))

        form = ttk.Frame(card)
        form.pack(fill=tk.X)

        adm_var = tk.StringVar(master=dialog)
        name_var = tk.StringVar(master=dialog)
        gender_var = tk.StringVar(master=dialog, value="Male")
        dob_var = tk.StringVar(master=dialog)
        class_var = tk.StringVar(master=dialog, value="Form 1 East")
        parent_var = tk.StringVar(master=dialog)
        parent_phone_var = tk.StringVar(master=dialog)
        email_var = tk.StringVar(master=dialog)
        addr_var = tk.StringVar(master=dialog)

        adm_ent = self._grid_field(form, 0, "Admission No *", adm_var)
        name_ent = self._grid_field(form, 1, "Full Name *", name_var)
        gender_ent = self._grid_field(form, 2, "Gender *", gender_var, widget_type="combobox", values=("Male", "Female", "Other"), state="readonly")
        dob_ent = self._grid_field(form, 3, "DOB (YYYY-MM-DD)", dob_var)
        class_ent = self._grid_field(form, 4, "Class *", class_var, widget_type="combobox", values=CLASSES[1:], state="readonly")
        parent_ent = self._grid_field(form, 5, "Parent / Guardian *", parent_var)
        phone_ent = self._grid_field(form, 6, "Parent Phone *", parent_phone_var)
        email_ent = self._grid_field(form, 7, "Email", email_var)
        addr_ent = self._grid_field(form, 8, "Home Address", addr_var)

        def save_student() -> None:
            raw_adm = (adm_ent.get() if hasattr(adm_ent, "get") else "").strip() or adm_var.get().strip()
            raw_name = (name_ent.get() if hasattr(name_ent, "get") else "").strip() or name_var.get().strip()
            raw_gender = (gender_ent.get() if hasattr(gender_ent, "get") else "").strip() or gender_var.get().strip()
            raw_dob = (dob_ent.get() if hasattr(dob_ent, "get") else "").strip() or dob_var.get().strip()
            raw_class = (class_ent.get() if hasattr(class_ent, "get") else "").strip() or class_var.get().strip()
            raw_parent = (parent_ent.get() if hasattr(parent_ent, "get") else "").strip() or parent_var.get().strip()
            raw_phone = (phone_ent.get() if hasattr(phone_ent, "get") else "").strip() or parent_phone_var.get().strip()
            raw_email = (email_ent.get() if hasattr(email_ent, "get") else "").strip() or email_var.get().strip()
            raw_addr = (addr_ent.get() if hasattr(addr_ent, "get") else "").strip() or addr_var.get().strip()

            res = validate_student_fields(
                raw_adm,
                raw_name,
                raw_gender,
                raw_dob,
                raw_class,
                raw_parent,
                raw_phone,
                raw_email,
                raw_addr,
            )
            if not res.ok:
                messagebox.showerror("Validation Error", res.message, parent=dialog)
                return

            def action() -> None:
                new_id = insert_student(
                    raw_adm,
                    raw_name,
                    raw_gender,
                    raw_dob,
                    raw_class,
                    raw_parent,
                    raw_phone,
                    raw_email,
                    raw_addr,
                )
                dialog.destroy()
                self._show_page("students")
                self._refresh_students()
                if self._stu_tree.exists(str(new_id)):
                    self._stu_tree.selection_set(str(new_id))
                    self._stu_tree.see(str(new_id))
                self._refresh_combobox_data()
                messagebox.showinfo(
                    "Student Saved to Database",
                    f"'{raw_name}' was successfully enrolled in the database.\n\nDatabase: ManagementSystem\nTable: dbo.Students\nStudent ID: #{new_id}",
                    parent=self._root,
                )

            self._run_db(action, f"Student '{raw_name}' committed to database.")

        addr_ent.bind("<Return>", lambda _e: save_student())

        btn_box = ttk.Frame(card)
        btn_box.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(btn_box, text="Enroll Student", style="Dash.Success.TButton", command=save_student).pack(side=tk.LEFT)
        ttk.Button(btn_box, text="Cancel", style="Dash.Secondary.TButton", command=dialog.destroy).pack(side=tk.LEFT, padx=(8, 0))

    def _show_add_teacher_dialog(self) -> None:
        """Modal dialog to add a teaching staff member directly into SQL Server."""
        d = DASHBOARD_THEME
        dialog = tk.Toplevel(self._root)
        dialog.title("Add Teaching Faculty Member")
        dialog.geometry("480x480")
        dialog.minsize(440, 440)
        dialog.transient(self._root)
        dialog.grab_set()
        dialog.configure(bg=d.canvas_bg)

        card = ttk.Frame(dialog, padding=20)
        card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(card, text="New Teaching Staff Profile", style="Dash.CardTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(
            card,
            text="Faculty records are committed directly to SQL Server.",
            style="Dash.PageLead.TLabel",
        ).pack(anchor=tk.W, pady=(2, 14))

        form = ttk.Frame(card)
        form.pack(fill=tk.X)

        name_var = tk.StringVar(master=dialog)
        tsc_var = tk.StringVar(master=dialog)
        email_var = tk.StringVar(master=dialog)
        phone_var = tk.StringVar(master=dialog)
        dept_var = tk.StringVar(master=dialog, value="Sciences")
        sub1_var = tk.StringVar(master=dialog, value="Mathematics")
        sub2_var = tk.StringVar(master=dialog)
        sal_var = tk.StringVar(master=dialog)

        name_ent = self._grid_field(form, 0, "Full Name *", name_var)
        tsc_ent = self._grid_field(form, 1, "TSC Number *", tsc_var)
        email_ent = self._grid_field(form, 2, "Email *", email_var)
        phone_ent = self._grid_field(form, 3, "Phone *", phone_var)
        dept_ent = self._grid_field(form, 4, "Department *", dept_var, widget_type="combobox", values=DEPARTMENTS[1:], state="readonly")
        sub1_ent = self._grid_field(form, 5, "Primary Subject *", sub1_var)
        sub2_ent = self._grid_field(form, 6, "Secondary Subject", sub2_var)
        sal_ent = self._grid_field(form, 7, "Monthly Salary (KSh)", sal_var)

        def save_tea() -> None:
            raw_name = (name_ent.get() if hasattr(name_ent, "get") else "").strip() or name_var.get().strip()
            raw_tsc = (tsc_ent.get() if hasattr(tsc_ent, "get") else "").strip() or tsc_var.get().strip()
            raw_email = (email_ent.get() if hasattr(email_ent, "get") else "").strip() or email_var.get().strip()
            raw_phone = (phone_ent.get() if hasattr(phone_ent, "get") else "").strip() or phone_var.get().strip()
            raw_dept = (dept_ent.get() if hasattr(dept_ent, "get") else "").strip() or dept_var.get().strip()
            raw_sub1 = (sub1_ent.get() if hasattr(sub1_ent, "get") else "").strip() or sub1_var.get().strip()
            raw_sub2 = (sub2_ent.get() if hasattr(sub2_ent, "get") else "").strip() or sub2_var.get().strip()
            raw_sal = (sal_ent.get() if hasattr(sal_ent, "get") else "").strip() or sal_var.get().strip()

            res, sal = validate_teacher_fields(
                raw_name,
                raw_tsc,
                raw_email,
                raw_phone,
                raw_dept,
                raw_sub1,
                raw_sub2,
                raw_sal,
            )
            if not res.ok or sal is None:
                messagebox.showerror("Validation Error", res.message, parent=dialog)
                return

            def action() -> None:
                new_id = insert_teacher(
                    raw_name,
                    raw_tsc,
                    raw_email,
                    raw_phone,
                    raw_dept,
                    raw_sub1,
                    raw_sub2,
                    sal,
                )
                dialog.destroy()
                self._show_page("teachers")
                self._refresh_teachers()
                if self._tea_tree.exists(str(new_id)):
                    self._tea_tree.selection_set(str(new_id))
                    self._tea_tree.see(str(new_id))
                messagebox.showinfo(
                    "Teacher Saved to Database",
                    f"'{raw_name}' was successfully recorded in faculty.\n\nDatabase: ManagementSystem\nTable: dbo.TeachingStaff\nTeacher ID: #{new_id}",
                    parent=self._root,
                )

            self._run_db(action, f"Teacher '{raw_name}' committed to database.")

        sal_ent.bind("<Return>", lambda _e: save_tea())

        btn_box = ttk.Frame(card)
        btn_box.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(btn_box, text="Save Teacher", style="Dash.Success.TButton", command=save_tea).pack(side=tk.LEFT)
        ttk.Button(btn_box, text="Cancel", style="Dash.Secondary.TButton", command=dialog.destroy).pack(side=tk.LEFT, padx=(8, 0))

    def _show_add_employee_dialog(self) -> None:
        """Modal dialog to add an administrative/support workforce member."""
        d = DASHBOARD_THEME
        dialog = tk.Toplevel(self._root)
        dialog.title("Add Support Staff Member")
        dialog.geometry("480x420")
        dialog.minsize(440, 380)
        dialog.transient(self._root)
        dialog.grab_set()
        dialog.configure(bg=d.canvas_bg)

        card = ttk.Frame(dialog, padding=20)
        card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(card, text="New Staff Member Record", style="Dash.CardTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(
            card,
            text="Employee records are saved to the ManagementSystem database.",
            style="Dash.PageLead.TLabel",
        ).pack(anchor=tk.W, pady=(2, 14))

        form = ttk.Frame(card)
        form.pack(fill=tk.X)

        name_var = tk.StringVar(master=dialog)
        email_var = tk.StringVar(master=dialog)
        phone_var = tk.StringVar(master=dialog)
        role_var = tk.StringVar(master=dialog)
        salary_var = tk.StringVar(master=dialog)

        name_ent = self._grid_field(form, 0, "Full Name *", name_var)
        email_ent = self._grid_field(form, 1, "Email *", email_var)
        phone_ent = self._grid_field(form, 2, "Phone *", phone_var)
        role_ent = self._grid_field(form, 3, "Role / Designation *", role_var)
        sal_ent = self._grid_field(form, 4, "Monthly Salary (KSh) *", salary_var)

        def save_emp() -> None:
            raw_name = (name_ent.get() if hasattr(name_ent, "get") else "").strip() or name_var.get().strip()
            raw_email = (email_ent.get() if hasattr(email_ent, "get") else "").strip() or email_var.get().strip()
            raw_phone = (phone_ent.get() if hasattr(phone_ent, "get") else "").strip() or phone_var.get().strip()
            raw_role = (role_ent.get() if hasattr(role_ent, "get") else "").strip() or role_var.get().strip()
            raw_sal = (sal_ent.get() if hasattr(sal_ent, "get") else "").strip() or salary_var.get().strip()

            res, sal = validate_employee_fields(
                raw_name,
                raw_email,
                raw_phone,
                raw_role,
                raw_sal,
            )
            if not res.ok or sal is None:
                messagebox.showerror("Validation Error", res.message, parent=dialog)
                return

            def action() -> None:
                new_id = insert_employee(raw_name, raw_email, raw_phone, raw_role, sal)
                dialog.destroy()
                self._show_page("employees")
                self._refresh_employees()
                if self._emp_tree.exists(str(new_id)):
                    self._emp_tree.selection_set(str(new_id))
                    self._emp_tree.see(str(new_id))
                messagebox.showinfo(
                    "Employee Saved to Database",
                    f"'{raw_name}' was successfully saved to the database.\n\nDatabase: ManagementSystem\nTable: dbo.Employees\nEmployee ID: #{new_id}",
                    parent=self._root,
                )

            self._run_db(action, f"Employee '{raw_name}' committed to database.")

        sal_ent.bind("<Return>", lambda _e: save_emp())

        btn_box = ttk.Frame(card)
        btn_box.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(btn_box, text="Save Employee", style="Dash.Success.TButton", command=save_emp).pack(side=tk.LEFT)
        ttk.Button(btn_box, text="Cancel", style="Dash.Secondary.TButton", command=dialog.destroy).pack(side=tk.LEFT, padx=(8, 0))

    # ========================================================================
    # STUDENTS MODULE
    # ========================================================================

    def _build_students_page(self, parent: tk.Frame) -> None:
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        ent = ttk.Entry(toolbar, textvariable=self._stu_search, width=20)
        ent.pack(side=tk.LEFT, padx=(0, 8))
        ent.bind("<Return>", lambda _e: self._refresh_students())

        ttk.Label(toolbar, text="Class:").pack(side=tk.LEFT, padx=(4, 4))
        cb = ttk.Combobox(toolbar, textvariable=self._stu_class_filter, values=CLASSES, state="readonly", width=14)
        cb.pack(side=tk.LEFT, padx=(0, 8))
        cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_students())

        ttk.Button(toolbar, text="Filter", style="Dash.Secondary.TButton", command=self._refresh_students).pack(side=tk.LEFT)
        ttk.Button(
            toolbar,
            text="Reset",
            style="Dash.Secondary.TButton",
            command=lambda: [self._stu_search.set(""), self._stu_class_filter.set("All Classes"), self._refresh_students()],
        ).pack(side=tk.LEFT, padx=(4, 0))

        ttk.Button(toolbar, text="+ Enroll Student Dialog", style="Dash.Primary.TButton", command=self._show_add_student_dialog).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(toolbar, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_student_form).pack(side=tk.RIGHT)

        paned = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        table_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg)
        form_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg, width=350)
        paned.add(table_wrap, weight=3)
        paned.add(form_wrap, weight=2)

        table_card = self._section_card(table_wrap)
        ttk.Label(table_card, text="Enrolled Students", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        tframe = ttk.Frame(table_card)
        tframe.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "adm", "name", "gender", "dob", "class", "parent", "phone", "email")
        self._stu_tree = ttk.Treeview(tframe, columns=cols, show="headings")
        headings = (
            ("id", "ID", 40),
            ("adm", "Adm No", 80),
            ("name", "Student Name", 130),
            ("gender", "Gender", 60),
            ("dob", "DOB", 75),
            ("class", "Class", 85),
            ("parent", "Parent", 110),
            ("phone", "Parent Phone", 90),
            ("email", "Email", 120),
        )
        for cid, label, width in headings:
            self._stu_tree.heading(cid, text=label)
            self._stu_tree.column(cid, width=width, anchor=tk.W)

        self._stu_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(tframe, orient=tk.VERTICAL, command=self._stu_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._stu_tree.configure(yscrollcommand=scroll.set)
        self._stu_tree.bind("<<TreeviewSelect>>", self._on_student_select)

        form_card = self._section_card(form_wrap)
        ttk.Label(form_card, text="Student Record Editor", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        form = ttk.Frame(form_card)
        form.pack(fill=tk.X)
        self._grid_field(form, 0, "Admission No *", self._stu_adm)
        self._grid_field(form, 1, "Full Name *", self._stu_name)
        self._grid_field(form, 2, "Gender *", self._stu_gender, widget_type="combobox", values=("Male", "Female", "Other"), state="readonly")
        self._grid_field(form, 3, "DOB (YYYY-MM-DD)", self._stu_dob)
        self._grid_field(form, 4, "Class *", self._stu_class, widget_type="combobox", values=CLASSES[1:], state="readonly")
        self._grid_field(form, 5, "Parent / Guardian *", self._stu_parent)
        self._grid_field(form, 6, "Parent Phone *", self._stu_parent_phone)
        self._grid_field(form, 7, "Email", self._stu_email)
        self._grid_field(form, 8, "Home Address", self._stu_address)

        btns = ttk.Frame(form_card)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Save New Student", style="Dash.Success.TButton", command=self._add_student).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Update Record", style="Dash.Primary.TButton", command=self._update_student).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Delete Student", style="Dash.Danger.TButton", command=self._delete_student).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_student_form).pack(fill=tk.X)

    def _refresh_students(self) -> None:
        try:
            records = list_students(self._stu_search.get(), self._stu_class_filter.get())
        except DatabaseError as exc:
            self._status.set(f"Error loading students: {exc}")
            return
        self._stu_tree.delete(*self._stu_tree.get_children())
        for r in records:
            self._stu_tree.insert(
                "",
                tk.END,
                iid=str(r.student_id),
                values=(r.student_id, r.admission_number, r.name, r.gender, r.dob, r.student_class, r.parent_name, r.parent_phone, r.email),
            )

    def _on_student_select(self, _event: tk.Event) -> None:
        sel = self._stu_tree.selection()
        if not sel:
            return
        v = self._stu_tree.item(sel[0], "values")
        self._selected_student_id = int(v[0])
        self._set_field(self._stu_adm, v[1])
        self._set_field(self._stu_name, v[2])
        self._set_field(self._stu_gender, v[3])
        self._set_field(self._stu_dob, v[4] if v[4] != "None" else "")
        self._set_field(self._stu_class, v[5])
        self._set_field(self._stu_parent, v[6])
        self._set_field(self._stu_parent_phone, v[7])
        self._set_field(self._stu_email, v[8] if v[8] != "None" else "")

    def _clear_student_form(self) -> None:
        self._selected_student_id = None
        self._clear_field(self._stu_adm)
        self._clear_field(self._stu_name)
        self._clear_field(self._stu_gender, "Male")
        self._clear_field(self._stu_dob)
        self._clear_field(self._stu_class, "Form 1 East")
        self._clear_field(self._stu_parent)
        self._clear_field(self._stu_parent_phone)
        self._clear_field(self._stu_email)
        self._clear_field(self._stu_address)
        if hasattr(self, "_stu_tree"):
            self._stu_tree.selection_remove(self._stu_tree.selection())

    def _add_student(self) -> None:
        adm = self._val(self._stu_adm)
        name = self._val(self._stu_name)
        gender = self._val(self._stu_gender)
        dob = self._val(self._stu_dob)
        sclass = self._val(self._stu_class)
        parent = self._val(self._stu_parent)
        parent_phone = self._val(self._stu_parent_phone)
        email = self._val(self._stu_email)
        address = self._val(self._stu_address)

        res = validate_student_fields(
            adm,
            name,
            gender,
            dob,
            sclass,
            parent,
            parent_phone,
            email,
            address,
        )
        if not res.ok:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = insert_student(
                adm,
                name,
                gender,
                dob,
                sclass,
                parent,
                parent_phone,
                email,
                address,
            )
            self._refresh_students()
            if self._stu_tree.exists(str(new_id)):
                self._stu_tree.selection_set(str(new_id))
                self._stu_tree.see(str(new_id))
            messagebox.showinfo("Student Saved", f"'{name}' was successfully saved to the database (ID #{new_id}).")

        if self._run_db(action, f"Student {name} registered successfully.", on_success=self._clear_student_form):
            self._refresh_combobox_data()

    def _update_student(self) -> None:
        if self._selected_student_id is None:
            messagebox.showwarning("Select Student", "Please select a student from the directory first.")
            return
        adm = self._val(self._stu_adm)
        name = self._val(self._stu_name)
        gender = self._val(self._stu_gender)
        dob = self._val(self._stu_dob)
        sclass = self._val(self._stu_class)
        parent = self._val(self._stu_parent)
        parent_phone = self._val(self._stu_parent_phone)
        email = self._val(self._stu_email)
        address = self._val(self._stu_address)

        res = validate_student_fields(
            adm,
            name,
            gender,
            dob,
            sclass,
            parent,
            parent_phone,
            email,
            address,
        )
        if not res.ok:
            messagebox.showerror("Validation", res.message)
            return

        sid = self._selected_student_id

        def action() -> None:
            update_student(
                sid,
                adm,
                name,
                gender,
                dob,
                sclass,
                parent,
                parent_phone,
                email,
                address,
            )
            self._refresh_students()
            messagebox.showinfo("Student Updated", f"Student #{sid} '{name}' records updated.")

        if self._run_db(action, "Student biodata updated."):
            self._refresh_combobox_data()

    def _delete_student(self) -> None:
        if self._selected_student_id is None:
            messagebox.showwarning("Select Student", "Please select a student to delete.")
            return
        name = self._stu_name.get().strip()
        if not messagebox.askyesno("Confirm Delete", f"Permanently delete student {name} and their records?"):
            return
        sid = self._selected_student_id

        def action() -> None:
            delete_student(sid)

        if self._run_db(action, f"Student {name} deleted.", on_success=self._clear_student_form):
            self._refresh_combobox_data()

    # ========================================================================
    # TEACHING STAFF MODULE
    # ========================================================================

    def _build_teachers_page(self, parent: tk.Frame) -> None:
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        ent = ttk.Entry(toolbar, textvariable=self._tea_search, width=20)
        ent.pack(side=tk.LEFT, padx=(0, 8))
        ent.bind("<Return>", lambda _e: self._refresh_teachers())

        ttk.Label(toolbar, text="Department:").pack(side=tk.LEFT, padx=(4, 4))
        cb = ttk.Combobox(toolbar, textvariable=self._tea_dept_filter, values=DEPARTMENTS, state="readonly", width=16)
        cb.pack(side=tk.LEFT, padx=(0, 8))
        cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_teachers())

        ttk.Button(toolbar, text="Filter", style="Dash.Secondary.TButton", command=self._refresh_teachers).pack(side=tk.LEFT)
        ttk.Button(
            toolbar,
            text="Reset",
            style="Dash.Secondary.TButton",
            command=lambda: [self._tea_search.set(""), self._tea_dept_filter.set("All Departments"), self._refresh_teachers()],
        ).pack(side=tk.LEFT, padx=(4, 0))

        ttk.Button(toolbar, text="+ Add Teacher Dialog", style="Dash.Primary.TButton", command=self._show_add_teacher_dialog).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(toolbar, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_teacher_form).pack(side=tk.RIGHT)

        paned = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        table_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg)
        form_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg, width=350)
        paned.add(table_wrap, weight=3)
        paned.add(form_wrap, weight=2)

        table_card = self._section_card(table_wrap)
        ttk.Label(table_card, text="Teaching Faculty Roster", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        tframe = ttk.Frame(table_card)
        tframe.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "tsc", "dept", "sub1", "sub2", "phone", "email", "salary")
        self._tea_tree = ttk.Treeview(tframe, columns=cols, show="headings")
        headings = (
            ("id", "ID", 40),
            ("name", "Teacher Name", 130),
            ("tsc", "TSC No", 80),
            ("dept", "Department", 100),
            ("sub1", "Subject 1", 90),
            ("sub2", "Subject 2", 90),
            ("phone", "Phone", 90),
            ("email", "Email", 120),
            ("salary", "Salary", 80),
        )
        for cid, label, width in headings:
            self._tea_tree.heading(cid, text=label)
            self._tea_tree.column(cid, width=width, anchor=tk.W if cid != "salary" else tk.E)

        self._tea_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(tframe, orient=tk.VERTICAL, command=self._tea_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._tea_tree.configure(yscrollcommand=scroll.set)
        self._tea_tree.bind("<<TreeviewSelect>>", self._on_teacher_select)

        form_card = self._section_card(form_wrap)
        ttk.Label(form_card, text="Teacher Profile Editor", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        form = ttk.Frame(form_card)
        form.pack(fill=tk.X)
        self._grid_field(form, 0, "Full Name *", self._tea_name)
        self._grid_field(form, 1, "TSC Number *", self._tea_tsc)
        self._grid_field(form, 2, "Email *", self._tea_email)
        self._grid_field(form, 3, "Phone *", self._tea_phone)
        self._grid_field(form, 4, "Department *", self._tea_dept, widget_type="combobox", values=DEPARTMENTS[1:], state="readonly")
        self._grid_field(form, 5, "Primary Subject *", self._tea_sub1)
        self._grid_field(form, 6, "Secondary Subject", self._tea_sub2)
        sal_ent = self._grid_field(form, 7, "Monthly Salary", self._tea_salary)
        sal_ent.bind("<Return>", lambda _e: self._add_teacher())

        btns = ttk.Frame(form_card)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Add Teacher", style="Dash.Success.TButton", command=self._add_teacher).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Update Record", style="Dash.Primary.TButton", command=self._update_teacher).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Delete Teacher", style="Dash.Danger.TButton", command=self._delete_teacher).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_teacher_form).pack(fill=tk.X)

    def _refresh_teachers(self) -> None:
        try:
            records = list_teachers(self._tea_search.get(), self._tea_dept_filter.get())
        except DatabaseError as exc:
            self._status.set(f"Error loading teachers: {exc}")
            return
        self._tea_tree.delete(*self._tea_tree.get_children())
        for r in records:
            self._tea_tree.insert(
                "",
                tk.END,
                iid=str(r.teacher_id),
                values=(
                    r.teacher_id,
                    r.name,
                    r.tsc_number,
                    r.department,
                    r.subject1,
                    r.subject2,
                    r.phone,
                    r.email,
                    f"{r.salary:,.2f}" if r.salary else "—",
                ),
            )

    def _on_teacher_select(self, _event: tk.Event) -> None:
        sel = self._tea_tree.selection()
        if not sel:
            return
        v = self._tea_tree.item(sel[0], "values")
        self._selected_teacher_id = int(v[0])
        self._set_field(self._tea_name, v[1])
        self._set_field(self._tea_tsc, v[2])
        self._set_field(self._tea_dept, v[3])
        self._set_field(self._tea_sub1, v[4])
        self._set_field(self._tea_sub2, v[5] if v[5] != "None" else "")
        self._set_field(self._tea_phone, v[6])
        self._set_field(self._tea_email, v[7])
        self._set_field(self._tea_salary, str(v[8]).replace(",", "") if v[8] != "—" else "")

    def _clear_teacher_form(self) -> None:
        self._selected_teacher_id = None
        self._clear_field(self._tea_name)
        self._clear_field(self._tea_tsc)
        self._clear_field(self._tea_dept, "Sciences")
        self._clear_field(self._tea_sub1, "Mathematics")
        self._clear_field(self._tea_sub2, "Physics")
        self._clear_field(self._tea_phone)
        self._clear_field(self._tea_email)
        self._clear_field(self._tea_salary)
        if hasattr(self, "_tea_tree"):
            self._tea_tree.selection_remove(self._tea_tree.selection())

    def _add_teacher(self) -> None:
        name = self._val(self._tea_name)
        tsc = self._val(self._tea_tsc)
        email = self._val(self._tea_email)
        phone = self._val(self._tea_phone)
        dept = self._val(self._tea_dept)
        sub1 = self._val(self._tea_sub1)
        sub2 = self._val(self._tea_sub2)
        sal_str = self._val(self._tea_salary)

        res, salary = validate_teacher_fields(
            name,
            tsc,
            email,
            phone,
            dept,
            sub1,
            sub2,
            sal_str,
        )
        if not res.ok or salary is None:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = insert_teacher(
                name,
                tsc,
                email,
                phone,
                dept,
                sub1,
                sub2,
                salary,
            )
            self._refresh_teachers()
            if self._tea_tree.exists(str(new_id)):
                self._tea_tree.selection_set(str(new_id))
                self._tea_tree.see(str(new_id))
            messagebox.showinfo("Teacher Saved", f"'{name}' was successfully recorded in faculty (ID #{new_id}).")

        self._run_db(action, f"Teacher {name} added.", on_success=self._clear_teacher_form)

    def _update_teacher(self) -> None:
        if self._selected_teacher_id is None:
            messagebox.showwarning("Select Teacher", "Select a teacher from the table first.")
            return
        name = self._val(self._tea_name)
        tsc = self._val(self._tea_tsc)
        email = self._val(self._tea_email)
        phone = self._val(self._tea_phone)
        dept = self._val(self._tea_dept)
        sub1 = self._val(self._tea_sub1)
        sub2 = self._val(self._tea_sub2)
        sal_str = self._val(self._tea_salary)

        res, salary = validate_teacher_fields(
            name,
            tsc,
            email,
            phone,
            dept,
            sub1,
            sub2,
            sal_str,
        )
        if not res.ok or salary is None:
            messagebox.showerror("Validation", res.message)
            return

        tid = self._selected_teacher_id

        def action() -> None:
            update_teacher(
                tid,
                name,
                tsc,
                email,
                phone,
                dept,
                sub1,
                sub2,
                salary,
            )
            self._refresh_teachers()
            messagebox.showinfo("Teacher Updated", f"Teacher '{name}' records updated.")

        self._run_db(action, "Teacher record updated.")

    def _delete_teacher(self) -> None:
        if self._selected_teacher_id is None:
            messagebox.showwarning("Select Teacher", "Select a teacher to delete.")
            return
        name = self._tea_name.get().strip()
        if not messagebox.askyesno("Confirm Delete", f"Remove teacher {name} from faculty?"):
            return
        tid = self._selected_teacher_id

        def action() -> None:
            delete_teacher(tid)

        self._run_db(action, f"Teacher {name} removed.", on_success=self._clear_teacher_form)

    # ========================================================================
    # ACADEMICS (EXAMS & SUBJECTS) MODULE
    # ========================================================================

    def _build_academics_page(self, parent: tk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        res_tab = ttk.Frame(notebook, padding=8)
        sub_tab = ttk.Frame(notebook, padding=8)
        notebook.add(res_tab, text="  📊 Exam Results & Grading  ")
        notebook.add(sub_tab, text="  📚 Curriculum Subjects  ")

        # ---- Tab 1: Exam Results ----
        toolbar = ttk.Frame(res_tab)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        ent = ttk.Entry(toolbar, textvariable=self._res_search, width=20)
        ent.pack(side=tk.LEFT, padx=(0, 8))
        ent.bind("<Return>", lambda _e: self._refresh_results())
        ttk.Button(toolbar, text="Filter", style="Dash.Secondary.TButton", command=self._refresh_results).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Clear", style="Dash.Secondary.TButton", command=self._clear_result_form).pack(side=tk.RIGHT)

        paned = ttk.Panedwindow(res_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        table_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg)
        form_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg, width=340)
        paned.add(table_wrap, weight=3)
        paned.add(form_wrap, weight=2)

        table_card = self._section_card(table_wrap)
        ttk.Label(table_card, text="Examination Marks Ledger", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        tframe = ttk.Frame(table_card)
        tframe.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "adm", "student", "subject", "cat", "exam", "total", "grade")
        self._res_tree = ttk.Treeview(tframe, columns=cols, show="headings")
        headings = (
            ("id", "ID", 40),
            ("adm", "Adm No", 80),
            ("student", "Student Name", 140),
            ("subject", "Subject", 120),
            ("cat", "CAT (30)", 65),
            ("exam", "Exam (70)", 65),
            ("total", "Total (100)", 75),
            ("grade", "Grade", 55),
        )
        for cid, label, width in headings:
            self._res_tree.heading(cid, text=label)
            self._res_tree.column(cid, width=width, anchor=tk.W if cid not in ("cat", "exam", "total", "grade") else tk.E)

        self._res_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(tframe, orient=tk.VERTICAL, command=self._res_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._res_tree.configure(yscrollcommand=scroll.set)
        self._res_tree.bind("<<TreeviewSelect>>", self._on_result_select)

        form_card = self._section_card(form_wrap)
        ttk.Label(form_card, text="Marks Entry & Calculator", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        form = ttk.Frame(form_card)
        form.pack(fill=tk.X)
        ttk.Label(form, text="Student *").grid(row=0, column=0, sticky=tk.E, padx=(0, 10), pady=4)
        self._res_stu_cb = ttk.Combobox(form, textvariable=self._res_student_pick, state="readonly", width=28)
        self._res_stu_cb.grid(row=0, column=1, sticky=tk.EW, pady=4)

        ttk.Label(form, text="Subject *").grid(row=1, column=0, sticky=tk.E, padx=(0, 10), pady=4)
        self._res_sub_cb = ttk.Combobox(form, textvariable=self._res_subject_pick, state="readonly", width=28)
        self._res_sub_cb.grid(row=1, column=1, sticky=tk.EW, pady=4)

        cat_entry = self._grid_field(form, 2, "CAT Marks (0–30) *", self._res_cat)
        exam_entry = self._grid_field(form, 3, "Exam Marks (0–70) *", self._res_exam)

        for ent in (cat_entry, exam_entry):
            ent.bind("<KeyRelease>", lambda _e: self._calculate_result_preview())

        ttk.Label(form_card, textvariable=self._res_preview, style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(8, 0))

        btns = ttk.Frame(form_card)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Save / Post Marks", style="Dash.Success.TButton", command=self._add_result).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Delete Result", style="Dash.Danger.TButton", command=self._delete_result).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_result_form).pack(fill=tk.X)

        # ---- Tab 2: Curriculum Subjects ----
        sub_card = self._section_card(sub_tab)
        ttk.Label(sub_card, text="Curriculum Subject Catalog", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        sub_add_bar = ttk.Frame(sub_card)
        sub_add_bar.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(sub_add_bar, text="New Subject Name:").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Entry(sub_add_bar, textvariable=self._new_subject_name, width=28).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(sub_add_bar, text="+ Add Subject", style="Dash.Success.TButton", command=self._add_subject).pack(side=tk.LEFT)
        ttk.Button(sub_add_bar, text="Delete Selected", style="Dash.Danger.TButton", command=self._delete_subject).pack(side=tk.RIGHT)

        stframe = ttk.Frame(sub_card)
        stframe.pack(fill=tk.BOTH, expand=True)

        self._sub_tree = ttk.Treeview(stframe, columns=("id", "name", "count"), show="headings")
        self._sub_tree.heading("id", text="Subject ID")
        self._sub_tree.heading("name", text="Subject Name")
        self._sub_tree.heading("count", text="Recorded Exam Results")
        self._sub_tree.column("id", width=60, anchor=tk.W)
        self._sub_tree.column("name", width=240, anchor=tk.W)
        self._sub_tree.column("count", width=120, anchor=tk.E)
        self._sub_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sscroll = ttk.Scrollbar(stframe, orient=tk.VERTICAL, command=self._sub_tree.yview)
        sscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._sub_tree.configure(yscrollcommand=sscroll.set)
        self._sub_tree.bind("<<TreeviewSelect>>", self._on_subject_select)

    def _calculate_result_preview(self) -> None:
        try:
            c = int(self._res_cat.get().strip() or "0")
            e = int(self._res_exam.get().strip() or "0")
            tot = c + e
            grd = calculate_grade(tot)
            self._res_preview.set(f"Total: {tot} / 100  |  Grade: {grd}")
        except ValueError:
            self._res_preview.set("Total: — | Grade: —")

    def _refresh_results(self) -> None:
        try:
            records = list_results(self._res_search.get())
        except DatabaseError as exc:
            self._status.set(f"Error loading results: {exc}")
            return
        self._res_tree.delete(*self._res_tree.get_children())
        for r in records:
            self._res_tree.insert(
                "",
                tk.END,
                iid=str(r.result_id),
                values=(r.result_id, r.admission_number, r.student_name, r.subject_name, r.cat_marks, r.exam_marks, r.total_marks, r.grade),
            )

    def _refresh_subjects(self) -> None:
        try:
            records = list_subjects()
        except DatabaseError as exc:
            self._status.set(f"Error loading subjects: {exc}")
            return
        self._subject_choices = records
        self._sub_tree.delete(*self._sub_tree.get_children())
        for r in records:
            self._sub_tree.insert("", tk.END, iid=str(r.subject_id), values=(r.subject_id, r.name, r.results_count))
        self._res_sub_cb["values"] = [f"{s.subject_id}: {s.name}" for s in records]

    def _on_result_select(self, _event: tk.Event) -> None:
        sel = self._res_tree.selection()
        if not sel:
            return
        v = self._res_tree.item(sel[0], "values")
        self._selected_result_id = int(v[0])
        self._set_field(self._res_cat, v[4])
        self._set_field(self._res_exam, v[5])
        self._calculate_result_preview()

    def _on_subject_select(self, _event: tk.Event) -> None:
        sel = self._sub_tree.selection()
        if not sel:
            return
        v = self._sub_tree.item(sel[0], "values")
        self._selected_subject_id = int(v[0])

    def _clear_result_form(self) -> None:
        self._selected_result_id = None
        self._clear_field(self._res_cat)
        self._clear_field(self._res_exam)
        self._res_preview.set("Total: — | Grade: —")
        if hasattr(self, "_res_tree"):
            self._res_tree.selection_remove(self._res_tree.selection())

    def _add_result(self) -> None:
        stu_id = self._parse_id_from_pick(self._val(self._res_student_pick))
        sub_id = self._parse_id_from_pick(self._val(self._res_subject_pick))
        cat_str = self._val(self._res_cat)
        exam_str = self._val(self._res_exam)

        res, cat, exam = validate_result_fields(stu_id, sub_id, cat_str, exam_str)
        if not res.ok or cat is None or exam is None:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = insert_result(stu_id, sub_id, cat, exam)
            self._refresh_results()
            if self._res_tree.exists(str(new_id)):
                self._res_tree.selection_set(str(new_id))
                self._res_tree.see(str(new_id))
            messagebox.showinfo("Result Saved", "Examination score has been recorded in the database.")

        self._run_db(action, "Marks saved successfully.", on_success=self._clear_result_form)

    def _delete_result(self) -> None:
        if self._selected_result_id is None:
            messagebox.showwarning("Select Result", "Select an exam result to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Permanently remove this examination record?"):
            return
        rid = self._selected_result_id

        def action() -> None:
            delete_result(rid)

        self._run_db(action, "Result record deleted.", on_success=self._clear_result_form)

    def _add_subject(self) -> None:
        name = self._val(self._new_subject_name)
        res = validate_subject_fields(name)
        if not res.ok:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            insert_subject(name)

        if self._run_db(action, f"Subject '{name}' added.", on_success=lambda: self._clear_field(self._new_subject_name)):
            self._refresh_subjects()

    def _delete_subject(self) -> None:
        if self._selected_subject_id is None:
            messagebox.showwarning("Select Subject", "Select a subject to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete subject and all related exam marks?"):
            return
        sid = self._selected_subject_id

        def action() -> None:
            delete_subject(sid)

        if self._run_db(action, "Subject deleted."):
            self._selected_subject_id = None
            self._refresh_subjects()

    # ========================================================================
    # FEES & BURSARIES MODULE
    # ========================================================================

    def _build_fees_page(self, parent: tk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        fee_tab = ttk.Frame(notebook, padding=8)
        bur_tab = ttk.Frame(notebook, padding=8)
        notebook.add(fee_tab, text="  💳 Fee Ledger & Collections  ")
        notebook.add(bur_tab, text="  🎓 Bursaries & Scholarships  ")

        # ---- Tab 1: Fees ----
        toolbar = ttk.Frame(fee_tab)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        ent = ttk.Entry(toolbar, textvariable=self._fee_search, width=20)
        ent.pack(side=tk.LEFT, padx=(0, 8))
        ent.bind("<Return>", lambda _e: self._refresh_fees())

        ttk.Label(toolbar, text="Status:").pack(side=tk.LEFT, padx=(4, 4))
        cb = ttk.Combobox(toolbar, textvariable=self._fee_status_filter, values=("All", "Fully Paid", "Has Balance"), state="readonly", width=12)
        cb.pack(side=tk.LEFT, padx=(0, 8))
        cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_fees())

        ttk.Button(toolbar, text="Filter", style="Dash.Secondary.TButton", command=self._refresh_fees).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Clear", style="Dash.Secondary.TButton", command=self._clear_fee_form).pack(side=tk.RIGHT)

        paned = ttk.Panedwindow(fee_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        table_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg)
        form_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg, width=340)
        paned.add(table_wrap, weight=3)
        paned.add(form_wrap, weight=2)

        table_card = self._section_card(table_wrap)
        ttk.Label(table_card, text="Student Fee Balances", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        tframe = ttk.Frame(table_card)
        tframe.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "adm", "student", "class", "req", "paid", "bal", "status")
        self._fee_tree = ttk.Treeview(tframe, columns=cols, show="headings")
        headings = (
            ("id", "ID", 40),
            ("adm", "Adm No", 75),
            ("student", "Student Name", 130),
            ("class", "Class", 80),
            ("req", "Required", 85),
            ("paid", "Paid", 85),
            ("bal", "Balance", 85),
            ("status", "Status", 75),
        )
        for cid, label, width in headings:
            self._fee_tree.heading(cid, text=label)
            self._fee_tree.column(cid, width=width, anchor=tk.W if cid not in ("req", "paid", "bal") else tk.E)

        self._fee_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(tframe, orient=tk.VERTICAL, command=self._fee_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._fee_tree.configure(yscrollcommand=scroll.set)
        self._fee_tree.bind("<<TreeviewSelect>>", self._on_fee_select)

        form_card = self._section_card(form_wrap)
        ttk.Label(form_card, text="Payment & Invoice Entry", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        form = ttk.Frame(form_card)
        form.pack(fill=tk.X)
        ttk.Label(form, text="Student *").grid(row=0, column=0, sticky=tk.E, padx=(0, 10), pady=4)
        self._fee_stu_cb = ttk.Combobox(form, textvariable=self._fee_student_pick, state="readonly", width=28)
        self._fee_stu_cb.grid(row=0, column=1, sticky=tk.EW, pady=4)

        r_ent = self._grid_field(form, 1, "Amount Required (KSh) *", self._fee_required)
        p_ent = self._grid_field(form, 2, "Amount Paid (KSh) *", self._fee_paid)

        for ent in (r_ent, p_ent):
            ent.bind("<KeyRelease>", lambda _e: self._calculate_fee_preview())

        ttk.Label(form_card, textvariable=self._fee_preview, style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(8, 0))

        btns = ttk.Frame(form_card)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Record / Update Payment", style="Dash.Success.TButton", command=self._add_fee).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Delete Fee Entry", style="Dash.Danger.TButton", command=self._delete_fee).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_fee_form).pack(fill=tk.X)

        # ---- Tab 2: Bursaries ----
        bpaned = ttk.Panedwindow(bur_tab, orient=tk.HORIZONTAL)
        bpaned.pack(fill=tk.BOTH, expand=True)

        btable_wrap = tk.Frame(bpaned, bg=DASHBOARD_THEME.canvas_bg)
        bform_wrap = tk.Frame(bpaned, bg=DASHBOARD_THEME.canvas_bg, width=340)
        bpaned.add(btable_wrap, weight=3)
        bpaned.add(bform_wrap, weight=2)

        btable_card = self._section_card(btable_wrap)
        ttk.Label(btable_card, text="Bursary & Scholarship Awards", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        btframe = ttk.Frame(btable_card)
        btframe.pack(fill=tk.BOTH, expand=True)

        bcols = ("id", "adm", "student", "sponsor", "amount", "date")
        self._bur_tree = ttk.Treeview(btframe, columns=bcols, show="headings")
        bheadings = (
            ("id", "ID", 40),
            ("adm", "Adm No", 80),
            ("student", "Student Name", 140),
            ("sponsor", "Sponsor / Scheme", 140),
            ("amount", "Amount Awarded", 95),
            ("date", "Award Date", 80),
        )
        for cid, label, width in bheadings:
            self._bur_tree.heading(cid, text=label)
            self._bur_tree.column(cid, width=width, anchor=tk.W if cid != "amount" else tk.E)

        self._bur_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bscroll = ttk.Scrollbar(btframe, orient=tk.VERTICAL, command=self._bur_tree.yview)
        bscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._bur_tree.configure(yscrollcommand=bscroll.set)
        self._bur_tree.bind("<<TreeviewSelect>>", self._on_bursary_select)

        bform_card = self._section_card(bform_wrap)
        ttk.Label(bform_card, text="Award Bursary / Scholarship", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        bform = ttk.Frame(bform_card)
        bform.pack(fill=tk.X)
        ttk.Label(bform, text="Student *").grid(row=0, column=0, sticky=tk.E, padx=(0, 10), pady=4)
        self._bur_stu_cb = ttk.Combobox(bform, textvariable=self._bur_student_pick, state="readonly", width=28)
        self._bur_stu_cb.grid(row=0, column=1, sticky=tk.EW, pady=4)
        self._grid_field(bform, 1, "Sponsor Name *", self._bur_sponsor)
        self._grid_field(bform, 2, "Amount (KSh) *", self._bur_amount)
        self._grid_field(bform, 3, "Date (YYYY-MM-DD)", self._bur_date)

        bbtns = ttk.Frame(bform_card)
        bbtns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(bbtns, text="Award Bursary", style="Dash.Success.TButton", command=self._add_bursary).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(bbtns, text="Update Award", style="Dash.Primary.TButton", command=self._update_bursary).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(bbtns, text="Delete Award", style="Dash.Danger.TButton", command=self._delete_bursary).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(bbtns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_bursary_form).pack(fill=tk.X)

    def _calculate_fee_preview(self) -> None:
        try:
            req = float(self._fee_required.get().replace(",", "") or "0")
            paid = float(self._fee_paid.get().replace(",", "") or "0")
            bal = req - paid
            self._fee_preview.set(f"Calculated Balance: KSh {bal:,.2f}")
        except ValueError:
            self._fee_preview.set("Balance: —")

    def _refresh_fees(self) -> None:
        try:
            records = list_fees(self._fee_search.get(), self._fee_status_filter.get())
        except DatabaseError as exc:
            self._status.set(f"Error loading fees: {exc}")
            return
        self._fee_tree.delete(*self._fee_tree.get_children())
        for r in records:
            self._fee_tree.insert(
                "",
                tk.END,
                iid=str(r.fee_id),
                values=(
                    r.fee_id,
                    r.admission_number,
                    r.student_name,
                    r.student_class,
                    f"{r.amount_required:,.2f}",
                    f"{r.amount_paid:,.2f}",
                    f"{r.balance:,.2f}",
                    r.status,
                ),
            )

    def _refresh_bursaries(self) -> None:
        try:
            records = list_bursaries(self._bur_search.get())
        except DatabaseError as exc:
            self._status.set(f"Error loading bursaries: {exc}")
            return
        self._bur_tree.delete(*self._bur_tree.get_children())
        for r in records:
            self._bur_tree.insert(
                "",
                tk.END,
                iid=str(r.bursary_id),
                values=(r.bursary_id, r.admission_number, r.student_name, r.sponsor_name, f"{r.amount_awarded:,.2f}", r.date_awarded),
            )

    def _on_fee_select(self, _event: tk.Event) -> None:
        sel = self._fee_tree.selection()
        if not sel:
            return
        v = self._fee_tree.item(sel[0], "values")
        self._selected_fee_id = int(v[0])
        self._set_field(self._fee_required, str(v[4]).replace(",", ""))
        self._set_field(self._fee_paid, str(v[5]).replace(",", ""))
        self._calculate_fee_preview()

    def _on_bursary_select(self, _event: tk.Event) -> None:
        sel = self._bur_tree.selection()
        if not sel:
            return
        v = self._bur_tree.item(sel[0], "values")
        self._selected_bursary_id = int(v[0])
        self._set_field(self._bur_sponsor, v[3])
        self._set_field(self._bur_amount, str(v[4]).replace(",", ""))
        self._set_field(self._bur_date, v[5] if v[5] != "None" else "")

    def _clear_fee_form(self) -> None:
        self._selected_fee_id = None
        self._clear_field(self._fee_paid, "0.00")
        self._calculate_fee_preview()
        if hasattr(self, "_fee_tree"):
            self._fee_tree.selection_remove(self._fee_tree.selection())

    def _clear_bursary_form(self) -> None:
        self._selected_bursary_id = None
        self._clear_field(self._bur_sponsor)
        self._clear_field(self._bur_amount)
        self._clear_field(self._bur_date)
        if hasattr(self, "_bur_tree"):
            self._bur_tree.selection_remove(self._bur_tree.selection())

    def _add_fee(self) -> None:
        stu_id = self._parse_id_from_pick(self._val(self._fee_student_pick))
        req_str = self._val(self._fee_required)
        paid_str = self._val(self._fee_paid)
        res, req, paid = validate_fee_fields(stu_id, req_str, paid_str)
        if not res.ok or req is None or paid is None:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = upsert_fee(stu_id, req, paid)
            self._refresh_fees()
            if self._fee_tree.exists(str(new_id)):
                self._fee_tree.selection_set(str(new_id))
                self._fee_tree.see(str(new_id))
            messagebox.showinfo("Payment Recorded", f"Fee payment recorded in database for student #{stu_id}.")

        self._run_db(action, "Fee payment ledger recorded.", on_success=self._clear_fee_form)

    def _delete_fee(self) -> None:
        if self._selected_fee_id is None:
            messagebox.showwarning("Select Record", "Select a fee record to delete.")
            return
        fid = self._selected_fee_id

        def action() -> None:
            delete_fee(fid)

        self._run_db(action, "Fee record deleted.", on_success=self._clear_fee_form)

    def _add_bursary(self) -> None:
        stu_id = self._parse_id_from_pick(self._val(self._bur_student_pick))
        spon = self._val(self._bur_sponsor)
        amt_str = self._val(self._bur_amount)
        dt = self._val(self._bur_date)
        res, amt = validate_bursary_fields(stu_id, spon, amt_str, dt)
        if not res.ok or amt is None:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = insert_bursary(stu_id, spon, amt, dt)
            self._refresh_bursaries()
            if self._bur_tree.exists(str(new_id)):
                self._bur_tree.selection_set(str(new_id))
                self._bur_tree.see(str(new_id))
            messagebox.showinfo("Bursary Recorded", f"Bursary award of KSh {amt:,.2f} recorded in database.")

        self._run_db(action, "Bursary award recorded.", on_success=self._clear_bursary_form)

    def _update_bursary(self) -> None:
        if self._selected_bursary_id is None:
            messagebox.showwarning("Select Award", "Select a bursary record to update.")
            return
        stu_id = self._parse_id_from_pick(self._val(self._bur_student_pick))
        spon = self._val(self._bur_sponsor)
        amt_str = self._val(self._bur_amount)
        dt = self._val(self._bur_date)
        res, amt = validate_bursary_fields(stu_id, spon, amt_str, dt)
        if not res.ok or amt is None:
            messagebox.showerror("Validation", res.message)
            return

        bid = self._selected_bursary_id

        def action() -> None:
            update_bursary(bid, spon, amt, dt)
            self._refresh_bursaries()
            messagebox.showinfo("Bursary Updated", "Bursary record updated successfully.")

        self._run_db(action, "Bursary award updated.")

    def _delete_bursary(self) -> None:
        if self._selected_bursary_id is None:
            messagebox.showwarning("Select Award", "Select a bursary record to delete.")
            return
        bid = self._selected_bursary_id

        def action() -> None:
            delete_bursary(bid)

        self._run_db(action, "Bursary record removed.", on_success=self._clear_bursary_form)

    # ========================================================================
    # BOARDING MODULE
    # ========================================================================

    def _build_boarding_page(self, parent: tk.Frame) -> None:
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        ent = ttk.Entry(toolbar, textvariable=self._bd_search, width=20)
        ent.pack(side=tk.LEFT, padx=(0, 8))
        ent.bind("<Return>", lambda _e: self._refresh_boarding())

        ttk.Label(toolbar, text="Dormitory:").pack(side=tk.LEFT, padx=(4, 4))
        cb = ttk.Combobox(toolbar, textvariable=self._bd_dorm_filter, values=DORMITORIES, state="readonly", width=18)
        cb.pack(side=tk.LEFT, padx=(0, 8))
        cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_boarding())

        ttk.Button(toolbar, text="Filter", style="Dash.Secondary.TButton", command=self._refresh_boarding).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Clear", style="Dash.Secondary.TButton", command=self._clear_boarding_form).pack(side=tk.RIGHT)

        paned = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        table_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg)
        form_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg, width=340)
        paned.add(table_wrap, weight=3)
        paned.add(form_wrap, weight=2)

        table_card = self._section_card(table_wrap)
        ttk.Label(table_card, text="Boarding Students Ledger", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        tframe = ttk.Frame(table_card)
        tframe.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "adm", "name", "class", "dorm", "bed")
        self._bd_tree = ttk.Treeview(tframe, columns=cols, show="headings")
        headings = (
            ("id", "ID", 40),
            ("adm", "Adm No", 80),
            ("name", "Student Name", 140),
            ("class", "Class", 85),
            ("dorm", "Dormitory", 140),
            ("bed", "Bed / Cubicle", 100),
        )
        for cid, label, width in headings:
            self._bd_tree.heading(cid, text=label)
            self._bd_tree.column(cid, width=width, anchor=tk.W)

        self._bd_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(tframe, orient=tk.VERTICAL, command=self._bd_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._bd_tree.configure(yscrollcommand=scroll.set)
        self._bd_tree.bind("<<TreeviewSelect>>", self._on_boarding_select)

        form_card = self._section_card(form_wrap)
        ttk.Label(form_card, text="Bed & Dormitory Allocation", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        form = ttk.Frame(form_card)
        form.pack(fill=tk.X)
        ttk.Label(form, text="Student *").grid(row=0, column=0, sticky=tk.E, padx=(0, 10), pady=4)
        self._bd_stu_cb = ttk.Combobox(form, textvariable=self._bd_student_pick, state="readonly", width=28)
        self._bd_stu_cb.grid(row=0, column=1, sticky=tk.EW, pady=4)

        self._grid_field(form, 1, "Dormitory *", self._bd_dorm, widget_type="combobox", values=DORMITORIES[1:], state="readonly")
        self._grid_field(form, 2, "Bed / Cubicle *", self._bd_bed)

        btns = ttk.Frame(form_card)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Assign / Save Bed", style="Dash.Success.TButton", command=self._add_boarding).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Update Bed Assignment", style="Dash.Primary.TButton", command=self._update_boarding).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Check Out / Remove", style="Dash.Danger.TButton", command=self._delete_boarding).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_boarding_form).pack(fill=tk.X)

    def _refresh_boarding(self) -> None:
        try:
            records = list_boarding(self._bd_search.get(), self._bd_dorm_filter.get())
        except DatabaseError as exc:
            self._status.set(f"Error loading boarding: {exc}")
            return
        self._bd_tree.delete(*self._bd_tree.get_children())
        for r in records:
            self._bd_tree.insert(
                "",
                tk.END,
                iid=str(r.boarding_id),
                values=(r.boarding_id, r.admission_number, r.student_name, r.student_class, r.dormitory, r.bed_number),
            )

    def _on_boarding_select(self, _event: tk.Event) -> None:
        sel = self._bd_tree.selection()
        if not sel:
            return
        v = self._bd_tree.item(sel[0], "values")
        self._selected_boarding_id = int(v[0])
        self._set_field(self._bd_dorm, v[4])
        self._set_field(self._bd_bed, v[5])

    def _clear_boarding_form(self) -> None:
        self._selected_boarding_id = None
        self._clear_field(self._bd_dorm, "Mount Kenya House")
        self._clear_field(self._bd_bed)
        if hasattr(self, "_bd_tree"):
            self._bd_tree.selection_remove(self._bd_tree.selection())

    def _add_boarding(self) -> None:
        stu_id = self._parse_id_from_pick(self._val(self._bd_student_pick))
        dorm = self._val(self._bd_dorm)
        bed = self._val(self._bd_bed)
        res = validate_boarding_fields(stu_id, dorm, bed)
        if not res.ok:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = assign_boarding(stu_id, dorm, bed)
            self._refresh_boarding()
            if self._bd_tree.exists(str(new_id)):
                self._bd_tree.selection_set(str(new_id))
                self._bd_tree.see(str(new_id))
            messagebox.showinfo("Bed Allocated", f"Student #{stu_id} assigned to {dorm} (Bed: {bed}).")

        self._run_db(action, "Boarding bed allocated.", on_success=self._clear_boarding_form)

    def _update_boarding(self) -> None:
        if self._selected_boarding_id is None:
            messagebox.showwarning("Select Allocation", "Select a student boarding record to update.")
            return
        bid = self._selected_boarding_id
        dorm = self._val(self._bd_dorm)
        bed = self._val(self._bd_bed)

        def action() -> None:
            update_boarding(bid, dorm, bed)
            self._refresh_boarding()
            messagebox.showinfo("Allocation Updated", "Boarding bed assignment updated.")

        self._run_db(action, "Boarding allocation updated.")

    def _delete_boarding(self) -> None:
        if self._selected_boarding_id is None:
            messagebox.showwarning("Select Allocation", "Select a boarding record to check out.")
            return
        bid = self._selected_boarding_id

        def action() -> None:
            delete_boarding(bid)

        self._run_db(action, "Student checked out of boarding.", on_success=self._clear_boarding_form)

    # ========================================================================
    # CLUBS & SOCIETIES MODULE
    # ========================================================================

    def _build_clubs_page(self, parent: tk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        club_tab = ttk.Frame(notebook, padding=8)
        mem_tab = ttk.Frame(notebook, padding=8)
        notebook.add(club_tab, text="  👥 Registered Clubs  ")
        notebook.add(mem_tab, text="  📝 Student Memberships  ")

        # ---- Tab 1: Clubs ----
        cpaned = ttk.Panedwindow(club_tab, orient=tk.HORIZONTAL)
        cpaned.pack(fill=tk.BOTH, expand=True)

        ctable_wrap = tk.Frame(cpaned, bg=DASHBOARD_THEME.canvas_bg)
        cform_wrap = tk.Frame(cpaned, bg=DASHBOARD_THEME.canvas_bg, width=340)
        cpaned.add(ctable_wrap, weight=3)
        cpaned.add(cform_wrap, weight=2)

        ctable_card = self._section_card(ctable_wrap)
        ttk.Label(ctable_card, text="School Clubs & Societies Roster", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        ctframe = ttk.Frame(ctable_card)
        ctframe.pack(fill=tk.BOTH, expand=True)

        self._club_tree = ttk.Treeview(ctframe, columns=("id", "name", "patron", "day", "count"), show="headings")
        self._club_tree.heading("id", text="ID")
        self._club_tree.heading("name", text="Club Name")
        self._club_tree.heading("patron", text="Patron Teacher")
        self._club_tree.heading("day", text="Meeting Day & Time")
        self._club_tree.heading("count", text="Members")
        self._club_tree.column("id", width=40, anchor=tk.W)
        self._club_tree.column("name", width=160, anchor=tk.W)
        self._club_tree.column("patron", width=130, anchor=tk.W)
        self._club_tree.column("day", width=120, anchor=tk.W)
        self._club_tree.column("count", width=60, anchor=tk.E)

        self._club_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cscroll = ttk.Scrollbar(ctframe, orient=tk.VERTICAL, command=self._club_tree.yview)
        cscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._club_tree.configure(yscrollcommand=cscroll.set)
        self._club_tree.bind("<<TreeviewSelect>>", self._on_club_select)

        cform_card = self._section_card(cform_wrap)
        ttk.Label(cform_card, text="Club Registration Editor", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        cform = ttk.Frame(cform_card)
        cform.pack(fill=tk.X)
        self._grid_field(cform, 0, "Club Name *", self._club_name)
        self._grid_field(cform, 1, "Patron Teacher *", self._club_patron)
        days = (
            "Monday 4:00 PM",
            "Tuesday 4:00 PM",
            "Wednesday 4:00 PM",
            "Thursday 4:00 PM",
            "Friday 4:30 PM",
            "Saturday 10:00 AM",
        )
        self._grid_field(cform, 2, "Meeting Schedule *", self._club_day, widget_type="combobox", values=days, state="readonly")

        cbtns = ttk.Frame(cform_card)
        cbtns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(cbtns, text="Register New Club", style="Dash.Success.TButton", command=self._add_club).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(cbtns, text="Update Club Details", style="Dash.Primary.TButton", command=self._update_club).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(cbtns, text="Disband / Delete Club", style="Dash.Danger.TButton", command=self._delete_club).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(cbtns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_club_form).pack(fill=tk.X)

        # ---- Tab 2: Memberships ----
        mpaned = ttk.Panedwindow(mem_tab, orient=tk.HORIZONTAL)
        mpaned.pack(fill=tk.BOTH, expand=True)

        mtable_wrap = tk.Frame(mpaned, bg=DASHBOARD_THEME.canvas_bg)
        mform_wrap = tk.Frame(mpaned, bg=DASHBOARD_THEME.canvas_bg, width=340)
        mpaned.add(mtable_wrap, weight=3)
        mpaned.add(mform_wrap, weight=2)

        mtable_card = self._section_card(mtable_wrap)
        ttk.Label(mtable_card, text="Active Club Memberships", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        mtframe = ttk.Frame(mtable_card)
        mtframe.pack(fill=tk.BOTH, expand=True)

        mcols = ("id", "adm", "student", "class", "club")
        self._mem_tree = ttk.Treeview(mtframe, columns=mcols, show="headings")
        mheadings = (
            ("id", "ID", 40),
            ("adm", "Adm No", 80),
            ("student", "Student Name", 140),
            ("class", "Class", 85),
            ("club", "Club Name", 150),
        )
        for cid, label, width in mheadings:
            self._mem_tree.heading(cid, text=label)
            self._mem_tree.column(cid, width=width, anchor=tk.W)

        self._mem_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mscroll = ttk.Scrollbar(mtframe, orient=tk.VERTICAL, command=self._mem_tree.yview)
        mscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._mem_tree.configure(yscrollcommand=mscroll.set)
        self._mem_tree.bind("<<TreeviewSelect>>", self._on_membership_select)

        mform_card = self._section_card(mform_wrap)
        ttk.Label(mform_card, text="Enroll Student in Club", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        mform = ttk.Frame(mform_card)
        mform.pack(fill=tk.X)
        ttk.Label(mform, text="Student *").grid(row=0, column=0, sticky=tk.E, padx=(0, 10), pady=4)
        self._mem_stu_cb = ttk.Combobox(mform, textvariable=self._mem_student_pick, state="readonly", width=28)
        self._mem_stu_cb.grid(row=0, column=1, sticky=tk.EW, pady=4)

        ttk.Label(mform, text="Select Club *").grid(row=1, column=0, sticky=tk.E, padx=(0, 10), pady=4)
        self._mem_club_cb = ttk.Combobox(mform, textvariable=self._mem_club_pick, state="readonly", width=28)
        self._mem_club_cb.grid(row=1, column=1, sticky=tk.EW, pady=4)

        mbtns = ttk.Frame(mform_card)
        mbtns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(mbtns, text="Enroll Member", style="Dash.Success.TButton", command=self._add_membership).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(mbtns, text="Remove Member", style="Dash.Danger.TButton", command=self._delete_membership).pack(fill=tk.X, pady=(0, 4))

    def _refresh_clubs(self) -> None:
        try:
            records = list_clubs()
        except DatabaseError as exc:
            self._status.set(f"Error loading clubs: {exc}")
            return
        self._club_choices = records
        self._club_tree.delete(*self._club_tree.get_children())
        for r in records:
            self._club_tree.insert("", tk.END, iid=str(r.club_id), values=(r.club_id, r.name, r.patron, r.meeting_day, r.member_count))
        self._mem_club_cb["values"] = [f"{c.club_id}: {c.name}" for c in records]

    def _refresh_memberships(self) -> None:
        try:
            records = list_club_members()
        except DatabaseError as exc:
            self._status.set(f"Error loading memberships: {exc}")
            return
        self._mem_tree.delete(*self._mem_tree.get_children())
        for r in records:
            self._mem_tree.insert(
                "",
                tk.END,
                iid=str(r.membership_id),
                values=(r.membership_id, r.admission_number, r.student_name, r.student_class, r.club_name),
            )

    def _on_club_select(self, _event: tk.Event) -> None:
        sel = self._club_tree.selection()
        if not sel:
            return
        v = self._club_tree.item(sel[0], "values")
        self._selected_club_id = int(v[0])
        self._set_field(self._club_name, v[1])
        self._set_field(self._club_patron, v[2])
        self._set_field(self._club_day, v[3])

    def _on_membership_select(self, _event: tk.Event) -> None:
        sel = self._mem_tree.selection()
        if not sel:
            return
        v = self._mem_tree.item(sel[0], "values")
        self._selected_membership_id = int(v[0])

    def _clear_club_form(self) -> None:
        self._selected_club_id = None
        self._clear_field(self._club_name)
        self._clear_field(self._club_patron)
        self._clear_field(self._club_day, "Wednesday 4:00 PM")
        if hasattr(self, "_club_tree"):
            self._club_tree.selection_remove(self._club_tree.selection())

    def _add_club(self) -> None:
        name = self._val(self._club_name)
        patron = self._val(self._club_patron)
        day = self._val(self._club_day)
        res = validate_club_fields(name, patron, day)
        if not res.ok:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = insert_club(name, patron, day)
            self._refresh_clubs()
            if self._club_tree.exists(str(new_id)):
                self._club_tree.selection_set(str(new_id))
                self._club_tree.see(str(new_id))
            messagebox.showinfo("Club Saved", f"'{name}' was successfully registered in the database.")

        if self._run_db(action, f"Club '{name}' registered.", on_success=self._clear_club_form):
            self._refresh_clubs()

    def _update_club(self) -> None:
        if self._selected_club_id is None:
            messagebox.showwarning("Select Club", "Select a club to update.")
            return
        name = self._val(self._club_name)
        patron = self._val(self._club_patron)
        day = self._val(self._club_day)
        res = validate_club_fields(name, patron, day)
        if not res.ok:
            messagebox.showerror("Validation", res.message)
            return

        cid = self._selected_club_id

        def action() -> None:
            update_club(cid, name, patron, day)
            self._refresh_clubs()
            messagebox.showinfo("Club Updated", f"Club '{name}' details updated.")

        if self._run_db(action, "Club updated."):
            self._refresh_clubs()

    def _delete_club(self) -> None:
        if self._selected_club_id is None:
            messagebox.showwarning("Select Club", "Select a club to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Disband this club and remove all memberships?"):
            return
        cid = self._selected_club_id

        def action() -> None:
            delete_club(cid)

        if self._run_db(action, "Club disbanded.", on_success=self._clear_club_form):
            self._refresh_clubs()
            self._refresh_memberships()

    def _add_membership(self) -> None:
        stu_id = self._parse_id_from_pick(self._val(self._mem_student_pick))
        club_id = self._parse_id_from_pick(self._val(self._mem_club_pick))
        if not stu_id or not club_id:
            messagebox.showerror("Validation", "Please select both a student and a club.")
            return

        def action() -> None:
            new_id = add_club_member(stu_id, club_id)
            self._refresh_memberships()
            if self._mem_tree.exists(str(new_id)):
                self._mem_tree.selection_set(str(new_id))
                self._mem_tree.see(str(new_id))
            messagebox.showinfo("Member Enrolled", "Student has been successfully enrolled in the club.")

        if self._run_db(action, "Student enrolled in club."):
            self._refresh_clubs()
            self._refresh_memberships()
            self._refresh_clubs()
            self._refresh_memberships()

    def _delete_membership(self) -> None:
        if self._selected_membership_id is None:
            messagebox.showwarning("Select Member", "Select a membership row to remove.")
            return
        mid = self._selected_membership_id

        def action() -> None:
            remove_club_member(mid)

        if self._run_db(action, "Member removed from club."):
            self._selected_membership_id = None
            self._refresh_clubs()
            self._refresh_memberships()

    # ========================================================================
    # EMPLOYEES (SUPPORT WORKFORCE) MODULE
    # ========================================================================

    def _build_employees_page(self, parent: tk.Frame) -> None:
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        ent = ttk.Entry(toolbar, textvariable=self._emp_search, width=22)
        ent.pack(side=tk.LEFT, padx=(0, 8))
        ent.bind("<Return>", lambda _e: self._refresh_employees())
        ttk.Button(toolbar, text="Filter", style="Dash.Secondary.TButton", command=self._refresh_employees).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="+ Add Staff Dialog", style="Dash.Primary.TButton", command=self._show_add_employee_dialog).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(toolbar, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_employee_form).pack(side=tk.RIGHT)

        paned = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        table_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg)
        form_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg, width=340)
        paned.add(table_wrap, weight=3)
        paned.add(form_wrap, weight=2)

        table_card = self._section_card(table_wrap)
        ttk.Label(table_card, text="Administrative & Support Staff", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        tframe = ttk.Frame(table_card)
        tframe.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "email", "phone", "role", "salary")
        self._emp_tree = ttk.Treeview(tframe, columns=cols, show="headings")
        headings = (
            ("id", "ID", 40),
            ("name", "Name", 130),
            ("email", "Email", 160),
            ("phone", "Phone", 95),
            ("role", "Role", 110),
            ("salary", "Salary", 85),
        )
        for cid, label, width in headings:
            self._emp_tree.heading(cid, text=label)
            self._emp_tree.column(cid, width=width, anchor=tk.W if cid != "salary" else tk.E)

        self._emp_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(tframe, orient=tk.VERTICAL, command=self._emp_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._emp_tree.configure(yscrollcommand=scroll.set)
        self._emp_tree.bind("<<TreeviewSelect>>", self._on_employee_select)

        form_card = self._section_card(form_wrap)
        ttk.Label(form_card, text="Staff Record Editor", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        form = ttk.Frame(form_card)
        form.pack(fill=tk.X)
        self._grid_field(form, 0, "Full Name *", self._emp_name)
        self._grid_field(form, 1, "Email *", self._emp_email)
        self._grid_field(form, 2, "Phone *", self._emp_phone)
        self._grid_field(form, 3, "Role / Designation *", self._emp_role)
        sal_ent = self._grid_field(form, 4, "Monthly Salary *", self._emp_salary)
        sal_ent.bind("<Return>", lambda _e: self._add_employee())

        btns = ttk.Frame(form_card)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Add Employee", style="Dash.Success.TButton", command=self._add_employee).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Save Changes", style="Dash.Primary.TButton", command=self._update_employee).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Delete Record", style="Dash.Danger.TButton", command=self._delete_employee).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_employee_form).pack(fill=tk.X)

    def _refresh_employees(self) -> None:
        try:
            records = list_employees(self._emp_search.get())
        except DatabaseError as exc:
            self._status.set(f"Error loading staff: {exc}")
            return
        self._emp_tree.delete(*self._emp_tree.get_children())
        for r in records:
            self._emp_tree.insert(
                "",
                tk.END,
                iid=str(r.employee_id),
                values=(r.employee_id, r.name, r.email, r.phone, r.role, f"{r.salary:,.2f}"),
            )

    def _on_employee_select(self, _event: tk.Event) -> None:
        sel = self._emp_tree.selection()
        if not sel:
            return
        v = self._emp_tree.item(sel[0], "values")
        self._selected_employee_id = int(v[0])
        self._set_field(self._emp_name, v[1])
        self._set_field(self._emp_role, v[2])
        self._set_field(self._emp_email, v[3])
        self._set_field(self._emp_phone, v[4])
        self._set_field(self._emp_salary, str(v[5]).replace(",", ""))

    def _clear_employee_form(self) -> None:
        self._selected_employee_id = None
        self._clear_field(self._emp_name)
        self._clear_field(self._emp_email)
        self._clear_field(self._emp_phone)
        self._clear_field(self._emp_role)
        self._clear_field(self._emp_salary)
        if hasattr(self, "_emp_tree"):
            self._emp_tree.selection_remove(self._emp_tree.selection())

    def _add_employee(self) -> None:
        name = self._val(self._emp_name)
        email = self._val(self._emp_email)
        phone = self._val(self._emp_phone)
        role = self._val(self._emp_role)
        sal_str = self._val(self._emp_salary)

        res, sal = validate_employee_fields(
            name,
            email,
            phone,
            role,
            sal_str,
        )
        if not res.ok or sal is None:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = insert_employee(name, email, phone, role, sal)
            self._refresh_employees()
            if self._emp_tree.exists(str(new_id)):
                self._emp_tree.selection_set(str(new_id))
                self._emp_tree.see(str(new_id))
            messagebox.showinfo("Employee Saved", f"'{name}' was successfully recorded in the database (ID #{new_id}).")

        self._run_db(action, f"Staff member '{name}' added.", on_success=self._clear_employee_form)

    def _update_employee(self) -> None:
        if self._selected_employee_id is None:
            messagebox.showwarning("Select Employee", "Select a staff member from the directory first.")
            return
        name = self._val(self._emp_name)
        email = self._val(self._emp_email)
        phone = self._val(self._emp_phone)
        role = self._val(self._emp_role)
        sal_str = self._val(self._emp_salary)
        res, sal = validate_employee_fields(
            name,
            email,
            phone,
            role,
            sal_str,
        )
        if not res.ok or sal is None:
            messagebox.showerror("Validation", res.message)
            return

        eid = self._selected_employee_id

        def action() -> None:
            update_employee(eid, name, email, phone, role, sal)
            self._refresh_employees()
            messagebox.showinfo("Employee Updated", f"Staff record for '{name}' updated.")

        self._run_db(action, "Employee record updated.")

    def _delete_employee(self) -> None:
        if self._selected_employee_id is None:
            messagebox.showwarning("Select Employee", "Select an employee to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Remove this employee record permanently?"):
            return
        eid = self._selected_employee_id

        def action() -> None:
            delete_employee(eid)

        self._run_db(action, "Employee record deleted.", on_success=self._clear_employee_form)

    # ========================================================================
    # INVENTORY MODULE
    # ========================================================================

    def _build_inventory_page(self, parent: tk.Frame) -> None:
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        ent = ttk.Entry(toolbar, textvariable=self._inv_search, width=22)
        ent.pack(side=tk.LEFT, padx=(0, 8))
        ent.bind("<Return>", lambda _e: self._refresh_inventory())
        ttk.Button(toolbar, text="Filter", style="Dash.Secondary.TButton", command=self._refresh_inventory).pack(side=tk.LEFT)

        ttk.Button(
            toolbar,
            text="+ Add New Item Dialog",
            style="Dash.Primary.TButton",
            command=self._show_add_inventory_dialog,
        ).pack(side=tk.RIGHT, padx=(8, 0))

        ttk.Button(toolbar, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_inventory_form).pack(side=tk.RIGHT)

        paned = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        table_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg)
        form_wrap = tk.Frame(paned, bg=DASHBOARD_THEME.canvas_bg, width=340)
        paned.add(table_wrap, weight=3)
        paned.add(form_wrap, weight=2)

        table_card = self._section_card(table_wrap)
        ttk.Label(table_card, text="School Inventory & Supplies Ledger", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        tframe = ttk.Frame(table_card)
        tframe.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "item", "category", "qty", "price", "val", "supplier")
        self._inv_tree = ttk.Treeview(tframe, columns=cols, show="headings")
        headings = (
            ("id", "ID", 40),
            ("item", "Item Name", 140),
            ("category", "Category", 100),
            ("qty", "Qty", 55),
            ("price", "Unit Price", 80),
            ("val", "Total Value", 90),
            ("supplier", "Supplier", 120),
        )
        for cid, label, width in headings:
            self._inv_tree.heading(cid, text=label)
            self._inv_tree.column(cid, width=width, anchor=tk.W if cid not in ("qty", "price", "val") else tk.E)

        self._inv_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(tframe, orient=tk.VERTICAL, command=self._inv_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._inv_tree.configure(yscrollcommand=scroll.set)
        self._inv_tree.bind("<<TreeviewSelect>>", self._on_inventory_select)

        form_card = self._section_card(form_wrap)
        ttk.Label(form_card, text="Item Stock Editor", style="Dash.CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        form = ttk.Frame(form_card)
        form.pack(fill=tk.X)
        self._grid_field(form, 0, "Item Name *", self._inv_name)
        cats = ("Electronics", "Stationery", "Science Lab", "Sports Equipment", "Furniture", "Textbooks", "Food & Kitchen", "Maintenance")
        self._grid_field(form, 1, "Category *", self._inv_category, widget_type="combobox", values=cats)
        self._grid_field(form, 2, "Quantity *", self._inv_quantity)
        self._grid_field(form, 3, "Unit Price (KSh) *", self._inv_price)
        sup_ent = self._grid_field(form, 4, "Supplier *", self._inv_supplier)
        sup_ent.bind("<Return>", lambda _e: self._add_inventory())

        btns = ttk.Frame(form_card)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Add Inventory Item", style="Dash.Success.TButton", command=self._add_inventory).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Save Changes", style="Dash.Primary.TButton", command=self._update_inventory).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Delete Item", style="Dash.Danger.TButton", command=self._delete_inventory).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btns, text="Clear Form", style="Dash.Secondary.TButton", command=self._clear_inventory_form).pack(fill=tk.X)

    def _refresh_inventory(self) -> None:
        try:
            records = list_inventory(self._inv_search.get())
        except DatabaseError as exc:
            self._status.set(f"Error loading inventory: {exc}")
            return
        self._inv_tree.delete(*self._inv_tree.get_children())
        for r in records:
            tot = r.quantity * r.price
            self._inv_tree.insert(
                "",
                tk.END,
                iid=str(r.inventory_id),
                values=(r.inventory_id, r.item_name, r.category, r.quantity, f"{r.price:,.2f}", f"{tot:,.2f}", r.supplier),
            )

    def _on_inventory_select(self, _event: tk.Event) -> None:
        sel = self._inv_tree.selection()
        if not sel:
            return
        v = self._inv_tree.item(sel[0], "values")
        self._selected_inventory_id = int(v[0])
        self._set_field(self._inv_name, v[1])
        self._set_field(self._inv_category, v[2])
        self._set_field(self._inv_quantity, str(v[3]))
        self._set_field(self._inv_price, str(v[4]).replace(",", ""))
        self._set_field(self._inv_supplier, v[6])

    def _clear_inventory_form(self) -> None:
        self._selected_inventory_id = None
        self._clear_field(self._inv_name)
        self._clear_field(self._inv_category, "Stationery")
        self._clear_field(self._inv_quantity)
        self._clear_field(self._inv_price)
        self._clear_field(self._inv_supplier)
        if hasattr(self, "_inv_tree"):
            self._inv_tree.selection_remove(self._inv_tree.selection())

    def _add_inventory(self) -> None:
        name = self._val(self._inv_name)
        cat = self._val(self._inv_category)
        qty_str = self._val(self._inv_quantity)
        price_str = self._val(self._inv_price)
        sup = self._val(self._inv_supplier)

        res, qty, prc = validate_inventory_fields(
            name,
            cat,
            qty_str,
            price_str,
            sup,
        )
        if not res.ok or qty is None or prc is None:
            messagebox.showerror("Validation", res.message)
            return

        def action() -> None:
            new_id = insert_inventory_item(name, cat, qty, prc, sup)
            self._refresh_inventory()
            if self._inv_tree.exists(str(new_id)):
                self._inv_tree.selection_set(str(new_id))
                self._inv_tree.see(str(new_id))
            messagebox.showinfo(
                "Item Saved to Database",
                f"'{name}' was successfully added to SQL Server database.\n\nDatabase: ManagementSystem\nTable: dbo.Inventory\nItem ID: #{new_id}",
            )

        self._run_db(action, f"Inventory item '{name}' committed to database.", on_success=self._clear_inventory_form)

    def _update_inventory(self) -> None:
        if self._selected_inventory_id is None:
            messagebox.showwarning("Select Item", "Select an inventory item to update.")
            return
        name = self._val(self._inv_name)
        cat = self._val(self._inv_category)
        qty_str = self._val(self._inv_quantity)
        price_str = self._val(self._inv_price)
        sup = self._val(self._inv_supplier)

        res, qty, prc = validate_inventory_fields(
            name,
            cat,
            qty_str,
            price_str,
            sup,
        )
        if not res.ok or qty is None or prc is None:
            messagebox.showerror("Validation", res.message)
            return

        iid = self._selected_inventory_id

        def action() -> None:
            update_inventory_item(iid, name, cat, qty, prc, sup)
            self._refresh_inventory()
            messagebox.showinfo("Inventory Updated", f"Item '{name}' updated successfully.")

        self._run_db(action, "Inventory updated.")

    def _delete_inventory(self) -> None:
        if self._selected_inventory_id is None:
            messagebox.showwarning("Select Item", "Select an item to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Remove this item permanently from inventory?"):
            return
        iid = self._selected_inventory_id

        def action() -> None:
            delete_inventory_item(iid)

        self._run_db(action, "Item deleted.", on_success=self._clear_inventory_form)

    # ========================================================================
    # SHARED HELPERS & DATA SYNC
    # ========================================================================

    def _parse_id_from_pick(self, text: str) -> int | None:
        try:
            return int(text.split(":")[0].strip())
        except Exception:
            return None

    def _refresh_combobox_data(self) -> None:
        """Update student, subject, and club choices across dropdowns."""
        try:
            self._student_choices = get_student_choices()
            opts = [f"{s[0]}: {s[1]} - {s[2]} ({s[3]})" for s in self._student_choices]
            self._res_stu_cb["values"] = opts
            self._fee_stu_cb["values"] = opts
            self._bur_stu_cb["values"] = opts
            self._bd_stu_cb["values"] = opts
            self._mem_stu_cb["values"] = opts

            self._refresh_subjects()
            self._refresh_clubs()
        except DatabaseError as exc:
            self._status.set(f"Combobox sync warning: {exc}")

    def _run_db(
        self,
        action: Callable[[], None],
        success_message: str,
        *,
        on_success: Callable[[], None] | None = None,
    ) -> bool:
        try:
            action()
        except DatabaseError as exc:
            messagebox.showerror("Database Error", str(exc))
            self._status.set(str(exc))
            return False
        self._status.set(success_message)
        self._refresh_all()
        if on_success:
            on_success()
        return True

    def _refresh_all(self) -> None:
        try:
            ping()
            ensure_schema()
            stats = dashboard_stats()
        except DatabaseError as exc:
            messagebox.showerror("Database Connection", str(exc))
            self._status.set(str(exc))
            return

        self._stat_students.set(str(stats["student_count"]))
        self._stat_teachers.set(str(stats["teacher_count"]))
        self._stat_employees.set(str(stats["employee_count"]))
        self._stat_fees_collected.set(f"{stats['fees_paid']:,.2f}")
        self._stat_fees_balance.set(f"{stats['fees_balance']:,.2f}")
        self._stat_boarders.set(str(stats["boarder_count"]))
        self._stat_clubs.set(f"{stats['club_count']} ({stats['club_members_count']} members)")
        self._stat_inventory.set(str(stats["inventory_count"]))
        self._stat_inv_value.set(f"{stats['inventory_value']:,.2f}")
        self._stat_low_stock.set(str(stats["low_stock"]))

        self._refresh_combobox_data()
        self._refresh_students()
        self._refresh_teachers()
        self._refresh_results()
        self._refresh_fees()
        self._refresh_bursaries()
        self._refresh_boarding()
        self._refresh_memberships()
        self._refresh_employees()
        self._refresh_inventory()

        self._status.set("All modules synchronized with SQL Server.")

    def _close(self) -> None:
        try:
            self._root.destroy()
        except Exception:
            pass
        if self._on_sign_out:
            self._on_sign_out()

    def _sign_out(self) -> None:
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out and return to the login screen?", parent=self._root):
            self._close()

    def run(self) -> None:
        if self._owns_root:
            self._root.mainloop()
