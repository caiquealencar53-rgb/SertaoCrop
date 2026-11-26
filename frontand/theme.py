# -*- coding: utf-8 -*-
"""Identidade visual do SertãoCrop (verde, bege e neutros)."""

from string import Template

PALETA = {
    "bg": "#F4F7F4",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAF8",
    "border": "#E1E8E2",
    "border_strong": "#CBD6CD",
    "side_bg": "#12372A",
    "side_hover": "#1C4D3B",
    "side_text": "#D5E6DC",
    "side_active_bg": "#DFF0E5",
    "side_active_tx": "#12372A",
    "primary": "#1F6F4A",
    "primary_hover": "#17583A",
    "primary_press": "#12472F",
    "primary_soft": "#E3F1E8",
    "disabled_bg": "#B7C6BC",
    "disabled_tx": "#F1F5F2",
    "text": "#1E2A23",
    "text_title": "#14342A",
    "text_muted": "#6B7B71",
    "danger": "#B83227",
    "danger_bg": "#FDEEEC",
    "danger_border": "#F0B4AD",
    "danger_hover": "#FADBD7",
    "accent": "#D9A441",
    "warning_bg": "#FFF6DE",
    "warning_tx": "#7A5410",
}

QSS_TEMPLATE = Template("""
QWidget {
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
    color: $text;
}
QMainWindow, #Central, #ContentArea { background: $bg; }
QDialog, QMessageBox { background: $surface; }

#Sidebar { background: $side_bg; }
#Brand { color: #FFFFFF; font-size: 24px; font-weight: 800; }
#SidebarCaption {
    color: #A9C2B8; font-size: 10px; font-weight: 700; letter-spacing: 1px;
}
QPushButton#NavButton {
    color: $side_text; background: transparent; border: none;
    border-radius: 8px; text-align: left; padding: 12px 14px;
}
QPushButton#NavButton:hover { background: $side_hover; color: #FFFFFF; }
QPushButton#NavButton:checked {
    background: $side_active_bg; color: $side_active_tx; font-weight: bold;
}

#Topbar { background: $surface; border-bottom: 1px solid $border; }
#TopbarTitle { font-size: 16px; font-weight: bold; color: $text_title; }
#SystemStatus { color: $primary; font-size: 12px; font-weight: 600; }

QScrollArea#PageScroll, #PageContent { background: transparent; border: none; }

#PageTitle { color: $text_title; font-size: 26px; font-weight: 700; }
#MutedText { color: $text_muted; font-size: 12px; }
#SectionTitle { color: $text_title; font-size: 16px; font-weight: bold; }
#BodyText { color: #52635A; font-size: 13px; }
QLabel { background: transparent; }

#MetricCard, #Panel {
    background: $surface; border: 1px solid $border; border-radius: 12px;
}
#MetricCard { border-top: 3px solid $accent; }
#MetricTitle { color: $text_muted; font-size: 12px; font-weight: 600; }
#MetricValue { color: $primary; font-size: 28px; font-weight: 700; }

#WarningPanel {
    background: $warning_bg; border: 1px solid $accent; border-radius: 10px;
    padding: 10px; color: $warning_tx;
}

QPushButton { border-radius: 6px; padding: 8px 16px; }
QPushButton#PrimaryButton {
    background: $primary; color: #FFFFFF; border: none; font-weight: bold;
}
QPushButton#PrimaryButton:hover { background: $primary_hover; }
QPushButton#PrimaryButton:pressed { background: $primary_press; }
QPushButton#PrimaryButton:disabled { background: $disabled_bg; color: $disabled_tx; }
QPushButton#DangerButton {
    background: $danger_bg; color: $danger; border: 1px solid $danger_border;
    font-weight: bold;
}
QPushButton#DangerButton:hover { background: $danger_hover; }
QPushButton#SecondaryButton {
    background: $surface; color: $text; border: 1px solid $border_strong;
}

QDialogButtonBox QPushButton, QMessageBox QPushButton {
    background: $surface; color: $text; border: 1px solid $border_strong;
    min-width: 70px;
}
QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover {
    background: $primary_soft; border-color: $primary;
}
QDialogButtonBox QPushButton:default, QMessageBox QPushButton:default {
    background: $primary; color: #FFFFFF; border: none;
}

QTabWidget::pane { border: 1px solid $border; border-radius: 8px; background: $surface; }
QTabBar::tab {
    background: $surface_alt; color: $text_muted; padding: 9px 16px;
    border: 1px solid $border; border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: $surface; color: $primary; font-weight: bold; }

QTableWidget {
    background: $surface; alternate-background-color: $surface_alt;
    border: 1px solid $border; border-radius: 8px; gridline-color: $border;
    selection-background-color: $primary_soft; selection-color: $text_title;
}
QHeaderView::section {
    background: $surface_alt; color: $text_muted; font-weight: bold;
    padding: 8px; border: none; border-bottom: 1px solid $border;
}

QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox {
    background: $surface; border: 1px solid $border_strong;
    border-radius: 6px; padding: 5px 8px; min-height: 20px;
    selection-background-color: $primary; selection-color: #FFFFFF;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
QDoubleSpinBox:focus, QSpinBox:focus { border: 1px solid $primary; }
QComboBox QAbstractItemView {
    background: $surface; border: 1px solid $border_strong;
    selection-background-color: $primary_soft; selection-color: $text_title;
    outline: 0;
}
QTextEdit#LogBox {
    background: $surface; border: 1px solid $border; border-radius: 8px;
    padding: 10px; font-family: "JetBrains Mono", "Consolas", monospace;
}

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical {
    background: $border_strong; border-radius: 4px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: $text_muted; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
""")

APP_QSS = QSS_TEMPLATE.substitute(PALETA)
