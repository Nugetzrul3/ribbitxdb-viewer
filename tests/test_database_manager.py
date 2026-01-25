import pytest

class TestDatabaseManager:
    def test_exception_raised(
            self,
            db_manager
    ):
        # set invalid path
        db_manager.db_path = 'invalid/path/to/db.rbx'

        with pytest.raises(RuntimeError):
            db_manager._get_connection()


    # Test database info functions
    def test_get_tables(
            self,
            db_manager
    ):
        tables = db_manager.get_tables()

        assert 'posts' in tables
        assert 'users' in tables
        assert len(tables) == 2

    def test_get_views(
            self,
            db_manager
    ):
        views = db_manager.get_views()

        assert 'users_view' in views
        assert len(views) == 1

    def test_get_table_schema(
            self,
            db_manager
    ):
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

        users_schema = db_manager.get_table_schema('users')
        # Expect 5 cols to be returned
        assert len(users_schema) == len(users_schema_expected.values())

        for schema in users_schema:
            expected_schema = users_schema_expected.get(schema['column_name'])
            # col exists in our expected schema
            assert expected_schema is not None
            for schema_def in expected_schema:
                assert schema[schema_def] == expected_schema[schema_def]

    def test_get_table_data_paginated(
            self,
            populated_db_manager
    ):
        # tests: get data, data filtered, data paginated, combine filter and paginated

        # Fetch data normally
        data = populated_db_manager.get_table_data_paginated('users')

        assert len(data['columns']) == 5
        assert len(data['rows']) == 10
        assert data['total_rows'] == 10
        assert data['displayed_rows'] == 10

        # search filters
        filters = {
            'columns': [
                {
                    'condition': ('body', 'Ydob'),
                    'type': 'LIKE'
                }
            ]
        }

        data = populated_db_manager.get_table_data_paginated(
            'posts',
            filters=filters
        )

        assert len(data['columns']) == 4
        assert len(data['rows']) == 5
        assert data['total_rows'] == 10
        assert data['displayed_rows'] == 5

        filters['columns'] = [
            {
                'condition': ('user_id', 1),
                'type': 'EQUALS'
            }
        ]

        data = populated_db_manager.get_table_data_paginated(
            'posts',
            filters=filters
        )

        assert len(data['rows']) == 1
        assert data['total_rows'] == 10
        assert data['displayed_rows'] == 1

        # invalid filter type
        filters['columns'] = [
            {
                'condition': ('user_id', 1),
                'type': 'LESS'
            }
        ]

        with pytest.raises(ValueError):
            populated_db_manager.get_table_data_paginated(
                'users',
                filters=filters
            )

        # sorting
        filters.clear()
        filters = {
            'sorting': {
                'id': 'DESC'
            }
        }

        data = populated_db_manager.get_table_data_paginated(
            'users',
            filters=filters
        )

        assert data['rows'] == sorted(data['rows'], key=lambda row: row[0])

        # pagination
        data = populated_db_manager.get_table_data_paginated(
            'users',
            page_size=5
        )

        assert len(data['rows']) == 5
        assert data['total_rows'] == 10
        assert data['displayed_rows'] == 5

        data = populated_db_manager.get_table_data_paginated(
            'users',
            page=2
        )

        assert len(data['rows']) == 0
        assert data['total_rows'] == 10
        assert data['displayed_rows'] == 0

    # Test CUD ops
    def test_insert_row(
            self,
            db_manager
    ):
        data = db_manager.get_table_data_paginated('users')

        # initially no data should exist
        assert len(data['rows']) == 0

        data = {
            'name': 'Test Name',
            'email': 'email@email.com',
            'age': 22,
        }
        db_manager.insert_row('users', data)
        data = db_manager.get_table_data_paginated('users')

        # data should exist now
        assert len(data['rows']) == 1

    def test_update_row(
            self,
            populated_db_manager
    ):
        # get user
        filters = {
            'columns': [
                {
                    'condition': ('id', 1),
                    'type': 'EQUALS'
                }
            ]
        }

        data = populated_db_manager.get_table_data_paginated(
            'users',
            filters=filters
        )

        user: tuple = data['rows'][0]

        # initial age (column 4)
        assert user[3] == 20

        user_id = user[0]
        update_data = {
            'age': 24
        }

        # update row
        populated_db_manager.update_row('users', update_data, user_id)
        # query again
        data = populated_db_manager.get_table_data_paginated(
            'users',
            filters=filters
        )

        # check age
        user: tuple = data['rows'][0]
        assert user[3] == 24

    def test_delete_row(
            self,
            populated_db_manager
    ):
        # get post
        filters = {
            'columns': [
                {
                    'condition': ('user_id', 1),
                    'type': 'EQUALS'
                }
            ]
        }

        data = populated_db_manager.get_table_data_paginated(
            'posts',
            filters=filters
        )

        # row exists
        assert len(data['rows']) == 1
        post = data['rows'][0]

        populated_db_manager.delete_row('posts', post[0])
        data = populated_db_manager.get_table_data_paginated(
            'posts',
            filters=filters
        )

        # row deleted
        assert len(data['rows']) == 0


    def test_delete_table(
            self,
            db_manager
    ):
        initial_table_count = len(db_manager.get_tables())
        db_manager.delete_table('posts')
        final_table_count = len(db_manager.get_tables())

        assert initial_table_count - 1 == final_table_count

    def test_delete_view(
            self,
            db_manager
    ):
        initial_view_count = len(db_manager.get_views())
        db_manager.delete_view('users_view')
        final_view_count = len(db_manager.get_views())

        assert initial_view_count - 1 == final_view_count


