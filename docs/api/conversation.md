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
- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 대화 세션만 조회한다.
- 삭제된 대화 세션(`deleted_at`이 null이 아닌 항목)은 반환하지 않는다.
- 대화가 한 번도 이루어지지 않아 메시지가 없는 세션은 반환하지 않는다.
- 세션의 마지막 메시지 기준 최신순으로 정렬한다.
- 텍스트 대화 조회에서는 마지막 메시지의 `content`를 반환한다.
- 음성 대화 조회에서는 마지막 메시지의 `content`를 `null`로 반환한다.
- 음성 대화 조회에서는 세션의 `audioUrl`, `audioDurationSeconds`를 함께 반환한다.
- 조회 결과가 없으면 빈 배열과 페이지 정보를 200으로 반환한다.

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





## 대화 세션 상세 조회
- http 메서드: get
- 엔드포인트: api/v1/users/me/conversation-sessions/{conversationSessionId}

### API 설명

텍스트 대화에서 세션을 클릭하면 호출된다. 음성대화에서는 불가능하다. 만약 음성대화 세션으로 대화 세션 상세 조회를 하면 404를 반환한다. 또한 대화가 한 번도 오가지 않은 대화 세션도 404로 처리한다.

세션에서 나눴던 대화와 대화 전송 시각을 반환한다. 전체 대화를 한번에 반환하고, sequenceNumber를 기준으로 내림차순 정렬해서 반환한다.

- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 텍스트 대화 세션만 조회할 수 있다.
- 삭제된 대화 세션(`deleted_at`이 null이 아닌 항목)은 조회하지 않는다.
- `conversation_type = VOICE`인 세션 id로 요청하면 음성 대화 상세 조회 불가 404를 반환한다.
- 대화 메시지의 `status`는 필터링하지 않고 `ALLOWED`, `BLOCKED` 모두 반환한다.
- `sentAt`은 한국시간 기준 offset 없는 date-time으로 반환한다.

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

- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 대화 세션만 삭제할 수 있다.
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




## 대화 텍스트 보관
- http 메서드: patch
- 엔드포인트: api/v1/users/me/conversation-messages/{conversationMessageId}/save

### API 설명

아바타의 응답에 대해 보관함에 저장을 시도하면 호출한다.

대화 메시지 id를 받아서 보관 여부를 토글한다.

- `sender_type = AVATAR`인 메시지만 보관할 수 있다.
- `sender_type = USER`인 메시지는 보관할 수 없다.
- 텍스트 대화 세션(`conversation_type = TEXT`)에 속한 메시지만 보관할 수 있다.
- 음성 대화 세션(`conversation_type = VOICE`)에 속한 메시지는 보관할 수 없다.
- 삭제된 대화 세션(`deleted_at`이 null이 아닌 항목)에 속한 메시지는 찾을 수 없는 메시지로 처리한다.
- 대화 메시지의 `status`는 필터링하지 않고 `ALLOWED`, `BLOCKED` 모두 보관할 수 있다.
- `content` 값은 별도로 검사하지 않는다.
- `is_text_saved = false`인 메시지에 요청하면 `true`로 변경한다.
- `is_text_saved = true`인 메시지에 요청하면 `false`로 변경한다.

---

### 요청 Query

---

### 요청 Path

```json
{
	"conversationMessageId": 5006
}
```

요청 예시: api/v1/users/me/conversation-messages/5006/save

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 200

```json
{
  "conversationMessage": {
    "id": 5006,
    "isTextSaved": true
  }
}
```

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

```json
{
  "code": "CONVERSATION_MESSAGE_NOT_FOUND",
  "message": "대화 메시지를 찾을 수 없습니다."
}
```

- 존재하지 않는 메시지 id, 삭제된 대화 세션에 속한 메시지인 경우 위 응답을 반환한다.

```json
{
  "code": "USER_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE",
  "message": "사용자 대화는 보관이 불가합니다."
}
```

- `sender_type = USER`인 메시지 id로 요청한 경우 위 응답을 반환한다.

```json
{
  "code": "VOICE_CONVERSATION_MESSAGE_SAVE_NOT_AVAILABLE",
  "message": "음성 대화는 보관이 불가합니다."
}
```

- `conversation_type = VOICE`인 세션에 속한 메시지 id로 요청한 경우 위 응답을 반환한다.




## 대화 메시지 응답
- http 메서드: post
- 엔드포인트: api/v1/users/me/conversation-sessions/{conversationSessionId}/messages

### API 설명

사용자가 텍스트 또는 음성으로 아바타에게 말을 걸면 호출된다.

백엔드에서 사용자 대화를 GPT로 처리해서 응답과 그 시간을 반환한다. 이때 사용자는 이미지도 같이 보낼 수 있는데 앱 내부 갤러리에 존재하는 사진에 한해서만 전송 가능하다. 갤러리 조회를 이용해서 사용자가 선택할 이미지를 조회할 수 있다.

또한 사용자는 최대 5장의 사진까지 전송이 가능하다.

- `content`는 필수이며 빈 문자열은 허용하지 않는다.
- `imageUrls`는 선택값이며, 보내지 않으면 이미지가 없는 요청으로 처리한다.
- `imageUrls`는 최대 5개까지 허용한다.
- `content`가 빈 문자열이거나 `imageUrls`가 6개 이상이면 공통 `400 INVALID_REQUEST`를 반환한다.
- 프론트는 갤러리 조회 API로 받은 Blob URL만 전송한다.
- 백엔드는 이미지 URL의 갤러리 소유 여부를 별도로 검증하지 않는다.
- 삭제된 갤러리 이미지 URL이 전송된 것으로 확인되면 404를 반환한다.
- 전송된 이미지는 아바타 응답 생성을 위한 일회성 입력으로만 사용하며 DB에 보관하지 않는다.
- 사용자가 보낸 이미지 URL은 아바타 응답 메시지에는 포함하지 않는다.

---

### 요청 Query

---

### 요청 Path

```json
{
	"conversationSessionId": 1
}
```

요청 예시: api/v1/users/me/conversation-sessions/1/messages

---

### 요청 Body

```json
{
	"content": "오늘 뭐 하고 있었어?"
}
```

```json
{
  "content": "이 사진어때?",
  "imageUrls": [
    "https://haniumstorage.blob.core.windows.net/hanium/album_image_001.jpeg"
  ]
}
```

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

```json
{
  "code": "CONVERSATION_SESSION_NOT_FOUND",
  "message": "대화 세션을 찾을 수 없습니다."
}
```

```json
{
  "code": "CONVERSATION_IMAGE_NOT_FOUND",
  "message": "전송할 이미지를 찾을 수 없습니다."
}
```

- 삭제된 갤러리 이미지 URL이 전송된 것으로 확인된 경우 위 응답을 반환한다.




## 대화 세션 상태 저장
- http 메서드: patch
- 엔드포인트: api/v1/users/me/conversation-sessions/{conversationSessionId}

### API 설명

사용자가 대화를 진행하다가 뒤로 가기를 누르면 호출한다.

conversation_title이 null일 때만 해당 세션의 첫 대화 메시지 2개를 GPT에 전달해 대화 제목을 생성하고 저장한다.

호출할 때마다 ended_at을 현재 한국 시간으로 갱신하고, 세션 상태를 NOT_ACTIVE로 변경한다.

음성 대화인 경우 프론트에서 전달한 실제 오디오 파일을 Azure Blob Storage에 저장하고, 생성된 Blob URL을 `avatar_conversation_session.audio_url`에 저장한다.

오디오 파일 저장 경로는 `conversation_audio/{userId}/{conversationSessionId}/{UUID}.{확장자}` 형식을 사용한다.

프론트에서 전달한 `audioDurationSeconds`는 `avatar_conversation_session.audio_duration_seconds`에 저장한다.

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

음성 대화 세션 종료 시에는 JSON이 아니라 `multipart/form-data` 형식으로 전송한다.

```text
audio: <오디오 파일>
audioDurationSeconds: 300
```

- `audio`: 프론트가 녹음한 실제 음성 파일
  - 허용 형식: M4A(`audio/mp4`, `audio/x-m4a`), MPEG/MP3(`audio/mpeg`), WAV(`audio/wav`), WebM(`audio/webm`)
- `audioDurationSeconds`: 음성 파일의 전체 길이, 초 단위

텍스트 대화 세션 종료 시에는 오디오 파일이 존재하지 않으므로 요청 body를 보내지 않는다.

```json
{
}
```

텍스트 대화 세션 종료여서 오디오 파일이 존재하지 않을 때에는 요청 body를 `{}`로 보내거나 아예 전송하지 않는다.

음성 대화 세션 종료인 경우 `audio`, `audioDurationSeconds`를 반드시 전송한다.

---

### 정상 응답 데이터

Status Code : 204

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "CONVERSATION_SESSION_NOT_FOUND",
  "message": "대화 세션을 찾을 수 없습니다."
}
```
