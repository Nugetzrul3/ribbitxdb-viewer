from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor
from typing import Dict, Any


class HistoryTableModel(QAbstractTableModel):
    def __init__(self, data: Dict[str, Any] = None):
        super().__init__()
        self._columns = []
        self._rows = []

        if data:
            self.set_data(data)

    def headerData(self, section, orientation, role = Qt.ItemDataRole.DisplayRole):
        """Return header data to display"""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self._columns):
                    return self._columns[section]
            else:
                return str(section + 1)

        return None

    def data(self, index, role = Qt.ItemDataRole.DisplayRole):
        """Return data for a given cell"""
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row >= len(self._rows) or column >= len(self._columns):
            return None

        value = self._rows[row][column]

        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(value, float):
                return f"{value:.4f}"
            return str(value)
        elif role == Qt.ItemDataRole.ForegroundRole:
            if value is None:
                return QColor("#6B7280")
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, (int, float)):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    def columnCount(self, parent = QModelIndex()):
        return len(self._columns)

    def rowCount(self, parent = QModelIndex()):
        return len(self._rows)

    def set_data(self, data: Dict[str, Any]):
        """Set row and column data"""
        self.beginResetModel()
        self._columns = ['Database', 'Execution Timestamp', 'Execution Time (s)', 'Query']
        self._rows = data.get("rows", [])
        self.endResetModel()

    def flags(self, index: QModelIndex):
        """Item flags for table data item"""
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable