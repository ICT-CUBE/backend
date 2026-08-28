## 아바타 닉네임 설정
- http 메서드: patch
- domain: cube
- endpoint: api/v1/users/me/cube-ownerships/{cubeOwnershipId}/avatar-nickname

### API 설명

큐브 소유권 인증 후 사용자가 아바타 닉네임을 설정하거나 변경할 때 호출한다.

현재 사용자의 지정된 큐브 소유권에 아바타 닉네임을 저장한다.

---

### 처리 정책

- 로그인한 현재 사용자의 소유권만 수정할 수 있다. 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- `cubeOwnershipId`에 해당하는 큐브 소유권의 `user_id`가 현재 사용자와 일치해야 한다.
- 해당 큐브 소유권의 `ownership_status = ACTIVE`이고 `is_last_accessed = true`인 경우에만 닉네임을 설정할 수 있다.
- 큐브 소유권이 존재하지 않거나 현재 사용자 소유가 아니거나, `ACTIVE` 또는 마지막 접근 소유권 조건을 충족하지 않으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- `avatarNickname`은 필수이며 `null`, 빈 문자열, 공백으로만 구성된 문자열을 허용하지 않는다.
- `avatarNickname`의 앞뒤 공백을 제거한 후 길이가 1자 이상 30자 이하여야 한다.
- 한글, 영문, 숫자, 공백, 특수문자 등 문자 종류는 별도로 제한하지 않는다.
- 유효하지 않은 요청값은 공통 오류 정책에 따라 400: INVALID_REQUEST를 반환한다.
- 이미 닉네임이 설정되어 있어도 새로운 값으로 변경할 수 있다.
- 기존 닉네임과 동일한 값으로 요청해도 정상 처리한다.
- 다른 사용자 또는 다른 큐브 소유권과 동일한 닉네임을 사용할 수 있다.
- 검증이 완료된 닉네임을 `cube_ownership.avatar_nickname`에 저장한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `cubeOwnershipId` | number | O | 닉네임을 설정할 큐브 소유권 id |

```json
{
  "cubeOwnershipId": 12
}
```

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `avatarNickname` | string | O | 설정할 아바타 닉네임, 앞뒤 공백 제거 후 1자 이상 30자 이하 |

```json
{
  "avatarNickname": "젠득이"
}
```

---

### 정상 응답 데이터

Status Code : 204

---

### 오류 응답 데이터

Status Code : 404

큐브 소유권이 존재하지 않거나 현재 사용자의 활성 마지막 접근 소유권이 아닌 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```