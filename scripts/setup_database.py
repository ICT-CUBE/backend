"""Azure 개발·시연 환경의 DB, Hardhat 체인, NFT 백필을 한 번에 초기화합니다.

프로젝트 루트에서 실행합니다.
    .venv\\Scripts\\python.exe scripts\\setup_database.py

확인 입력을 생략하려면 `--yes`를 사용합니다.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from io import TextIOWrapper
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

import pymysql
from pydantic import BaseModel, Field, SecretStr, ValidationError
from pymysql.constants import CLIENT

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

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
DEFAULT_RESOURCE_GROUP = "hanium-rg"
DEFAULT_BACKEND_APP = "hanium"
DEFAULT_BLOCKCHAIN_APP = "hanium-blockchain"
HEALTH_TIMEOUT_SECONDS = 600


class DatabaseSettings(BaseModel):
    mysql_host: str = Field(alias="MYSQL_HOST")
    mysql_port: int = Field(alias="MYSQL_PORT")
    mysql_database: str = Field(alias="MYSQL_DATABASE")
    mysql_user: str = Field(alias="MYSQL_USER")
    mysql_password: SecretStr = Field(alias="MYSQL_PASSWORD")
    mysql_ssl_enabled: bool = Field(alias="MYSQL_SSL_ENABLED")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Azure 개발 DB와 Hardhat 체인을 초기화하고 ACTIVE 큐브 NFT를 백필합니다."
        )
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="DB 이름 확인 입력 없이 바로 초기화합니다.",
    )
    parser.add_argument(
        "--resource-group",
        default=DEFAULT_RESOURCE_GROUP,
        help=f"Azure 리소스 그룹 (기본값: {DEFAULT_RESOURCE_GROUP})",
    )
    parser.add_argument(
        "--backend-app",
        default=DEFAULT_BACKEND_APP,
        help=f"Backend App Service 이름 (기본값: {DEFAULT_BACKEND_APP})",
    )
    parser.add_argument(
        "--blockchain-app",
        default=DEFAULT_BLOCKCHAIN_APP,
        help=(
            "Blockchain App Service 이름 "
            f"(기본값: {DEFAULT_BLOCKCHAIN_APP})"
        ),
    )
    return parser.parse_args()


def run_az(*arguments: str, capture_output: bool = False) -> str:
    """로그인된 Azure CLI를 실행하고 secret을 콘솔에 출력하지 않습니다."""
    az_command = shutil.which("az")
    if az_command is None:
        raise RuntimeError("Azure CLI를 찾을 수 없습니다. az login 후 다시 실행하세요.")

    completed = subprocess.run(
        [az_command, *arguments],
        check=True,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout if capture_output else ""


def load_webapp_settings(*, resource_group: str, app_name: str) -> dict[str, str]:
    raw = run_az(
        "webapp",
        "config",
        "appsettings",
        "list",
        "--resource-group",
        resource_group,
        "--name",
        app_name,
        "--output",
        "json",
        capture_output=True,
    )
    values = json.loads(raw)
    if not isinstance(values, list):
        raise RuntimeError(f"{app_name} 환경변수 응답 형식이 올바르지 않습니다.")
    return {
        str(item["name"]): str(item["value"])
        for item in values
        if isinstance(item, dict) and "name" in item and "value" in item
    }


def parse_backend_database_settings(settings: dict[str, str]) -> DatabaseSettings:
    try:
        return DatabaseSettings.model_validate(settings)
    except ValidationError as exc:
        raise RuntimeError(
            "Backend App Service의 MySQL 환경변수가 올바르지 않습니다."
        ) from exc


def parse_blockchain_database_settings(settings: dict[str, str]) -> DatabaseSettings:
    database_url = settings.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Blockchain App Service에 DATABASE_URL이 없습니다.")

    parsed = urlsplit(database_url)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise RuntimeError("Blockchain DATABASE_URL은 MySQL URL이어야 합니다.")
    if not all((parsed.hostname, parsed.username, parsed.password, parsed.path[1:])):
        raise RuntimeError("Blockchain DATABASE_URL 형식이 올바르지 않습니다.")

    try:
        return DatabaseSettings.model_validate(
            {
                "MYSQL_HOST": parsed.hostname,
                "MYSQL_PORT": parsed.port or 3306,
                "MYSQL_DATABASE": parsed.path[1:],
                "MYSQL_USER": unquote(parsed.username or ""),
                "MYSQL_PASSWORD": unquote(parsed.password or ""),
                "MYSQL_SSL_ENABLED": settings.get(
                    "DATABASE_SSL_ENABLED", "false"
                ),
            }
        )
    except ValidationError as exc:
        raise RuntimeError(
            "Blockchain App Service의 DB 환경변수가 올바르지 않습니다."
        ) from exc


def confirm_reset(
    *,
    backend_database: str,
    blockchain_database: str,
    skip_confirmation: bool,
) -> None:
    if skip_confirmation:
        return

    print("다음 시연 환경 데이터가 모두 삭제되고 다시 생성됩니다.")
    print(f"- Backend DB: {backend_database}")
    print(f"- Blockchain DB: {blockchain_database}")
    print("- Azure 내부 Hardhat 체인 및 기존 NFT")
    confirmation = input(
        f"계속하려면 Backend DB 이름 '{backend_database}'을 입력하세요: "
    ).strip()
    if confirmation != backend_database:
        raise SystemExit("DB 이름이 일치하지 않아 초기화를 취소했습니다.")


def connect_database(settings: DatabaseSettings) -> pymysql.Connection:
    ssl_options = {"check_hostname": True} if settings.mysql_ssl_enabled else None
    return pymysql.connect(
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


def reset_backend_database(settings: DatabaseSettings) -> None:
    connection = connect_database(settings)
    try:
        for filename in SQL_FILES:
            sql_path = SQL_DIRECTORY / filename
            print(f"실행 중: {filename}")
            try:
                execute_sql_file(connection=connection, sql_path=sql_path)
            except Exception as exc:
                raise RuntimeError(f"Backend DB 초기화 실패: {filename}") from exc
            print(f"완료: {filename}")
    finally:
        connection.close()


def reset_blockchain_database(settings: DatabaseSettings) -> None:
    """Hardhat 재시작 전 Blockchain DB의 이전 체인 작업 기록을 제거합니다."""
    connection = connect_database(settings)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = %s AND table_type = 'BASE TABLE'",
                (settings.mysql_database,),
            )
            table_names = [str(row[0]) for row in cursor.fetchall()]
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            try:
                for table_name in table_names:
                    escaped_name = table_name.replace("`", "``")
                    cursor.execute(f"DROP TABLE IF EXISTS `{escaped_name}`")
            finally:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    finally:
        connection.close()


def set_webapp_state(
    *, resource_group: str, app_name: str, action: str
) -> None:
    print(f"Azure App Service {action}: {app_name}")
    run_az(
        "webapp",
        action,
        "--resource-group",
        resource_group,
        "--name",
        app_name,
        "--output",
        "none",
    )


def wait_for_endpoint(*, url: str, label: str) -> None:
    deadline = time.monotonic() + HEALTH_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=15) as response:
                body = json.loads(response.read().decode("utf-8"))
                if response.status == 200:
                    print(f"준비 완료: {label} {body}")
                    return
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            pass
        time.sleep(10)
    raise RuntimeError(f"{label}이 {HEALTH_TIMEOUT_SECONDS}초 안에 준비되지 않았습니다.")


def inject_process_environment(settings: dict[str, str]) -> None:
    for name, value in settings.items():
        os.environ[name] = value


def run_backfill() -> None:
    """Azure 설정을 사용하는 현재 프로세스에서 ACTIVE 소유권 NFT를 발행합니다."""
    from app.core.config import get_settings

    get_settings.cache_clear()
    from scripts.backfill_mint import main as backfill_main

    backfill_main()


def validate_sql_files() -> None:
    missing_files = [
        str(SQL_DIRECTORY / filename)
        for filename in SQL_FILES
        if not (SQL_DIRECTORY / filename).is_file()
    ]
    if missing_files:
        missing = "\n".join(missing_files)
        raise RuntimeError(f"SQL 파일을 찾을 수 없습니다:\n{missing}")


def main() -> None:
    args = parse_args()
    validate_sql_files()

    print("Azure App Service 환경변수를 불러옵니다.")
    backend_app_settings = load_webapp_settings(
        resource_group=args.resource_group,
        app_name=args.backend_app,
    )
    blockchain_app_settings = load_webapp_settings(
        resource_group=args.resource_group,
        app_name=args.blockchain_app,
    )
    backend_database = parse_backend_database_settings(backend_app_settings)
    blockchain_database = parse_blockchain_database_settings(
        blockchain_app_settings
    )

    confirm_reset(
        backend_database=backend_database.mysql_database,
        blockchain_database=blockchain_database.mysql_database,
        skip_confirmation=args.yes,
    )

    backend_started = True
    blockchain_started = True
    try:
        set_webapp_state(
            resource_group=args.resource_group,
            app_name=args.blockchain_app,
            action="stop",
        )
        blockchain_started = False
        set_webapp_state(
            resource_group=args.resource_group,
            app_name=args.backend_app,
            action="stop",
        )
        backend_started = False

        print(f"Backend DB 초기화: {backend_database.mysql_database}")
        reset_backend_database(backend_database)
        print(f"Blockchain DB 초기화: {blockchain_database.mysql_database}")
        reset_blockchain_database(blockchain_database)

        set_webapp_state(
            resource_group=args.resource_group,
            app_name=args.backend_app,
            action="start",
        )
        backend_started = True
        wait_for_endpoint(
            url=f"https://{args.backend_app}.azurewebsites.net/health",
            label="Backend",
        )

        set_webapp_state(
            resource_group=args.resource_group,
            app_name=args.blockchain_app,
            action="start",
        )
        blockchain_started = True
        wait_for_endpoint(
            url=f"https://{args.blockchain_app}.azurewebsites.net/ready",
            label="Blockchain Server",
        )

        print("ACTIVE 큐브 소유권 NFT 백필을 시작합니다.")
        inject_process_environment(backend_app_settings)
        run_backfill()
    finally:
        if not backend_started:
            set_webapp_state(
                resource_group=args.resource_group,
                app_name=args.backend_app,
                action="start",
            )
        if not blockchain_started:
            set_webapp_state(
                resource_group=args.resource_group,
                app_name=args.blockchain_app,
                action="start",
            )

    print("Azure 시연 환경 초기화와 NFT 백필이 완료되었습니다.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"시연 환경 초기화 실패: {exc}") from exc
