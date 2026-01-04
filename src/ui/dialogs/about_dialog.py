from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QLabel, QWidget


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About RibbitXDB Viewer")
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.tab_widget = QTabWidget()
        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(600, 400)

        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)

        about_description = """
            About description here!
        """
        about_layout.addWidget(QLabel(about_description))
        print("hello")

        self.tab_widget.addTab(about_widget, "About")

        print("hello")


        self.main_layout.addWidget(self.tab_widget)