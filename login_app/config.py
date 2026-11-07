"""Application configuration and visual theme."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
USERS_FILE = DATA_DIR / "users.json"


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    driver: str = "ODBC Driver 17 for SQL Server"
    server: str = os.environ.get("LOGIN_APP_DB_SERVER", r"RUBENSIRO\SQLEXPRESS01")
    database: str = os.environ.get("LOGIN_APP_DB_NAME", "ManagementSystem")
    trusted_connection: bool = True
    uid: str = os.environ.get("LOGIN_APP_DB_UID", "")
    pwd: str = os.environ.get("LOGIN_APP_DB_PWD", "")
    timeout_seconds: int = 15


@dataclass(frozen=True, slots=True)
class WindowConfig:
    title: str = "Capitalism High School - Access Portal"
    subtitle: str = "Integrated High School Management System"
    width: int = 760
    height: int = 500
    min_width: int = 680
    min_height: int = 450


@dataclass(frozen=True, slots=True)
class DashboardWindowConfig:
    title: str = "CAPITALISM HIGH SCHOOL - Management System"
    product_name: str = "CAPITALISM HIGH SCHOOL"
    subtitle: str = "School ERP & Administration System"
    width: int = 1320
    height: int = 760
    min_width: int = 1080
    min_height: int = 650


@dataclass(frozen=True, slots=True)
class Theme:
    primary_bg: str = "#0f172a"
    panel_bg: str = "#1e293b"
    accent: str = "#38bdf8"
    accent_hover: str = "#0ea5e9"
    text: str = "#f8fafc"
    text_muted: str = "#94a3b8"
    error: str = "#f87171"
    font_family: str = "Segoe UI"
    title_size: int = 22
    label_size: int = 11
    entry_size: int = 11
    button_size: int = 11


@dataclass(frozen=True, slots=True)
class DashboardTheme:
    """Light, high-contrast palette for the post-login workspace."""

    canvas_bg: str = "#f1f5f9"
    header_bg: str = "#ffffff"
    header_text: str = "#0f172a"
    header_subtext: str = "#64748b"
    sidebar_bg: str = "#0f172a"
    sidebar_text: str = "#cbd5e1"
    sidebar_muted: str = "#64748b"
    sidebar_active_bg: str = "#1e293b"
    sidebar_active_text: str = "#ffffff"
    sidebar_accent_bar: str = "#6366f1"
    surface: str = "#ffffff"
    surface_muted: str = "#f8fafc"
    status_bar: str = "#e2e8f0"
    border: str = "#e2e8f0"
    text: str = "#1e293b"
    text_muted: str = "#64748b"
    accent: str = "#4f46e5"
    accent_soft: str = "#818cf8"

    # Stat / Card colors
    stat_students: str = "#4f46e5"
    stat_teachers: str = "#0284c7"
    stat_fees: str = "#059669"
    stat_boarding: str = "#d97706"
    stat_clubs: str = "#7c3aed"
    stat_employees: str = "#6366f1"
    stat_inventory: str = "#0891b2"
    stat_value: str = "#059669"
    stat_low: str = "#d97706"

    # Table styles
    row_alt: str = "#f8fafc"
    selection: str = "#c7d2fe"
    danger: str = "#ef4444"
    success: str = "#10b981"
    warning: str = "#f59e0b"

    font_family: str = "Segoe UI"
    title_size: int = 20
    label_size: int = 11
    button_size: int = 11


WINDOW = WindowConfig()
DASHBOARD_WINDOW = DashboardWindowConfig()
DB_CONFIG = DatabaseConfig()
THEME = Theme()
DASHBOARD_THEME = DashboardTheme()

EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"
PHONE_LENGTH = 10
PHONE_PREFIXES = ("07", "01")


def resolve_background_image() -> Path | None:
    """Return a background image path inside this project folder, or None."""
    for path in (
        ASSETS_DIR / "background.jpg",
        ASSETS_DIR / "background.png",
        ASSETS_DIR / "OIP.jpg",
        PROJECT_ROOT / "background.jpg",
    ):
        if path.is_file():
            return path.resolve()
    return None
