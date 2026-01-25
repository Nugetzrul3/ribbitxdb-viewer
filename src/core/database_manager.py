from typing import List, Dict, Any, Optional
from pathlib import Path
import ribbitxdb
import time


class DatabaseManager:
    """Handles DB interactions"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path).as_posix()
        self.db_name = self.db_path.split("/")[-1]

    # CUD operations
    def insert_row(self, table_name: str, row: Dict[str, Any]):
        """Insert row into specified table"""
        connection = self._get_connection()
        cursor = connection.cursor()
        columns = list(row.keys())
        values = list(row.values())

        query = f"INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({", ".join(['?' for _ in values])})"
        cursor.execute(query, values)
        connection.commit()
        connection.close()

    def update_row(self, table_name: str, row: Dict[str, Any], id: int):
        """Update row based on specified pk column"""
        connection = self._get_connection()
        cursor = connection.cursor()
        columns = list(row.keys())
        values = list(row.values()) + [id]

        set_clause = ','.join([f"{col} = ?" for col in columns])
        query = f"UPDATE {table_name} SET {set_clause} WHERE 'id' = ?"
        cursor.execute(query, values)
        connection.commit()
        connection.close()

    def delete_row(self, table_name: str, id: int):
        """Delete row based on id"""
        connection = self._get_connection()
        cursor = connection.cursor()
        query = f"DELETE FROM {table_name} WHERE 'id' = ?"
        cursor.execute(query, (id,))
        connection.commit()
        connection.close()

    def get_tables(self) -> List[str]:
        """Returns a list of table names"""
        connection = self._get_connection()
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
        connection = self._get_connection()
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
        connection = self._get_connection()
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
        connection = self._get_connection()
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

    def get_table_data_paginated(self, table_name: str, page: int = 1, page_size: int = 100, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Returns paginated data from the selected table
        :param table_name: Table name
        :param page: Page number (1-indexed)
        :param page_size: Number of rows per page
        :param filters: Filters for searching and sorting
        :return: Dict[str, Any]
        """
        connection = self._get_connection()
        offset = (page - 1) * page_size
        cursor = connection.cursor()
        query = f"{table_name}"

        if filters:
            # apply search filters first
            if columns := filters.get("columns", None):
                query += " WHERE "
                final_filters = []
                for column in columns:
                    col, val = column.get("condition")
                    filter_type = column.get("type")

                    match filter_type:
                        case "EQUALS":
                            # id = 1
                            final_filters.append(f"{col} = {val}")
                        case "LIKE":
                            # text LIKE '%text%'
                            final_filters.append(f"{col} LIKE '%{val}%'")
                        case _:
                            raise ValueError(f"Invalid filter type: {filter_type}")

                filter_string = " OR ".join(final_filters)
                query += f"{filter_string}"

            # apply sort after
            if sorting := filters.get("sorting", None):
                column = sorting.get("column")
                order = sorting.get("order")

                query += f" ORDER BY {column} {order}"

        count_query = cursor.execute(f" SELECT COUNT(*) FROM {table_name}")
        total_rows = count_query.fetchone()[0]

        query = cursor.execute(
            f"SELECT * FROM {query} LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        if columns[0] == "count_*":
            columns.pop()
        rows = query.fetchall()

        cursor.close()
        connection.close()

        return {
            'columns': columns,
            'rows': rows,
            'total_rows': total_rows,
            'displayed_rows': len(rows)
        }

    def delete_table(self, table_name: str):
        connection = self._get_connection()
        cursor = connection.cursor()
        cursor.execute(f"DROP TABLE {table_name}")
        cursor.close()
        connection.commit()
        connection.close()

    def delete_view(self, view_name: str):
        connection = self._get_connection()
        cursor = connection.cursor()
        cursor.execute(f"DROP VIEW {view_name}")
        cursor.close()
        connection.commit()
        connection.close()

    def execute_query(self, sql: str, max_rows: int = 5000) -> Dict[str, Any]:
        """
        Executes arbitrary query
        :param sql: SQL query
        :param max_rows: Maximum number of rows to fetch
        :return: Dict[str, Any]
        """

        connection = self._get_connection()
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
                'rows_affected': row_count if row_count > 0 else 0,
                'total_rows': 0,
                'truncated': False,
                **time_data
            }

    def _get_connection(self):
        try:
            connection = ribbitxdb.connect(self.db_path)
        except Exception:
            raise RuntimeError(f"Failed to connect to {self.db_path}")

        return connection
