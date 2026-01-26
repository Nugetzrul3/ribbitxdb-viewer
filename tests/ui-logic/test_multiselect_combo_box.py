from src.ui.custom import MultiSelectComboBox
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QMimeData
import unittest
import sys


class TestMultiSelectComboBox(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        self.mscb = MultiSelectComboBox()
        self.mscb.show()

    def tearDown(self):
        self.mscb.close()
        self.mscb.deleteLater()

    def test_add_item(self):
        self.mscb.add_item(('test_col', 'INTEGER'))
        list_widget_items = [self.mscb.list_widget.item(x) for x in range(self.mscb.list_widget.count())]
        self.assertEqual(1, len(list_widget_items), 'One item should be in list widget')
        self.assertEqual(1, len(self.mscb.all_columns), 'One item should be in all columns array')
        item = list_widget_items[0]
        self.assertEqual('test_col', item.text(), 'Item text should be properly set')
        self.assertEqual('INTEGER', item.data(Qt.ItemDataRole.UserRole), 'Item data should be properly set')
        self.assertEqual(Qt.CheckState.Unchecked, item.checkState(), 'Item initially should be unchecked')

    def test_add_items(self):
        self.assertFalse(self.mscb.isEnabled(), 'Initially ListWidget should be disabled')
        self.mscb.add_items([(f'test_col {x}', f'{'INTEGER' if x % 2 == 0 else 'STRING'}') for x in range(10)])
        self.assertEqual(10, len(self.mscb.all_columns), '10 items should be in all columns array')
        self.assertTrue(self.mscb.isEnabled(), 'ListWidget should now be enabled')

    def test_on_item_pressed(self):
        self.mscb.add_item(('test_col', 'INTEGER'))
        item = self.mscb.list_widget.item(0)
        item.setCheckState(Qt.CheckState.Unchecked)
        # mock an item being pressed
        self.mscb.on_item_pressed(item)
        self.assertEqual(1, len(self.mscb.selected_items.keys()), 'One item should be in selected items')
        self.assertIn('test_col', self.mscb.toolTip(), 'Column name should be in tool tip')
        item.setCheckState(Qt.CheckState.Checked)
        # mock item being pressed again
        self.mscb.on_item_pressed(item)
        self.assertEqual(0, len(self.mscb.selected_items.keys()), 'One item should be in selected items')
        self.assertNotIn('test_col', self.mscb.toolTip(), 'Tool tip should be default state')

    def test_clear_items(self):
        self.mscb.add_items([(f'test_col {x}', f'{'INTEGER' if x % 2 == 0 else 'STRING'}') for x in range(10)])

        # Set some items as pressed
        items_to_press = [self.mscb.list_widget.item(x) for x in range(self.mscb.list_widget.count() - 5)]
        for item in items_to_press:
            item.setCheckState(Qt.CheckState.Unchecked)
            self.mscb.on_item_pressed(item)

        # initial state assertions
        self.assertEqual(10, len(self.mscb.all_columns), '10 items should be in all columns')
        self.assertEqual(5, len(self.mscb.selected_items.keys()), '5 items should be selected')
        self.assertTrue(self.mscb.isEnabled(), 'ListWidget should be enabled')

        # clear items
        self.mscb.clear_items()

        # check state after clear
        self.assertEqual(0, len(self.mscb.all_columns), '0 items should be in all columns')
        self.assertEqual(0, len(self.mscb.selected_items.keys()), '0 items should be selected')
        self.assertFalse(self.mscb.isEnabled(), 'ListWidget should be disabled')

    def test_get_selected_items(self):
        self.mscb.add_items([('test_col 1', 'INTEGER'), ('test_col 2', 'TEXT')])
        item = self.mscb.list_widget.item(0)
        item.setCheckState(Qt.CheckState.Unchecked)
        self.mscb.on_item_pressed(item)

        # get selected items
        selected_items = self.mscb.get_selected_items()
        self.assertEqual(1, len(selected_items), 'One item should be returned')

        # uncheck the item
        item.setCheckState(Qt.CheckState.Checked)
        self.mscb.on_item_pressed(item)

        selected_items = self.mscb.get_selected_items()
        # all items should come back
        self.assertEqual(2, len(selected_items), 'All items should be returned')