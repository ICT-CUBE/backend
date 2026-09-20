## 알림 목록 조회
- http 메서드: get
- domain: home
- endpoint: api/v1/users/me/notifications

### API 설명

현재 로그인한 사용자의 알림 목록을 조회할 때 호출한다.

프론트는 알림 화면의 상단 탭을 이동할 때 동일한 API를 호출하고 `type` 값만 변경한다.

---

### 처리 정책

- 현재 로그인한 사용자의 `notification.user_id`와 일치하는 알림만 조회한다.
- 큐브 소유권은 알림 조회 조건으로 사용하지 않는다.
- `type`은 `ALL`, `MISSION`, `EVENT`, `MARKET` 중 하나를 전달한다.
- `type = ALL`이면 알림 유형 조건 없이 현재 사용자의 모든 알림을 조회한다.
- `ALL`은 전체 조회를 위한 Query 값이며 알림의 저장 유형으로 사용하지 않는다.
- `type = MISSION`, `EVENT`, `MARKET`이면 `notification_type`이 요청 유형과 일치하는 알림만 조회한다.
- 알림은 `sent_at DESC`, 동일한 전송 시각이면 `id DESC` 순으로 정렬한다.
- 페이지 번호는 0부터 시작한다.
- 다음 페이지에 데이터가 존재할 때만 `hasNext`를 `true`로 반환한다.
- 조회 결과가 없으면 오류 없이 빈 배열과 `hasNext = false`를 반환한다.
- 목록 조회만으로 `is_read` 또는 `read_at`을 변경하지 않는다.
- `sentAt`은 KST 기준의 offset 없는 ISO 8601 date-time으로 반환한다.

---

### 요청 Query

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `type` | string | O | 조회 유형: `ALL` \| `MISSION` \| `EVENT` \| `MARKET` |
| `page` | number | X | 0부터 시작하는 페이지 번호. 기본값 0 |
| `size` | number | X | 페이지당 조회 개수. 기본값 20 |

```http
GET /api/v1/users/me/notifications?type=ALL&page=0&size=20
```

---

### 요청 Path

없음

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `notifications` | array | 알림 목록 |
| `notifications[].id` | number | 알림 id |
| `notifications[].notificationType` | string | 알림 유형: `MISSION` \| `EVENT` \| `MARKET` |
| `notifications[].title` | string | 알림 제목 |
| `notifications[].content` | string | 알림 내용 |
| `notifications[].isRead` | boolean | 알림 읽음 여부 |
| `notifications[].sentAt` | string(date-time) | 알림 전송 시각. KST 기준 offset 없는 ISO 8601 형식 |
| `pagination.page` | number | 현재 페이지 번호 |
| `pagination.size` | number | 페이지당 조회 개수 |
| `pagination.hasNext` | boolean | 다음 페이지 존재 여부 |

```json
{
  "notifications": [
    {
      "id": 4,
      "notificationType": "MARKET",
      "title": "거래 알림",
      "content": "거래 제안이 도착했어요.",
      "isRead": false,
      "sentAt": "2026-07-28T14:25:00"
    },
    {
      "id": 3,
      "notificationType": "MISSION",
      "title": "데일리 미션을 완료했어요",
      "content": "미션 보상을 수령해보세요.",
      "isRead": true,
      "sentAt": "2026-07-28T13:30:00"
    }
  ],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": true
  }
}
```

조회 결과가 없는 경우

```json
{
  "notifications": [],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": false
  }
}
```

---

### 오류 응답 데이터

이 API에서 별도로 정의하는 도메인 오류는 없음.

Query 값이 올바르지 않은 경우의 400, 인증 실패에 대한 401과 서버 내부 오류에 대한 500은 공통 오류 정책을 따른다.


## 개별 알림 읽음 처리
- http 메서드: patch
- domain: home
- endpoint: api/v1/users/me/notifications/{notificationId}/read

### API 설명

사용자가 특정 알림을 클릭하면 호출한다.

현재 로그인한 사용자에게 속한 해당 알림을 읽음 상태로 변경한다.

---

### 처리 정책

- `notificationId`와 현재 로그인한 사용자의 ID가 모두 일치하는 알림만 읽음 처리할 수 있다.
- 큐브 소유권은 알림 읽음 처리 조건으로 사용하지 않는다.
- 알림을 처음 읽음 처리할 때 `is_read`를 `true`로 변경한다.
- 알림을 처음 읽음 처리할 때 `read_at`에 요청을 처리한 현재 KST 시각을 timezone 없는 값으로 저장한다.
- 이미 읽은 알림을 다시 요청해도 정상 처리하고 204를 반환한다.
- 이미 읽은 알림의 `read_at`은 기존 값을 유지한다.
- `notificationId`에 해당하는 알림이 없거나 현재 사용자의 알림이 아니면 404: NOTIFICATION_NOT_FOUND를 반환한다.
- 다른 사용자의 알림인지 여부는 응답에서 구분하지 않는다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `notificationId` | number | O | 읽음 처리할 알림 id. 1 이상의 정수 |

```json
{
  "notificationId": 31
}
```

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 204

응답 Body 없음.

---

### 오류 응답 데이터

Status Code : 404

알림이 존재하지 않거나 현재 사용자의 알림이 아닌 경우

```json
{
  "code": "NOTIFICATION_NOT_FOUND",
  "message": "알림을 찾을 수 없습니다."
}
```

Path 값이 올바르지 않은 경우의 400, 인증 실패에 대한 401과 서버 내부 오류에 대한 500은 공통 오류 정책을 따른다.


## 전체 알림 읽음 처리
- http 메서드: patch
- domain: home
- endpoint: api/v1/users/me/notifications/read-all

### API 설명

사용자가 알림 화면에서 `모두 읽음` 버튼을 누르면 호출한다.

현재 로그인한 사용자의 모든 미읽음 알림을 읽음 상태로 변경한다.

---

### 처리 정책

- 현재 로그인한 사용자의 알림만 읽음 처리한다.
- 큐브 소유권은 전체 알림 읽음 처리 조건으로 사용하지 않는다.
- 알림 유형과 관계없이 현재 사용자의 `is_read = false`인 모든 알림을 처리한다.
- 처리 대상 알림의 `is_read`를 `true`로 변경한다.
- 요청을 처리한 현재 KST 시각을 한 번 생성하고, 모든 처리 대상의 `read_at`에 동일한 timezone 없는 값으로 저장한다.
- 이미 `is_read = true`인 알림은 수정하지 않으며 기존 `read_at`을 유지한다.
- 미읽음 알림이 없거나 알림이 하나도 없어도 정상 처리하고 204를 반환한다.
- 전체 알림 읽음 처리는 멱등성을 보장한다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 204

응답 Body 없음.

---

### 오류 응답 데이터

이 API에서 별도로 정의하는 도메인 오류는 없음.

인증 실패에 대한 401과 서버 내부 오류에 대한 500은 공통 오류 정책을 따른다.
