## 텍스트 및 음성 대화 조회
- http 메서드: GET
- 엔드포인트: `/api/v1/users/me/conversation-sessions`
- 도메인: conversation

### API 설명

사용자가 텍스트 대화 혹은 음성 대화를 들어가면 호출된다.

텍스트 대화 또는 음성 대화에 맞는 대화 세션 목록을 반환한다.

이때 대화가 한번도 이루어지지 않은 세션은 조회하지 않는다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- `conversationType`은 `TEXT`, `VOICE` 중 하나다.
- `page`를 보내지 않으면 기본값은 0이다.
- `size`를 보내지 않으면 기본값은 20이다.
- `size`는 1 이상의 숫자를 허용한다.
- 프론트가 전달한 `size` 값을 기준으로 페이징해서 반환한다.
- 현재 사용자의 `ACTIVE` 큐브 소유권 중 `is_last_accessed = true`인 소유권에 속한 대화 세션만 조회한다.
- 조건에 맞는 큐브 소유권이 존재하지 않으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- 삭제된 대화 세션(`deleted_at`이 null이 아닌 항목)은 반환하지 않는다.
- 대화가 한 번도 이루어지지 않아 메시지가 없는 세션은 반환하지 않는다.
- 세션의 마지막 메시지 기준 최신순으로 정렬한다.
- 텍스트 대화 조회에서는 마지막 메시지의 `content`를 반환한다.
- 음성 대화 조회에서는 마지막 메시지의 `content`를 `null`로 반환한다.
- 음성 대화 조회에서는 세션의 `audioUrl`, `audioDurationSeconds`를 함께 반환한다.
- 조건에 맞는 큐브 소유권은 있지만 조회할 대화 세션이 없으면 빈 배열과 페이지 정보를 200으로 반환한다.

---

### 요청 Query

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `conversationType` | string | O | 조회할 대화 타입. `TEXT`, `VOICE` 중 하나 |
| `page` | number | X | 조회할 페이지 번호. 0부터 시작 |
| `size` | number | X | 페이지 크기. 1 이상의 숫자 |

요청 예시: /api/v1/users/me/conversation-sessions?conversationType=TEXT&page=0&size=20

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
|---|---:|---|
| `conversationSessions[].id` | number | 대화 세션 id |
| `conversationSessions[].conversationType` | string | 대화 타입 |
| `conversationSessions[].conversationTitle` | string \| null | 대화 목록에 표시할 제목 |
| `conversationSessions[].audioUrl` | string \| null | 음성 대화 녹음 파일 URL |
| `conversationSessions[].audioDurationSeconds` | number \| null | 음성 대화 녹음 파일 길이 |
| `conversationSessions[].lastMessage.id` | number | 마지막 메시지 id |
| `conversationSessions[].lastMessage.content` | string \| null | 마지막 메시지 내용 |
| `conversationSessions[].lastMessage.sentAt` | string(date-time) | 마지막 메시지 전송 시각 |
| `pagination.page` | number | 현재 페이지 번호 |
| `pagination.size` | number | 페이지 크기 |
| `pagination.hasNext` | boolean | 다음 페이지 존재 여부 |

`conversationType = TEXT`인 경우

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
        "sentAt": "2026-07-29T12:25:00"
      }
    },
    {
      "id": 1002,
      "conversationType": "TEXT",
      "conversationTitle": "오늘 의상 이야기",
      "audioUrl": null,
      "audioDurationSeconds": null,
      "lastMessage": {
        "id": 5010,
        "content": "오늘 무대 진짜 최고였어!",
        "sentAt": "2026-07-28T18:30:00"
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

`conversationType = VOICE`인 경우

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
        "sentAt": "2026-07-29T12:25:00"
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
        "sentAt": "2026-07-29T12:25:00"
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

조회 결과가 없는 경우

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

Status Code : 404

현재 사용자의 마지막 접근 `ACTIVE` 큐브 소유권이 존재하지 않는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```




## 대화 세션 상세 조회
- http 메서드: GET
- 엔드포인트: `/api/v1/users/me/conversation-sessions/{conversationSessionId}`
- 도메인: conversation

### API 설명

텍스트 대화 목록 화면에서 사용자가 특정 대화 세션을 클릭했을 때 호출한다.

`conversationSessionId`를 기준으로 텍스트 대화 세션의 전체 메시지를 조회한다.

---

### 처리 정책

- 텍스트 대화 세션만 상세 조회할 수 있다.
- `conversationSessionId`에 해당하는 세션이 현재 사용자의 `ACTIVE`이면서 `is_last_accessed = true`인 큐브 소유권에 속한 경우에만 조회할 수 있다.
- 삭제된 대화 세션(`deleted_at`이 null이 아닌 항목)은 조회하지 않는다.
- `conversation_type = VOICE`인 세션 id로 요청하면 404: VOICE_CONVERSATION_DETAIL_NOT_AVAILABLE을 반환한다.
- 대화가 한 번도 오가지 않은 텍스트 대화 세션은 상세 조회 대상에서 제외하며 404: CONVERSATION_SESSION_NOT_FOUND를 반환한다.
- 대화 메시지의 `status`는 필터링하지 않고 `ALLOWED`, `BLOCKED` 모두 반환한다.
- 메시지는 `sequenceNumber` 내림차순으로 반환한다. 대화 메시지가 많아질 수 있으므로 화면 진입 시 가장 최근 메시지를 우선 보여주기 위한 정책이다.
- `sentAt`은 한국시간 기준 offset 없는 ISO 8601 date-time으로 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `conversationSessionId` | number | O | 상세 조회할 대화 세션 id |

요청 예시: `/api/v1/users/me/conversation-sessions/1001`

---

### 요청 Body

없음

---

### 정상 응답 데이터
Status Code : 200

| 필드 | 타입 | 설명 |
|---|---:|---|
| `conversationSession.id` | number | 대화 세션 id |
| `conversationSession.messages[].id` | number | 대화 메시지 id |
| `conversationSession.messages[].senderType` | string | 메시지 발신자 타입. `USER` 또는 `AVATAR` |
| `conversationSession.messages[].content` | string | 메시지 내용 |
| `conversationSession.messages[].sequenceNumber` | number | 대화 세션 안에서의 메시지 순서 |
| `conversationSession.messages[].sentAt` | string(date-time) | 메시지 전송 시각 |

```json
{
  "conversationSession": {
    "id": 1001,
    "messages": [
      {
        "id": 5003,
        "senderType": "AVATAR",
        "content": "헐!! 대박인데? 나도 거기 가보고 싶었는데!",
        "sequenceNumber": 3,
        "sentAt": "2026-07-29T12:25:00"
      },
      {
        "id": 5002,
        "senderType": "USER",
        "content": "나 지금 카페에서 공부하고 있어.",
        "sequenceNumber": 2,
        "sentAt": "2026-07-29T12:23:30"
      },
      {
        "id": 5001,
        "senderType": "AVATAR",
        "content": "@@아! 지금 뭐하고 있어?",
        "sequenceNumber": 1,
        "sentAt": "2026-07-29T12:23:00"
      }
    ]
  }
}
```

---

### 오류 응답 데이터
Status Code : 404

대화 세션이 존재하지 않거나, 현재 사용자의 `ACTIVE`이면서 `is_last_accessed = true`인 큐브 소유권에 속하지 않거나, 삭제된 세션이거나, 메시지가 하나도 없는 텍스트 세션인 경우

```json
{
  "code": "CONVERSATION_SESSION_NOT_FOUND",
  "message": "대화 세션을 찾을 수 없습니다."
}
```

현재 사용자의 `ACTIVE`이면서 `is_last_accessed = true`인 큐브 소유권에 속한 세션이지만 음성 대화 세션인 경우

```json
{
  "code": "VOICE_CONVERSATION_DETAIL_NOT_AVAILABLE",
  "message": "음성 대화는 세션 상세 조회가 불가능합니다."
}
```




## 대화 세션 생성
- http 메서드: POST
- 엔드포인트: `/api/v1/users/me/conversation-sessions`
- 도메인: conversation

### API 설명

사용자가 새로운 텍스트 대화 또는 음성 대화를 시작할 때 호출한다.

호출 시점은 다음과 같다.

- 텍스트 대화 화면에서 `새 대화 시작하기` 선택
- 음성 대화 화면에서 `통화` 버튼 선택

요청값을 기준으로 현재 사용자의 마지막 활성 큐브 소유권에 대화 세션을 생성한다.

---

### 처리 정책

- `conversationType`은 `TEXT` 또는 `VOICE`만 허용한다.
- 현재 사용자의 `ACTIVE` 큐브 소유권 중 `is_last_accessed = true`인 소유권에 대화 세션을 생성한다.
- 현재 사용자의 마지막 활성 큐브 소유권이 존재하지 않으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- `avatar_conversation_session.conversation_type`은 요청의 `conversationType` 값으로 저장한다.
- `avatar_conversation_session.status`는 `ACTIVE`로 저장한다.
- `avatar_conversation_session.started_at`은 서버의 현재 한국시간 기준 offset 없는 datetime으로 저장한다.
- `ended_at`, `audio_url`, `audio_duration_seconds`, `conversation_title`, `deleted_at`은 `null`로 저장한다.
- 생성 직후 메시지가 하나도 없는 세션도 DB에는 저장된다.
- 메시지가 하나도 없는 세션은 대화 목록 조회와 대화 세션 상세 조회에서 반환하지 않는다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `conversationType` | string | O | 생성할 대화 세션 타입. `TEXT` 또는 `VOICE` |

```json
{
  "conversationType": "TEXT"
}
```

---

### 정상 응답 데이터
Status Code : 201

| 필드 | 타입 | 설명 |
|---|---:|---|
| `conversationSession.id` | number | 생성된 대화 세션 id |
| `conversationSession.conversationType` | string | 생성된 대화 세션 타입. `TEXT` 또는 `VOICE` |

```json
{
  "conversationSession": {
    "id": 1001,
    "conversationType": "TEXT"
  }
}
```

음성 대화 세션 생성 예시

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

Status Code : 404

현재 사용자의 마지막 활성 큐브 소유권이 존재하지 않는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```




## 대화 세션 삭제
- http 메서드: DELETE
- 엔드포인트: `/api/v1/users/me/conversation-sessions/{conversationSessionId}`
- 도메인: conversation

### API 설명

사용자가 텍스트 대화 또는 음성 대화 세션을 삭제할 때 호출한다.

대화 세션 row를 실제로 삭제하지 않고 `deleted_at`에 삭제 시각을 저장하는 소프트 딜리트 방식으로 처리한다.

---

### 처리 정책

- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 대화 세션만 삭제할 수 있다.
- 대화 메시지가 하나도 없는 빈 세션도 정상 삭제할 수 있다.
- 삭제된 세션은 대화 목록 조회와 대화 세션 상세 조회에서 제외된다.
- 이미 삭제된 세션에 대해 다시 삭제 요청을 보내면 중복 삭제로 보고 404: CONVERSATION_SESSION_NOT_FOUND를 반환한다.
- 세션이 존재하지 않거나 현재 사용자의 활성 큐브 소유권에 속하지 않는 세션이면 404: CONVERSATION_SESSION_NOT_FOUND를 반환한다.
- API 호출이 성공하면 `avatar_conversation_session.deleted_at`을 서버의 현재 한국시간 기준 offset 없는 datetime으로 저장한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `conversationSessionId` | number | O | 삭제할 대화 세션 id |

요청 예시: `/api/v1/users/me/conversation-sessions/1001`

---

### 요청 Body

없음

---

### 정상 응답 데이터
Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터
Status Code : 404

대화 세션이 존재하지 않거나, 현재 사용자의 활성 큐브 소유권에 속하지 않거나, 이미 삭제된 세션인 경우

```json
{
  "code": "CONVERSATION_SESSION_NOT_FOUND",
  "message": "삭제할 대화 세션을 찾을 수 없습니다."
}
```




## 대화 텍스트 보관
- http 메서드: PATCH
- 엔드포인트: `/api/v1/users/me/conversation-messages/{conversationMessageId}/save`
- 도메인: conversation

### API 설명

사용자가 아바타 텍스트 대화 메시지의 보관 버튼을 눌렀을 때 호출한다.

`conversationMessageId`를 기준으로 대화 메시지의 보관 여부를 토글한다.

---

### 처리 정책

- `sender_type = AVATAR`인 메시지만 보관할 수 있다.
- `sender_type = USER`인 메시지는 보관할 수 없으며 404: USER_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE을 반환한다.
- 텍스트 대화 세션(`conversation_type = TEXT`)에 속한 메시지만 보관할 수 있다.
- 음성 대화 세션(`conversation_type = VOICE`)에 속한 메시지는 보관할 수 없으며 404: VOICE_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE을 반환한다.
- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 대화 메시지만 보관할 수 있다.
- 삭제된 대화 세션(`deleted_at`이 null이 아닌 항목)에 속한 메시지는 찾을 수 없는 메시지로 처리하며 404: CONVERSATION_MESSAGE_NOT_FOUND를 반환한다.
- 메시지가 존재하지 않거나 현재 사용자의 활성 큐브 소유권에 속하지 않는 메시지이면 404: CONVERSATION_MESSAGE_NOT_FOUND를 반환한다.
- 대화 메시지의 `status`는 필터링하지 않고 `ALLOWED`, `BLOCKED` 모두 보관할 수 있다.
- `content` 값은 별도로 검사하지 않는다.
- `is_text_saved = false`인 메시지에 요청하면 `true`로 변경한다.
- `is_text_saved = true`인 메시지에 요청하면 `false`로 변경한다.
- API 호출이 성공하면 변경된 `is_text_saved` 값을 응답으로 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `conversationMessageId` | number | O | 보관 여부를 토글할 대화 메시지 id |

요청 예시: `/api/v1/users/me/conversation-messages/5006/save`

---

### 요청 Body

없음

---

### 정상 응답 데이터
Status Code : 200

| 필드 | 타입 | 설명 |
|---|---:|---|
| `conversationMessage.id` | number | 보관 여부가 변경된 대화 메시지 id |
| `conversationMessage.isTextSaved` | boolean | 변경 후 보관 여부 |

보관 처리된 경우

```json
{
  "conversationMessage": {
    "id": 5006,
    "isTextSaved": true
  }
}
```

보관 해제된 경우

```json
{
  "conversationMessage": {
    "id": 5006,
    "isTextSaved": false
  }
}
```

---

### 오류 응답 데이터
Status Code : 404

대화 메시지가 존재하지 않거나, 현재 사용자의 활성 큐브 소유권에 속하지 않거나, 삭제된 대화 세션에 속한 메시지인 경우

```json
{
  "code": "CONVERSATION_MESSAGE_NOT_FOUND",
  "message": "대화 메시지를 찾을 수 없습니다."
}
```

사용자 메시지를 보관하려는 경우

```json
{
  "code": "USER_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE",
  "message": "사용자 대화는 보관이 불가합니다."
}
```

음성 대화 세션에 속한 메시지를 보관하려는 경우

```json
{
  "code": "VOICE_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE",
  "message": "음성 대화는 보관이 불가합니다."
}
```




## 대화 메시지 응답
- http 메서드: POST
- 엔드포인트: `/api/v1/users/me/conversation-sessions/{conversationSessionId}/messages`
- 도메인: conversation

### API 설명

사용자가 텍스트 또는 음성 대화 세션 안에서 아바타에게 메시지를 전송했을 때 호출한다.

백엔드는 사용자 메시지를 저장하고, OpenAI GPT로 아바타 응답을 생성한 뒤 아바타 메시지도 함께 저장해 반환한다.

사용자는 텍스트만 보내거나, 텍스트와 이미지를 함께 보낼 수 있다.

---

### 처리 정책

- `content`는 필수이며 빈 문자열은 허용하지 않는다.
- `imageUrls`는 선택값이며, 보내지 않으면 이미지가 없는 요청으로 처리한다.
- `imageUrls`는 최대 5개까지 허용한다.
- `content`가 빈 문자열이거나 `imageUrls`가 6개 이상이면 공통 400: INVALID_REQUEST를 반환한다.
- `conversationSessionId`에 해당하는 대화 세션이 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 경우에만 메시지를 전송할 수 있다.
- 대화 세션이 존재하지 않거나, 현재 사용자의 활성 큐브 소유권에 속하지 않거나, 삭제된 세션이면 404: CONVERSATION_SESSION_NOT_FOUND를 반환한다.
- `ACTIVE` 상태의 텍스트 또는 음성 대화 세션에서 메시지를 전송할 수 있다.
- 음성 대화 세션에서는 사용자 음성 인식 결과를 `content`에 담아 텍스트와 동일한 형식으로 요청한다.
- 텍스트 대화 세션이 `NOT_ACTIVE` 상태이면 `ACTIVE` 상태로 변경한 뒤 메시지 전송을 진행한다.
- 음성 대화 세션이 `NOT_ACTIVE` 상태이면 404: CONVERSATION_SESSION_NOT_FOUND를 반환한다.
- 프론트는 갤러리 조회 API로 받은 Blob URL만 전송한다.
- 백엔드는 이미지 URL의 갤러리 소유 여부를 별도로 검증하지 않는다.
- 삭제된 갤러리 이미지 URL이 전송된 것으로 확인되면 404: CONVERSATION_IMAGE_NOT_FOUND를 반환한다.
- 전송된 이미지는 아바타 응답 생성을 위한 일회성 입력으로만 사용하며 DB에 보관하지 않는다.
- 사용자 메시지와 아바타 메시지를 각각 `avatar_conversation_message`에 저장한다.
- 사용자 메시지의 `sender_type`은 `USER`로 저장한다.
- 아바타 메시지의 `sender_type`은 `AVATAR`로 저장한다.
- 두 메시지의 `status`는 `ALLOWED`로 저장한다.
- 두 메시지의 `is_text_saved`는 `false`로 저장한다.
- 두 메시지의 `sent_at`은 서버의 현재 한국시간 기준 offset 없는 datetime으로 저장한다.
- `sequence_number`는 현재 세션의 마지막 메시지 순서 다음 값부터 사용자 메시지, 아바타 메시지 순서로 저장한다.
- 응답의 `userMessage.imageUrls`에는 요청으로 받은 `imageUrls`를 그대로 반환한다.
- 응답의 `avatarMessage`에는 `imageUrls`를 반환하지 않는다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `conversationSessionId` | number | O | 메시지를 전송할 대화 세션 id |

요청 예시: `/api/v1/users/me/conversation-sessions/1/messages`

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `content` | string | O | 사용자가 입력한 메시지 내용 |
| `imageUrls` | string[] | X | 아바타 응답 생성에 함께 사용할 이미지 URL 목록. 최대 5개 |

텍스트만 보내는 경우

```json
{
	"content": "오늘 뭐 하고 있었어?"
}
```

이미지를 함께 보내는 경우

```json
{
  "content": "이 사진어때?",
  "imageUrls": [
    "https://haniumstorage.blob.core.windows.net/hanium/album_image_001.jpeg"
  ]
}
```

여러 이미지를 함께 보내는 경우

```json
{
  "content": "이 사진들 어때?",
  "imageUrls": [
    "https://haniumstorage.blob.core.windows.net/hanium/stage_capture/1/501/3f8a.jpg",
    "https://haniumstorage.blob.core.windows.net/hanium/track_capture/1/601/a91b.jpg"
  ]
}
```

---

### 정상 응답 데이터
Status Code : 201

| 필드 | 타입 | 설명 |
|---|---:|---|
| `userMessage.id` | number | 저장된 사용자 메시지 id |
| `userMessage.senderType` | string | 사용자 메시지 발신자 타입. `USER` |
| `userMessage.content` | string | 사용자 메시지 내용 |
| `userMessage.imageUrls` | string[] | 요청으로 전달한 이미지 URL 목록 |
| `userMessage.sequenceNumber` | number | 사용자 메시지 순서 |
| `userMessage.sentAt` | string(date-time) | 사용자 메시지 전송 시각 |
| `avatarMessage.id` | number | 저장된 아바타 메시지 id |
| `avatarMessage.senderType` | string | 아바타 메시지 발신자 타입. `AVATAR` |
| `avatarMessage.content` | string | GPT로 생성된 아바타 응답 내용 |
| `avatarMessage.sequenceNumber` | number | 아바타 메시지 순서 |
| `avatarMessage.sentAt` | string(date-time) | 아바타 메시지 전송 시각 |

텍스트만 보낸 경우

```json
{
  "userMessage": {
    "id": 5025,
    "senderType": "USER",
    "content": "오늘 뭐 하고 있었어?",
    "imageUrls": [],
    "sequenceNumber": 13,
    "sentAt": "2026-07-29T18:25:02"
  },
  "avatarMessage": {
    "id": 5005,
    "senderType": "AVATAR",
    "content": "오늘 연습하고 있었어! 너는 오늘 하루 어떻게 보냈어?",
    "sequenceNumber": 14,
    "sentAt": "2026-07-29T18:25:02"
  }
}
```

이미지를 함께 보낸 경우

```json
{
  "userMessage": {
    "id": 5026,
    "senderType": "USER",
    "content": "이 사진들 어때?",
    "imageUrls": [
      "https://haniumstorage.blob.core.windows.net/hanium/stage_capture/1/501/3f8a.jpg",
      "https://haniumstorage.blob.core.windows.net/hanium/track_capture/1/601/a91b.jpg"
    ],
    "sequenceNumber": 15,
    "sentAt": "2026-07-29T18:27:02"
  },
  "avatarMessage": {
    "id": 5006,
    "senderType": "AVATAR",
    "content": "사진 분위기 진짜 좋다! 무대 조명 색감이 특히 예뻐.",
    "sequenceNumber": 16,
    "sentAt": "2026-07-29T18:27:02"
  }
}
```

---

### 오류 응답 데이터
Status Code : 404

대화 세션이 존재하지 않거나, 현재 사용자의 활성 큐브 소유권에 속하지 않거나, 삭제된 세션인 경우

```json
{
  "code": "CONVERSATION_SESSION_NOT_FOUND",
  "message": "대화 세션을 찾을 수 없습니다."
}
```

삭제된 갤러리 이미지 URL이 전송된 것으로 확인된 경우

```json
{
  "code": "CONVERSATION_IMAGE_NOT_FOUND",
  "message": "전송할 이미지를 찾을 수 없습니다."
}
```


## 대화 세션 상태 저장
- http 메서드: PATCH
- 엔드포인트: `/api/v1/users/me/conversation-sessions/{conversationSessionId}`
- 도메인: conversation

### API 설명

사용자가 대화를 진행하다가 뒤로 가기를 누르거나 대화 화면을 종료할 때 호출한다.

대화 세션의 종료 시각과 상태를 저장한다.

음성 대화 세션인 경우 프론트에서 전달한 실제 오디오 파일을 Azure Blob Storage에 저장하고, 생성된 Blob URL과 오디오 길이를 대화 세션에 저장한다.

---

### 처리 정책

- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 대화 세션만 상태를 저장할 수 있다.
- 삭제된 대화 세션은 상태를 저장할 수 없다.
- 세션의 `ended_at`은 서버에서 생성한 현재 한국 시간으로 저장한다.
- 세션의 `status`는 `NOT_ACTIVE`로 변경한다.
- `conversation_title`이 `null`이고 대화 메시지가 존재하면, 해당 세션의 첫 대화 메시지 2개를 기준으로 제목을 생성해 저장한다.
- 대화 메시지가 없으면 제목 생성은 하지 않고 세션 상태만 저장한다.
- 텍스트 대화 세션은 요청 Body 없이 상태 저장이 가능하다.
- 음성 대화 세션은 `audio`, `audioDurationSeconds`를 반드시 함께 전송해야 한다.
- 음성 대화 세션의 오디오 파일은 Azure Blob Storage에 저장한다.
- 오디오 파일 저장 경로는 `conversation_audio/{userId}/{conversationSessionId}/{UUID}.{확장자}` 형식을 사용한다.
- 저장된 오디오 URL은 `avatar_conversation_session.audio_url`에 저장한다.
- 프론트에서 전달한 `audioDurationSeconds`는 `avatar_conversation_session.audio_duration_seconds`에 저장한다.


---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| conversationSessionId | number | O | 상태를 저장할 대화 세션 id |

```json
{
  "conversationSessionId": 1001
}
```

요청 예시: `/api/v1/users/me/conversation-sessions/1001`

---

### 요청 Body

Content-Type : `multipart/form-data`

| 필드 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| audio | file | X | 음성 대화 세션의 녹음 파일 |
| audioDurationSeconds | number | X | 음성 파일 전체 길이, 초 단위 |

텍스트 대화 세션인 경우 요청 Body를 보내지 않는다.

음성 대화 세션인 경우 `audio`, `audioDurationSeconds`를 모두 전송한다.

```text
audio: <오디오 파일>
audioDurationSeconds: 300
```

허용 오디오 형식은 M4A(`audio/mp4`, `audio/x-m4a`), MP3(`audio/mpeg`), WAV(`audio/wav`), WebM(`audio/webm`)이다.

---

### 정상 응답 데이터

Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터

Status Code : 404

대화 세션이 존재하지 않거나, 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 세션이 아니거나, 이미 삭제된 세션이면 404를 반환한다.

```json
{
  "code": "CONVERSATION_SESSION_NOT_FOUND",
  "message": "대화 세션을 찾을 수 없습니다."
}
```




## 대화 보관함 조회
- http 메서드: GET
- 엔드포인트: `/api/v1/users/me/conversation-archive`
- 도메인: conversation

### API 설명

대화 보관함 화면에 진입했을 때 호출한다.

현재 사용자가 마지막으로 접근한 활성 큐브에서 보관한 아바타 텍스트 대화 메시지를 조회한다.

---

### 처리 정책

- 현재 사용자의 `ACTIVE` 큐브 소유권 중 `is_last_accessed = true`인 소유권에 속한 대화 메시지만 조회한다.
- 조건에 맞는 큐브 소유권이 존재하지 않으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- `avatar_conversation_message.sender_type = AVATAR`이고 `is_text_saved = true`인 텍스트 대화 메시지만 반환한다.
- 음성 대화 메시지와 사용자가 보낸 메시지는 반환하지 않는다.
- 삭제되지 않은 대화 세션(`deleted_at IS NULL`)에 속한 메시지만 반환한다.
- 대화 세션의 `status`가 `ACTIVE` 또는 `NOT_ACTIVE`인지와 관계없이 반환한다.
- 대화 메시지의 차단 상태는 조회 조건으로 사용하지 않는다.
- 보관한 메시지는 `sent_at` 내림차순으로 정렬하고, 같은 시각이면 메시지 `id` 내림차순으로 정렬한다.
- 페이지네이션 없이 전체 보관 메시지를 반환한다.
- 보관한 메시지가 없으면 `savedTexts`를 빈 배열로 반환한다.
- 날짜/시간 값은 한국시간 기준 offset 없는 ISO 8601 형식으로 반환한다.

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
Status Code : 200

| 필드 | 타입 | 설명 |
|---|---:|---|
| `savedTexts` | array | 보관한 대화 메시지 목록 |
| `savedTexts[].id` | number | 대화 메시지 id |
| `savedTexts[].conversationSessionId` | number | 메시지가 속한 대화 세션 id |
| `savedTexts[].content` | string | 보관한 아바타 대화 내용 |
| `savedTexts[].sequenceNumber` | number | 대화 세션 내 메시지 순서 |
| `savedTexts[].sentAt` | string(date-time) | 메시지 전송 시각 |

```json
{
  "savedTexts": [
    {
      "id": 5006,
      "conversationSessionId": 1001,
      "content": "오늘 하루는 어땠어? 힘든 일은 없었지?",
      "sequenceNumber": 6,
      "sentAt": "2026-07-29T15:30:02"
    },
    {
      "id": 4982,
      "conversationSessionId": 995,
      "content": "오늘 무대 정말 멋졌어!",
      "sequenceNumber": 12,
      "sentAt": "2026-07-28T20:10:00"
    }
  ]
}
```

---

### 오류 응답 데이터
Status Code : 404

현재 사용자의 마지막 접근 `ACTIVE` 큐브 소유권이 존재하지 않는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```




## 대화 보관함 삭제
- http 메서드: DELETE
- 엔드포인트: `/api/v1/users/me/conversation-messages/{conversationMessageId}/unsave`
- 도메인: conversation

### API 설명

대화 보관함에서 사용자가 보관한 대화 메시지를 삭제했을 때 호출한다.

대화 메시지 row를 삭제하지 않고 `is_text_saved`를 `false`로 변경하여 보관을 해제한다.

---

### 처리 정책

- `conversationMessageId`에 해당하는 대화 메시지를 조회한다.
- 현재 사용자의 `ACTIVE` 큐브 소유권 중 `is_last_accessed = true`인 소유권에 속한 메시지만 보관 해제할 수 있다.
- 현재 보관 중인 메시지(`is_text_saved = true`)만 보관 해제할 수 있다.
- API 호출이 성공하면 `avatar_conversation_message.is_text_saved`를 `false`로 변경한다.
- 대화 메시지 row와 대화 세션 row는 삭제하지 않는다.
- 메시지가 존재하지 않거나, 현재 사용자의 마지막 접근 활성 큐브 소유권에 속하지 않거나, 이미 `is_text_saved = false`이면 404: CONVERSATION_MESSAGE_NOT_FOUND를 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `conversationMessageId` | number | O | 보관 해제할 대화 메시지 id |

요청 예시: `/api/v1/users/me/conversation-messages/5006/unsave`

---

### 요청 Body

없음

---

### 정상 응답 데이터
Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터
Status Code : 404

대화 메시지를 찾을 수 없거나 보관 해제할 수 없는 메시지인 경우

```json
{
  "code": "CONVERSATION_MESSAGE_NOT_FOUND",
  "message": "대화 메시지를 찾을 수 없습니다."
}
```
