from unittest.mock import patch
import unittest
import pytest
import time

@pytest.mark.usefixtures("db_manager", "populated_db_manager")
class TestDatabaseManager(unittest.TestCase):
    def test_exception_raised(self):
        # set invalid path
        self.db_manager.db_path = 'invalid/path/to/db.rbx'

        with pytest.raises(RuntimeError):
            self.db_manager._get_connection()


    # Test database info functions
    def test_get_tables(self):
        tables = self.db_manager.get_tables()

        self.assertIn('posts', tables, 'Posts table not found')
        self.assertIn('users', tables, 'Users table not found')
        self.assertEqual(2, len(tables), 'Tables length is incorrect')


    def test_get_views(self):
        views = self.db_manager.get_views()

        self.assertIn('users_view', views)
        self.assertEqual(1, len(views), 'Views length is incorrect')

    def test_get_table_schema(self):
        users_schema_expected = {
            'id': {
                'column_type': 'INTEGER',
                'not_null': False,
                'default_value': None,
                'primary_key': True,
                'auto_increment': True,
                'unique_constraint': False,
                'column_position': 0,
                'check_expression': None,
                'foreign_key': None,
            },
            'name': {
                'column_type': 'TEXT',
                'not_null': True,
                'default_value': None,
                'primary_key': False,
                'auto_increment': False,
                'unique_constraint': False,
                'column_position': 1,
                'check_expression': None,
                'foreign_key': None,
            },
            'email': {
                'column_type': 'TEXT',
                'not_null': False,
                'default_value': None,
                'primary_key': False,
                'auto_increment': False,
                'unique_constraint': True,
                'column_position': 2,
                'check_expression': None,
                'foreign_key': None,
            },
            'age': {
                'column_type': 'INTEGER',
                'not_null': False,
                'default_value': None,
                'primary_key': False,
                'auto_increment': False,
                'unique_constraint': False,
                'column_position': 3,
                'check_expression': None,
                'foreign_key': None,
            },
            'created_at': {
                'column_type': 'TEXT',
                'not_null': False,
                'default_value': 'CURRENT_TIMESTAMP',
                'primary_key': False,
                'auto_increment': False,
                'unique_constraint': False,
                'column_position': 4,
                'check_expression': None,
                'foreign_key': None,
            }
        }

        users_schema = self.db_manager.get_table_schema('users')
        # Expect 5 cols to be returned
        self.assertEqual(len(users_schema_expected.values()), len(users_schema), 'Users table schema length does not match')

        for schema in users_schema:
            expected_schema = users_schema_expected.get(schema['column_name'])
            # col exists in our expected schema
            self.assertIsNotNone(expected_schema, "Column doesn't exist in expected schema")
            for schema_def in expected_schema:
                self.assertEqual(expected_schema[schema_def], schema[schema_def], 'Schema def should match expected')

        invalid_schema = self.db_manager.get_table_schema('unknown')
        # no schema
        self.assertEqual(0, len(invalid_schema), 'Invalid schema should be empty')

    def test_get_view_schema(self):
        schema = self.db_manager.get_view_schema('users_view')
        self.assertEqual('CREATE VIEW users_view AS SELECT name, email FROM users WHERE age < 40', " ".join(schema['sql'].split()))

        schema = self.db_manager.get_view_schema('invalid_view')
        # no schema
        self.assertEqual(0, len(schema.keys()))

    def test_get_table_data_paginated(self):
        # Fetch data normally
        data = self.populated_db_manager.get_table_data_paginated('users')

        self.assertEqual(5, len(data['columns']), 'Expected 5 columns to be returned')
        self.assertEqual(10, data['total_rows'], 'Expected 10 as total row count')
        self.assertEqual(10, data['displayed_rows'], 'Expected 10 rows to be displayed')

        # search filters
        filters = {
            'columns': [
                {
                    'condition': ('body', 'Ydob'),
                    'type': 'LIKE'
                }
            ]
        }

        data = self.populated_db_manager.get_table_data_paginated(
            'posts',
            filters=filters
        )

        self.assertEqual(4, len(data['columns']), 'Expected 4 columns to be returned')
        self.assertEqual(10, data['total_rows'], 'Expected 10 as total row count')
        self.assertEqual(5, data['displayed_rows'], 'Expected 5 rows to be displayed')

        filters['columns'] = [
            {
                'condition': ('user_id', 1),
                'type': 'EQUALS'
            }
        ]

        data = self.populated_db_manager.get_table_data_paginated(
            'posts',
            filters=filters
        )

        self.assertEqual(10, data['total_rows'], 'Expected 10 as total row count')
        self.assertEqual(1, data['displayed_rows'], 'Expected 1 row to be displayed')

        # invalid filter type
        filters['columns'] = [
            {
                'condition': ('user_id', 1),
                'type': 'LESS'
            }
        ]

        with self.assertRaises(ValueError, msg='ValueError expected to be raised'):
            self.populated_db_manager.get_table_data_paginated(
                'users',
                filters=filters
            )


        # sorting
        filters.clear()
        filters = {
            'sorting': {
                'column': 'name',
                'order': 'ASC'
            }
        }

        data = self.populated_db_manager.get_table_data_paginated(
            'users',
            filters=filters
        )

        self.assertTrue(data['rows'] == sorted(data['rows'], key=lambda row: row[1]), 'Rows should be sorted')

        # pagination
        data = self.populated_db_manager.get_table_data_paginated(
            'users',
            page_size=5
        )

        self.assertEqual(10, data['total_rows'], 'Expected 10 as total row count')
        self.assertEqual(5, data['displayed_rows'], 'Expected 5 rows to be displayed')

        data = self.populated_db_manager.get_table_data_paginated(
            'users',
            page=2
        )

        self.assertEqual(10, data['total_rows'], 'Expected 10 as total row count')
        self.assertEqual(0, data['displayed_rows'], 'Expected no rows to be displayed')

    # Test CUD ops
    def test_insert_row(self):
        data = self.populated_db_manager.get_table_data_paginated('users')

        # initially data should exist
        self.assertEqual(10, data['displayed_rows'], 'Expected 10 rows to be displayed')

        data = {
            'name': 'Test Name',
            'email': 'email@email.com',
            'age': 22,
        }
        self.populated_db_manager.insert_row('users', data)
        data = self.populated_db_manager.get_table_data_paginated('users')

        # updated row count
        self.assertEqual(11, data['displayed_rows'], 'Expected 11 rows to be displayed')

    def test_update_row(self):
        # get user
        filters = {
            'columns': [
                {
                    'condition': ('id', 1),
                    'type': 'EQUALS'
                }
            ]
        }

        data = self.populated_db_manager.get_table_data_paginated(
            'users',
            filters=filters
        )

        user: tuple = data['rows'][0]

        # initial age (column 4)
        self.assertEqual(20, user[3], 'Initial age should be 20')

        user_id = user[0]
        update_data = {
            'age': 24
        }

        # update row
        self.populated_db_manager.update_row('users', update_data, user_id)
        # query again
        data = self.populated_db_manager.get_table_data_paginated(
            'users',
            filters=filters
        )

        # check age
        user: tuple = data['rows'][0]
        self.assertEqual(24, user[3], 'Updated age should be 24')

    def test_delete_row(self):
        # get post
        filters = {
            'columns': [
                {
                    'condition': ('user_id', 1),
                    'type': 'EQUALS'
                }
            ]
        }

        data = self.populated_db_manager.get_table_data_paginated(
            'posts',
            filters=filters
        )

        # row exists
        self.assertEqual(1, data['displayed_rows'], 'Expected 1 row to be displayed')
        post = data['rows'][0]

        self.populated_db_manager.delete_row('posts', post[0])
        data = self.populated_db_manager.get_table_data_paginated(
            'posts',
            filters=filters
        )

        # row deleted
        self.assertEqual(0, data['displayed_rows'], 'Expected 0 rows to be displayed')

    def test_delete_table(self):
        initial_table_count = len(self.db_manager.get_tables())
        self.db_manager.delete_table('posts')
        final_table_count = len(self.db_manager.get_tables())

        self.assertTrue(initial_table_count - 1 == final_table_count, 'Table should have been deleted')

    def test_delete_view(self):
        initial_view_count = len(self.db_manager.get_views())
        self.db_manager.delete_view('users_view')
        final_view_count = len(self.db_manager.get_views())

        self.assertTrue(initial_view_count - 1 == final_view_count, 'View should have been deleted')

    @patch('src.core.database_manager.time.time')
    def test_execute_query(
            self,
            mock_time
    ):
        # 10 ms execution time
        mock_time.side_effect = time_side_effect
        # Select query, with max rows condition
        # This mocks the real case where a user does a blind SELECT query
        # and too many rows are returned, forcing the manager to truncate
        # the data
        query = 'SELECT * FROM posts'
        result = self.populated_db_manager.execute_query(query, 9)

        self.assertEqual(4, len(result['columns']), 'Expected 4 columns to be returned')
        self.assertEqual(9, len(result['rows']), 'Expected 9 rows to be returned')
        self.assertEqual(9, result['total_rows'], 'Expected 9 as total row count')
        self.assertTrue(result['truncated'], 'Data should be truncated')
        # test mock execution time
        self.assertEqual(10, result['execution_time'])
        self.assertEqual(1000, result['execution_timestamp'])

        # Select query, with max rows but no truncation
        # This is due to max_rows being equal to the total number
        # of rows in the db
        result = self.populated_db_manager.execute_query(query, 10)
        self.assertFalse(result['truncated'], 'Data should not be truncated')

        # Select query, without max rows
        # User has selected to perform the query without truncation
        result = self.populated_db_manager.execute_query(query, 0)
        self.assertEqual(10, len(result['rows']), 'Expected 10 rows to be returned')
        self.assertEqual(10, result['total_rows'], 'Expected 10 as total row count')
        self.assertFalse(result['truncated'], 'Data should not be truncated')

        # DML ops
        # Insert
        query = "INSERT INTO users(name, email, age) VALUES ('Test User 12', 'email12@email.com', 45)"
        result = self.populated_db_manager.execute_query(query)
        self.assertEqual(0, len(result['columns']), 'Expected 0 columns to be returnd')
        self.assertEqual(0, len(result['rows']), 'Expected 0 rows to be returned')
        self.assertEqual(0, result['total_rows'], 'Expected 0 as total row count')
        self.assertIn('rows_affected', result, 'rows_affected should be in return result')
        self.assertEqual(1, result['rows_affected'], 'Expected 1 row to be affected')
        self.assertFalse(result['truncated'], 'Data should not be truncated')

        # Update
        query = "UPDATE users SET name = 'Test User 21' WHERE id = 1"
        result = self.populated_db_manager.execute_query(query)
        self.assertEqual(1, result['rows_affected'], 'Expected 1 row to be affected')

        # Delete
        query = 'DELETE FROM users WHERE id = 1'
        result = self.populated_db_manager.execute_query(query)
        self.assertEqual(1, result['rows_affected'], 'Expected 1 rows to be affected')

        # No rows affected
        query = 'DELETE FROM users WHERE id = 1'
        result = self.populated_db_manager.execute_query(query)
        self.assertEqual(0, result['rows_affected'], 'Expected 0 rows to be affected')


real_time = time.time
calls = iter([1000, 1010])
def time_side_effect():
    try:
        return next(calls)
    except StopIteration:
        return real_time()




