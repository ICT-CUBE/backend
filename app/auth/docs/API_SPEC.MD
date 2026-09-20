## 이메일 회원가입
- http 메서드: post
- domain: auth
- endpoint: /api/v1/auth/signup

### API 설명

이메일, 비밀번호, 닉네임과 프로필 캐릭터를 등록하고, 생성된 사용자 정보와 1년 동안 사용할 Access Token을 반환한다.

---

### 처리 정책

- 이메일은 일반적인 이메일 형식이며 최대 255자여야 한다.
- 비밀번호는 별도의 조합 제한 없이 8자 이상 64자 이하만 허용한다.
- 닉네임은 앞뒤 공백을 제외하고 1자 이상 20자 이하이며 중복을 허용한다.
- 프로필 캐릭터 코드는 `profile_001`, `profile_002`, `profile_003` 중 하나만 허용한다.
- 동일한 이메일로 가입한 사용자가 존재하면 사용자 상태와 관계없이 재가입할 수 없다.
- 회원가입 성공 시 365일 동안 유효한 JWT Access Token을 반환하며 Refresh Token은 제공하지 않는다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `email` | string | O | 가입할 이메일. 일반적인 이메일 형식, 최대 255자 |
| `password` | string | O | 사용할 비밀번호. 8~64자 |
| `nickname` | string | O | 사용자 닉네임. 앞뒤 공백 제거 후 1~20자, 중복 허용 |
| `profileCharacterCode` | string | O | 프로필 캐릭터 코드: profile_001 | profile_002 | profile_003 |

```json
{
  "email": "user@example.com",
  "password": "password123!",
  "nickname": "아르조니",
  "profileCharacterCode": "profile_001"
}
```

---

### 정상 응답 데이터

Status Code : 201

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `user.id` | number | 생성된 사용자 id |
| `auth.accessToken` | string | 발급된 JWT Access Token |
| `auth.tokenType` | string | 인증 방식. 항상 Bearer |
| `auth.expiresIn` | number | 토큰 유효시간(초). 31536000 |
| `auth.expiresAt` | string(date-time) | Access Token 만료 시각. 한국시간 기준 offset 없는 ISO 8601 |

```json
{
  "user": {
    "id": 11
  },
  "auth": {
    "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
    "tokenType": "Bearer",
    "expiresIn": 31536000,
    "expiresAt": "2027-08-29T10:30:00"
  }
}
```

---

### 오류 응답 데이터

Status Code : 409

동일한 이메일을 사용하는 사용자가 이미 존재하는 경우

```json
{
  "code": "EMAIL_ALREADY_EXISTS",
  "message": "이미 사용 중인 이메일입니다."
}
```


## 이메일 로그인
- http 메서드: post
- domain: auth
- endpoint: /api/v1/auth/login/email

### API 설명

이메일과 비밀번호로 사용자를 확인하고, 로그인 성공 시 사용자 정보와 1년 동안 사용할 Access Token을 반환한다.

---

### 처리 정책

- 이메일은 앞뒤 공백을 제거하고 소문자로 변환한 값을 사용한다.
- 비밀번호는 별도의 길이·조합 검증 없이 저장된 비밀번호와의 일치 여부만 확인한다.
- 이메일과 비밀번호가 일치하는 활성 이메일 사용자인 경우에만 로그인할 수 있다.
- 사용자 없음, 비밀번호 불일치, 이메일 계정 아님, 탈퇴·정지·삭제된 사용자는 모두 같은 401 오류를 반환한다.
- 로그인 성공 시 발급 시점부터 365일 동안 유효한 JWT Access Token을 새로 반환한다.
- Refresh Token은 제공하지 않는다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `email` | string | O | 가입한 이메일. 일반적인 이메일 형식, 최대 255자 |
| `password` | string | O | 가입 시 등록한 비밀번호 |

```json
{
  "email": "user@example.com",
  "password": "password123!"
}
```

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `user.id` | number | 로그인한 사용자 id |
| `auth.accessToken` | string | 발급된 JWT Access Token |
| `auth.tokenType` | string | 인증 방식. 항상 Bearer |
| `auth.expiresIn` | number | 토큰 유효시간(초). 31536000 |
| `auth.expiresAt` | string(date-time) | Access Token 만료 시각. 한국시간 기준 offset 없는 ISO 8601 |

```json
{
  "user": {
    "id": 1
  },
  "auth": {
    "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
    "tokenType": "Bearer",
    "expiresIn": 31536000,
    "expiresAt": "2027-08-29T10:30:00"
  }
}
```

---

### 오류 응답 데이터

Status Code : 401

이메일 또는 비밀번호가 일치하는 로그인 가능한 사용자를 찾을 수 없는 경우

```json
{
  "code": "INVALID_CREDENTIALS",
  "message": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```