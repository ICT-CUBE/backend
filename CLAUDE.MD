# CLAUDE.MD — 구현 규칙

이 문서는 Claude가 이 저장소에서 작업할 때 지키는 규칙입니다.
**기존 코드의 형태와 구조가 항상 정답**이며, 이 문서는 그 구조를 글로 옮긴 것입니다.
새로운 패턴이 필요해 보이면 임의로 도입하지 않고 먼저 물어봅니다.

---

## 1. 프로젝트 개요

FastAPI + SQLAlchemy 2.0(ORM, sync) + MySQL 기반 백엔드입니다.

```text
app/
  main.py                     앱 생성, 예외 핸들러 등록, 헬스체크
  api/router.py               도메인 라우터를 prefix/tag와 함께 등록
  api/routes/<도메인>.py       HTTP 계층 (검증·직렬화·OpenAPI 문서)
  services/<도메인>.py         비즈니스 로직 + DB 접근
  schemas/<도메인>.py          요청/응답 Pydantic 스키마
  models/<도메인>.py           SQLAlchemy ORM 매핑
  models/enums.py             DDL CHECK 제약과 1:1로 대응하는 고정 코드값
  core/                       config, database, auth, exceptions, openapi
docs/
  erd.md                      ERD (진실의 원천 1)
  <도메인>/API_SPEC.MD         API 명세 (진실의 원천 2)
  <도메인>/BUISNESS_RULE.MD    비즈니스 룰 (진실의 원천 3)
  <도메인>/TEST_GUIDE.MD       테스트 결과 정리 (내가 작성)
scripts/sql/01-schema.sql     DDL (진실의 원천 4)
tests/test_<도메인>.py         도메인당 테스트 파일 1개
tests/conftest.py             테스트 공용 헬퍼
```

---

## 2. 작업 흐름

구현 요청을 받으면 항상 이 순서로 진행합니다.

1. `docs/<도메인>/API_SPEC.MD` 와 `docs/<도메인>/BUISNESS_RULE.MD` 를 먼저 읽습니다.
2. `docs/erd.md` 와 `scripts/sql/01-schema.sql` 로 테이블·컬럼·제약을 확인합니다.
3. `app/models/` 에 해당 ORM 매핑이 있는지 확인합니다. 없으면 DDL 기준으로 추가합니다.
4. 같은 도메인 또는 가장 비슷한 기존 도메인의 route/service/schema를 열어 형태를 그대로 따릅니다.
5. schema → service → route → router 등록 순으로 구현합니다.
6. `tests/test_<도메인>.py` 에 테스트를 추가하고 실행합니다.
7. `docs/<도메인>/TEST_GUIDE.MD` 를 갱신합니다.
8. 작업 내용을 정리해서 보고합니다. (7장 참고)

명세와 기존 코드/DDL이 충돌하면 **임의로 판단하지 않고 물어봅니다.**

---

## 3. 계층별 규칙

### 3.1 schemas (`app/schemas/<도메인>.py`)

- 모듈 docstring: `"""<한글 도메인명> 도메인 API 요청·응답 스키마."""`
- 모든 스키마는 `app.schemas.base.ApiSchema` 를 상속합니다.
  내부는 `snake_case`, JSON은 `alias_generator=to_camel` 로 자동 `camelCase` 변환됩니다.
- 네이밍: `<도메인><대상>Request` / `<도메인><대상>Response`.
  중첩 응답은 `StageListResponse` → `StageListItemResponse` 처럼 바깥/안쪽을 나눕니다.
- 응답 필드는 명세의 JSON 구조를 그대로 반영합니다. 명세에 없는 필드를 추가하지 않습니다.
- Nullable은 `str | None` 처럼 표기합니다.
- 특정 API에서만 허용되는 부분집합 enum은 `app/schemas/` 안에 `StrEnum` 으로 따로 둡니다
  (예: `StageSessionEndStatus`). DB 전체 코드값은 `app/models/enums.py` 를 임포트해 씁니다.
- 공통 오류 응답은 `app.schemas.common.ErrorResponse` 를 씁니다.

### 3.2 services (`app/services/<도메인>.py`)

- 모듈 docstring: 그 파일이 담당하는 로직을 한 줄로 씁니다.
- 함수 시그니처는 **키워드 전용**입니다: `def xxx(*, db: Session, current_user_id: int, ...)`.
- 함수마다 한 줄 한글 docstring을 답니다.
- 조회는 `db.scalar(select(...))` / `db.scalars(select(...))` 를 씁니다.
  동시성 보호가 필요한 행은 `.limit(1).with_for_update()` 를 붙입니다.
- 오류는 `ApiError(status_code=, code=, message=)` 를 raise 합니다.
  code/message는 **명세에 적힌 문자열을 글자 그대로** 사용합니다.
- 쓰기 트랜잭션은 `db.add()` → (id가 필요하면 `db.flush()`) → `db.commit()`.
  기존 코드처럼 `try/except: db.rollback(); raise` 로 감쌉니다.
- 시각 저장은 **KST naive datetime**:
  `datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)`.
  `KOREA_TIMEZONE = timezone(timedelta(hours=9))` 는 서비스 모듈 상단에 둡니다(기존 관례).
- 외부 저장소(Azure Blob)는 `app/services/blob_storage.py` 의 함수를 통해서만 접근하고,
  실패는 공통 500(`INTERNAL_SERVER_ERROR`)으로 변환합니다.
- 라우터는 서비스만 호출하고, 서비스는 라우터를 모릅니다. 서비스끼리의 임의 호출도 만들지 않습니다.

### 3.3 routes (`app/api/routes/<도메인>.py`)

- 모듈 docstring: `"""<한글 도메인명> 도메인 API 라우터."""`
- `router = APIRouter()` 를 선언하고, prefix가 다른 엔드포인트 묶음이 필요하면
  `album.py` 처럼 `album_router`, `track_session_router` 같은 추가 라우터를 같은 파일에 둡니다.
- 데코레이터에 항상 채우는 것:
  `response_model`(204는 생략), `status_code`(200 외), `summary`, `description`,
  `responses`(발생 가능한 모든 오류를 `ErrorResponse` + `example`/`examples` 로 문서화).
- 함수 docstring은 `"""GET /api/v1/..."""` 처럼 **실제 메서드와 전체 경로 한 줄**입니다.
- 의존성 주입 순서: path/query/body → `db: Annotated[Session, Depends(get_db)]`
  → `current_user_id: Annotated[int, Depends(get_current_user_id)]`.
- Path/Query/Form의 외부 이름이 camelCase면 `alias="trackId"` 를 붙입니다.
  자연스러운 범위 제약(`ge=1` 등)은 기존 관례대로 붙입니다.
- 204 응답은 `-> Response` 로 선언하고 `return Response(status_code=status.HTTP_204_NO_CONTENT)`.
- 새 라우터는 `app/api/router.py` 에 `prefix`/`tags` 와 함께 등록합니다.

### 3.4 models (`app/models/<도메인>.py`)

- DDL(`scripts/sql/01-schema.sql`)이 기준입니다. 컬럼명·타입·nullable을 그대로 반영합니다.
- enum 컬럼은 기존 패턴 유지:
  `Enum(XxxEnum, values_callable=enum_values, native_enum=False, create_constraint=False)`.
- 새 모델을 만들면 `app/models/__init__.py` 의 import와 `__all__` 에 **알파벳 순**으로 추가합니다.
- 순환 임포트를 피하기 위해 관계 타입은 `TYPE_CHECKING` 블록에서 임포트하고 문자열로 씁니다.
- 스키마 변경이 필요하면 코드만 고치지 않고 ERD/DDL과 함께 처리할지 먼저 확인합니다.

### 3.5 오류 코드

- 공통: `INVALID_REQUEST`(400), `INTERNAL_SERVER_ERROR`(500) — `app/core/exceptions.py` 가 처리.
- 도메인 오류는 명세에 적힌 코드를 씁니다. 명세에 없는 코드를 만들지 않습니다.
- 자주 쓰이는 기존 코드: `CUBE_NOT_FOUND`, `CUBE_OWNERSHIP_NOT_FOUND`, `CUBE_NOT_REGISTRABLE`,
  `TRACK_NOT_FOUND`, `TRACK_SESSION_NOT_FOUND`, `TRACK_SESSION_ALREADY_ENDED`,
  `STAGE_NOT_FOUND`, `STAGE_SESSION_NOT_FOUND`, `STAGE_SESSION_ALREADY_ENDED`.
  같은 의미의 오류는 새 코드를 만들지 말고 기존 코드를 재사용합니다.

### 3.6 코드 스타일

- 주석/문서/docstring은 **한글**, 식별자는 영어 `snake_case`(클래스는 `PascalCase`).
- ruff 0.16 기본 설정 기준, 한 줄 88자.
- 타입 힌트는 모든 공개 함수에 붙입니다.
- 주석은 "왜"를 설명할 때만 답니다. 기존 파일의 주석 밀도를 넘지 않습니다.

---

## 4. 테스트 규칙

### 4.1 파일 구성

- **도메인당 파일 1개**: `tests/test_<도메인>.py`. (기존 구조 유지)
- 한 파일 안에서 API 단위로 섹션을 나눕니다.
  API마다 `request_<동작>()` 요청 헬퍼를 하나 두고, 그 아래에 해당 API 테스트들을 모읍니다.
- 공용 보일러플레이트는 `tests/conftest.py` 의 `api_client(db)` 컨텍스트 매니저를 씁니다.
  `tests/test_*.py` 전부가 이 방식이므로 `override_get_db` 를 새로 만들지 않습니다.
  500 응답을 확인할 때만 `api_client(db, raise_server_exceptions=False)` 를 씁니다.
  (예외: `tests/test_exceptions.py` 는 `create_app()` 으로 별도 앱을 만들고 DB를 쓰지 않아
  `TestClient` 를 직접 사용합니다.)

```python
from tests.conftest import api_client


def request_cube_verification(db, *, body=None):
    with api_client(db) as client:
        return client.post("/api/v1/cubes/verification", json=body or {...})
```

### 4.2 테스트 방식

- DB는 `Mock(spec=Session)` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
  실제 MySQL에 붙지 않습니다. `spec` 을 붙여야 `Session` 에 없는 메서드 호출을 오타로 잡아냅니다.
  (Session이 아닌 조회 결과 객체를 흉내 낼 때는 `spec` 없는 `Mock()` 을 씁니다.)
- 요청 헬퍼의 파라미터 타입 힌트는 기존대로 `db: Mock` 입니다.
- 조회 순서대로 `db.scalar.side_effect = [...]` 를 지정합니다.
- 저장 검증은 `db.add.side_effect` 로 수집한 객체를 확인하고,
  `db.commit.assert_called_once()` / `db.commit.assert_not_called()` 로 트랜잭션을 확인합니다.
- 외부 의존성은 `patch("app.services.<도메인>.<함수>")` 로 서비스 모듈이 참조하는 이름을 패치합니다.
- 응답은 `response.status_code` 와 `response.json()` **전체**를 비교합니다.
- 공통 500 응답을 검증할 때는 `patch("app.main.get_settings", return_value=Settings(debug=False))`
  로 앱을 만듭니다. `debug=true` 에서는 Starlette이 공통 핸들러 대신 HTML 트레이스백을 반환합니다.

### 4.3 API 하나당 반드시 만드는 케이스

| 분류 | 내용 |
|---|---|
| 정상 | 명세의 대표 성공 경로. 상태코드 + 응답 JSON 전체 + DB 부수효과(add/commit) 검증 |
| 정상 변형 | enum 값별 분기, 옵션 파라미터 유무, 빈 목록 등 성공이지만 결과가 달라지는 경로 |
| 오류 | 명세에 적힌 모든 오류 코드마다 1개씩 (404 / 409 / 400 ...) |
| 요청 검증 | 필수 필드 누락, 타입 불일치, 허용되지 않는 enum 값 → 400 `INVALID_REQUEST` |
| 경계값 | 숫자·문자열 제약의 최소/최대 유효값과 그 바로 바깥값 (`ge=1` 이면 1은 통과, 0은 400) |
| 소유권 | 다른 사용자의 리소스 접근 시 404 (존재를 노출하지 않음) |
| 상태 전이 | 이미 종료/이미 처리된 리소스 재요청 시 409 |
| 예외 | commit이 실패하면 rollback 되는지 (`raise_server_exceptions=False` 로 500 확인) |
| 문서 | `test_<동작>_swagger_contract` — OpenAPI의 응답 코드 집합이 라우터 선언과 일치하는지 |

- Mock DB로는 구분할 수 없는 조건(예: "없는 리소스" vs "남의 리소스")은 억지로 나누지 말고,
  `db.scalar.call_args` 로 꺼낸 select 문을 `literal_binds` 로 컴파일해 WHERE 절 조건을 검증합니다.

- 테스트 이름: `test_<동작>_<기대결과>_when_<조건>` 형태.
  예) `test_create_cube_verification_returns_404_when_cube_not_found`
- 해당 없는 분류는 억지로 만들지 말고 TEST_GUIDE에 "해당 없음"으로 남깁니다.

### 4.4 실행

```powershell
.venv\Scripts\python.exe -m pytest -q
```

새 코드는 반드시 전부 통과시키고, 통과하지 못하면 그 사실과 출력을 그대로 보고합니다.

---

## 5. TEST_GUIDE 작성 규칙

`docs/<도메인>/TEST_GUIDE.MD` 에 API별로 아래 형식으로 정리합니다.

```markdown
# <도메인> 테스트 가이드

테스트 파일: `tests/test_<도메인>.py`
실행: `.venv\Scripts\python.exe -m pytest tests/test_<도메인>.py -q`
최종 실행 결과: N passed (YYYY-MM-DD)

---

## <API 이름> — `<METHOD> /api/v1/...`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_... | ... | 201 + `{...}` | PASS |
| 오류 | test_... | 큐브 없음 | 404 CUBE_NOT_FOUND | PASS |
| 경계값 | test_... | page=0 | 200 | PASS |

### 검증하지 않은 항목
- (검증 대상에서 제외한 것과 그 이유)
```

---

## 6. 허용된 정리 작업

동작을 바꾸지 않는 선에서 아래는 별도 허락 없이 해도 됩니다. **단, 반드시 보고합니다.**

- 사용되지 않는 import / 변수 / 함수 / 스키마 제거
- 중복 코드의 기존 헬퍼로의 치환
- 오타, 잘못된 docstring, 잘못된 타입 힌트 수정
- 포맷팅 정리

아래는 **하지 않습니다.** 필요해 보이면 먼저 물어봅니다.

- API 동작·응답 형태·오류 코드 변경
- 계층 구조, 파일 배치, 네이밍 컨벤션 변경
- DDL / ERD / 모델 스키마 변경
- 라이브러리 추가, 설정(`config.py`, `.env`) 변경
- 요청받지 않은 기능 추가

---

## 7. 보고 규칙

작업이 끝나면 항상 아래를 정리해서 보고합니다.

1. **구현한 것** — 파일별로 무엇을 추가/수정했는지
2. **판단한 것** — 명세가 모호해서 내가 정한 부분과 그 근거
3. **테스트** — 추가한 케이스 수, 실행 결과(통과/실패 수), 실패가 있으면 원인
4. **정리한 것** — 6장에서 허용된 범위로 손댄 죽은 코드/중복 (없으면 "없음")
5. **확인 필요** — 물어봐야 할 것, 남은 이슈

---

## 8. 알려진 이슈

- 없음. (2026-08-28 기준 `pytest -q` 전체 통과)
