from PySide6.QtWidgets import QApplication
from typing import Any, List, Optional
from platformdirs import user_data_dir
from ribbitxdb import BatchOperations
from src import APP_NAME, APP_AUTHOR
from datetime import datetime
import ribbitxdb


def trim_string(text):
    return text[:50] + "..." if len(text) > 50 else text

def parse_timestamp(timestamp: str):
    date_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    return date_time.strftime("%Y-%m-%d %H:%M:%S")

def try_convert_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def try_convert_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def get_dummy_data(col_type: str, column: str) -> Any:
    if col_type == 'INTEGER':
        return 0
    if col_type == 'REAL':
        return 0.0
    return f'\'{column}\''
    # How to determine boolean?

def copy_to_clipboard(text: str):
    clipboard = QApplication.clipboard()
    clipboard.setText(text)

def query_viewer_db(
        query: Any,
        params: Optional[tuple] = None,
        table: Optional[str] = None,
        key_cols: Optional[List[str]] = None
): # pragma: no cover
    try:
        data_dir = user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=True)
        conn = ribbitxdb.connect(data_dir + "/viewer.rbx")
        # regular query
        if isinstance(query, str):
            cursor = conn.cursor()
            if params:
                query = cursor.execute(query, params)
            else:
                query = cursor.execute(query)

            if query.description:
                columns = [desc[0] for desc in query.description]
                rows = query.fetchall()

                conn.commit()
                cursor.close()
                conn.close()
                return {
                    'columns': columns,
                    'rows': rows,
                }
            else:
                conn.commit()
                cursor.close()
                conn.close()
                return {
                    'columns': [],
                    'rows': [],
                }
        # bulk query
        elif isinstance(query, list):
            if table and key_cols:
                batch_ops = BatchOperations(conn)
                batch_ops.bulk_upsert(table, query, key_cols)
                conn.close()
                return

            # multiple queries
            cur = conn.cursor()
            for q in query:
                cur.execute(q)

            conn.commit()
            cur.close()
            conn.close()
        else:
            raise ValueError
    except Exception as e:
        raise e

