## 대화 메시지 응답
- http 메서드: post
- domain: conversation
- endpoint: api/v1/users/me/conversation-sessions/{conversationSessionId}/messages

### API 설명

사용자가 텍스트 또는 음성 대화 세션 안에서 아바타에게 메시지를 전송했을 때 호출한다.

백엔드는 사용자 메시지를 저장하고, OpenAI GPT로 아바타의 텍스트 응답을 생성한 뒤 아바타 메시지도 함께 저장해 반환한다.

텍스트 대화에서는 아바타의 텍스트 응답만 반환하고, 음성 대화에서는 텍스트 응답을 음성으로 합성해 Azure Blob Storage에 저장한 오디오 URL도 함께 반환한다.

사용자는 텍스트만 보내거나, 텍스트와 이미지를 함께 보낼 수 있다.

---

### 처리 정책

- `conversationType`은 필수이며 `TEXT`, `VOICE` 중 하나만 허용한다.
- 요청의 `conversationType`은 `conversationSessionId`에 해당하는 세션의 `conversation_type`과 일치해야 한다.
- 요청의 대화 유형과 저장된 세션 유형이 일치하지 않으면 404: CONVERSATION_SESSION_NOT_FOUND를 반환한다.
- `content`는 필수이며 빈 문자열은 허용하지 않는다.
- `imageUrls`는 선택값이며, 보내지 않으면 이미지가 없는 요청으로 처리한다.
- `imageUrls`는 최대 5개까지 허용한다.
- `content`가 빈 문자열이거나 `imageUrls`가 6개 이상이면 공통 400: INVALID_REQUEST를 반환한다.
- `conversationSessionId`에 해당하는 대화 세션이 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 경우에만 메시지를 전송할 수 있다.
- 대화 세션이 존재하지 않거나, 현재 사용자의 활성 큐브 소유권에 속하지 않거나, 삭제된 세션이면 404: CONVERSATION_SESSION_NOT_FOUND를 반환한다.
- `ACTIVE` 상태의 텍스트 또는 음성 대화 세션에서 메시지를 전송할 수 있다.
- 음성 대화 세션에서는 사용자 음성 인식 결과를 `content`에 담아 텍스트 대화와 동일한 형식으로 요청한다.
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
- `TEXT` 요청에서는 아바타 응답 음성을 생성하지 않으며 `avatarMessage.audioUrl`을 `null`로 반환한다.
- `VOICE` 요청에서는 GPT로 생성된 아바타 응답 텍스트를 OpenAI 음성 합성 API로 변환한다.
- 음성 합성에는 특정 실존 인물의 음성을 복제하거나 모사하지 않고, 서비스에서 제공·허용하는 여성 TTS 음성을 사용한다.
- 생성한 음성 파일은 Azure Blob Storage에 업로드하고 해당 Blob URL을 `avatarMessage.audioUrl`로 반환한다.
- 텍스트와 음성 대화의 응답 구조는 동일하며 `avatarMessage.audioUrl`은 항상 포함한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `conversationSessionId` | number | O | 메시지를 전송할 대화 세션 id |

요청 예시: `/api/v1/users/me/conversation-sessions/1/messages`

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `conversationType` | string | O | 대화 유형. `TEXT` 또는 `VOICE` |
| `content` | string | O | 사용자가 입력한 메시지 또는 사용자 음성의 인식 결과 |
| `imageUrls` | string[] | X | 아바타 응답 생성에 함께 사용할 이미지 URL 목록. 최대 5개 |

텍스트 대화에서 텍스트만 보내는 경우

```json
{
  "conversationType": "TEXT",
  "content": "오늘 뭐 하고 있었어?"
}
```

텍스트 대화에서 이미지를 함께 보내는 경우

```json
{
  "conversationType": "TEXT",
  "content": "이 사진들 어때?",
  "imageUrls": [
    "https://haniumstorage.blob.core.windows.net/hanium/stage_capture/1/501/3f8a.jpg",
    "https://haniumstorage.blob.core.windows.net/hanium/track_capture/1/601/a91b.jpg"
  ]
}
```

음성 대화에서 음성 인식 결과를 보내는 경우

```json
{
  "conversationType": "VOICE",
  "content": "오늘 뭐 하고 있었어?"
}
```

---

### 정상 응답 데이터

Status Code : 201

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `userMessage.id` | number | 저장된 사용자 메시지 id |
| `userMessage.senderType` | string | 사용자 메시지 발신자 타입. `USER` |
| `userMessage.content` | string | 사용자 메시지 또는 음성 인식 결과 |
| `userMessage.imageUrls` | string[] | 요청으로 전달한 이미지 URL 목록 |
| `userMessage.sequenceNumber` | number | 사용자 메시지 순서 |
| `userMessage.sentAt` | string(date-time) | 사용자 메시지 전송 시각 |
| `avatarMessage.id` | number | 저장된 아바타 메시지 id |
| `avatarMessage.senderType` | string | 아바타 메시지 발신자 타입. `AVATAR` |
| `avatarMessage.content` | string | GPT로 생성된 아바타 응답 내용 |
| `avatarMessage.audioUrl` | string | null | 음성 대화에서 생성한 아바타 응답 음성의 Blob URL. 텍스트 대화에서는 `null` |
| `avatarMessage.sequenceNumber` | number | 아바타 메시지 순서 |
| `avatarMessage.sentAt` | string(date-time) | 아바타 메시지 전송 시각 |

텍스트 대화인 경우

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
    "audioUrl": null,
    "sequenceNumber": 14,
    "sentAt": "2026-07-29T18:25:02"
  }
}
```

음성 대화인 경우

```json
{
  "userMessage": {
    "id": 5026,
    "senderType": "USER",
    "content": "오늘 뭐 하고 있었어?",
    "imageUrls": [],
    "sequenceNumber": 15,
    "sentAt": "2026-07-29T18:27:02"
  },
  "avatarMessage": {
    "id": 5006,
    "senderType": "AVATAR",
    "content": "오늘 연습하고 있었어! 너는 오늘 하루 어떻게 보냈어?",
    "audioUrl": "https://haniumstorage.blob.core.windows.net/hanium/conversation_audio/1/12/550e8400-e29b-41d4-a716-446655440000.mp3",
    "sequenceNumber": 16,
    "sentAt": "2026-07-29T18:27:02"
  }
}
```

---

### 오류 응답 데이터

Status Code : 404

대화 세션이 존재하지 않거나, 요청의 대화 유형과 세션 유형이 일치하지 않거나, 현재 사용자의 활성 큐브 소유권에 속하지 않거나, 삭제된 세션인 경우

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