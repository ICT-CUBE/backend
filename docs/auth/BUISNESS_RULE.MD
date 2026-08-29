# 인증 도메인 비즈니스 룰

## 이메일 회원가입

### API 기본 규칙

- 이메일 회원가입은 `POST /api/v1/auth/signup` 엔드포인트를 사용한다.
- 요청 Body는 JSON 형식으로 전달받는다.
- 필수 입력값은 `email`, `password`, `nickname`, `profileCharacterCode`이다.
- 필수값 누락과 입력값 검증 실패는 공통 `400 INVALID_REQUEST`로 처리한다.
- 회원가입 성공 시 `201 Created`와 생성된 사용자 id 및 JWT Access Token 정보를 반환한다.

### 이메일 검증과 저장

- 이메일은 문자열 앞뒤 공백을 제거하고 전체를 소문자로 변환한 뒤 검증하고 저장한다.
- 이메일은 일반적인 `local-part@domain` 형식이어야 한다.
- 이메일은 DB의 `user.email VARCHAR(255)`에 맞춰 최대 255자까지 허용한다.
- 정규화한 이메일과 동일한 `user.email`이 이미 존재하면 사용자 상태와 관계없이 `409 EMAIL_ALREADY_EXISTS`를 반환한다.
- 이메일 중복 여부를 먼저 조회하더라도 동시 회원가입 요청에 대비해 DB의 `uk_user_email` UNIQUE 제약을 최종 기준으로 사용한다.
- INSERT 과정에서 이메일 UNIQUE 제약 위반이 발생해도 `409 EMAIL_ALREADY_EXISTS`로 변환한다.

### 비밀번호 검증과 저장

- 비밀번호는 8자 이상 64자 이하로 제한한다.
- 영문, 숫자, 특수문자 포함 여부는 검증하지 않는다.
- 공백 포함 여부도 검증하지 않는다.
- 비밀번호는 앞뒤 공백 제거, 대소문자 변경 또는 Unicode 정규화 없이 입력받은 값을 그대로 Argon2id에 전달한다.
- 입력받은 비밀번호 원문은 DB, 로그 또는 응답에 저장하거나 출력하지 않는다.
- 비밀번호는 무작위 Salt가 포함된 Argon2id 해시로 변환하여 `user.password_hash`에 저장한다.
- Argon2id 해시는 Salt를 포함하므로 같은 비밀번호라도 사용자마다 서로 다른 해시 문자열이 생성되는 것을 정상으로 처리한다.
- 비밀번호 확인 시 입력값을 다시 단순 해싱하여 문자열끼리 비교하지 않고 Argon2id 검증 함수를 사용한다.
- 개발용 목데이터 사용자들의 실제 로그인 비밀번호는 모두 `12345678`로 사용한다.
- `12345678`는 신규 회원가입의 최소 길이를 충족하지 않지만 기존 목데이터 로그인은 허용한다.
- 목데이터의 `password_hash`에는 임의 형식의 문자열이 아니라 실제로 `12345678`를 Argon2id로 해싱한 유효한 값을 저장한다.

### 닉네임 검증과 저장

- 닉네임은 필수값이지만 중복을 허용한다.
- 닉네임은 앞뒤 공백을 제거한 값을 검증하고 저장한다.
- 공백 제거 결과가 빈 문자열이면 공통 `400 INVALID_REQUEST`를 반환한다.
- 닉네임은 DB의 `user.nickname VARCHAR(20)`에 맞춰 1자 이상 20자 이하로 제한한다.

### 프로필 캐릭터 저장

- `profileCharacterCode`는 `profile_001`, `profile_002`, `profile_003`만 허용한다.
- 허용 목록에 없는 값은 공통 `400 INVALID_REQUEST`를 반환한다.
- 프로필 이미지 URL은 `https://haniumstorage.blob.core.windows.net/hanium/profile_image/{profileCharacterCode}.png` 형식으로 조합한다.
- 조합한 절대 URL을 `user.profile_character_img_url`에 저장한다.
- 회원가입 과정에서는 Azure Blob에 파일을 새로 업로드하지 않는다.

### USER 생성값

- 이메일 회원가입 사용자의 `user.login_provider`는 `EMAIL`로 저장한다.
- 소셜 로그인 식별자를 사용하지 않으므로 `user.provider_user_id`는 `NULL`로 저장한다.
- `user.status`는 `ACTIVE`로 저장한다.
- `user.chat_violation_count`는 0으로 저장한다.
- `user.deleted_at`은 `NULL`로 저장한다.
- `user.created_at`과 `user.updated_at`은 DB 기본값을 사용한다.
- 사용자 생성과 Access Token 생성 과정에서 오류가 발생하면 DB 트랜잭션을 롤백한다.

### USER_SETTING 기본값

- 새 사용자의 `user` INSERT 후 flush하여 생성된 `user.id`를 확보한다.
- 확보한 사용자 id로 `user_setting` 행을 같은 DB 트랜잭션 안에서 생성한다.
- `push_enabled`, `new_conversation_enabled`, `affinity_change_enabled`, `daily_mission_refresh_enabled`, `trade_completed_enabled`, `trade_offer_enabled`, `community_comment_notice_enabled`를 모두 `true`로 생성한다.
- `user_setting.created_at`과 `user_setting.updated_at`은 DB 기본값을 사용한다.
- 사용자 또는 기본 설정 생성 중 하나라도 실패하면 둘 다 저장되지 않도록 전체 트랜잭션을 롤백한다.

### JWT Access Token 발급

- 회원가입 성공 시 Refresh Token 없이 JWT Access Token 하나만 발급한다.
- Access Token은 `JWT_SECRET_KEY`를 사용해 `HS256`으로 서명한다.
- HS256은 JWT 무결성 검증용 HMAC-SHA256이며 비밀번호 저장용 해시가 아니다.
- JWT 비밀키는 최소 32바이트 이상의 예측 불가능한 랜덤값을 사용하고 Git에 커밋하지 않는다.
- `JWT_ALGORITHM`은 `HS256`, `JWT_ACCESS_TOKEN_EXPIRE_DAYS`는 `365`로 설정한다.
- JWT 비밀키가 변경되면 기존 비밀키로 발급된 모든 토큰이 무효가 된다.
- JWT Payload에는 사용자 id를 문자열로 변환한 `sub`, 발급 시각 `iat`, 만료 시각 `exp`를 포함한다.
- `iat`와 `exp`는 UTC 기준 NumericDate로 JWT에 기록한다.
- Access Token 유효기간은 발급 시점부터 365일로 고정한다.
- `expiresIn`은 365일을 초로 환산한 `31536000`을 반환한다.
- `expiresAt`은 JWT의 `exp`와 동일한 시점을 한국시간 기준 offset 없는 ISO 8601 문자열로 반환한다.
- `tokenType`은 항상 `Bearer`를 반환한다.
- Access Token 원문과 해시는 DB에 저장하지 않는다.
- 회원가입 시 `auth_session` 데이터를 생성하지 않는다.
- Refresh Token을 발급하거나 저장하지 않는다.

### Access Token을 이용한 사용자 인증

- 프론트엔드는 발급받은 Access Token을 보관하고 인증이 필요한 요청의 `Authorization: Bearer {accessToken}` 헤더로 전송한다.
- 회원가입과 로그인 API에는 인증 의존성을 적용하지 않는다.
- 현재 사용자 id 1을 고정 반환하는 `get_current_user_id()`는 HTTP Bearer Token과 DB 세션을 주입받는 JWT 검증 의존성으로 교체한다.
- 기존 인증 필요 라우터는 계속 `Depends(get_current_user_id)`를 사용하며, 서비스 함수에는 검증이 끝난 실제 사용자 id를 전달한다.
- 서버는 요청으로 전달된 JWT의 서명을 검증한다.
- JWT 디코딩 시 허용 알고리즘을 `HS256`으로 명시하고 다른 알고리즘은 허용하지 않는다.
- 서버는 JWT의 `exp`를 검증하여 만료된 토큰을 거부한다.
- 서명과 만료 검증을 통과하면 JWT의 `sub`에서 사용자 id를 추출한다.
- `sub`가 없거나 정수 사용자 id로 변환할 수 없으면 인증 실패로 처리한다.
- 추출한 사용자 id로 DB의 사용자를 조회하여 현재 요청의 사용자로 사용한다.
- 사용자 조회 시 존재하며 `status = ACTIVE`, `deleted_at IS NULL`인 사용자만 인증된 사용자로 인정한다.
- JWT가 없거나 Bearer 형식이 잘못됐거나 서명이 유효하지 않거나 만료됐거나 사용자를 찾을 수 없거나 사용자가 비활성 상태이면 모두 `401 INVALID_ACCESS_TOKEN`으로 처리한다.
- 401 응답은 `{"code": "INVALID_ACCESS_TOKEN", "message": "유효하지 않거나 만료된 액세스 토큰입니다."}` 형식을 사용한다.
- 서버는 요청마다 `auth_session` 또는 별도의 토큰 저장 컬럼을 조회하지 않는다.
- 이 인증 방식은 서버에 토큰 상태를 저장하지 않는 Stateless 방식이다.
- 로그아웃은 프론트엔드가 보관 중인 Access Token을 삭제하는 방식으로 처리한다.
- 토큰을 서버에서 즉시 폐기하거나 기기별 세션을 관리하는 기능은 제공하지 않는다.

### 오류 응답

- 입력값 검증 실패는 공통 `400 INVALID_REQUEST`를 사용한다.
- 동일한 이메일이 이미 존재하면 `409 EMAIL_ALREADY_EXISTS`를 사용한다.
- 공통 `500 INTERNAL_SERVER_ERROR` 외 추가 오류 응답은 정의하지 않는다.

### 구현 라이브러리

- Argon2id 비밀번호 해시와 검증에는 `pwdlib[argon2]`를 사용한다.
- JWT 생성과 검증에는 `PyJWT`를 사용한다.
- 이메일 형식 검증에는 `email-validator`를 사용한다.

## 이메일 로그인

### API와 요청 검증

- 이메일 로그인은 `POST /api/v1/auth/login/email` 엔드포인트를 사용한다.
- 로그인은 Access Token 발급 전 호출하는 공개 API이므로 JWT 인증 의존성을 적용하지 않는다.
- 요청 Body는 JSON 형식이며 `email`과 `password`를 필수값으로 받는다.
- `email` 또는 `password` 필드가 누락되면 공통 `400 INVALID_REQUEST`를 반환한다.
- 이메일은 일반적인 이메일 형식이며 최대 255자인지 검증한다.
- 이메일 형식 또는 길이가 올바르지 않으면 공통 `400 INVALID_REQUEST`를 반환한다.
- 로그인 비밀번호에는 길이, 문자 조합 또는 공백 포함 여부 검증을 적용하지 않는다.
- 빈 문자열을 포함해 전달된 비밀번호 값은 별도 요청값 오류로 막지 않고 저장된 해시와의 일치 여부만 확인한다.

### 이메일과 비밀번호 처리

- 이메일은 앞뒤 공백을 제거하고 전체를 소문자로 변환한 뒤 사용자 조회에 사용한다.
- 비밀번호는 앞뒤 공백 제거, 대소문자 변경 또는 Unicode 정규화 없이 요청받은 값을 그대로 Argon2id 검증 함수에 전달한다.
- 입력받은 비밀번호를 새로 해시한 뒤 문자열끼리 비교하지 않는다.
- `pwdlib`의 Argon2id 검증 함수를 사용해 입력 비밀번호와 저장된 Salt 포함 해시를 검증한다.
- 회원가입 때 사용한 비밀번호 검증 규칙을 로그인에서 다시 적용하지 않는다.
- 따라서 개발용 목데이터 사용자는 신규 회원가입 최소 길이보다 짧은 `1234`로 로그인할 수 있다.

### 로그인 가능 사용자 조회

- 정규화한 `user.email`이 일치하는 사용자를 조회한다.
- `user.login_provider = EMAIL`인 사용자만 이메일 로그인을 허용한다.
- `user.password_hash IS NOT NULL`인 사용자만 비밀번호 검증 대상으로 사용한다.
- `user.status = ACTIVE`이고 `user.deleted_at IS NULL`인 사용자만 로그인할 수 있다.
- 사용자 없음, 비밀번호 불일치, 이메일 계정 아님, `password_hash` 없음, `WITHDRAWN`, `SUSPENDED` 또는 소프트 삭제 상태는 모두 같은 로그인 실패로 처리한다.
- 로그인 실패 원인을 외부에 구분해서 반환하지 않는다.
- 저장된 `password_hash` 자체가 올바른 Argon2id 문자열이 아니어서 검증 함수가 예외를 발생시키는 경우에는 별도 변환 없이 공통 `500 INTERNAL_SERVER_ERROR`로 처리해도 된다.

### 로그인 실패 응답

- 로그인 가능한 사용자를 찾지 못하거나 비밀번호가 일치하지 않으면 `401 INVALID_CREDENTIALS`를 반환한다.
- 401 응답은 `{"code": "INVALID_CREDENTIALS", "message": "이메일 또는 비밀번호가 올바르지 않습니다."}` 형식을 사용한다.
- 이메일 존재 여부, 계정 상태 또는 비밀번호 일치 여부와 관계없이 동일한 코드와 메시지를 사용한다.

### 로그인 성공과 Access Token 발급

- 사용자 조회와 Argon2id 검증을 모두 통과하면 해당 `user.id`로 JWT Access Token을 새로 발급한다.
- 토큰 생성은 이메일 회원가입의 공통 JWT 규칙과 같은 `JWT_SECRET_KEY`, `HS256`, 365일 만료 설정을 사용한다.
- JWT Payload에는 사용자 id를 문자열로 변환한 `sub`, 발급 시각 `iat`, 만료 시각 `exp`를 포함한다.
- 로그인할 때마다 새로운 `iat`와 `exp`를 가진 Access Token을 발급한다.
- 로그인 성공만으로 `user` 또는 다른 DB 데이터를 갱신하지 않는다.
- `auth_session` 데이터와 Refresh Token은 생성하지 않는다.
- 성공 시 `200 OK`와 `user.id`, `auth.accessToken`, `auth.tokenType`, `auth.expiresIn`, `auth.expiresAt`을 반환한다.
