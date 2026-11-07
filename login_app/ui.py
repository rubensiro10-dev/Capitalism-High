"""Shared Tk/ttk styling for the application."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from login_app.config import DASHBOARD_THEME, THEME


def configure_styles(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")

    style.configure("App.TFrame", background=THEME.primary_bg)
    style.configure("Panel.TFrame", background=THEME.panel_bg)
    style.configure("Card.TFrame", background=THEME.panel_bg, relief="flat")

    style.configure(
        "TLabel",
        background=THEME.panel_bg,
        foreground=THEME.text,
        font=(THEME.font_family, THEME.label_size),
    )
    style.configure(
        "OnPrimary.TLabel",
        background=THEME.primary_bg,
        foreground=THEME.text,
        font=(THEME.font_family, THEME.label_size),
    )
    style.configure(
        "Muted.TLabel",
        background=THEME.panel_bg,
        foreground=THEME.text_muted,
        font=(THEME.font_family, 9),
    )
    style.configure(
        "OnPrimaryMuted.TLabel",
        background=THEME.primary_bg,
        foreground=THEME.text_muted,
        font=(THEME.font_family, 9),
    )
    style.configure(
        "Title.TLabel",
        background=THEME.panel_bg,
        foreground=THEME.text,
        font=(THEME.font_family, THEME.title_size, "bold"),
    )
    style.configure(
        "Header.TLabel",
        background=THEME.primary_bg,
        foreground=THEME.text,
        font=(THEME.font_family, 18, "bold"),
    )
    style.configure(
        "StatValue.TLabel",
        background=THEME.panel_bg,
        foreground=THEME.accent,
        font=(THEME.font_family, 22, "bold"),
    )
    style.configure(
        "TNotebook",
        background=THEME.primary_bg,
        borderwidth=0,
        tabmargins=(2, 4, 2, 0),
    )
    style.configure(
        "TNotebook.Tab",
        padding=(18, 10),
        font=(THEME.font_family, THEME.label_size),
    )
    style.configure("TFrame", background=THEME.panel_bg)
    style.configure(
        "Primary.TButton",
        font=(THEME.font_family, THEME.button_size, "bold"),
        padding=(14, 8),
    )
    style.configure(
        "Secondary.TButton",
        font=(THEME.font_family, THEME.button_size),
        padding=(12, 6),
    )
    style.configure(
        "Treeview",
        font=(THEME.font_family, 10),
        rowheight=28,
    )
    style.configure(
        "Treeview.Heading",
        font=(THEME.font_family, 10, "bold"),
        padding=(8, 6),
    )
    return style


def configure_dashboard_styles(root: tk.Misc) -> ttk.Style:
    """Styles tuned for the management dashboard (light, high-contrast, professional)."""
    d = DASHBOARD_THEME
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("Dash.App.TFrame", background=d.canvas_bg)
    style.configure("Dash.Panel.TFrame", background=d.surface)
    style.configure("Dash.Card.TFrame", background=d.surface, relief="flat")
    style.configure("TFrame", background=d.surface)
    style.configure("TLabelframe", background=d.surface, foreground=d.text, bordercolor=d.border)
    style.configure("TLabelframe.Label", background=d.surface, foreground=d.accent, font=(d.font_family, 11, "bold"))

    style.configure(
        "TLabel",
        background=d.surface,
        foreground=d.text,
        font=(d.font_family, d.label_size),
    )
    style.configure(
        "Dash.Title.TLabel",
        background=d.canvas_bg,
        foreground=d.text,
        font=(d.font_family, d.title_size, "bold"),
    )
    style.configure(
        "Dash.Muted.TLabel",
        background=d.canvas_bg,
        foreground=d.text_muted,
        font=(d.font_family, 10),
    )
    style.configure(
        "Dash.CardTitle.TLabel",
        background=d.surface,
        foreground=d.text,
        font=(d.font_family, 11, "bold"),
    )
    style.configure(
        "Dash.Stat.TLabel",
        background=d.surface,
        font=(d.font_family, 24, "bold"),
    )
    style.configure(
        "Dash.Header.TLabel",
        background=d.header_bg,
        foreground=d.header_text,
        font=(d.font_family, 13, "bold"),
    )
    style.configure(
        "Dash.HeaderSub.TLabel",
        background=d.header_bg,
        foreground=d.header_subtext,
        font=(d.font_family, 10),
    )
    style.configure(
        "Dash.PageTitle.TLabel",
        background=d.header_bg,
        foreground=d.text,
        font=(d.font_family, 20, "bold"),
    )
    style.configure(
        "Dash.PageLead.TLabel",
        background=d.canvas_bg,
        foreground=d.text_muted,
        font=(d.font_family, 10),
    )
    style.configure(
        "Dash.PageHeaderLead.TLabel",
        background=d.header_bg,
        foreground=d.text_muted,
        font=(d.font_family, 10),
    )
    style.configure(
        "Dash.Breadcrumb.TLabel",
        background=d.header_bg,
        foreground=d.text_muted,
        font=(d.font_family, 9),
    )
    style.configure(
        "Dash.Status.TLabel",
        background=d.status_bar,
        foreground=d.text,
        font=(d.font_family, 9),
    )
    style.configure(
        "Dash.Badge.Paid.TLabel",
        background="#dcfce7",
        foreground="#166534",
        font=(d.font_family, 9, "bold"),
        padding=(6, 2),
    )
    style.configure(
        "Dash.Badge.Pending.TLabel",
        background="#fef3c7",
        foreground="#92400e",
        font=(d.font_family, 9, "bold"),
        padding=(6, 2),
    )

    style.configure(
        "TNotebook",
        background=d.canvas_bg,
        borderwidth=0,
        tabmargins=(4, 6, 4, 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=d.surface_muted,
        foreground=d.text_muted,
        padding=(16, 8),
        font=(d.font_family, d.label_size, "bold"),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", d.surface), ("active", d.surface)],
        foreground=[("selected", d.accent), ("active", d.text)],
        expand=[("selected", (1, 1, 1, 0))],
    )

    # Primary action button (Indigo / Accent)
    style.configure(
        "Dash.Primary.TButton",
        font=(d.font_family, d.button_size, "bold"),
        padding=(14, 8),
        background=d.accent,
        foreground="#ffffff",
        borderwidth=0,
    )
    style.map(
        "Dash.Primary.TButton",
        background=[("active", "#4338ca"), ("pressed", "#3730a3")],
        foreground=[("disabled", "#e2e8f0")],
    )

    # Secondary action button (Clean bordered button)
    style.configure(
        "Dash.Secondary.TButton",
        font=(d.font_family, d.button_size),
        padding=(12, 7),
        background=d.surface,
        foreground=d.accent,
        bordercolor=d.border,
        borderwidth=1,
    )
    style.map(
        "Dash.Secondary.TButton",
        background=[("active", d.canvas_bg), ("pressed", d.status_bar)],
    )

    # Danger action button (Delete / Remove - Red)
    style.configure(
        "Dash.Danger.TButton",
        font=(d.font_family, d.button_size, "bold"),
        padding=(12, 7),
        background="#ef4444",
        foreground="#ffffff",
        borderwidth=0,
    )
    style.map(
        "Dash.Danger.TButton",
        background=[("active", "#dc2626"), ("pressed", "#b91c1c")],
        foreground=[("disabled", "#fca5a5")],
    )

    # Success action button (Confirm / Save - Emerald)
    style.configure(
        "Dash.Success.TButton",
        font=(d.font_family, d.button_size, "bold"),
        padding=(14, 8),
        background="#10b981",
        foreground="#ffffff",
        borderwidth=0,
    )
    style.map(
        "Dash.Success.TButton",
        background=[("active", "#059669"), ("pressed", "#047857")],
        foreground=[("disabled", "#a7f3d0")],
    )

    # Treeview styling
    style.configure(
        "Treeview",
        background=d.surface,
        fieldbackground=d.surface,
        foreground=d.text,
        rowheight=28,
        bordercolor=d.border,
        font=(d.font_family, 10),
    )
    style.configure(
        "Treeview.Heading",
        background=d.status_bar,
        foreground=d.text,
        relief="flat",
        font=(d.font_family, 10, "bold"),
        padding=(8, 6),
    )
    style.map(
        "Treeview",
        background=[("selected", d.selection)],
        foreground=[("selected", "#0f172a")],
    )

    # Form inputs
    style.configure("TEntry", fieldbackground="#ffffff", foreground=d.text, bordercolor=d.border)
    style.configure("TCombobox", fieldbackground="#ffffff", foreground=d.text, bordercolor=d.border)
    style.configure("Vertical.TScrollbar", background=d.surface_muted, troughcolor=d.canvas_bg)
    style.configure("Horizontal.TScrollbar", background=d.surface_muted, troughcolor=d.canvas_bg)

    return style
