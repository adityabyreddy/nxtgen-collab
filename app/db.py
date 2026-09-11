import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.models import Project, ProjectCreate, ProjectUpdate

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "projects.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                git_repo_url TEXT DEFAULT '',
                jira_project_url TEXT DEFAULT '',
                contributors TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def _row_to_project(row: sqlite3.Row) -> Project:
    return Project(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        git_repo_url=row["git_repo_url"],
        jira_project_url=row["jira_project_url"],
        contributors=json.loads(row["contributors"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def list_projects() -> list[Project]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        return [_row_to_project(r) for r in rows]


def get_project(project_id: int) -> Project | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        return _row_to_project(row) if row else None


def create_project(data: ProjectCreate) -> Project:
    now = datetime.now(timezone.utc).isoformat()
    contributors_json = json.dumps([c.model_dump() for c in data.contributors])
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO projects
                (name, description, git_repo_url, jira_project_url, contributors, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.description,
                data.git_repo_url,
                data.jira_project_url,
                contributors_json,
                now,
                now,
            ),
        )
        new_id = cursor.lastrowid
    return get_project(new_id)  # type: ignore[return-value]


def update_project(project_id: int, data: ProjectUpdate) -> Project | None:
    if get_project(project_id) is None:
        return None
    now = datetime.now(timezone.utc).isoformat()
    contributors_json = json.dumps([c.model_dump() for c in data.contributors])
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE projects
            SET name = ?, description = ?, git_repo_url = ?, jira_project_url = ?,
                contributors = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                data.name,
                data.description,
                data.git_repo_url,
                data.jira_project_url,
                contributors_json,
                now,
                project_id,
            ),
        )
    return get_project(project_id)


def delete_project(project_id: int) -> bool:
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cursor.rowcount > 0
