## 텍스트 및 음성 대화 조회
- http 메서드: get
- 엔드포인트: api/v1/users/me/conversation-sessions

### API 설명

사용자가 텍스트 대화 혹은 음성 대화를 들어가면 호출된다.

텍스트  대화, 음성 대화에 맞는 대화 세션 정보를 반환한다.

이때 대화가 한번도 이루어지지 않은 세션은 조회하지 않는다.

---

### 요청 Query

```json
{
	"conversationType": "TEXT",
	"page": 0,
	"size": 20
}
```

```json
{
  "conversationType": "VOICE",
  "page": 0,
  "size": 20
}
```

요청 예시: api/v1/users/me/conversation-sessions?conversationType=TEXT&page=0&size=20

---

### 요청 Path

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 200

- conversationType=TEXT

```json
{
  "conversationSessions": [
    {
      "id": 1001,
      "conversationType": "TEXT",
      "conversationTitle": "오늘의 무대 이야기",
      "audioUrl": null,
      "audioDurationSeconds": null,
      "lastMessage": {
        "id": 5003,
        "content": "헐! 대박인데? 나도 거기 가보고 싶었는데!",
        "sentAt": "2026-07-29T12:25:00+09:00"
      }
    },
    {
      "id": 1002,
      "conversationType": "TEXT",
      "conversationTitle": "오늘 무대 어땠어?",
      "audioUrl": null,
      "audioDurationSeconds": null,
      "lastMessage": {
        "id": 5010,
        "content": "오늘 무대 진짜 최고였어!",
        "sentAt": "2026-07-28T18:30:00+09:00"
      }
    }
  ],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": false
  }
}
```

- conversationType=VOICE

```json
{
  "conversationSessions": [
    {
      "id": 1101,
      "conversationType": "VOICE",
      "conversationTitle": "저녁 메뉴 추천",
      "audioUrl": "https://cdn.example.com/conversations/VOICE_CONVERSATION_1101.m4a",
      "audioDurationSeconds": 264,
      "lastMessage": {
        "id": 5003,
        "content": null,
        "sentAt": "2026-07-29T12:25:00+09:00"
      }
    },
    {
      "id": 1102,
      "conversationType": "VOICE",
      "conversationTitle": "지난 콘서트에 대한 감상평",
      "audioUrl": "https://cdn.example.com/conversations/VOICE_CONVERSATION_1102.m4a",
      "audioDurationSeconds": 264,
      "lastMessage": {
        "id": 5003,
        "content": null,    
        "sentAt": "2026-07-29T12:25:00+09:00"
      }
    }
  ],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": false
  }
}
```

```json
{
  "conversationSessions": [],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": false
  }
}
```

---

### 오류 응답 데이터




## 대화 세션 상세 조회
- http 메서드: get
- 엔드포인트: api/v1/users/me/conversation-sessions/{conversationSessionId}

### API 설명

텍스트 대화에서 세션을 클릭하면 호출된다. 음성대화에서는 불가능하다. 만약 음성대화 세션으로 대화 세션 상세 조회를 하면 404를 반환한다. 또한 대화가 한 번도 오가지 않은 대화 세션도 404로 처리한다.

세션에서 나눴던 대화와 대화 전송 시각을 반환한다. 전체 대화를 한번에 반환하고, sequenceNumber를 기준으로 내림차순 정렬해서 반환한다.

- 고정 사용자 ID 1의 `ACTIVE` 큐브 소유권에 속한 텍스트 대화 세션만 조회할 수 있다.
- 삭제된 대화 세션(`deleted_at`이 null이 아닌 항목)은 조회하지 않는다.
- `conversation_type = VOICE`인 세션 id로 요청하면 음성 대화 상세 조회 불가 404를 반환한다.
- 대화 메시지의 `status`는 필터링하지 않고 `ALLOWED`, `BLOCKED` 모두 반환한다.
- `sentAt`은 한국 시간 기준 오프셋(+09:00)을 포함해 반환한다.

---

### 요청 Query

---

### 요청 Path

```json
{
	"conversationSessionId": 1001
}
```

요청 예시: api/v1/users/me/conversation-sessions/1001

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 200

```json
{
  "conversationSession": {
    "id": 1001,
    "messages": [
      {
        "id": 5001,
        "senderType": "AVATAR",
        "content": "@@아! 지금 뭐하고 있어?",
        "sequenceNumber": 1,
        "sentAt": "2026-07-29T12:23:00+09:00"
      },
      {
        "id": 5002,
        "senderType": "USER",
        "content": "나 지금 카페에서 공부하고 있어.",
        "sequenceNumber": 2,
        "sentAt": "2026-07-29T12:23:30+09:00"
      },
      {
        "id": 5003,
        "senderType": "AVATAR",
        "content": "헐!! 대박인데? 나도 거기 가보고 싶었는데!",
        "sequenceNumber": 3,
        "sentAt": "2026-07-29T12:25:00+09:00"
      }
    ]
  }
}
```

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "CONVERSATION_SESSION_NOT_FOUND",
  "message": "대화 세션을 찾을 수 없습니다."
}
```

- 존재하지 않는 세션 id, 현재 사용자의 활성 큐브 소유권에 속하지 않는 세션, 삭제된 세션, 메시지가 하나도 없는 텍스트 세션인 경우 위 응답을 반환한다.

```json
{
  "code": "VOICE_CONVERSATION_DETAIL_NOT_AVAILABLE",
  "message": "음성 대화는 세션 상세 조회가 불가능합니다."
}
```

- 현재 사용자의 활성 큐브 소유권에 속한 세션이지만 `conversation_type = VOICE`인 경우 위 응답을 반환한다.




## 대화 세션 생성
- http 메서드: post
- 엔드포인트: api/v1/users/me/conversation-sessions

### API 설명

사용자가 새로운 텍스트 대화 또는 음성 대화를 시작할 때 호출한다. 

호출 시점은 다음과 같다.

- 텍스트 대화 화면에서 `새 대화 시작하기` 선택
- 음성 대화 화면에서 `통화` 버튼 선택

사용자가 새 대화 시작을 하고 아무 대화를 진행하지 않아도 세션은 db에 저장된다. 하지만 세션 조회 및 상세 조회는 불가능하다. 

---

### 요청 Query

---

### 요청 Path

---

### 요청 Body

```json
{
	"conversationType": "TEXT"
}
```

```json
{
  "conversationType": "VOICE"
}
```

---

### 정상 응답 데이터

Status Code : 201

```json
{
  "conversationSession": {
    "id": 1001,
    "conversationType": "TEXT"
  }
}
```

```json
{
  "conversationSession": {
    "id": 1101,
    "conversationType": "VOICE"
  }
}
```

---

### 오류 응답 데이터




## 대화 세션 삭제
- http 메서드: delete
- 엔드포인트: api/v1/users/me/conversation-sessions/{conversationSessionId}

### API 설명

사용자가 텍스트 대화 또는 음성 대화 세션을 삭제할 때 호출한다.

대화 세션 row를 실제로 삭제하지 않고 `deleted_at`에 삭제 시각을 저장하는 소프트 딜리트 방식으로 처리한다.

- 고정 사용자 ID 1의 `ACTIVE` 큐브 소유권에 속한 대화 세션만 삭제할 수 있다.
- 대화 메시지가 하나도 없는 빈 세션도 정상 삭제할 수 있다.
- 삭제된 세션은 대화 목록 조회와 대화 세션 상세 조회에서 제외된다.
- 이미 삭제된 세션에 대해 다시 삭제 요청을 보내면 중복 삭제로 보고 404를 반환한다.
- 삭제 시각은 한국 시간 기준으로 `deleted_at`에 저장한다.

---

### 요청 Query

---

### 요청 Path

```json
{
  "conversationSessionId": 1001
}
```

요청 예시: api/v1/users/me/conversation-sessions/1001

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "CONVERSATION_SESSION_NOT_FOUND",
  "message": "삭제할 대화 세션을 찾을 수 없습니다."
}
```

- 존재하지 않는 세션 id, 현재 사용자의 활성 큐브 소유권에 속하지 않는 세션, 이미 삭제된 세션인 경우 위 응답을 반환한다.
