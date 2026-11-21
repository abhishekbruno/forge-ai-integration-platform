"""Desktop UI themes and stylesheets."""

DARK_THEME_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #1e1e24;
    color: #e0e0e6;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    font-size: 13px;
}

QSplitter::handle {
    background-color: #2b2b36;
}

QTabWidget::pane {
    border: 1px solid #323242;
    background-color: #1e1e24;
}

QTabBar::tab {
    background: #252530;
    color: #a0a0b0;
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #1e1e24;
    color: #ffffff;
    border: 1px solid #323242;
    border-bottom: none;
}

QGroupBox {
    border: 1px solid #323242;
    border-radius: 6px;
    margin-top: 14px;
    font-weight: bold;
    padding: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #7aa2f7;
}

QPushButton {
    background-color: #2d3142;
    color: #ffffff;
    border: 1px solid #3f4458;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3b425a;
    border-color: #7aa2f7;
}

QPushButton:pressed {
    background-color: #1f2330;
}

QPushButton:disabled {
    background-color: #23232d;
    color: #555566;
    border-color: #2d2d38;
}

QPushButton#PrimaryButton {
    background-color: #3d59a1;
    border-color: #7aa2f7;
}

QPushButton#PrimaryButton:hover {
    background-color: #4d6ebc;
}

QPushButton#DangerButton {
    background-color: #8c2d2d;
    border-color: #f7768e;
}

QPushButton#DangerButton:hover {
    background-color: #a83636;
}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background-color: #16161c;
    color: #ffffff;
    border: 1px solid #323242;
    border-radius: 4px;
    padding: 6px 8px;
    selection-background-color: #3d59a1;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border-color: #7aa2f7;
}

QTableWidget, QTreeWidget, QListWidget {
    background-color: #16161c;
    color: #e0e0e6;
    border: 1px solid #323242;
    border-radius: 4px;
    gridline-color: #262633;
}

QHeaderView::section {
    background-color: #23232f;
    color: #a0a0b0;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #323242;
    border-bottom: 1px solid #323242;
    font-weight: bold;
}

QScrollBar:vertical {
    background: #1a1a22;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #323242;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #4a4a60;
}

QStatusBar {
    background-color: #16161c;
    color: #888899;
    border-top: 1px solid #2b2b38;
}
"""

LIGHT_THEME_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #f5f5f7;
    color: #222226;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid #dcdce2;
    border-radius: 6px;
    margin-top: 14px;
    font-weight: bold;
    padding: 12px;
}

QGroupBox::title {
    color: #1a56db;
}

QPushButton {
    background-color: #ffffff;
    color: #222226;
    border: 1px solid #cfcfd8;
    border-radius: 4px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #eef2ff;
    border-color: #6366f1;
}

QPushButton#PrimaryButton {
    background-color: #2563eb;
    color: #ffffff;
    border-color: #1d4ed8;
}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    color: #111115;
    border: 1px solid #cfcfd8;
    border-radius: 4px;
    padding: 6px 8px;
}

QTableWidget, QTreeWidget, QListWidget {
    background-color: #ffffff;
    color: #222226;
    border: 1px solid #dcdce2;
}

QHeaderView::section {
    background-color: #f0f0f4;
    color: #555566;
    padding: 6px 8px;
    border: 1px solid #e0e0e6;
}

QStatusBar {
    background-color: #e8e8ee;
    color: #555566;
    border-top: 1px solid #d0d0d8;
}
"""
