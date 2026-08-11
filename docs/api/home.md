## 홈 정보 조회
- http 메서드: get
- 엔드포인트: api/v1/users/me/home

### API 설명

서비스 메인 홈 화면에서 호출된다.

홈 화면에 노출 되는 정보들을 반환한다.

---

### 요청 Query

---

### 요청 Path

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 200

```json
{
  "user": {
    "id": 1,
	  "profileCharacterImgURl": "https//PROFILE_01"
  },
  "cubeOwnership": {
    "id": 12,
    "avatarNickname": "젠득이",
    "acquiredAt": "2026-03-19T10:30:00"
  },
  "cube": {
    "id": 15,
    "artistName": "JENNIE"
  },
  "affinity": {
    "id": 7,
    "currentXp": 1245,
    "level": {
      "id": 3,
      "level": 3,
      "levelName": "close",
      "levelXp": 2000
    }
  }
}
```

- 프로필 이미지 컨텐츠는 서버에서 관리한다.

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```

Status Code : 403

```json
{
  "code": "CUBE_OWNERSHIP_FORBIDDEN",
  "message": "해당 큐브 소유권 정보를 조회할 권한이 없습니다."
}
```