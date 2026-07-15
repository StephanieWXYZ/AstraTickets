from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_migrations_upgrade_and_downgrade(tmp_path: Path) -> None:
    database_path = tmp_path / "migration-test.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    inspector = inspect(engine)
    assert {"tickets", "users"}.issubset(inspector.get_table_names())
    assert {column["name"] for column in inspector.get_columns("users")} == {
        "id",
        "email",
        "password_hash",
        "full_name",
        "role",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert {column["name"] for column in inspector.get_columns("tickets")} == {
        "id",
        "title",
        "description",
        "status",
        "priority",
        "category",
        "requester_id",
        "assignee_id",
        "created_at",
        "updated_at",
        "resolved_at",
    }

    command.downgrade(config, "0001_create_users")

    inspector = inspect(engine)
    assert "tickets" not in inspector.get_table_names()
    assert "users" in inspector.get_table_names()

    command.downgrade(config, "base")

    inspector = inspect(engine)
    assert "users" not in inspector.get_table_names()
