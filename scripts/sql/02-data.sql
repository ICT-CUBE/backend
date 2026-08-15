SET NAMES utf8mb4;

INSERT INTO `user` (`id`, `email`, `password_hash`, `login_provider`, `provider_user_id`, `nickname`, `profile_character_img_url`, `chat_violation_count`, `status`) VALUES
(1, 'mina@arzone.local', '$2b$12$mockhashmina', 'EMAIL', NULL, '미나', 'CHAR_MINA', 0, 'ACTIVE'),
(2, 'jun@arzone.local', NULL, 'GOOGLE', 'google-jun-001', '준', 'CHAR_JUN', 0, 'ACTIVE'),
(3, 'seo@arzone.local', NULL, 'APPLE', 'apple-seo-001', '서아', 'CHAR_SEO', 1, 'ACTIVE');

INSERT INTO `auth_session` (`id`, `user_id`, `token_jti`, `status`, `issued_at`, `expires_at`, `device_id`) VALUES
(1, 1, 'jti-mock-0001', 'ACTIVE', '2026-08-07 09:00:00', '2026-08-14 09:00:00', 'ios-mina'),
(2, 2, 'jti-mock-0002', 'ACTIVE', '2026-08-07 09:10:00', '2026-08-14 09:10:00', 'android-jun'),
(3, 3, 'jti-mock-0003', 'REVOKED', '2026-08-06 20:00:00', '2026-08-13 20:00:00', 'ios-seo');

INSERT INTO `cube` (`id`, `serial_number`, `product_name`, `ownership_code_hash`, `artist_name`, `status`) VALUES
(1, 'ARZ-CUBE-0001', 'arzone Cube A', 'mock_hash_cube_001', 'ARZONE', 'OWNED'),
(2, 'ARZ-CUBE-0002', 'arzone Cube B', 'mock_hash_cube_002', 'ARZONE', 'OWNED'),
(3, 'ARZ-CUBE-0003', 'arzone Cube C', 'mock_hash_cube_003', 'ARZONE', 'UNREGISTERED');

INSERT INTO `cube_verification` (`id`, `user_id`, `cube_id`, `verification_status`, `code_expires_at`, `verified_at`) VALUES
(1, 1, 1, 'SUCCESS', '2026-08-07 10:10:00', '2026-08-07 09:15:00'),
(2, 2, 2, 'SUCCESS', '2026-08-07 10:20:00', '2026-08-07 09:25:00'),
(3, 3, 3, 'PENDING', '2026-08-07 11:00:00', NULL);

INSERT INTO `cube_ownership` (`id`, `user_id`, `cube_id`, `avatar_nickname`, `ownership_status`, `is_last_accessed`, `acquired_at`) VALUES
(1, 1, 1, '루미', 'ACTIVE', TRUE, '2026-08-07 09:20:00'),
(2, 2, 2, '아리', 'ACTIVE', TRUE, '2026-08-07 09:30:00'),
(3, 3, 3, '조이', 'REVOKED', FALSE, '2026-08-06 18:00:00');

INSERT INTO `reward_item` (`id`, `name`, `reward_type`, `description`, `reward_count`) VALUES
(1, '첫 대화 보상', 'AVATAR_FIRST_TALK', '아바타와 첫 대화 완료', 1),
(2, '친밀도 50 포인트', 'AFFINITY_POINT', '미션 완료 친밀도 보상', 50),
(3, 'AR 뱃지', 'BADGE', 'AR 스테이지 감상 뱃지', 1);

INSERT INTO `level` (`id`, `reward_item_id`, `level`, `level_xp`, `level_name`) VALUES
(1, 1, 1, 0, 'Intro'),
(2, 2, 2, 100, 'Friend'),
(3, 3, 3, 300, 'Close');

INSERT INTO `affinity` (`id`, `cube_ownership_id`, `level_id`, `current_xp`) VALUES
(1, 1, 2, 120),
(2, 2, 1, 40),
(3, 3, 1, 10);

INSERT INTO `mission` (`id`, `reward_item_id`, `mission_type`, `title`, `description`, `mission_info`, `target_action`, `target_count`, `start_at`, `end_at`, `is_active`) VALUES
(1, 2, 'DAILY', '오늘의 대화', '아바타와 1회 대화하기', 'conversation_count=1', 'CONVERSATION', 1, '2026-08-07 00:00:00', '2026-08-07 23:59:59', TRUE),
(2, 3, 'DAILY', 'AR 스테이지 감상', 'AR 모드로 영상 보기', 'view_mode=AR', 'PLAY_MUSIC_VIDEO', 1, '2026-08-07 00:00:00', '2026-08-07 23:59:59', TRUE),
(3, 1, 'EVENT', '갤러리 방문', '앨범 갤러리 열기', 'open_gallery=1', 'OPEN_GALLERY', 1, '2026-08-01 00:00:00', '2026-08-31 23:59:59', TRUE);

INSERT INTO `mission_progress` (`id`, `cube_ownership_id`, `mission_id`, `current_count`, `status`, `reward_claimed`, `completed_at`, `claimed_at`) VALUES
(1, 1, 1, 1, 'REWARDED', TRUE, '2026-08-07 10:00:00', '2026-08-07 10:01:00'),
(2, 2, 2, 1, 'COMPLETED', FALSE, '2026-08-07 10:20:00', NULL),
(3, 3, 3, 0, 'IN_PROGRESS', FALSE, NULL, NULL);

INSERT INTO `user_reward` (`id`, `cube_ownership_id`, `reward_item_id`, `acquired_at`) VALUES
(1, 1, 1, '2026-08-07 09:35:00'),
(2, 1, 2, '2026-08-07 10:01:00'),
(3, 2, 3, '2026-08-07 10:25:00');

INSERT INTO `notification` (`id`, `user_id`, `notification_type`, `title`, `content`, `is_read`, `sent_at`, `read_at`) VALUES
(1, 1, 'MISSION', '미션 완료', '오늘의 대화 미션 보상을 받았어요.', TRUE, '2026-08-07 10:01:00', '2026-08-07 10:02:00'),
(2, 2, 'EVENT', '이벤트 진행 중', '8월 갤러리 방문 이벤트가 진행 중이에요.', FALSE, '2026-08-07 10:05:00', NULL),
(3, 3, 'MARKET', '거래 알림', '관심 상품에 새 거래가 등록됐어요.', FALSE, '2026-08-07 10:10:00', NULL);

INSERT INTO `user_setting` (`id`, `user_id`, `push_enabled`, `new_conversation_enabled`, `affinity_change_enabled`, `daily_mission_refresh_enabled`, `trade_completed_enabled`, `trade_offer_enabled`, `community_comment_notice_enabled`) VALUES
(1, 1, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(2, 2, TRUE, TRUE, FALSE, TRUE, TRUE, FALSE, TRUE),
(3, 3, FALSE, TRUE, TRUE, TRUE, FALSE, TRUE, FALSE);

INSERT INTO `album` (`id`, `title`, `artist_name`, `artist_company`, `track_count`, `track_total_second`, `description`, `cover_image_url`, `release_date`) VALUES
(1, 'ARZONE First Light', 'ARZONE', 'AR Studio', 3, 620, 'arzone 데뷔 앨범 목데이터', 'cover_first_light', '2026-07-01'),
(2, 'Virtual Stage', 'ARZONE', 'AR Studio', 3, 690, 'AR 공연 중심 앨범', 'cover_virtual_stage', '2026-08-01'),
(3, 'Memory Cube', 'ARZONE', 'AR Studio', 3, 600, '큐브와 추억을 담은 앨범', 'cover_memory_cube', '2026-09-01');

INSERT INTO `stage` (`id`, `album_id`, `title`, `description`, `video_url`, `video_type`, `thumbnail_url`, `duration_seconds`, `recorded_at`, `is_active`, `is_title_video`) VALUES
(1, 1, 'First Light MV', '타이틀 뮤직비디오', 'www.video_1.com', 'MUSIC_VIDEO', 'thumb_first_light', 210, '2026-07-01 18:00:00', TRUE, TRUE),
(2, 2, 'Virtual Stage Concert', 'AR 콘서트 영상', 'video_virtual_concert', 'CONCERT_VIDEO', 'thumb_virtual_concert', 540, '2026-08-01 20:00:00', TRUE, FALSE),
(3, 3, 'Memory Cube MV', '큐브 테마 뮤직비디오', 'video_memory_cube_mv', 'MUSIC_VIDEO', 'thumb_memory_cube', 230, '2026-09-01 18:00:00', TRUE, TRUE);

INSERT INTO `stage_session` (`id`, `cube_ownership_id`, `stage_id`, `started_at`, `ended_at`, `last_position_seconds`, `viewed_seconds`, `view_mode`, `status`) VALUES
(1, 1, 1, '2026-08-07 10:30:00', '2026-08-07 10:33:30', 210, 210, 'AR', 'COMPLETED'),
(2, 2, 2, '2026-08-07 10:40:00', NULL, 120, 120, 'NORMAL', 'PLAYING'),
(3, 3, 3, '2026-08-07 10:50:00', '2026-08-07 10:51:00', 60, 60, 'AR', 'CANCELLED');

INSERT INTO `stage_capture` (`id`, `stage_session_id`, `stage_capture_img_url`, `captured_position_seconds`, `captured_at`) VALUES
(1, 1, 'stage_capture_001', 45, '2026-08-07 10:30:45'),
(2, 2, 'stage_capture_002', 90, '2026-08-07 10:41:30'),
(3, 3, 'stage_capture_003', 30, '2026-08-07 10:50:30');

INSERT INTO `track` (`id`, `album_id`, `title`, `artist_name`, `audio_url`, `duration_seconds`, `lyrics`, `track_number`, `is_title_track`) VALUES
(1, 1, 'First Light', 'ARZONE', 'audio_first_light', 210, 'Mock lyrics for First Light', 1, TRUE),
(2, 2, 'Virtual Beat', 'ARZONE', 'audio_virtual_beat', 230, 'Mock lyrics for Virtual Beat', 1, TRUE),
(3, 3, 'Memory Cube', 'ARZONE', 'audio_memory_cube', 200, 'Mock lyrics for Memory Cube', 1, TRUE);

INSERT INTO `track_session` (`id`, `cube_ownership_id`, `track_id`, `started_at`, `ended_at`, `last_position_seconds`, `viewed_seconds`, `play_mode`, `status`) VALUES
(1, 1, 1, '2026-08-07 11:00:00', '2026-08-07 11:03:30', 210, 210, 'SPECIAL', 'COMPLETED'),
(2, 2, 2, '2026-08-07 11:10:00', NULL, 80, 80, 'NORMAL', 'PLAYING'),
(3, 3, 3, '2026-08-07 11:20:00', '2026-08-07 11:21:00', 60, 60, 'NORMAL', 'CANCELLED');

INSERT INTO `track_capture` (`id`, `track_session_id`, `track_capture_img_url`, `captured_position_seconds`, `captured_at`) VALUES
(1, 1, 'track_capture_001', 30, '2026-08-07 11:00:30'),
(2, 2, 'track_capture_002', 70, '2026-08-07 11:11:10'),
(3, 3, 'track_capture_003', 45, '2026-08-07 11:20:45');

INSERT INTO `album_image` (`id`, `album_id`, `title`, `image_type`, `album_contents_img_url`) VALUES
(1, 1, 'First Light 포토', 'ALBUM_IMAGE', 'album_image_first_light_001'),
(2, 2, '콘서트 스틸컷', 'CONCERT_STILLCUT', 'album_image_virtual_stage_001'),
(3, 3, '예줄 프레임', 'YEZUL_FRAME', 'album_image_memory_cube_001');

INSERT INTO `avatar_conversation_session` (`id`, `cube_ownership_id`, `conversation_type`, `started_at`, `ended_at`, `audio_url`, `audio_duration_seconds`, `conversation_title`, `status`) VALUES
(1, 1, 'TEXT', '2026-08-07 12:00:00', NULL, NULL, NULL, '오늘의 인사', 'ACTIVE'),
(2, 2, 'VOICE', '2026-08-07 12:10:00', '2026-08-07 12:12:00', 'voice_conversation_002', 120, '음성 대화', 'NOT_ACTIVE'),
(3, 3, 'TEXT', '2026-08-07 12:20:00', NULL, NULL, NULL, '앨범 이야기', 'ACTIVE');

INSERT INTO `avatar_conversation_message` (`id`, `conversation_session_id`, `sender_type`, `content`, `sequence_number`, `is_text_saved`, `status`, `violation_type`, `sent_at`) VALUES
(1, 1, 'USER', '안녕, 오늘 기분 어때?', 1, TRUE, 'ALLOWED', NULL, '2026-08-07 12:00:10'),
(2, 1, 'AVATAR', '좋아! 오늘은 First Light를 들어볼까?', 2, TRUE, 'ALLOWED', NULL, '2026-08-07 12:00:12'),
(3, 3, 'USER', '이 앨범 설명해줘.', 1, FALSE, 'BLOCKED', 'PROFANITY', '2026-08-07 12:20:10');

INSERT INTO `conversation_report` (`id`, `conversation_message_id`, `reason`, `detail_reason`) VALUES
(1, 1, 'INCORRECT_PERSONA', '페르소나 응답이 부정확한 예시'),
(2, 2, 'HALLUCINATION', '존재하지 않는 이벤트 언급'),
(3, 3, 'INAPPROPRIATE_EXPRESSION', '부적절한 표현 감지');

INSERT INTO `avatar_interaction_session` (`id`, `cube_ownership_id`, `started_at`, `ended_at`, `status`) VALUES
(1, 1, '2026-08-07 13:00:00', NULL, 'ACTIVE'),
(2, 2, '2026-08-07 13:10:00', '2026-08-07 13:15:00', 'COMPLETED'),
(3, 3, '2026-08-07 13:20:00', NULL, 'ACTIVE');

INSERT INTO `avatar_interaction_picture` (`id`, `interaction_session_id`, `picture_img_url`, `pictured_at`) VALUES
(1, 1, 'interaction_picture_001', '2026-08-07 13:01:00'),
(2, 2, 'interaction_picture_002', '2026-08-07 13:12:00'),
(3, 3, 'interaction_picture_003', '2026-08-07 13:21:00');

INSERT INTO `post` (`id`, `user_id`, `board_type`, `title`, `content`, `status`) VALUES
(1, 1, 'FREE', '첫 큐브 등록했어요', 'arzone 큐브 등록 후기입니다.', 'ACTIVE'),
(2, 2, 'CERTIFICATION', '인증 완료', '오늘 인증 성공했습니다.', 'ACTIVE'),
(3, 3, 'FREE', 'AR 모드 질문', 'AR 모드 사용 방법이 궁금합니다.', 'REPORTED');

INSERT INTO `post_media` (`id`, `post_id`, `post_image_url`) VALUES
(1, 1, 'https://example.com/mock/post-001.jpg'),
(2, 2, 'https://example.com/mock/post-002.jpg'),
(3, 3, 'https://example.com/mock/post-003.jpg');

INSERT INTO `comment` (`id`, `post_id`, `user_id`, `content`, `status`) VALUES
(1, 1, 2, '축하해요!', 'ACTIVE'),
(2, 2, 1, '인증 이미지 멋져요.', 'ACTIVE'),
(3, 3, 1, '설정에서 AR 권한을 확인해보세요.', 'ACTIVE');

INSERT INTO `post_like` (`id`, `post_id`, `user_id`, `is_liked`) VALUES
(1, 1, 2, TRUE),
(2, 2, 1, TRUE),
(3, 3, 1, FALSE);

INSERT INTO `comment_like` (`id`, `comment_id`, `user_id`, `is_liked`) VALUES
(1, 1, 1, TRUE),
(2, 2, 2, TRUE),
(3, 3, 3, FALSE);

INSERT INTO `market_product` (`id`, `cube_id`, `product_image_url`) VALUES
(1, 1, 'https://example.com/mock/market-product-001.jpg'),
(2, 2, 'https://example.com/mock/market-product-002.jpg'),
(3, 3, 'https://example.com/mock/market-product-003.jpg');

INSERT INTO `sell_listing` (`id`, `market_product_id`, `user_id`, `product_status`, `title`, `description`, `price`, `status`) VALUES
(1, 1, 1, '좋음', '퍼스트 큐브', '상태 좋은 큐브 판매합니다.', 35000, 'ACTIVE'),
(2, 2, 2, '미개봉', '스테이지 큐브', '미개봉 상품입니다.', 42000, 'SOLD'),
(3, 3, 3, '구성품 포함', '메모리 큐브', '구성품 모두 포함되어 있습니다.', 39000, 'ACTIVE');

INSERT INTO `trade` (`id`, `sell_listing_id`, `buyer_user_id`, `buyer_phone_number`, `buyer_address`, `total_price`, `paid_time`, `sent_time`, `shipped_time`, `delivered_time`, `completed_time`, `status`) VALUES
(1, 1, 2, '010-1111-2222', '서울특별시 강남구 테헤란로 1', 35000, '2026-08-07 14:30:00', NULL, NULL, NULL, NULL, 'PAID'),
(2, 2, 1, '010-3333-4444', '서울특별시 마포구 월드컵로 2', 42000, '2026-08-07 14:35:00', '2026-08-07 15:00:00', '2026-08-07 15:30:00', '2026-08-07 18:00:00', '2026-08-07 19:00:00', 'COMPLETED'),
(3, 3, 1, '010-5555-6666', '서울특별시 성동구 왕십리로 3', 39000, '2026-08-07 14:40:00', '2026-08-07 15:10:00', '2026-08-07 15:40:00', NULL, NULL, 'SHIPPING');

INSERT INTO `listing_media` (`id`, `sell_listing_id`, `image_url`) VALUES
(1, 1, 'https://example.com/mock/listing-001.jpg'),
(2, 2, 'https://example.com/mock/listing-002.jpg'),
(3, 3, 'https://example.com/mock/listing-003.jpg');

INSERT INTO `digital_certificate` (`id`, `trade_id`, `network`, `token_standard`, `token_id`, `contract_address`, `tx_hash`, `metadata_url`) VALUES
(1, 2, 'Polygon Amoy', 'ERC-721', '1000002', '0x0000000000000000000000000000000000000002', '0xmocktxhash000000000000000000000000000000000000000000000000000000000002', 'https://example.com/mock/certificates/2.json');
