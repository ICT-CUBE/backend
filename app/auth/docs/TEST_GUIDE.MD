# 인증 도메인 테스트 가이드

테스트 파일: `app/auth/tests/test_auth.py`
실행: `.venv\Scripts\python.exe -m pytest app/auth/tests/test_auth.py -q`
최종 실행 결과: 50 passed (2026-09-15)

DB는 `Mock(spec=Session)` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
실제 MySQL에는 접속하지 않습니다.

회원가입은 `db.scalar` 로 이메일 중복을 확인한 뒤 `db.add` → `db.flush` → `db.add` →
`db.commit` 순서로 저장하므로, `set_signup_results()` 헬퍼가 중복 조회 결과를 지정하고
저장된 ORM 객체를 순서대로 모읍니다. `db.flush` 시점에 사용자 id를 11로 부여합니다.
Argon2id 해시와 JWT는 모킹하지 않고 실제 라이브러리로 생성한 값을 검증합니다.

---

## 이메일 회원가입 — `POST /api/v1/auth/signup`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_signup_creates_user_with_default_setting_and_token | 유효한 회원가입 요청 | 201 + `user.id`·`auth` 4개 필드, `login_provider=EMAIL`·`status=ACTIVE`·`chat_violation_count=0`·`provider_user_id=None` 저장, flush·commit 1회 | PASS |
| 정상 | test_signup_creates_user_setting_with_all_notifications_enabled | 유효한 회원가입 요청 | `user_setting` 7개 알림 플래그가 모두 `true`, `user_id=11` | PASS |
| 정상 | test_signup_issues_access_token_signed_with_configured_secret | 유효한 회원가입 요청 | 설정된 비밀키·HS256으로 검증되는 JWT, `sub="11"`, `exp-iat=31536000`, `expiresAt`가 `exp`의 KST naive 값 | PASS |
| 정책 | test_signup_stores_argon2id_hash_instead_of_raw_password | 유효한 회원가입 요청 | `password_hash` 가 `$argon2id$` 로 시작, 원문이 해시·응답에 없음 | PASS |
| 정상 변형 | test_signup_normalizes_email_before_saving | `  User@Example.COM  ` | 공백 제거·소문자로 저장, 중복 조회 SQL도 정규화된 값 사용 | PASS |
| 정상 변형 | test_signup_strips_nickname_before_saving | 앞뒤 공백 포함 닉네임 | 공백 제거한 값으로 저장 | PASS |
| 정상 변형 | test_signup_builds_profile_image_url_from_character_code | `profile_003` | `.../profile_image/profile_003.png` 저장 | PASS |
| 경계값 | test_signup_allows_minimum_password_and_nickname_length | 비밀번호 8자, 닉네임 1자 | 201 | PASS |
| 경계값 | test_signup_allows_maximum_password_and_nickname_length | 비밀번호 64자, 닉네임 20자 | 201 | PASS |
| 경계값 | test_signup_returns_400_when_password_is_too_short | 비밀번호 7자 | 400 INVALID_REQUEST, 저장 없음 | PASS |
| 경계값 | test_signup_returns_400_when_password_is_too_long | 비밀번호 65자 | 400 INVALID_REQUEST, 저장 없음 | PASS |
| 경계값 | test_signup_returns_400_when_nickname_is_too_long | 닉네임 21자 | 400 INVALID_REQUEST, 저장 없음 | PASS |
| 경계값 | test_signup_returns_400_when_email_exceeds_max_length | 이메일 262자 | 400 INVALID_REQUEST, 저장 없음 | PASS |
| 요청 검증 | test_signup_returns_400_when_nickname_is_blank | 닉네임이 공백뿐 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_signup_returns_400_for_invalid_email_format | `user-example.com` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_signup_returns_400_for_unsupported_profile_character_code | `profile_009` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_signup_returns_400_when_required_field_is_missing | `profileCharacterCode` 누락 | 400 INVALID_REQUEST | PASS |
| 오류 | test_signup_returns_409_when_email_is_already_used | 같은 이메일 사용자 존재 | 409 EMAIL_ALREADY_EXISTS, 저장·commit 없음 | PASS |
| 오류 | test_signup_returns_409_when_unique_constraint_is_violated | commit에서 `IntegrityError` | 409 EMAIL_ALREADY_EXISTS, rollback 1회 | PASS |
| 예외 | test_signup_rolls_back_when_commit_fails | commit이 예외 발생 | 500 + rollback 1회 | PASS |
| 문서 | test_signup_swagger_contract | OpenAPI 스키마 | 응답 코드 `{201, 400, 409}`, 요청 Body `{email, password, nickname, profileCharacterCode}`, tag `auth` | PASS |

### 검증하지 않은 항목

- **`uk_user_email` UNIQUE 제약의 실제 동작**은 Mock DB로 재현할 수 없어, `IntegrityError` 가
  409로 변환되는지만 확인했습니다.
- **`created_at`·`updated_at`** 은 DB 기본값이라 검증 대상에서 제외했습니다.
- **같은 비밀번호가 사용자마다 다른 해시가 되는 것**(무작위 Salt)은 Argon2id 라이브러리의
  동작이라 별도 테스트를 만들지 않았고, 해시 형식만 확인했습니다.
- **목데이터 사용자 로그인**은 실제 DB가 필요해 테스트하지 않습니다.
  `scripts/sql/02-data-mock.sql` 의 `password_hash` 는 `12345678` 의 Argon2id 해시입니다.

---

## 이메일 로그인 — `POST /api/v1/auth/login/email`

`db.scalar` 로 로그인 가능한 사용자를 한 번 조회합니다. `login_user()` 헬퍼가 실제
Argon2id 해시를 가진 사용자를 만들어, 비밀번호 검증도 모킹 없이 라이브러리로 수행합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_login_returns_user_id_and_new_access_token | 이메일·비밀번호 일치 | 200 + `user.id`, `Bearer`, `expiresIn=31536000`, `sub` 가 사용자 id, `expiresAt` 가 `exp` 의 KST naive 값 | PASS |
| 정책 | test_login_does_not_change_stored_data | 로그인 성공 | `db.add`·`db.commit` 호출 없음 | PASS |
| 정상 변형 | test_login_normalizes_email_before_lookup | `  User@Example.COM  ` | 조회 SQL이 정규화된 이메일 사용 | PASS |
| 정책 | test_login_queries_only_active_email_user_with_password | 조회 SQL 검증 | `login_provider='EMAIL'`, `password_hash IS NOT NULL`, `status='ACTIVE'`, `deleted_at IS NULL` | PASS |
| 오류 | test_login_returns_401_when_user_is_not_found | 조회 결과 없음 | 401 INVALID_CREDENTIALS | PASS |
| 오류 | test_login_returns_401_when_password_does_not_match | 비밀번호 불일치 | 401 INVALID_CREDENTIALS (같은 코드·메시지) | PASS |
| 정상 변형 | test_login_returns_401_for_empty_password_without_request_error | 비밀번호 빈 문자열 | 400이 아니라 401 INVALID_CREDENTIALS | PASS |
| 정상 변형 | test_login_allows_password_shorter_than_signup_minimum | 저장된 비밀번호 `1234` | 200 (회원가입 최소 길이 규칙 미적용) | PASS |
| 요청 검증 | test_login_returns_400_when_required_field_is_missing | `password` 누락 | 400 INVALID_REQUEST, 조회 없음 | PASS |
| 요청 검증 | test_login_returns_400_for_invalid_email_format | `user-example.com` | 400 INVALID_REQUEST, 조회 없음 | PASS |
| 경계값 | test_login_returns_400_when_email_exceeds_max_length | 이메일 262자 | 400 INVALID_REQUEST, 조회 없음 | PASS |
| 예외 | test_login_returns_500_when_stored_hash_is_broken | `password_hash` 가 Argon2id 형식이 아님 | 공통 500 | PASS |
| 문서 | test_login_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 400, 401}`, 요청 Body `{email, password}`, 인증 의존성 없음 | PASS |

### 검증하지 않은 항목

- **탈퇴·정지·소프트 삭제 사용자와 소셜 계정**은 Mock DB로 구분할 수 없어 모두 같은 401로
  처리되는 것만 확인하고, 조회 조건은 생성된 SQL로 검증했습니다.
- **`auth_session`·Refresh Token 미생성**은 서비스가 이들을 만들지 않으므로 `db.add` 미호출로
  대신 확인했습니다.

---

## Access Token 인증 의존성 — `Authorization: Bearer {accessToken}`

인증 자체를 검증하는 테스트는 `api_client(db, authenticate=False)` 로 의존성 오버라이드를
끄고, `db.execute` 만 사용하는 `GET /api/v1/users/me/sellable-cubes` 를 호출합니다.
`issue_token()` 헬퍼가 만료·비밀키·`sub` 를 바꿔 가며 토큰을 만듭니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_authentication_passes_user_id_from_token_to_service | `sub="7"` 유효 토큰 + ACTIVE 사용자 | 200, 서비스 쿼리가 `cube_ownership.user_id = 7` 사용 | PASS |
| 정책 | test_authentication_queries_only_active_user | 유효 토큰 | 사용자 조회 SQL이 `id`, `status='ACTIVE'`, `deleted_at IS NULL` 조건 사용 | PASS |
| 오류 | test_authentication_returns_401_without_authorization_header | 헤더 없음 | 401 INVALID_ACCESS_TOKEN, DB 조회 없음 | PASS |
| 오류 | test_authentication_returns_401_for_non_bearer_scheme | `Basic abcdef` | 401 INVALID_ACCESS_TOKEN | PASS |
| 오류 | test_authentication_returns_401_for_malformed_token | `Bearer not.a.jwt` | 401 INVALID_ACCESS_TOKEN | PASS |
| 오류 | test_authentication_returns_401_for_token_signed_with_other_secret | 다른 비밀키 서명 | 401 INVALID_ACCESS_TOKEN | PASS |
| 오류 | test_authentication_returns_401_for_expired_token | `exp` 가 과거 | 401 INVALID_ACCESS_TOKEN | PASS |
| 오류 | test_authentication_returns_401_when_subject_is_missing | `sub` 없음 | 401 INVALID_ACCESS_TOKEN | PASS |
| 오류 | test_authentication_returns_401_when_subject_is_not_a_number | `sub="abc"` | 401 INVALID_ACCESS_TOKEN | PASS |
| 오류 | test_authentication_returns_401_when_user_is_missing_or_inactive | 사용자 조회 결과 없음 | 401 INVALID_ACCESS_TOKEN, 서비스 쿼리 미실행 | PASS |
| 문서 | test_authenticated_endpoint_declares_bearer_security_scheme | OpenAPI 스키마 | `securitySchemes.HTTPBearer` 등록, 인증 API에 `security` 선언 | PASS |

### 검증하지 않은 항목

- **없는 사용자 / WITHDRAWN·SUSPENDED / 삭제된 사용자**는 Mock DB로 구분할 수 없어 모두 같은
  401로 처리되는 것만 확인하고, 조회 조건은 생성된 SQL로 검증했습니다.
- **다른 알고리즘(`none`, RS256 등)으로 서명한 토큰**은 `jwt.decode` 에 `algorithms=["HS256"]`
  을 넘겨 라이브러리가 거부하므로 별도 테스트를 만들지 않았습니다.
- **각 도메인 API의 401 응답**은 공통 의존성이 처리하므로 도메인 테스트에서는 다루지 않고,
  Swagger 계약 테스트에서 `security` 선언 여부만 확인합니다.
- `GET /api/v1/users/me/album/yezul-frames` 는 로그인한 사용자만 호출할 수 있습니다.
  프레임 목록 자체는 사용자별로 다르지 않아 큐브 소유권은 검증하지 않고, 인증 의존성만
  통과하면 동일한 목록을 반환합니다. 전용 테스트는 아래 절에 정리했습니다.

---

## 예절샷 프레임 조회 인증 — `GET /api/v1/users/me/album/yezul-frames`

로그인한 사용자만 호출할 수 있고, 큐브 소유권은 검증하지 않습니다.
`api_client(db, authenticate=False)` 로 인증 의존성을 살린 뒤 `issue_token()` 으로 만든
토큰을 붙여 호출합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_yezul_frames_returns_frames_with_valid_access_token | 유효 토큰 + ACTIVE 사용자 | 200 + 프레임 목록, 소유권 조회 없이 프레임 쿼리 1회 | PASS |
| 오류 | test_yezul_frames_returns_401_without_access_token | Authorization 헤더 없음 | 401 INVALID_ACCESS_TOKEN, DB 조회 없음 | PASS |
| 오류 | test_yezul_frames_returns_401_for_expired_token | `exp` 가 과거 | 401 INVALID_ACCESS_TOKEN, 프레임 쿼리 미실행 | PASS |
| 오류 | test_yezul_frames_returns_401_when_user_is_missing_or_inactive | 사용자 조회 결과 없음 | 401 INVALID_ACCESS_TOKEN, 프레임 쿼리 미실행 | PASS |
| 문서 | test_yezul_frames_declares_bearer_security_scheme | OpenAPI 스키마 | `security` 에 `HTTPBearer` 선언 | PASS |

`app/avatar/tests/test_avatar.py` 에도 도메인 쪽 테스트가 있습니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 오류 | test_yezul_frames_returns_401_without_access_token | 토큰 없음 | 401 INVALID_ACCESS_TOKEN, 프레임 쿼리 미실행 | PASS |
| 문서 | test_yezul_frames_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200}`, `security` 에 `HTTPBearer` 선언 | PASS |

### 검증하지 않은 항목

- **큐브 소유권 없는 사용자**는 이 API가 소유권을 보지 않으므로 별도 케이스를 만들지 않았습니다.
- **잘못된 서명·비Bearer 스킴 등 나머지 토큰 오류**는 공통 인증 의존성 테스트에서 이미
  검증하므로 이 API에서는 반복하지 않습니다.
