from typing import List, Dict, Any
from pathlib import Path
import ribbitxdb
import time


class DatabaseManager:
    """Handles DB interactions"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path).as_posix()
        self.db_name = self.db_path.split("/")[-1]

    def get_tables(self) -> List[str]:
        """Returns a list of table names"""

        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        cursor = connection.cursor()
        query = cursor.execute("SELECT name FROM __ribbit_tables WHERE type='table'")
        res = query.fetchall()
        tables = []

        for row in res:
            tables.append(row[0])

        cursor.close()
        connection.close()

        return tables

    def get_views(self) -> List[str]:
        """Get list of all views in database"""

        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        cursor = connection.cursor()
        query = cursor.execute("SELECT name, created_at FROM __ribbit_views ORDER BY created_at DESC")
        res = query.fetchall()
        views = []

        for row in res:
            views.append(row[0])

        cursor.close()
        connection.close()

        return views

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Returns schema from table name
        :param table_name: Table name
        :return: List[Dict[str, Any]]
        """

        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        cursor = connection.cursor()
        query = cursor.execute("PRAGMA table_info(?)", (table_name,))
        res = query.fetchall()
        schemas: List[Dict[str, Any]] = []

        for row in res:
            schema: Dict[str, Any] = {
                'column_name': row[1],
                'column_type': row[2],
                'not_null': bool(row[3]),
                'default_value': row[4],
                'primary_key': bool(row[5]),
                'auto_increment': bool(row[6]),
                'unique_constraint': bool(row[7]),
                'column_position': row[8],
                'check_expression': row[9],
                'foreign_key': row[10],
            }

            schemas.append(schema)

        cursor.close()
        connection.close()

        return schemas

    def get_view_schema(self, view_name: str) -> Dict[str, Any]:
        """
        Returns schema from view name
        :param view_name:
        :return: Dict[str, Any]
        """

        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        cursor = connection.cursor()
        query = cursor.execute("SELECT sql, created_at FROM __ribbit_views WHERE name = ?", (view_name,))
        res = query.fetchone()

        schema: Dict[str, Any] = {
            'sql': res[0],
            'created_at': res[1],
        }

        cursor.close()
        connection.close()

        return schema

    def get_table_data_paginated(self, table_name: str, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """
        Returns paginated data from the selected table
        :param table_name: Table name
        :param page: Page number (1-indexed)
        :param page_size: Number of rows per page
        :return: Dict[str, Any]
        """
        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        offset = (page - 1) * page_size
        cursor = connection.cursor()

        count_query = cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = count_query.fetchone()[0]

        query = cursor.execute(
            f"SELECT * FROM {table_name} LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = query.fetchall()

        cursor.close()
        connection.close()

        return {
            'columns': columns,
            'rows': rows,
            'total_rows': total_rows,
            'page': page,
            'page_size': page_size,
            'displayed_rows': len(rows)
        }

    def delete_table(self, table_name: str):
        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        cursor = connection.cursor()
        cursor.execute(f"DROP TABLE {table_name}")
        cursor.close()
        connection.close()

    def delete_view(self, view_name: str):
        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        cursor = connection.cursor()
        cursor.execute(f"DROP VIEW {view_name}")
        cursor.close()
        connection.close()

    def execute_query(self, sql: str, max_rows: int = 5000) -> Dict[str, Any]:
        """
        Executes arbitrary query
        :param sql: SQL query
        :param max_rows: Maximum number of rows to fetch
        :return: Dict[str, Any]
        """

        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        cursor = connection.cursor()
        start_time = time.time()
        query = cursor.execute(sql)
        end_time = time.time()
        execution_time = end_time - start_time

        time_data = {
            'execution_time': execution_time,
            'execution_timestamp': start_time
        }

        if query.description:
            # This is a SELECT query
            columns = [desc[0] for desc in query.description]

            if max_rows > 0:
                rows = query.fetchmany(max_rows + 1)
                has_more = len(rows) > 0
                cursor.close()
                connection.close()

                return {
                    'columns': columns,
                    'rows': rows,
                    'total_rows': len(rows),
                    'truncated': has_more,
                    'max_rows': max_rows,
                    **time_data
                }
            # For this case, we could allow the user to do a fetch all
            # for big tables however, since the rows are loaded into memory
            # it could be an issue
            else:
                rows = query.fetchall()
                cursor.close()
                connection.close()
                return {
                    'columns': columns,
                    'rows': rows,
                    'total_rows': len(rows),
                    'truncated': False,
                    **time_data
                }
        else:
            # INSERT/UPDATE/DELETE query
            row_count = query.rowcount
            connection.commit()
            cursor.close()
            connection.close()
            return {
                'columns': [],
                'rows': [],
                'rows_affected': row_count,
                'total_rows': 0,
                'truncated': False,
                **time_data
            }
