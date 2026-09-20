# 블록체인 연동 테스트 가이드

테스트 파일: `app/blockchain/tests/test_blockchain_signing.py`, `app/blockchain/tests/test_blockchain_client.py`,
`app/blockchain/tests/test_blockchain_mint.py`, `app/blockchain/tests/test_blockchain_transfer.py`,
`app/blockchain/tests/test_blockchain_notifications.py`, `app/blockchain/tests/test_blockchain_backfill.py`
실행: `.venv\Scripts\python.exe -m pytest app/blockchain/tests -q`
최종 실행 결과: 84 passed (2026-09-15)

DB는 `Mock(spec=Session)` 으로 대체하고, 블록체인 서버 호출은 `patch.object` 로 대체합니다.
Argon2id·JWT와 마찬가지로 **HMAC 서명과 승인 JWT는 모킹하지 않고 실제로 계산**해 검증합니다.

이 문서의 테스트와 별개로, 구현 단계마다 실제 기동한 블록체인 서버(`localhost:3100`)와
MySQL로 전 과정을 한 번씩 실행해 확인했습니다. 결과는 각 절의 "실환경 확인"에 적었습니다.

---

## 요청 서명·승인 JWT — `app/blockchain/tests/test_blockchain_signing.py` (21)

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_build_canonical_string_joins_five_lines_with_uppercase_method | POST + JSON 본문 | 메서드 대문자, 5줄, 본문 sha256 | PASS |
| 정상 변형 | test_build_canonical_string_hashes_empty_body | 빈 본문 | 빈 바이트의 sha256 사용 | PASS |
| 정책 | test_build_canonical_string_sorts_and_encodes_query | 배열·공백·슬래시 쿼리 | 키·값 정렬 후 URL 인코딩 | PASS |
| 정상 변형 | test_build_canonical_string_keeps_path_when_query_is_empty | 쿼리 없음 | 경로만 사용 | PASS |
| 정상 | test_build_signature_headers_signs_canonical_string | 요청 서명 | 헤더 4종, 서명이 canonical과 일치 | PASS |
| 정책 | test_build_signature_headers_uses_new_nonce_every_call | 두 번 호출 | nonce가 매번 다름 | PASS |
| 정상 | test_issue_approval_token_contains_mint_claims | MINT | `purpose`·`tokenId`·`userId`·`cubeId`·`to` | PASS |
| 정상 | test_issue_approval_token_contains_transfer_claims | TRANSFER | `tradeId`·`sellerUserId`·`buyerUserId`·`from`·`to` | PASS |
| 경계값 | test_issue_approval_token_stays_within_thirty_minutes | 만료 시간 | 30분 이하 (서버 강제 상한) | PASS |
| 정책 | test_issue_approval_token_uses_new_jti_every_call | 두 번 발급 | `jti` 가 매번 다름 | PASS |
| 정상 | test_verify_webhook_signature_accepts_valid_signature | 올바른 서명 | 통과 | PASS |
| 정상 변형 | test_verify_webhook_signature_accepts_lowercase_header_names | 소문자 헤더 | 통과 | PASS |
| 오류 | test_verify_webhook_signature_rejects_modified_body | 본문 변조 | 거부 | PASS |
| 오류 | test_verify_webhook_signature_rejects_other_secret | 다른 secret | 거부 | PASS |
| 오류 | test_verify_webhook_signature_rejects_unknown_key_id | 모르는 key id | 거부 | PASS |
| 오류 | test_verify_webhook_signature_rejects_expired_timestamp | 301초 전 | 거부 | PASS |
| 경계값 | test_verify_webhook_signature_accepts_timestamp_inside_window | 295초 전 | 통과 | PASS |
| 오류 | test_verify_webhook_signature_rejects_non_numeric_timestamp | 숫자가 아닌 timestamp | 거부 | PASS |
| 오류 | test_verify_webhook_signature_rejects_missing_headers | 서명 헤더 누락 | 거부 | PASS |
| 오류 | test_verify_webhook_signature_rejects_different_path | 경로 불일치 | 거부 | PASS |

### 실환경 확인

- 블록체인 서버의 `canonical-request.ts` 를 Node로 실행해 얻은 canonical string·서명과
  파이썬 결과를 3개 케이스(JSON 본문 / 빈 본문 / 배열 쿼리 + 한글 본문)로 대조해 **전부 일치**.
- 실제 서버에 `POST /internal/v1/wallets` 를 우리 서명으로 호출해 200, 무서명 호출은 401
  `HMAC_MISSING_HEADERS` 를 확인.
- 승인 JWT는 처음에 401 `APPROVAL_JWT_INVALID` 로 거절됐고, 서버가 secret을 base64url
  **디코딩한 바이트**로 검증한다는 점을 확인해 동일하게 맞춘 뒤 통과.

---

## 클라이언트·이미지 — `app/blockchain/tests/test_blockchain_client.py` (20)

HTTP 전송은 `_send` 를 대체해 호출 인자를 검증합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_ensure_wallet_returns_address | 지갑 확보 | 주소 반환, 경로·본문 확인 | PASS |
| 정책 | test_request_includes_signature_headers | 모든 요청 | 서명 헤더 4종 + Content-Type, 승인 JWT 없음 | PASS |
| 정상 | test_prepare_metadata_sends_fixed_grade_and_benefit | 메타데이터 준비 | `publicGrade=UNSPECIFIED`, `benefitReferenceId=NONE` | PASS |
| 정상 변형 | test_get_metadata_status_reads_ready_flag | 상태 재확인 | `ready` 반환 | PASS |
| 정상 | test_request_mint_sends_approval_token_with_mint_claims | Mint 접수 | 본문 4필드 + MINT 승인 JWT | PASS |
| 정상 | test_request_transfer_sends_approval_token_with_transfer_claims | Transfer 접수 | 본문 5필드 + TRANSFER 승인 JWT | PASS |
| 정상 변형 | test_get_operation_uses_operation_path | 작업 조회 | 경로 확인, 빈 본문 | PASS |
| 정상 변형 | test_get_nft_uses_token_path | NFT 조회 | 경로 확인 | PASS |
| 오류 | test_request_raises_blockchain_error_for_error_response | 409 응답 | code·status 보존 | PASS |
| 오류 | test_request_raises_blockchain_error_when_server_is_unreachable | 연결 실패 | `BLOCKCHAIN_UNREACHABLE` | PASS |
| 정상 | test_wait_for_confirmation_returns_confirmed_operation | 즉시 확정 | 작업 정보 반환 | PASS |
| 정상 변형 | test_wait_for_confirmation_polls_until_confirmed | REQUESTED→PENDING→COMPLETED | 3회 폴링 후 반환 | PASS |
| 오류 | test_wait_for_confirmation_raises_for_failed_status | FAILED | `OPERATION_NOT_CONFIRMED` | PASS |
| 오류 | test_wait_for_confirmation_raises_for_review_required_status | REVIEW_REQUIRED | 예외 | PASS |
| 경계값 | test_wait_for_confirmation_returns_none_after_timeout | 제한 시간 0 | `None` 반환, 1회만 조회 | PASS |
| 정상 | test_prepare_product_image_returns_base64_and_mime_type | PNG | base64 + `image/png` | PASS |
| 정상 변형 | test_prepare_product_image_detects_jpeg_webp_gif | JPEG·WebP·GIF | 매직 바이트로 형식 판별 | PASS |
| 경계값 | test_prepare_product_image_rejects_oversized_image | 2 MiB 초과 | `IMAGE_TOO_LARGE` | PASS |
| 오류 | test_prepare_product_image_rejects_unsupported_format | PDF | `IMAGE_TYPE_NOT_SUPPORTED` | PASS |
| 오류 | test_prepare_product_image_reports_download_failure | 다운로드 실패 | `IMAGE_DOWNLOAD_FAILED` | PASS |

### 실환경 확인

지갑 → 메타데이터(`ready=true`) → Mint 접수 → `ONCHAIN_CONFIRMED` → NFT 조회까지
`tokenId=9001` 로 전 과정 성공. 소유자·컨트랙트 주소·tokenURI 모두 확인.

---

## 큐브 인증 Mint — `app/blockchain/tests/test_blockchain_mint.py` (16)

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_to_token_id_converts_serial_number | `NO.0026`·`NO.0100` | 26·100 | PASS |
| 오류 | test_to_token_id_rejects_unsupported_serial_number | `ARZ-CUBE-0002` | `SERIAL_NUMBER_NOT_SUPPORTED` | PASS |
| 경계값 | test_to_token_id_rejects_out_of_range_value | `NO.10001` | `TOKEN_ID_OUT_OF_RANGE` | PASS |
| 경계값 | test_to_token_id_rejects_zero | `NO.0000` | `TOKEN_ID_OUT_OF_RANGE` | PASS |
| 정상 | test_mint_cube_nft_records_confirmed_operation | 정상 발행 | `CONFIRMED`, tokenId·tx_hash·소유자 기록 | PASS |
| 정상 | test_mint_cube_nft_sends_wallet_address_and_token_id | 정상 발행 | 지갑 주소·토큰 번호·멱등키 전달 | PASS |
| 정책 | test_mint_cube_nft_uses_official_product_image | 이미지 선택 | `cube.product_image_url` 공식 이미지 사용(`cube.id`, `deleted_at IS NULL`) | PASS |
| 정상 변형 | test_mint_cube_nft_checks_metadata_status_when_not_ready_yet | `ready=false` | 상태 재조회 후 진행 | PASS |
| 오류 | test_mint_cube_nft_records_failure_for_unsupported_serial_number | 시리얼 형식 오류 | `FAILED`, tokenId `NULL`, 접수 안 함 | PASS |
| 오류 | test_mint_cube_nft_records_failure_when_product_image_is_missing | 이미지 없음 | `FAILED`, 지갑 호출 안 함 | PASS |
| 오류 | test_mint_cube_nft_records_failure_when_metadata_is_not_ready | 계속 미준비 | `FAILED`, 접수 안 함 | PASS |
| 오류 | test_mint_cube_nft_records_failure_when_request_is_rejected | 접수 거절 | `FAILED` + 사유 기록 | PASS |
| 오류 | test_mint_cube_nft_records_failure_for_unexpected_error | 예상 못한 예외 | `FAILED` + `UNEXPECTED_ERROR` | PASS |
| 경계값 | test_mint_cube_nft_keeps_requested_status_after_timeout | 확정 대기 초과 | `REQUESTED` 유지, 사유 없음 | PASS |
| 정책 | test_mint_cube_nft_records_failure_when_final_owner_differs | 소유자 불일치 | `FAILED` + `OWNER_MISMATCH` | PASS |
| 예외 | test_mint_cube_nft_never_raises_to_caller | 모든 실패 | 예외를 밖으로 던지지 않음 | PASS |

`app/cube/tests/test_cube.py` 에는 인증 API가 커밋 후 Mint를 호출하는지(인자 포함),
인증 실패 시 호출하지 않는지 확인하는 테스트 2개가 있습니다.

### 실환경 확인

큐브 4번(`NO.0044`) 인증 → 소유권·친밀도·1레벨 보상 저장 → Mint `CONFIRMED`.
응답은 기존과 동일하게 `{"cubeOwnershipId": 8}`.

---

## 구매 확정 Transfer — `app/blockchain/tests/test_blockchain_transfer.py` (7)

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_transfer_cube_nft_returns_certificate_values | 정상 이전 | 인증서 5개 값 반환, NFT 1회 조회 | PASS |
| 정상 | test_transfer_cube_nft_records_confirmed_operation | 정상 이전 | `CONFIRMED`, trade_id·tx_hash 기록 | PASS |
| 정상 | test_transfer_cube_nft_sends_seller_and_buyer_addresses | 지갑 확보 | 판매자·구매자 순서로 조회해 from·to 전달 | PASS |
| 오류 | test_transfer_cube_nft_raises_for_unsupported_serial_number | 시리얼 형식 오류 | 예외 + `FAILED` | PASS |
| 오류 | test_transfer_cube_nft_records_failure_when_request_is_rejected | 접수 거절 | 예외 + `FAILED` | PASS |
| 경계값 | test_transfer_cube_nft_raises_timeout_and_keeps_requested_status | 확정 대기 초과 | `CONFIRMATION_TIMEOUT`, 상태는 `REQUESTED` 유지 | PASS |
| 정책 | test_transfer_cube_nft_raises_when_final_owner_is_not_buyer | 소유자 불일치 | `OWNER_MISMATCH`, NFT 조회 안 함 | PASS |

`app/market/tests/test_market.py` 에 구매 확정 API 쪽 테스트 14개가 있습니다: 실제 값 인증서 생성,
판매자·시리얼 전달, **외부 호출 전 거래 잠금 해제 순서**, 409 세 종류, 500, 확정된 작업 재사용,
구매 확정 후 큐브 `OWNED` 복귀. 표는 `app/market/docs/TEST_GUIDE.MD` 의 구매 확정 절에 있습니다.

### 실환경 확인

거래 1번(`NO.0031`)에서 판매자 사전 Mint → 구매 확정 → `COMPLETED`.
인증서에 실제 값(`localhost` / `ERC-721` / `31` / 실제 컨트랙트·tx·ipfs URI)이 저장되고,
최종 온체인 소유자가 구매자 지갑과 일치.

---

## 완료 알림 수신 — `app/blockchain/tests/test_blockchain_notifications.py` (12)

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_receive_notification_confirms_requested_operation | 대기 중 작업 | 200, `CONFIRMED` 로 확정, `duplicate=false` | PASS |
| 정상 변형 | test_receive_notification_returns_duplicate_for_recorded_notification | 같은 알림 재수신 | 200 + `duplicate=true`, 저장 없음 | PASS |
| 정책 | test_receive_notification_keeps_confirmed_operation_unchanged | 이미 확정된 작업 | 결과를 덮어쓰지 않음 | PASS |
| 정상 변형 | test_receive_notification_accepts_unknown_operation | 모르는 작업 | 200으로 수락(재전송 중단) | PASS |
| 정상 변형 | test_receive_notification_confirms_transfer_operation | TRANSFER 알림 | `CONFIRMED` | PASS |
| 정책 | test_receive_notification_locks_operation_row | 조회 SQL | `operation_id` 조건 + `FOR UPDATE` | PASS |
| 오류 | test_receive_notification_returns_401_without_signature | 서명 없음 | 401 `INVALID_WEBHOOK_SIGNATURE`, DB 조회 없음 | PASS |
| 오류 | test_receive_notification_returns_401_for_wrong_secret | 다른 secret | 401 | PASS |
| 오류 | test_receive_notification_returns_401_when_body_is_modified | 본문 변조 | 401 | PASS |
| 요청 검증 | test_receive_notification_returns_400_when_field_is_missing | `txHash` 누락 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_receive_notification_returns_400_for_broken_json | JSON 파싱 실패 | 400 INVALID_REQUEST | PASS |
| 문서 | test_receive_notification_swagger_contract | OpenAPI | `{200, 400, 401}`, 인증 의존성 없음 | PASS |

### 실환경 확인

백엔드를 8000 포트로 띄운 상태에서 큐브 5번을 인증하자 블록체인 서버가 실제로
`POST /api/v1/internal/blockchain/notifications` 를 호출해 **200**을 받았고,
작업 기록의 `notification_id` 가 채워졌습니다. 양방향 HMAC이 모두 실증됐습니다.

---

## 백필 Mint — `app/blockchain/tests/test_blockchain_backfill.py` (8)

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_backfill_mints_unminted_cube_to_current_owner | 미발행 큐브 | `MINTED`, 현재 소유자 앞으로 발행 | PASS |
| 정상 변형 | test_backfill_skips_cube_already_owned_by_same_wallet | 같은 소유자 보유 | `ALREADY_MINTED`, 발행 안 함 | PASS |
| 정책 | test_backfill_stops_cube_owned_by_other_wallet | 다른 소유자 보유 | `OWNED_BY_OTHER`, 발행 안 함 | PASS |
| 오류 | test_backfill_skips_unsupported_serial_number | 시리얼 형식 오류 | `SKIPPED`, 조회·발행 안 함 | PASS |
| 오류 | test_backfill_reports_failure_when_blockchain_call_fails | 연결 실패 | `FAILED` | PASS |
| 오류 | test_backfill_reports_failure_when_owner_is_not_confirmed | 발행 후 미확인 | `FAILED` | PASS |
| 정상 변형 | test_backfill_processes_every_active_ownership | 소유권 2건 | 두 건 모두 처리 | PASS |
| 정책 | test_backfill_queries_only_active_ownerships | 조회 SQL | `ACTIVE`, 삭제·`DISABLED` 제외, `cube.id ASC` | PASS |

### 실환경 확인

목데이터 9건 실행 → `MINTED 6, OWNED_BY_OTHER 1, ALREADY_MINTED 2`.
이미 발행된 큐브는 건너뛰고, 구매 확정으로 소유자가 바뀐 큐브는 손대지 않아 멱등성 확인.

---

## 검증하지 않은 항목

- **실제 Polygon Amoy 네트워크**는 로컬 하드햇 노드로 대체했습니다. 서명·확정·재시도 정책은
  같지만 수수료·지연·RBF 동작은 확인하지 않았습니다.
- **Web3Auth 수탁 지갑과 Pinata/Filebase IPFS**는 `fake` 어댑터로 동작했습니다.
  실제 provider 연동은 상대 팀 인수 항목입니다.
- **확정 대기 120초의 실제 소요 시간**은 로컬(`CONFIRMATION_BLOCKS_REQUIRED=1`) 기준이라
  운영 환경에서 다시 측정해야 합니다.
- **동시 요청**(같은 거래에 대한 구매 확정 중복 호출)은 거래 행 잠금과 멱등키로 막지만,
  Mock DB로는 재현할 수 없어 생성된 SQL의 `FOR UPDATE` 로만 확인했습니다.
- **완료 알림 재시도 backoff**는 블록체인 서버 책임이라 우리 쪽에서는 중복 수신 처리만
  확인했습니다.
