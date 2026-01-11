from PySide6.QtWidgets import QComboBox, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QEvent
from typing import List



class MultiSelectComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.list_widget = QListWidget()
        self.setModel(self.list_widget.model())
        self.setView(self.list_widget)

        self.list_widget.itemPressed.connect(self.on_item_pressed)
        self.list_widget.viewport().installEventFilter(self)
        self.selected_items = {}
        self.all_columns = []

        self.setEnabled(False)

    def add_item(self, data: tuple):
        name = data[0]
        col_type = data[1]
        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, col_type)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        self.list_widget.addItem(item)
        self.all_columns.append((name, item))

    def add_items(self, columns: List[tuple]):
        for col_data in columns:
            self.add_item(col_data)

        self.setEnabled(True)
        self.setToolTip('Select columns to search')

    def on_item_pressed(self, item):
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
            self.selected_items.pop(item.text())
        else:
            item.setCheckState(Qt.CheckState.Checked)
            self.selected_items[item.text()] = item
        self.update_tool_tip()

    def clear_items(self):
        self.list_widget.clear()
        self.selected_items = {}
        self.all_columns = []
        self.setEnabled(False)

    def eventFilter(self, obj, event):
        if obj == self.list_widget.viewport():
            if event.type() == QEvent.Type.MouseButtonRelease:
                return True
        return super().eventFilter(obj, event)

    def update_tool_tip(self):
        selected = self.selected_items.values()
        selected_item_names = [x.text() for x in selected]
        selected_tool_tip = "\n".join(selected_item_names)
        self.setToolTip(f'Selected columns: \n{selected_tool_tip}' if len(selected_item_names) > 0 else 'Select columns to search')

    def get_selected_items(self) -> List[tuple]:
        return self.selected_items.items() if len(self.selected_items) > 0 else self.all_columns