from typing import List, Dict, Any, Optional
from ribbitxdb.connection import Connection
from pathlib import Path
import ribbitxdb


class DatabaseManager:
    """Handles DB interactions"""

    def __init__(self):
        self.connection: Optional[Connection] = None
        self.db_path: Optional[str] = None

    def open(self, db_path: str):
        if self.connection:
            self.close()

        self.connection = ribbitxdb.connect(db_path)
        self.db_path = Path(db_path).as_posix()

    def get_tables(self) -> List[str]:
        """Returns a list of table names"""

        if not self.connection:
            raise RuntimeError("No database connection")
        cursor = self.connection.cursor()
        query = cursor.execute("SELECT name FROM __ribbit_tables WHERE type='table'")
        res = query.fetchall()
        tables = []

        for row in res:
            tables.append(row[0])

        return tables

    def get_views(self) -> List[str]:
        """Get list of all views in database"""

        if not self.connection:
            raise RuntimeError("No database connection")
        cursor = self.connection.cursor()
        query = cursor.execute("SELECT name, created_at FROM __ribbit_views ORDER BY created_at DESC")
        res = query.fetchall()
        views = []

        for row in res:
            views.append(row[0])

        return views

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Returns schema from table name
        :param table_name: Table name
        :return: Dict[str, Any]
        """

        if not self.connection:
            raise RuntimeError("No database connection")
        cursor = self.connection.cursor()
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

        return schemas

    def get_view_schema(self, view_name: str) -> Dict[str, Any]:
        """
        Returns schema from view name
        :param view_name:
        :return: Dict[str, Any]
        """

        if not self.connection:
            raise RuntimeError("No database connection")
        cursor = self.connection.cursor()
        query = cursor.execute("SELECT sql, created_at FROM __ribbit_views WHERE name = ?", (view_name,))
        res = query.fetchone()

        schema: Dict[str, Any] = {
            'sql': res[0],
            'created_at': res[1],
        }

        return schema

    def get_table_data(self, table_name: str, limit: int = 500) -> Dict[str, Any]:
        """
        Returns data from the selected table
        :param table_name: Table name
        :param limit: Number of rows to return (default 500)
        :return: Dict[str, Any]
        """

        if not self.connection:
            raise RuntimeError("No database connection")
        cursor = self.connection.cursor()
        query = cursor.execute(f"SELECT * FROM ? LIMIT ?", (table_name, limit))
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = query.fetchall()

        return {
            'columns': columns,
            'rows': rows,
            'total_rows': len(rows),
        }

    def get_table_data_paginated(self, table_name: str, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """
        Returns paginated data from the selected table
        :param table_name: Table name
        :param page: Page number (1-indexed)
        :param page_size: Number of rows per page
        :return: Dict[str, Any]
        """
        if not self.connection:
            raise RuntimeError("No database connection")

        offset = (page - 1) * page_size
        cursor = self.connection.cursor()

        count_query = cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = count_query.fetchone()[0]

        query = cursor.execute(
            f"SELECT * FROM {table_name} LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = query.fetchall()

        return {
            'columns': columns,
            'rows': rows,
            'total_rows': total_rows,
            'page': page,
            'page_size': page_size,
            'displayed_rows': len(rows)
        }

    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Executes arbitrary query
        :param sql: SQL query
        :return: Dict[str, Any]
        """

        if not self.connection:
            raise RuntimeError("No database connection")
        cursor = self.connection.cursor()
        query = cursor.execute(sql)

        if query.description:
            # This is a SELECT query
            columns = [desc[0] for desc in query.description]
            rows = query.fetchall()
            return {
                'columns': columns,
                'rows': rows,
                'total_rows': len(rows)
            }
        else:
            # INSERT/UPDATE/DELETE query
            self.connection.commit()
            return {
                'columns': [],
                'rows': [],
                'total_rows': query.rowcount
            }


    def refresh_connection(self):
        if not self.connection or not self.db_path:
            raise RuntimeError("No database connection")

        db_path = self.db_path
        self.close()
        self.open(db_path)

    def close(self):
        """Closes the current connection"""

        if self.connection:
            self.connection.close()
        self.connection = None
        self.db_path = None

    def __del__(self):
        self.close()
