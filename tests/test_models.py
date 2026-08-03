"""ERD 모델과 최초 migration 스냅샷의 구조 검증."""

import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace

from sqlalchemy import MetaData, create_engine
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

import app.models  # noqa: F401
from app.db.base import Base

EXPECTED_TABLES = {
    "affinities",
    "album_images",
    "albums",
    "auth_sessions",
    "avatar_conversation_images",
    "avatar_conversation_messages",
    "avatar_conversation_sessions",
    "avatar_interaction_pictures",
    "avatar_interaction_sessions",
    "conversation_reports",
    "cube_ownerships",
    "cube_verifications",
    "cubes",
    "levels",
    "mission_progresses",
    "missions",
    "notifications",
    "reward_items",
    "stage_captures",
    "stage_sessions",
    "stages",
    "track_captures",
    "track_sessions",
    "tracks",
    "user_rewards",
    "user_settings",
    "users",
}


def _load_initial_migration() -> ModuleType:
    migration_path = (
        Path(__file__).parents[1]
        / "migrations"
        / "versions"
        / "20260803_0001_initial_schema.py"
    )
    spec = importlib.util.spec_from_file_location("initial_schema", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _foreign_keys(metadata: MetaData, table_name: str) -> set[tuple[str, str]]:
    table = metadata.tables[table_name]
    return {
        (foreign_key.parent.name, foreign_key.target_fullname)
        for foreign_key in table.foreign_keys
    }


def _unique_columns(metadata: MetaData, table_name: str) -> set[tuple[str, ...]]:
    table = metadata.tables[table_name]
    return {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }


def _indexes(metadata: MetaData, table_name: str) -> set[tuple[str, ...]]:
    return {
        tuple(column.name for column in index.columns)
        for index in metadata.tables[table_name].indexes
    }


def test_erd_contains_27_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_initial_migration_matches_model_structure() -> None:
    migration = _load_initial_migration()
    migration_metadata = migration._metadata()

    assert set(migration_metadata.tables) == set(Base.metadata.tables)
    for table_name, model_table in Base.metadata.tables.items():
        migration_table = migration_metadata.tables[table_name]
        assert list(migration_table.columns.keys()) == list(model_table.columns.keys())
        assert _foreign_keys(migration_metadata, table_name) == _foreign_keys(
            Base.metadata, table_name
        )
        assert _unique_columns(migration_metadata, table_name) == _unique_columns(
            Base.metadata, table_name
        )
        assert _indexes(migration_metadata, table_name) == _indexes(Base.metadata, table_name)

        for column_name, model_column in model_table.columns.items():
            migration_column = migration_table.columns[column_name]
            assert migration_column.nullable == model_column.nullable
            assert migration_column.primary_key == model_column.primary_key
            assert migration_column.type.compile(
                dialect=mysql.dialect()
            ) == model_column.type.compile(dialect=mysql.dialect())


def test_all_tables_compile_for_mysql() -> None:
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=mysql.dialect()))
        assert f"CREATE TABLE {table.name}" in ddl


def test_initial_migration_upgrade_and_downgrade_on_empty_database() -> None:
    migration = _load_initial_migration()
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        migration.op = SimpleNamespace(get_bind=lambda: connection)
        migration.upgrade()
        reflected = MetaData()
        reflected.reflect(bind=connection)
        assert set(reflected.tables) == EXPECTED_TABLES

        migration.downgrade()
        reflected_after_downgrade = MetaData()
        reflected_after_downgrade.reflect(bind=connection)
        assert not reflected_after_downgrade.tables
