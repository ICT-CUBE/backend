"""개발·데모 환경에서 기존 큐브 소유권의 NFT를 백필 발행하는 명령입니다.

서버 기동과 무관하게 수동으로만 실행합니다.

실행 (프로젝트 루트에서):
    .venv\\Scripts\\python.exe scripts/backfill_mint.py

호스트에서 실행할 때는 컨테이너 이름 대신 로컬 주소로 DB에 붙어야 합니다.
    MYSQL_HOST=localhost .venv\\Scripts\\python.exe scripts/backfill_mint.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.services.blockchain.backfill import backfill_mint


def main() -> None:
    db = SessionLocal()
    try:
        results = backfill_mint(db=db)
    finally:
        db.close()

    for result in results:
        print(
            f"{result['status']:<15}"
            f" cube_id={result['cube_id']:<3}"
            f" serial={result['serial_number']:<10}"
            f" token_id={result['token_id']}"
            f" {result['detail']}"
        )

    summary: dict[str, int] = {}
    for result in results:
        summary[result["status"]] = summary.get(result["status"], 0) + 1
    print("---")
    print(f"총 {len(results)}건: " + ", ".join(f"{k} {v}" for k, v in summary.items()))


if __name__ == "__main__":
    main()
