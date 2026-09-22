"""Azure MySQL의 거래 데이터를 구매 확정 시연 직전 상태로 준비합니다.

프로젝트 루트에서 실행합니다.
    .venv\\Scripts\\python.exe scripts\\setup_database.py

기본 대상은 목데이터의 배송 완료 거래 1번입니다. 다른 거래를 준비하려면
`--trade-id`를 사용하고, 확인 입력을 생략하려면 `--yes`를 사용합니다.

블록체인의 실제 NFT 소유권은 바꾸지 않습니다. 대신 해당 거래의 NFT 이전을
확정된 작업으로 미리 기록해 두어, 구매 확정 API가 온체인 이전 없이
인증서 발급과 거래 완료까지 진행하게 합니다.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import TextIOWrapper
from pathlib import Path
from uuid import uuid4

import pymysql
from pydantic import BaseModel, Field, SecretStr, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

if isinstance(sys.stdout, TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
if isinstance(sys.stderr, TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")


DEFAULT_RESOURCE_GROUP = "hanium-rg"
DEFAULT_BACKEND_APP = "hanium"
DEFAULT_TRADE_ID = 1
KOREA_TIMEZONE = timezone(timedelta(hours=9))
# 실제 온체인 트랜잭션이 없으므로 시연용임을 알 수 있는 고정 해시를 기록합니다.
DEMO_TX_HASH = "0x" + "0" * 63 + "1"


class DatabaseSettings(BaseModel):
    mysql_host: str = Field(alias="MYSQL_HOST")
    mysql_port: int = Field(alias="MYSQL_PORT")
    mysql_database: str = Field(alias="MYSQL_DATABASE")
    mysql_user: str = Field(alias="MYSQL_USER")
    mysql_password: SecretStr = Field(alias="MYSQL_PASSWORD")
    mysql_ssl_enabled: bool = Field(alias="MYSQL_SSL_ENABLED")


@dataclass(frozen=True)
class DemoTrade:
    trade_id: int
    listing_id: int
    cube_id: int
    serial_number: str
    token_id: int
    seller_user_id: int
    seller_nickname: str | None
    seller_ownership_id: int
    buyer_user_id: int
    buyer_nickname: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Azure MySQL의 거래를 구매 확정 시연 직전 상태로 준비합니다."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="대상 거래 확인 입력 없이 바로 준비합니다.",
    )
    parser.add_argument(
        "--trade-id",
        type=int,
        default=DEFAULT_TRADE_ID,
        help=f"준비할 거래 id (기본값: {DEFAULT_TRADE_ID})",
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
    args = parser.parse_args()
    if args.trade_id < 1:
        parser.error("--trade-id는 1 이상의 정수여야 합니다.")
    return args


def run_az(*arguments: str, capture_output: bool = False) -> str:
    """로그인된 Azure CLI를 실행하고 secret을 콘솔에 출력하지 않습니다."""
    az_command = shutil.which("az")
    if az_command is None:
        raise RuntimeError("Azure CLI를 찾을 수 없습니다. az login 후 다시 실행하세요.")

    completed = subprocess.run(
        [az_command, *arguments],
        check=False,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        # stdout에는 secret이 담길 수 있어 stderr만 오류 메시지로 보여줍니다.
        detail = (completed.stderr or "").strip() if capture_output else ""
        raise RuntimeError(
            f"Azure CLI 실행에 실패했습니다: {detail or 'az 출력을 확인하세요.'}"
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


def connect_database(settings: DatabaseSettings) -> pymysql.Connection:
    ssl_options = {"check_hostname": True} if settings.mysql_ssl_enabled else None
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password.get_secret_value(),
        database=settings.mysql_database,
        charset="utf8mb4",
        autocommit=False,
        ssl=ssl_options,
    )


def to_demo_token_id(serial_number: str) -> int:
    """구매 확정 API와 같은 규칙으로 시리얼 번호를 토큰 번호로 변환합니다."""
    from app.blockchain.errors import BlockchainError
    from app.blockchain.mint import to_token_id

    try:
        return to_token_id(serial_number)
    except BlockchainError as exc:
        raise RuntimeError(exc.message) from exc


def load_demo_trade(
    *, settings: DatabaseSettings, trade_id: int
) -> DemoTrade:
    """시연 거래와 판매자 소유권을 조회하고 필수 데이터를 검증합니다."""
    connection = connect_database(settings)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT trade.id, sell_listing.id, cube.id, cube.serial_number, "
                "sell_listing.user_id, seller.nickname, trade.buyer_user_id, "
                "buyer.nickname "
                "FROM trade "
                "JOIN sell_listing ON sell_listing.id = trade.sell_listing_id "
                "JOIN cube ON cube.id = sell_listing.cube_id "
                "JOIN user AS seller ON seller.id = sell_listing.user_id "
                "JOIN user AS buyer ON buyer.id = trade.buyer_user_id "
                "WHERE trade.id = %s AND seller.status = 'ACTIVE' "
                "AND buyer.status = 'ACTIVE' AND cube.deleted_at IS NULL "
                "AND sell_listing.deleted_at IS NULL",
                (trade_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError(
                    f"시연 가능한 거래를 찾을 수 없습니다: trade_id={trade_id}"
                )

            (
                loaded_trade_id,
                listing_id,
                cube_id,
                serial_number,
                seller_user_id,
                seller_nickname,
                buyer_user_id,
                buyer_nickname,
            ) = row
            if seller_user_id == buyer_user_id:
                raise RuntimeError("판매자와 구매자가 같은 거래는 시연할 수 없습니다.")

            cursor.execute(
                "SELECT id FROM cube_ownership "
                "WHERE cube_id = %s AND user_id = %s "
                "ORDER BY (ownership_status = 'ACTIVE') DESC, id DESC LIMIT 1",
                (cube_id, seller_user_id),
            )
            ownership_row = cursor.fetchone()
            if ownership_row is None:
                raise RuntimeError(
                    "판매자의 큐브 소유권을 찾을 수 없습니다: "
                    f"cube_id={cube_id}, seller_user_id={seller_user_id}"
                )
    finally:
        connection.close()

    return DemoTrade(
        trade_id=int(loaded_trade_id),
        listing_id=int(listing_id),
        cube_id=int(cube_id),
        serial_number=str(serial_number),
        token_id=to_demo_token_id(str(serial_number)),
        seller_user_id=int(seller_user_id),
        seller_nickname=seller_nickname,
        seller_ownership_id=int(ownership_row[0]),
        buyer_user_id=int(buyer_user_id),
        buyer_nickname=buyer_nickname,
    )


def confirm_prepare(*, target: DemoTrade, skip_confirmation: bool) -> None:
    if skip_confirmation:
        return

    print("다음 거래를 구매 확정 시연 직전 상태로 되돌립니다.")
    print(f"- 거래: {target.trade_id}")
    print(
        f"- 큐브: {target.serial_number} "
        f"(id={target.cube_id}, token_id={target.token_id})"
    )
    print(
        f"- 판매자: {target.seller_nickname or '-'} "
        f"(id={target.seller_user_id})"
    )
    print(
        f"- 구매자: {target.buyer_nickname or '-'} "
        f"(id={target.buyer_user_id})"
    )
    print("- 기존 디지털 인증서와 해당 거래의 블록체인 작업 기록은 삭제됩니다.")
    confirmation = input(
        f"계속하려면 거래 id '{target.trade_id}'을 입력하세요: "
    ).strip()
    if confirmation != str(target.trade_id):
        raise SystemExit("거래 id가 일치하지 않아 준비를 취소했습니다.")


def reset_demo_trade_database(
    *, settings: DatabaseSettings, target: DemoTrade
) -> None:
    """대상 거래에 관련된 행만 구매 확정 직전 상태로 복원합니다."""
    now = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None, microsecond=0)
    connection = connect_database(settings)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM trade WHERE id = %s FOR UPDATE",
                (target.trade_id,),
            )
            if cursor.fetchone() is None:
                raise RuntimeError(
                    f"준비 중 거래가 사라졌습니다: trade_id={target.trade_id}"
                )

            cursor.execute(
                "DELETE FROM digital_certificate WHERE trade_id = %s",
                (target.trade_id,),
            )
            cursor.execute(
                "DELETE FROM blockchain_operation WHERE trade_id = %s",
                (target.trade_id,),
            )
            # 확정된 이전 기록이 있으면 구매 확정 API가 온체인 이전을 건너뜁니다.
            cursor.execute(
                "INSERT INTO blockchain_operation "
                "(operation_type, status, token_id, trade_id, idempotency_key, "
                "tx_hash) VALUES ('TRANSFER', 'CONFIRMED', %s, %s, %s, %s)",
                (target.token_id, target.trade_id, str(uuid4()), DEMO_TX_HASH),
            )
            cursor.execute(
                "UPDATE cube_ownership SET ownership_status = 'TRANSFERRED', "
                "transferred_at = %s, is_last_accessed = FALSE "
                "WHERE cube_id = %s AND id <> %s "
                "AND ownership_status = 'ACTIVE'",
                (now, target.cube_id, target.seller_ownership_id),
            )
            cursor.execute(
                "UPDATE cube_ownership SET ownership_status = 'ACTIVE', "
                "transferred_at = NULL WHERE id = %s",
                (target.seller_ownership_id,),
            )
            cursor.execute(
                "UPDATE cube SET status = 'TRADE_PENDING' WHERE id = %s",
                (target.cube_id,),
            )
            cursor.execute(
                "UPDATE sell_listing SET status = 'SOLD' WHERE id = %s",
                (target.listing_id,),
            )
            cursor.execute(
                "UPDATE trade SET paid_time = %s, sent_time = %s, "
                "shipped_time = %s, delivered_time = %s, "
                "completed_time = NULL, status = 'DELIVERED' WHERE id = %s",
                (
                    now - timedelta(days=3),
                    now - timedelta(days=2),
                    now - timedelta(days=1),
                    now,
                    target.trade_id,
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> None:
    args = parse_args()

    print("Azure Backend App Service 환경변수를 불러옵니다.")
    backend_app_settings = load_webapp_settings(
        resource_group=args.resource_group,
        app_name=args.backend_app,
    )
    backend_database = parse_backend_database_settings(backend_app_settings)
    target = load_demo_trade(
        settings=backend_database,
        trade_id=args.trade_id,
    )
    confirm_prepare(target=target, skip_confirmation=args.yes)
    reset_demo_trade_database(settings=backend_database, target=target)

    print("구매 확정 시연 준비가 완료되었습니다.")
    print(
        f"구매자 id={target.buyer_user_id}로 로그인한 뒤 "
        f"PATCH /api/v1/users/me/trades/{target.trade_id}/complete 를 호출하세요."
    )


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"구매 확정 시연 준비 실패: {exc}") from exc
