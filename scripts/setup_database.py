"""네 개의 SQL 파일을 순서대로 실행해 MySQL 데이터베이스를 초기화합니다."""

from __future__ import annotations

import argparse
import sys
from io import TextIOWrapper
from pathlib import Path

import pymysql
from pydantic import BaseModel, Field, SecretStr, ValidationError
from pymysql.constants import CLIENT

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if isinstance(sys.stdout, TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
if isinstance(sys.stderr, TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")


SQL_FILES = (
    "01-schema.sql",
    "02-data-mock.sql",
    "03-track-lyrics.sql",
    "04-album-image.sql",
)
SQL_DIRECTORY = PROJECT_ROOT / "scripts" / "sql"
AZURE_ENV_FILE = PROJECT_ROOT / ".env.azure"


class AzureDatabaseSettings(BaseModel):
    mysql_host: str = Field(alias="MYSQL_HOST")
    mysql_port: int = Field(alias="MYSQL_PORT")
    mysql_database: str = Field(alias="MYSQL_DATABASE")
    mysql_user: str = Field(alias="MYSQL_USER")
    mysql_password: SecretStr = Field(alias="MYSQL_PASSWORD")
    mysql_ssl_enabled: bool = Field(alias="MYSQL_SSL_ENABLED")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=".env.azure의 MySQL DB를 삭제 후 목데이터로 초기화합니다."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="DB 이름 확인 입력 없이 바로 초기화합니다.",
    )
    return parser.parse_args()


def load_database_settings(env_path: Path) -> AzureDatabaseSettings:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        env_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"{env_path.name}:{line_number} 형식이 올바르지 않습니다.")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value

    return AzureDatabaseSettings.model_validate(values)


def confirm_reset(*, database: str, skip_confirmation: bool) -> None:
    if skip_confirmation:
        return

    print("기존 테이블과 데이터가 모두 삭제됩니다.")
    confirmation = input(f"계속하려면 DB 이름 '{database}'을 입력하세요: ").strip()
    if confirmation != database:
        raise SystemExit("DB 이름이 일치하지 않아 초기화를 취소했습니다.")


def execute_sql_file(
    *,
    connection: pymysql.Connection,
    sql_path: Path,
) -> None:
    sql = sql_path.read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        cursor.execute(sql)
        while cursor.nextset():
            pass


def main() -> None:
    args = parse_args()

    if not AZURE_ENV_FILE.is_file():
        raise SystemExit(f"Azure 환경변수 파일을 찾을 수 없습니다: {AZURE_ENV_FILE}")
    try:
        settings = load_database_settings(AZURE_ENV_FILE)
    except (OSError, ValueError, ValidationError) as exc:
        raise SystemExit(f"Azure 환경변수 파일을 읽을 수 없습니다:\n{exc}") from exc

    missing_files = [
        str(SQL_DIRECTORY / filename)
        for filename in SQL_FILES
        if not (SQL_DIRECTORY / filename).is_file()
    ]
    if missing_files:
        missing = "\n".join(missing_files)
        raise SystemExit(f"SQL 파일을 찾을 수 없습니다:\n{missing}")

    print(f"대상 호스트: {settings.mysql_host}:{settings.mysql_port}")
    print(f"대상 DB: {settings.mysql_database}")
    print(f"접속 사용자: {settings.mysql_user}")
    confirm_reset(
        database=settings.mysql_database,
        skip_confirmation=args.yes,
    )

    ssl_options = {"check_hostname": True} if settings.mysql_ssl_enabled else None
    connection = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password.get_secret_value(),
        database=settings.mysql_database,
        charset="utf8mb4",
        autocommit=True,
        ssl=ssl_options,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )

    try:
        for filename in SQL_FILES:
            sql_path = SQL_DIRECTORY / filename
            print(f"실행 중: {filename}")
            try:
                execute_sql_file(connection=connection, sql_path=sql_path)
            except Exception as exc:
                raise SystemExit(f"DB 초기화 실패: {filename}\n{exc}") from exc
            print(f"완료: {filename}")
    finally:
        connection.close()

    print("DB 초기화가 완료되었습니다.")


if __name__ == "__main__":
    main()
