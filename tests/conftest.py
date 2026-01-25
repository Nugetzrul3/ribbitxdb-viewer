from src.core.database_manager import DatabaseManager
from pathlib import Path
import ribbitxdb
import tempfile
import pytest

@pytest.fixture
def temp_db_path():
    # create temporary ribbitxdb database
    with tempfile.NamedTemporaryFile(suffix=".rbx") as f:
        path = f.name

    yield path

    Path(path).unlink(missing_ok=True)

@pytest.fixture
def db_manager(request, temp_db_path):
    # create db_manager and tables
    with ribbitxdb.connect(temp_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE posts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                body TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE VIEW users_view AS 
                SELECT name, email FROM users WHERE age < 40
        """)

        conn.commit()

    db_manager = DatabaseManager(temp_db_path)

    if request.cls:
        request.cls.db_manager = db_manager

    yield db_manager

@pytest.fixture
def populated_db_manager(request, db_manager):
    users = [
        {
            "name": f"Test User {x + 1}",
            "email": f"email{x + 1}@email.com",
            "age": (x * 5) + 20,
        }
        for x in range(10)
    ]

    posts = [
        {
            "user_id": x,
            "title": f"Test Title {x}",
            "body": f"Test {'Body' if x % 2 == 0 else 'Ydob'} {x}",

        }
        for x in range(10)
    ]

    for i, user in enumerate(users):
        db_manager.insert_row("users", user)
        db_manager.insert_row("posts", posts[i])

    if request.cls:
        request.cls.populated_db_manager = db_manager

    return db_manager

@pytest.fixture
def use_qapp(request, qapp):
    if request.cls:
        request.cls.qapp = qapp

@pytest.fixture
def use_qtbot(request, qtbot):
    if request.cls:
        request.cls.qtbot = qtbot

