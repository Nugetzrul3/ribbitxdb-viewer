from src.models.database_table_model import DatabaseTableModel, Qt
from PySide6.QtGui import QColor
from unittest.mock import patch
import unittest


class TestDatabaseTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.columns = ['Text', 'Number', 'Float', 'None']
        cls.rows = [
            [f'Test {x}', x, x / 2, None]
            for x in range(1, len(cls.columns) + 1)
        ]
        cls.data = {
            'columns': cls.columns,
            'rows': cls.rows
        }
        cls.model = DatabaseTableModel()

    def test_set_data(self):
        with patch.object(self.model, 'beginResetModel') as begin_mock, \
            patch.object(self.model, 'endResetModel') as end_mock:
            self.model.set_data(self.data)

            # assertions
            self.assertEqual(4, self.model.columnCount(), 'Data model columns not populated')
            self.assertEqual(4, self.model.rowCount(), 'Data model rows not populated')

            begin_mock.assert_called_once()
            end_mock.assert_called_once()

    def test_data_override(self):
        # Test different roles to enforce their expected return val
        self.model.set_data(self.data)

        # Test invalid calls
        result = self.model.data(self.model.index(-1, -1))
        self.assertIsNone(result, 'Invalid index should return None')

        # out of bound
        result = self.model.data(self.model.index(3, 5))
        self.assertIsNone(result, 'Out of bound index should return None')

        # Invalid role
        result = self.model.data(self.model.index(0, 0), Qt.ItemDataRole.RangeModelDataRole)
        self.assertIsNone(result, 'Invalid role should return None')

        # test role data
        # str
        result = self.model.data(self.model.index(0, 0))
        self.assertIsNotNone(result, 'Valid index should return a value')
        self.assertEqual(self.data['rows'][0][0], result, 'Data should match expected value')

        result = self.model.data(self.model.index(1, 0), Qt.ItemDataRole.TextAlignmentRole)
        self.assertIsNone(result, 'No text alignment for str')

        result = self.model.data(self.model.index(3, 0), Qt.ItemDataRole.ForegroundRole)
        self.assertIsNone(result, 'ForegroundRole for str should return None')

        # int
        result = self.model.data(self.model.index(1, 1))
        self.assertIsInstance(result, str, 'Display Role should return a string')
        self.assertEqual(str(self.data['rows'][1][1]), result, 'Data should match expected value')

        result = self.model.data(self.model.index(2, 1), Qt.ItemDataRole.TextAlignmentRole)
        self.assertEqual(result, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         'Flag type of AlignRight or AlignVCenter should be returned')

        # None should be expected
        result = self.model.data(self.model.index(3, 1), Qt.ItemDataRole.ForegroundRole)
        self.assertIsNone(result, 'ForegroundRole for int should return None')

        # float
        result = self.model.data(self.model.index(2, 2))
        self.assertIsInstance(result, str, 'Display Role should return a string')
        self.assertEqual(str(self.data['rows'][2][2]), result, 'Data should match expected value')

        result = self.model.data(self.model.index(3, 2), Qt.ItemDataRole.TextAlignmentRole)
        self.assertEqual(result, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         'Flag type of AlignRight or AlignVCenter should be returned')

        result = self.model.data(self.model.index(0, 2), Qt.ItemDataRole.ForegroundRole)
        self.assertIsNone(result, 'ForegroundRole for float should return None')

        # none
        result = self.model.data(self.model.index(1, 3))
        self.assertEqual('NULL', result, "None type should be rendered as 'NULL'")

        result = self.model.data(self.model.index(0, 3), Qt.ItemDataRole.ForegroundRole)
        self.assertIsInstance(result, QColor, 'Role should return a QColor')
        self.assertEqual('#6b7280', result.name(), 'Colour should be correct')

        result = self.model.data(self.model.index(2, 3), Qt.ItemDataRole.TextAlignmentRole)
        self.assertIsNone(result, 'No text alignment for none type')

    def test_headerData_override(self):
        self.model.set_data(self.data)

        # invalid role
        result = self.model.headerData(10, Qt.Orientation.Horizontal, Qt.ItemDataRole.TextAlignmentRole)
        self.assertIsNone(result, 'Invalid role type should return None')

        # vertical header
        result = self.model.headerData(24, Qt.Orientation.Vertical)
        self.assertEqual('25', result, 'Vertical header should be incremented')

        # section data
        result = self.model.headerData(3, Qt.Orientation.Horizontal)
        self.assertEqual('None', result, 'Incorrect horizontal header returned')

        result = self.model.headerData(5, Qt.Orientation.Horizontal)
        self.assertIsNone(result, 'Column index out of bound should return None')
