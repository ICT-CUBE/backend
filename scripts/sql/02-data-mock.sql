SET NAMES utf8mb4;

INSERT INTO `user` (`id`, `email`, `password_hash`, `login_provider`, `provider_user_id`, `nickname`, `profile_character_img_url`, `chat_violation_count`, `status`) VALUES
(1, 'cube@arzone.com', 'abcdef12!', 'EMAIL', 'jennylover', '블링크', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(2, 'cubelove@arzone.com', 'afkfkf!', 'EMAIL', 'GDlover', '지드래곤짱', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(3, 'cubelove2323@arzone.com', 'afkfkf!', 'EMAIL', 'ROSElover', '로제짱', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE');

INSERT INTO `auth_session` (`id`, `user_id`, `token_jti`, `status`, `issued_at`, `expires_at`, `device_id`) VALUES
(1, 1, 'jti-mock-0001', 'ACTIVE', '2025-03-07 19:20:00', '2030-03-07 19:20:00', 'ios-jennylover');

INSERT INTO `cube` (`id`, `serial_number`, `product_name`, `ownership_code_hash`, `artist_name`, `status`) VALUES
(1, 'NO.0026', 'JENNIE RUBY CUBE', '9999', 'Jennie', 'OWNED'),
(2, 'NO.0031', 'BIGBANG MADE CUBE', '1111', 'Big Bang', 'OWNED'),
(3, 'NO.0022', 'ROSE ROISE CUBE', '2222', 'ROSE', 'OWNED');

INSERT INTO `cube_verification` (`id`, `user_id`, `cube_id`, `verification_status`, `code_expires_at`, `verified_at`) VALUES
(1, 1, 1, 'SUCCESS', '2025-03-14 19:25:00', '2025-03-07 19:25:00');

INSERT INTO `cube_ownership` (`id`, `user_id`, `cube_id`, `avatar_nickname`, `ownership_status`, `is_last_accessed`, `acquired_at`) VALUES
(1, 1, 1, '젠득이', 'ACTIVE', TRUE, '2025-03-07 19:30:00'),
(2, 2, 2, '지디득이', 'ACTIVE', TRUE, '2025-03-07 19:30:00'),
(3, 3, 3, '로제득이', 'ACTIVE', TRUE, '2025-03-07 19:30:00');

INSERT INTO `reward_item` (`id`, `name`, `reward_type`, `description`, `reward_count`) VALUES
(1, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 3포인트 제공', 3),
(2, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 5포인트 제공', 5),
(3, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 10포인트 제공', 10),
(4, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 20포인트 제공', 20),
(5, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 30포인트 제공', 30),
(6, '일일 대화 가능 횟수', 'CONVERSATION_COUNT', '하루에 대화 제한 30회', 30),
(7, '일일 대화 가능 횟수', 'CONVERSATION_COUNT', '하루에 대화 제한 100회', 100),
(8, '일일 대화 가능 횟수', 'CONVERSATION_COUNT', '하루에 대화 제한 없음', NULL),
(9, '멘트 종류', 'COMMENT_TYPE', '일상 멘트와 애칭 부르기', NULL),
(10, '멘트 종류', 'COMMENT_TYPE', '사적인 멘트와 비하인드 대화', NULL),
(11, '스페절 음성', 'SPECIAL_COMMENT', '시즌 한정 음성 추가', NULL),
(12, '아바타 선대화', 'AVATAR_FIRST_TALK', '아바타 선대화 1일 1회', 1),
(13, '아바타 선대화', 'AVATAR_FIRST_TALK', '아바타 선대화 1일 5회', 5),
(14, '뱃지', 'BADGE', 'BORN PINK 마스터', 1);

INSERT INTO `level` (`id`, `reward_item_id`, `level`, `level_xp`, `level_name`) VALUES
(1, 1, 1, 0, 'Intro'),
(2, 2, 2, 100, 'Friend'),
(3, 3, 3, 800, 'Close'),
(4, 6, 4, 2000, 'Special');

INSERT INTO `affinity` (`id`, `cube_ownership_id`, `level_id`, `current_xp`) VALUES
(1, 1, 3, 840);

INSERT INTO `mission` (`id`, `reward_item_id`, `mission_type`, `title`, `description`, `mission_info`, `target_action`, `target_count`, `start_at`, `end_at`, `is_active`) VALUES
(1, 2, 'DAILY', '홈 화면 방문하기', 'AR ZONE 접속', 'home_view=1', 'HOME_VIEW', 1, NULL, NULL, TRUE),
(2, 1, 'DAILY', '아바타와 대화하기', '텍스트 또는 음성 대화', 'avatar_chat=3', 'CONVERSATION', 3, NULL, NULL, TRUE),
(3, 2, 'DAILY', '음원 재생하기', '앨범에서 노래 한 곡 재생', 'play_music=1', 'ALBUM_PLAY', 1, NULL, NULL, TRUE),
(4, 5, 'DAILY', '아바타 현실 소환하기', 'AR 카메라 3회 사용', 'summon_avatar=3', 'SUMMON_AVATAR', 3, NULL, NULL, TRUE),
(5, 4, 'DAILY', '갤러리 둘러보기', '아무 사진 5회 열람', 'open_gallery=5', 'OPEN_GALLERY', 5, NULL, NULL, TRUE),
(6, 3, 'DAILY', '커뮤니티 글 업로드하기', '게시물 1회 업로드', 'write_post=1', 'COMMUNITY_POST', 1, NULL, NULL, TRUE),
(7, 14, 'EVENT', '[RUBY] 콘서트 인증 이벤트', '아무 뮤직 비디오 5회 시청', 'watch_music_video=5', 'PLAY_MUSIC_VIDEO', 5, '2026-06-12 00:00:00', '2025-09-18 23:59:59', TRUE);

INSERT INTO `mission_progress` (`id`, `cube_ownership_id`, `mission_id`, `current_count`, `status`, `reward_claimed`, `completed_at`, `claimed_at`) VALUES
(1, 1, 1, 1, 'REWARDED', TRUE, '2025-03-24 10:00:00', '2025-03-24 10:02:00'),
(2, 1, 2, 3, 'COMPLETED', FALSE, '2025-03-24 12:25:00', NULL),
(3, 1, 3, 0, 'IN_PROGRESS', FALSE, NULL, NULL),
(4, 1, 4, 3, 'REWARDED', TRUE, '2025-03-24 21:10:00', '2025-03-24 21:11:00'),
(5, 1, 5, 5, 'COMPLETED', FALSE, '2025-03-24 20:40:00', NULL),
(6, 1, 6, 0, 'IN_PROGRESS', FALSE, NULL, NULL),
(7, 1, 7, 5, 'REWARDED', TRUE, '2025-03-18 22:30:00', '2025-03-18 22:32:00');

INSERT INTO `user_reward` (`id`, `cube_ownership_id`, `reward_item_id`, `acquired_at`) VALUES
(1, 1, 2, '2025-03-24 10:02:00'),
(2, 1, 6, '2025-03-18 22:32:00'),
(3, 1, 5, '2025-03-24 21:11:00');

INSERT INTO `notification` (`id`, `user_id`, `notification_type`, `title`, `content`, `is_read`, `sent_at`, `read_at`) VALUES
(1, 1, 'MISSION', '미션 완료', '홈 화면 조회 미션 보상을 받았어요.', TRUE, '2025-03-24 10:01:00', '2025-03-24 10:02:00'),
(2, 1, 'EVENT', '이벤트 진행 중', '루비 앨범 이벤트가 진행 중이에요.', TRUE, '2025-03-18 09:00:00', '2025-03-18 09:15:00'),
(3, 1, 'MISSION', '친밀도 상승', '젠득이와의 친밀도가 Close 레벨이 되었어요.', TRUE, '2025-03-23 20:45:00', '2025-03-23 21:00:00'),
(4, 1, 'MARKET', '거래 알림', '거래 제안이 도착했어요.', FALSE, '2025-04-08 14:45:00', NULL);

INSERT INTO `user_setting` (`id`, `user_id`, `push_enabled`, `new_conversation_enabled`, `affinity_change_enabled`, `daily_mission_refresh_enabled`, `trade_completed_enabled`, `trade_offer_enabled`, `community_comment_notice_enabled`) VALUES
(1, 1, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE);

INSERT INTO `album` (`id`, `title`, `artist_name`, `artist_company`, `track_count`, `track_total_second`, `description`, `cover_image_url`, `release_date`) VALUES
(1, 'Ruby', 'Jennie', 'Odd Atelier', 15, 2498, '제니 정규 1집 루비 앨범', 'https://haniumstorage.blob.core.windows.net/hanium/album_cover_img/RUBY_cover_img.jpeg', '2025-03-07');

INSERT INTO `stage` (`id`, `album_id`, `title`, `description`, `video_url`, `video_type`, `thumbnail_url`, `duration_seconds`, `recorded_at`, `is_active`, `is_title_video`) VALUES
(1, 1, 'Mantra MV', 'Mantra 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_mantra.mp4', 'MUSIC_VIDEO', NULL, 136, '2024-10-11 13:00:00', TRUE, FALSE),
(2, 1, 'ZEN MV', 'ZEN 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_zen.mp4', 'MUSIC_VIDEO', NULL, 201, '2025-01-25 13:00:00', TRUE, FALSE),
(3, 1, 'Love Hangover MV', 'Love Hangover (feat. Dominic Fike) 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_lovehangover.mp4', 'MUSIC_VIDEO', NULL, 180, '2025-01-31 13:00:00', TRUE, FALSE),
(4, 1, 'ExtraL MV', 'ExtraL (feat. Doechii) 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_extral.mp4', 'MUSIC_VIDEO', NULL, 168, '2025-02-21 13:00:00', TRUE, FALSE),
(5, 1, 'like JENNIE MV', 'like JENNIE 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_likejennie.mp4', 'MUSIC_VIDEO', NULL, 124, '2025-03-07 13:00:00', TRUE, TRUE),
(6, 1, 'Handlebars MV', 'Handlebars (feat. Dua Lipa) 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_handlebars.mp4', 'MUSIC_VIDEO', NULL, 185, '2025-03-10 13:00:00', TRUE, FALSE),
(7, 1, 'Seoul City MV', 'Seoul City 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_seoul city.mp4', 'MUSIC_VIDEO', NULL, 164, '2025-04-26 13:00:00', TRUE, FALSE),
(8, 1, 'start a war Live Performance', 'start a war 콘서트 영상', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_concert_video/concert_zen.mp4', 'CONCERT_VIDEO', NULL, 165, '2025-03-28 13:00:00', TRUE, FALSE),
(9, 1, 'Love Hangover Live Performance', 'Love Hangover 콘서트 영상', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_concert_video/concert_lovehangover.mp4', 'CONCERT_VIDEO', NULL, 180, '2025-02-12 13:00:00', TRUE, FALSE),
(10, 1, 'like JENNIE Live Performance', 'like JENNIE 콘서트 영상', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_concert_video/concert_likejennie.mp4', 'CONCERT_VIDEO', NULL, 124, '2025-03-12 13:00:00', TRUE, FALSE),
(11, 1, 'Handlebars Live Performance', 'Handlebars 콘서트 영상', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_concert_video/concert_handlebars.mp4', 'CONCERT_VIDEO', NULL, 185, '2025-03-12 13:00:00', TRUE, FALSE);

INSERT INTO `stage_session` (`id`, `cube_ownership_id`, `stage_id`, `started_at`, `ended_at`, `last_position_seconds`, `viewed_seconds`, `view_mode`, `status`) VALUES
(1, 1, 5, '2025-03-07 19:30:00', '2025-03-07 19:32:04', 124, 124, 'AR', 'COMPLETED'),
(2, 1, 2, '2025-03-24 10:40:00', '2025-03-24 10:42:00', 120, 120, 'NORMAL', 'COMPLETED'),
(3, 1, 10, '2025-04-15 10:50:00', '2025-04-16 10:51:00', 60, 60, 'AR', 'CANCELLED');

-- INSERT INTO `stage_capture` (`id`, `stage_session_id`, `stage_capture_img_url`, `captured_position_seconds`, `captured_at`) VALUES

INSERT INTO `track` (`id`, `album_id`, `title`, `artist_name`, `audio_url`, `duration_seconds`, `lyrics`, `track_number`, `is_title_track`) VALUES
(1, 1, 'Intro : JANE (with FKJ)', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_intro.mp3', 98, 'lyrics', 1, FALSE),
(2, 1, 'like JENNIE', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_likejennie.mp3', 124, 'lyrics', 2, TRUE),
(3, 1, 'start a war', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_startawar.mp3', 165, 'lyrics', 3, FALSE),
(4, 1, 'Handlebars (feat. Dua Lipa)', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_handlebars.mp3', 184, 'lyrics', 4, FALSE),
(5, 1, 'with the IE (way up)', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_withtheie.mp3', 164, 'lyrics', 5, FALSE),
(6, 1, 'ExtraL (feat. Doechii)', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_extral.mp3', 168, 'lyrics', 6, FALSE),
(7, 1, 'Mantra', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_mantra.mp3', 136, 'lyrics', 7, FALSE),
(8, 1, 'Love Hangover (feat. Dominic Fike)', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_lovehangover.mp3', 180, 'lyrics', 8, FALSE),
(9, 1, 'ZEN', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_zen.mp3', 201, 'lyrics', 9, FALSE),
(10, 1, 'Damn Right (feat. Childish Gambino & Kali Uchis)', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_damnright.mp3', 195, 'lyrics', 10, FALSE),
(11, 1, 'F.T.S.', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_fts.mp3', 170, 'lyrics', 11, FALSE),
(12, 1, 'Filter', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_filter.mp3', 160, 'lyrics', 12, FALSE),
(13, 1, 'Seoul City', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_seoulcity.mp3', 164, 'lyrics', 13, FALSE),
(14, 1, 'Starlight', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_starlight.mp3', 185, 'lyrics', 14, FALSE),
(15, 1, 'twin', 'Jennie', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_track/song_twin.mp3', 175, 'lyrics', 15, FALSE);

INSERT INTO `track_session` (`id`, `cube_ownership_id`, `track_id`, `started_at`, `ended_at`, `last_position_seconds`, `viewed_seconds`, `play_mode`, `status`) VALUES
(1, 1, 2, '2025-03-08 11:00:00', '2025-03-08 11:02:04', 124, 124, 'SPECIAL', 'COMPLETED'),
(2, 1, 9, '2025-04-23 11:10:00', '2025-04-23 11:11:20', 80, 80, 'NORMAL', 'COMPLETED'),
(3, 1, 15, '2025-05-01 11:20:00', '2025-05-01 11:21:00', 60, 60, 'NORMAL', 'CANCELLED');

-- INSERT INTO `track_capture` (`id`, `track_session_id`, `track_capture_img_url`, `captured_position_seconds`, `captured_at`) VALUES

INSERT INTO `album_image` (`id`, `album_id`, `title`, `image_type`, `album_contents_img_url`) VALUES
(1, 1, 'ZEN 무대 01', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/ZEN(1).jpeg'),
(2, 1, 'ZEN 무대 02', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/ZEN(2).jpeg'),
(3, 1, 'ZEN 무대 03', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/ZEN(3).jpeg'),
(4, 1, 'ZEN 무대 04', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/ZEN(4).jpeg'),
(5, 1, 'ZEN 무대 05', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/ZEN(5).jpeg'),
(6, 1, 'ZEN 무대 06', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/ZEN(6).jpeg'),
(7, 1, 'ZEN 무대 07', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/ZEN(7).jpeg'),
(8, 1, 'ZEN 무대 08', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/ZEN(8).jpeg'),
(9, 1, 'like JENNIE 무대 01', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/like JENNIE(1).jpeg'),
(10, 1, 'like JENNIE 무대 02', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/like JENNIE(2).jpeg'),
(11, 1, 'like JENNIE 무대 03', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/like JENNIE(3).jpeg'),
(12, 1, 'Seoul City 무대 01', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/Seoul City(1).jpeg'),
(13, 1, 'Seoul City 무대 02', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/Seoul City(2).jpeg'),
(14, 1, 'Seoul City 무대 03', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/Seoul City(3).jpeg'),
(15, 1, 'Seoul City 무대 04', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/Seoul City(4).jpeg'),
(16, 1, '2025 MMA 무대 01', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/20251220MMA(1).jpeg'),
(17, 1, '2025 MMA 무대 02', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/251220MMA(3).jpeg'),
(18, 1, '2025 MMA 무대 03', 'CONCERT_STILLCUT', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_concert_stillcut/251220MMA.jpeg'),
(19, 1, 'chromehearts', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/chromehearts.png'),
(20, 1, 'color_pencil', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/color_pencil.png'),
(21, 1, 'concert', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/concert.png'),
(22, 1, 'film_camera', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/film_camera.png'),
(23, 1, 'icecream', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/icecream.png'),
(24, 1, 'minimal_camera', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/minimal_camera.png'),
(25, 1, 'polaroid', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/polaroid.png'),
(26, 1, 'pudding', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/pudding.png'),
(27, 1, 'scrap_book', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/scrap_book.png'),
(28, 1, 'stars', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/stars.png'),
(29, 1, 'sticker', 'YEZUL_FRAME', 'https://haniumstorage.blob.core.windows.net/hanium/album/album_yezul_frame/sticker.png');


INSERT INTO `avatar_conversation_session` (`id`, `cube_ownership_id`, `conversation_type`, `started_at`, `ended_at`, `audio_url`, `audio_duration_seconds`, `conversation_title`, `status`) VALUES
(1, 1, 'TEXT', '2025-03-10 12:00:00', NULL, NULL, NULL, '오늘의 인사', 'NOT_ACTIVE'),
(2, 1, 'VOICE', '2025-03-29 21:10:00', '2025-03-29 21:12:00', NULL, 120, '음성 대화', 'NOT_ACTIVE'),
(3, 1, 'TEXT', '2025-04-12 20:20:00', '2025-04-12 20:31:00', NULL, NULL, 'Ruby 앨범 이야기', 'NOT_ACTIVE');

INSERT INTO `avatar_conversation_message` (`id`, `conversation_session_id`, `sender_type`, `content`, `sequence_number`, `is_text_saved`, `status`, `violation_type`, `sent_at`) VALUES
(1, 1, 'USER', '안녕, 오늘 기분 어때?', 1, FALSE, 'ALLOWED', NULL, '2025-03-10 12:00:10'),
(2, 1, 'AVATAR', '좋아! 오늘은 like JENNIE 들어볼까?', 2, TRUE, 'ALLOWED', NULL, '2025-03-10 12:00:12'),
(3, 1, 'USER', '뭐해?', 3, FALSE, 'ALLOWED', NULL, '2025-03-10 12:00:12'),
(4, 1, 'AVATAR', '몰라', 4, TRUE, 'ALLOWED', NULL, '2025-03-10 12:00:12'),
(5, 3, 'USER', 'Ruby 앨범 콘셉트 설명해줘.', 1, FALSE, 'ALLOWED', NULL, '2025-04-12 20:20:10');

INSERT INTO `conversation_report` (`id`, `conversation_message_id`, `reason`, `detail_reason`) VALUES
(1, 1, 'INCORRECT_PERSONA', '페르소나 응답이 부정확한 예시'),
(2, 2, 'HALLUCINATION', '존재하지 않는 이벤트 언급'),
(3, 3, 'INAPPROPRIATE_EXPRESSION', '부적절한 표현 감지');

INSERT INTO `avatar_interaction_session` (`id`, `cube_ownership_id`, `started_at`, `ended_at`, `status`) VALUES
(1, 1, '2025-03-10 13:00:00', NULL, 'COMPLETED'),
(2, 1, '2025-03-18 19:20:00', '2025-03-18 19:24:00', 'COMPLETED'),
(3, 1, '2025-03-20 21:00:00', '2025-03-20 21:05:00', 'COMPLETED');

-- INSERT INTO `avatar_interaction_picture` (`id`, `interaction_session_id`, `picture_img_url`, `pictured_at`) VALUES


INSERT INTO `post` (`id`, `user_id`, `board_type`, `title`, `content`, `status`) VALUES
(1, 1, 'FREE', 'Ruby 큐브 26번 등록했어요', '앨범 나오자마자 큐브 등록했습니다. AR로 like JENNIE 무대 보는데 진짜 눈앞에 있는 것 같아요.', 'ACTIVE'),
(2, 1, 'CERTIFICATION', '큐브 인증 완료', '발매일에 바로 인증 성공했습니다. 코드 입력하고 3초 만에 됐어요.', 'ACTIVE'),
(3, 1, 'FREE', '제니 다음 앨범', '제니 이번 앨범 너무 좋은데 다음 앨범은 언제쯤 나올까요?', 'ACTIVE');

-- INSERT INTO `post_media` (`id`, `post_id`, `post_image_url`) VALUES

INSERT INTO `comment` (`id`, `post_id`, `user_id`, `content`, `status`) VALUES
(1, 1, 1, '축하해요! 26번 부럽네요.', 'ACTIVE'),
(2, 2, 1, '인증 이미지 멋져요.', 'ACTIVE'),
(3, 3, 1, '저도 너무 기다리고 있어요.', 'ACTIVE');

INSERT INTO `post_like` (`id`, `post_id`, `user_id`, `is_liked`) VALUES
(1, 1, 1, TRUE),
(2, 2, 1, FALSE),
(3, 3, 1, TRUE);

INSERT INTO `comment_like` (`id`, `comment_id`, `user_id`, `is_liked`) VALUES
(1, 1, 1, TRUE),
(2, 2, 1, TRUE),
(3, 3, 1, FALSE);

INSERT INTO `market_product` (`id`, `cube_id`, `product_image_url`) VALUES
(1, 1, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/Icon%20Background.png'),
(2, 2, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png'),
(3, 3, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png');

INSERT INTO `sell_listing` (`id`, `market_product_id`, `user_id`, `product_status`, `title`, `description`, `price`, `status`) VALUES
(1, 2, 2, '좋음', '빅뱅 메이드 큐브 31번', '상태 좋은 큐브 판매합니다.', 35000, 'ACTIVE'),
(2, 3, 3, '좋음', '로제 큐브 판매', '상태 좋은 큐브 판매합니다.', 35000, 'ACTIVE');

INSERT INTO `trade` (`id`, `sell_listing_id`, `buyer_user_id`, `buyer_phone_number`, `buyer_address`, `total_price`, `paid_time`, `sent_time`, `shipped_time`, `delivered_time`, `completed_time`, `status`) VALUES
(1, 1, 1, '010-1234-5678', '서울특별시 강남구 테헤란로 1', 36250, '2025-04-08 14:30:00', '2025-04-09 10:00:00', '2025-04-09 15:30:00', NULL, NULL, 'SHIPPING');

INSERT INTO `listing_media` (`id`, `sell_listing_id`, `image_url`) VALUES
(1, 1, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card-2.png');

INSERT INTO `digital_certificate` (`id`, `trade_id`, `network`, `token_standard`, `token_id`, `contract_address`, `tx_hash`, `metadata_url`) VALUES
(1, 1, 'Polygon Amoy', 'ERC-721', '1000001', '0x0000000000000000000000000000000000000002', '0xmocktxhash000000000000000000000000000000000000000000000000000000000002', 'https://example.com/metadata/1.json');
