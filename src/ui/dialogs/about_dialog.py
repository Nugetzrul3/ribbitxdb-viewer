from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget,
    QTextBrowser, QListWidget, QPlainTextEdit,
    QSplitter, QListWidgetItem, QWidget
)
from PySide6.QtCore import Qt
from pathlib import Path
import sys


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About RibbitXDB Viewer")
        self.license_paths = []
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.tab_widget = QTabWidget()
        self._load_license_paths()
        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(600, 400)
        self.create_about_tab()
        self.create_license_tab()

    def create_about_tab(self):
        about_description = """
                    <h2 style="color: #00FF94">About RibbitXDB Viewer</h2>
                    <h4>
                    Copyright (c) 2025 Nugetzrul3
                    </h4>
                    <p>
                    RibbitXDB Viewer is a simple database viewer designed and created to allow management of <a href="https://github.com/ribbitx/ribbitxdb">RibbitXDB</a> databases.
                    It is free and open source, licensed under the MIT license. RibbitXDB Viewer utilises other libraries to function. See License tab for more information.
                    <br>
                    <br>
                    Author and active maintainer: <a target="_blank" href="https://github.com/Nugetzrul3">Nugetzrul3</a>
                    </p>
                """

        about_html_text_browser = QTextBrowser()
        about_html_text_browser.setAlignment(Qt.AlignmentFlag.AlignTop)
        about_html_text_browser.setOpenExternalLinks(True)
        about_html_text_browser.setReadOnly(True)
        about_html_text_browser.setFontFamily("Comic Sans MS")
        about_html_text_browser.setHtml(about_description)

        self.tab_widget.addTab(about_html_text_browser, "About")

        self.main_layout.addWidget(self.tab_widget)

    def create_license_tab(self):
        license_widget = QWidget()
        license_layout = QVBoxLayout(license_widget)
        license_list_widget = QListWidget()
        self.license_text_view = QPlainTextEdit()

        for path in self.license_paths:
            file = path.split("/")[-1]
            package = file.split(".")[0]
            item = QListWidgetItem(package)
            item.setData(Qt.ItemDataRole.UserRole, path)
            license_list_widget.addItem(item)

        self.license_text_view.setReadOnly(True)
        license_list_widget.itemClicked.connect(self.on_license_changed)

        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.addWidget(license_list_widget)
        h_splitter.addWidget(self.license_text_view)
        h_splitter.setStretchFactor(0, 1)
        h_splitter.setStretchFactor(1, 3)
        h_splitter.setChildrenCollapsible(False)
        h_splitter.handle(1).setEnabled(False)
        license_layout.addWidget(h_splitter)

        self.tab_widget.addTab(license_widget, "Licenses")

    def on_license_changed(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        with open(path, "r", encoding='utf-8') as f:
            self.license_text_view.setPlainText(f.read())

    def _load_license_paths(self):
        try:
            base_path = Path(sys._MEIPASS)
        except Exception:
            base_path = Path(__file__).parent.parent.parent

        licenses_path = base_path / 'resources' / 'licenses'

        for license_file in licenses_path.glob("*.txt"):
            self.license_paths.append(Path(license_file).as_posix())