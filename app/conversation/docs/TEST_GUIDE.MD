# 대화 도메인 테스트 가이드

테스트 파일: `app/conversation/tests/test_conversation.py`
실행: `.venv\Scripts\python.exe -m pytest app/conversation/tests/test_conversation.py -q`
최종 실행 결과: 85 passed (2026-09-22)

DB는 `Mock(spec=Session)` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
실제 MySQL, OpenAI, Azure Blob Storage에는 접속하지 않습니다.

외부 의존성은 서비스 모듈이 참조하는 이름으로 패치합니다.

```text
app.conversation.service.generate_avatar_reply        GPT 응답 텍스트
app.conversation.service.generate_avatar_reply_audio  TTS 음성 합성 (VOICE 전용)
app.conversation.service.upload_conversation_audio    Azure Blob 업로드 (VOICE 전용)
```

---

## 대화 메시지 응답 — `POST /api/v1/users/me/conversation-sessions/{conversationSessionId}/messages`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_reply_conversation_message_saves_user_and_avatar_messages | TEXT 세션, 마지막 순서 12 | 201 + 응답 JSON 전체 일치, USER 13·AVATAR 14 저장, `audioUrl=null` | PASS |
| 정상 변형 | test_reply_conversation_message_allows_active_voice_session | VOICE 세션 + TTS·업로드 성공 | 201, `audioUrl` 에 Blob URL 반환 | PASS |
| 정상 변형 | test_reply_conversation_message_uploads_voice_audio_to_blob_storage | VOICE 세션 | GPT 응답 텍스트로 TTS 호출, 업로드 인자가 `audio/mpeg` / `user_id` / `conversation_session_id` | PASS |
| 정상 변형 | test_reply_conversation_message_does_not_generate_audio_for_text_session | TEXT 세션 | `audioUrl=null`, TTS·업로드 호출 없음 | PASS |
| 정상 변형 | test_reply_conversation_message_allows_not_active_session | TEXT 세션이 `NOT_ACTIVE` | 201, 세션 상태가 `ACTIVE` 로 변경, `ended_at` 유지 | PASS |
| 정상 변형 | test_reply_conversation_message_passes_image_urls_to_gpt | 이미지 2개 동봉 | 201, GPT에 URL 전달, `userMessage.imageUrls` 그대로 반환, `avatarMessage` 에는 없음 | PASS |
| 오류 | test_reply_conversation_message_returns_404_when_conversation_type_differs | 요청 `TEXT` / 세션 `VOICE` | 404 CONVERSATION_SESSION_NOT_FOUND, 조회 SQL에 `conversation_type = 'TEXT'` 포함 | PASS |
| 오류 | test_reply_conversation_message_returns_404_for_not_active_voice_session | VOICE 세션이 `NOT_ACTIVE` | 404 CONVERSATION_SESSION_NOT_FOUND | PASS |
| 오류 | test_reply_conversation_message_returns_404_for_unknown_or_deleted_session | 세션 조회 결과 없음 | 404 CONVERSATION_SESSION_NOT_FOUND, 저장 없음 | PASS |
| 오류 | test_reply_conversation_message_returns_404_for_deleted_image_url | 삭제된 갤러리 이미지 URL | 404 CONVERSATION_IMAGE_NOT_FOUND, GPT 호출 없음 | PASS |
| 요청 검증 | test_reply_conversation_message_returns_400_without_conversation_type | `conversationType` 누락 | 400 INVALID_REQUEST, DB 조회 없음 | PASS |
| 요청 검증 | test_reply_conversation_message_returns_400_for_unknown_conversation_type | `conversationType="VIDEO"` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_reply_conversation_message_rejects_blank_content_with_common_400 | `content="   \n"` | 400 INVALID_REQUEST | PASS |
| 경계값 | test_reply_conversation_message_rejects_more_than_five_images | `imageUrls` 6개 | 400 INVALID_REQUEST | PASS |
| 예외 | test_reply_conversation_message_does_not_save_when_gpt_fails | GPT 호출 실패 | 500, 저장·롤백 없음(트랜잭션 시작 전) | PASS |
| 예외 | test_reply_conversation_message_does_not_save_when_voice_synthesis_fails | TTS 실패 | 500 INTERNAL_SERVER_ERROR, 메시지 저장 없음 | PASS |
| 예외 | test_reply_conversation_message_does_not_save_when_audio_upload_fails | Blob 업로드 실패 | 500, 메시지 저장 없음 | PASS |
| 예외 | test_reply_conversation_message_rolls_back_when_commit_fails | commit 실패 | 500, rollback 1회 | PASS |
| 맥락 | test_reply_conversation_message_passes_recent_history_to_gpt | 직전 메시지 2개 존재 | GPT 3번째 인자로 오래된 순서의 메시지 목록 전달 | PASS |
| 맥락 | test_reply_conversation_message_queries_only_recent_allowed_history | 맥락 조회 SQL 검증 | 세션 id 조건, `status='ALLOWED'`, `sequence_number DESC`, `LIMIT 30` | PASS |
| 맥락 | test_reply_conversation_message_sends_history_as_user_and_assistant_turns | USER/AVATAR 메시지 혼합 | `system → user → assistant → user(현재)` 순서, 시스템 프롬프트에 맥락 지시 포함 | PASS |
| 맥락 | test_reply_conversation_message_sends_only_system_and_user_without_history | 이전 대화 없음 | `system → user` 두 개만 전달 | PASS |
| 문서 | test_reply_conversation_message_swagger_contract | OpenAPI 스키마 | 응답 코드 `{201, 404}`, `security` 에 `HTTPBearer` | PASS |

### 대화 맥락 전달

GPT 호출 시 **직전 메시지 최대 30개(`CONVERSATION_HISTORY_SIZE`, 대화 15턴)** 를 함께 넘깁니다.
DB에서는 `sequence_number DESC` 로 최신순 조회한 뒤, GPT에는 대화 흐름대로 오래된 순서로
뒤집어 전달합니다. 저장된 `USER` 메시지는 `user`, `AVATAR` 메시지는 `assistant` 발화로 변환합니다.

```text
system     맥락 유지 지시가 포함된 제니 페르소나 프롬프트
user       (이전) 오늘 뭐 했어?
assistant  (이전) 연습하고 있었어!
...        최대 30개
user       (현재) 사용자 메시지 + 이미지
```

`status='BLOCKED'` 메시지는 맥락에서 제외합니다. 맥락 조회는 `db.scalars` 를 쓰므로
기존 `db.scalar.side_effect` 순서에는 영향을 주지 않습니다.

### 부분 저장 방지

음성 생성과 업로드는 **`db.commit()` 전에** 수행합니다. 그래서 TTS나 Blob 업로드가 실패하면
사용자·아바타 메시지가 하나도 저장되지 않습니다. `..._does_not_save_when_voice_synthesis_fails`
와 `..._does_not_save_when_audio_upload_fails` 가 `db.add.assert_not_called()` 로 이를 고정합니다.

### 검증하지 않은 항목

- **실제 GPT 응답 품질과 TTS 음성 품질**은 외부 API 결과라 검증 대상이 아닙니다.
  호출 인자(모델·음성·지시문은 서비스 모듈 상수)와 반환값 처리만 확인합니다.
- **맥락이 실제로 응답 품질을 개선하는지**는 모델 동작이라 검증하지 않고, 전달되는
  입력의 순서·역할·개수만 확인합니다.
- **Blob URL의 실제 경로 형식**(`conversation_audio/{userId}/{sessionId}/{uuid}.mp3`)은
  `app/core/blob_storage.py` 의 `upload_conversation_audio` 책임이라 이 API 테스트에서는
  전달 인자만 검증하고 URL 조립은 검증하지 않습니다.
- **이미지 URL의 갤러리 소유 여부**는 명세상 백엔드가 검증하지 않으므로 테스트하지 않고,
  삭제된 이미지 판별만 확인합니다.
- **"세션 없음" vs "다른 사용자 세션" vs "삭제된 세션"** 은 Mock DB에서 모두 `None` 이라
  구분하지 않고 같은 404로 처리되는 것만 확인했습니다.

---

## 그 밖의 대화 API

같은 파일에 대화 세션 목록·상세 조회, 세션 생성·삭제·저장, 보관 메시지 저장·해제,
신고 생성 테스트가 함께 있습니다(총 81개). 해당 API들의 명세 문서가 아직 없어 이 가이드에는
정리하지 않았습니다.

---

## 미션 진행도 반영 — `POST /api/v1/users/me/conversation-sessions/{conversationSessionId}/messages`

autouse fixture `mission_progress` 가 `app.conversation.service.increase_mission_progress` 를 patch 합니다.
진행도 계산 자체는 `app/mission/docs/TEST_GUIDE.MD` 의 미션 진행도 반영 섹션에서 검증합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_reply_conversation_message_increases_conversation_mission_progress | 메시지 응답 성공 | `CONVERSATION` 으로 1회 호출 | PASS |
| 오류 | test_reply_conversation_message_does_not_increase_progress_when_404 | 대화 세션 없음 | 404 + 호출 없음 | PASS |
