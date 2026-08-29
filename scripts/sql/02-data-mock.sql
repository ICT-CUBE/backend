SET NAMES utf8mb4;

INSERT INTO `user` (`id`, `email`, `password_hash`, `login_provider`, `provider_user_id`, `nickname`, `profile_character_img_url`, `chat_violation_count`, `status`) VALUES
(1, 'user1@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$e5rwJadaTZWYqHcAyaYlgw$NLj5gR1MqWDcNcFk4qOANuLkPKjN126Thk4xVjfKfZ4', 'EMAIL', 'jennylover', '블링크', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(2, 'user2@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$8TZ6+YYxwqiFBaVnMCNDYA$w2QekRkz1xjBZ35BFTeC+tPlUNkMVxO3wdIUa4MXCjI', 'EMAIL', 'GDlover', '지드래곤짱', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(3, 'user3@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$2wCJpZVvwEchjNil+r8xlg$qjCecKV0HkZ1oYFZLZ28j4jv1A9jYv/zJLOhx0scsVo', 'EMAIL', 'ROSElover', '로제짱', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(4, 'user4@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$Go04umJUR+j2PHFJdYjDRA$Ly221dEUOOsdU7vyvdsNaLnKr5bqWUwRuwkT+B7YMkc', 'EMAIL', 'blink04', '한강블링크', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(5, 'user5@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$Zu0ezQU872GI7T/A92rTVw$8yZFlLs3U7W+q1wc87Rrd1D+hKNBAnwkrMsA+LiOTx0', 'EMAIL', 'rubycollector', '루비수집가', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(6, 'user6@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$PncV/BsL0VTZ2D7G90AGJw$3a0j4XX91RRSMdE3ijGmq4JuFf+CdUVj/Q6YHCAnAK8', 'EMAIL', 'jendeukfan', '젠득이팬', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(7, 'user7@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$IEaDzTfBiEl+C6mRyBgLqg$FHxflpZNCt8PK4fNwXQPWq9GnFoyNvBaRYWUd1V0fFA', 'EMAIL', 'concertlover', '콘서트러버', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(8, 'user8@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$yBTAfLwfOtYt5Jx44mFa5g$iRI1tnNbxNEZThiQo3SPNX+a1HFeYwax3cmwHFkxA3g', 'EMAIL', 'arzoneexplorer', '아르존탐험가', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(9, 'user9@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$bXU1E7/2HjUNj87O5VJVRg$E9G5cPMlc2oiQQwQLPmd2z9KPNengCi1Oi1AdE2HTO0', 'EMAIL', 'cubemaster', '큐브마스터', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE'),
(10, 'user10@arzone.com', '$argon2id$v=19$m=65536,t=3,p=4$0g1TVF6arqDamTNG7UTj5g$rrBARIFw7lBp/DBwrJ2wRnqFprsVPQbX3+Lgct21r40', 'EMAIL', 'jenniesupport', '제니응원단', 'https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png', 0, 'ACTIVE');

INSERT INTO `cube` (`id`, `serial_number`, `product_name`, `ownership_code_hash`, `artist_name`, `status`) VALUES
(1, 'NO.0026', 'JENNIE RUBY CUBE', '9999', 'Jennie', 'OWNED'),
(2, 'NO.0031', 'BIGBANG MADE CUBE', '1111', 'Big Bang', 'TRADE_PENDING'),
(3, 'NO.0022', 'ROSE ROISE CUBE', '2222', 'ROSE', 'OWNED'),
(4, 'NO.0044', 'JENNIE SOLO CUBE', '4444', 'Jennie', 'UNREGISTERED'),
(5, 'NO.0055', 'BIGBANG STILL LIFE CUBE', '5555', 'Big Bang', 'UNREGISTERED'),
(6, 'NO.0066', 'ROSE ROSIE CUBE', '6666', 'ROSE', 'UNREGISTERED'),
(7, 'NO.0077', 'JENNIE RUBY CUBE', '7777', 'Jennie', 'OWNED'),
(8, 'NO.0088', 'AESPA ARMAGEDDON CUBE', '8888', 'AESPA', 'OWNED'),
(9, 'NO.0099', 'ROSE ROISE CUBE', '9990', 'ROSE', 'OWNED'),
(10, 'NO.0100', 'IU THE WINNING CUBE', '1010', 'IU', 'OWNED');

INSERT INTO `cube_verification` (`id`, `user_id`, `cube_id`, `verification_status`, `code_expires_at`, `verified_at`) VALUES
(1, 1, 1, 'SUCCESS', '2025-03-14 19:25:00', '2025-03-07 19:25:00'),
(2, 2, 2, 'SUCCESS', '2025-03-14 19:25:00', '2025-03-07 19:25:00'),
(3, 3, 3, 'SUCCESS', '2025-03-14 19:25:00', '2025-03-07 19:25:00'),
(4, 4, 7, 'SUCCESS', '2025-04-08 17:55:00', '2025-04-01 17:55:00'),
(5, 5, 8, 'SUCCESS', '2025-04-09 17:55:00', '2025-04-02 17:55:00'),
(6, 6, 9, 'SUCCESS', '2025-04-10 17:55:00', '2025-04-03 17:55:00'),
(7, 7, 10, 'SUCCESS', '2025-04-11 17:55:00', '2025-04-04 17:55:00');

INSERT INTO `cube_ownership` (`id`, `user_id`, `cube_id`, `avatar_nickname`, `ownership_status`, `is_last_accessed`, `acquired_at`) VALUES
(1, 1, 1, '젠득이', 'ACTIVE', TRUE, '2025-03-07 19:30:00'),
(2, 2, 2, '지디득이', 'ACTIVE', TRUE, '2025-03-07 19:30:00'),
(3, 3, 3, '로제득이', 'ACTIVE', TRUE, '2025-03-07 19:30:00'),
(4, 4, 7, '루비득이', 'ACTIVE', TRUE, '2025-04-01 18:00:00'),
(5, 5, 8, '아마겟돈', 'ACTIVE', TRUE, '2025-04-02 18:00:00'),
(6, 6, 9, '로지득이', 'ACTIVE', TRUE, '2025-04-03 18:00:00'),
(7, 7, 10, '아이유득이', 'ACTIVE', TRUE, '2025-04-04 18:00:00');

INSERT INTO `reward_item` (`id`, `name`, `reward_type`, `description`, `reward_count`, `reward_level`) VALUES
(1, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 3포인트 제공', 3, NULL),
(2, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 5포인트 제공', 5, NULL),
(3, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 10포인트 제공', 10, NULL),
(4, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 20포인트 제공', 20, NULL),
(5, '친밀도 포인트', 'AFFINITY_POINT', '친밀도 30포인트 제공', 30, NULL),
(6, '일일 대화 가능 횟수', 'CONVERSATION_COUNT', '하루에 대화 제한 5회', 5, 1),
(7, '일일 대화 가능 횟수', 'CONVERSATION_COUNT', '하루에 대화 제한 30회', 30, 2),
(8, '일일 대화 가능 횟수', 'CONVERSATION_COUNT', '하루에 대화 제한 100회', 100, 3),
(9, '일일 대화 가능 횟수', 'CONVERSATION_COUNT', '하루에 대화 제한 없음', NULL, 4),
(10, '멘트 종류', 'COMMENT_TYPE', '기본 인사', NULL, 1),
(11, '멘트 종류', 'COMMENT_TYPE', '일상 멘트와 애칭 부르기', NULL, 2),
(12, '멘트 종류', 'COMMENT_TYPE', '사적인 멘트와 비하인드 대화', NULL, 3),
(13, '스페셜 음성', 'SPECIAL_COMMENT', '유행어 음성 해금 및 시즌 한정 음성 추가', NULL, 3),
(14, '뱃지', 'BADGE', 'BORN PINK 마스터', 1, NULL),
(15, '아바타 선대화', 'AVATAR_FIRST_TALK', '아바타 선대화 1일 1회', 1, 3),
(16, '아바타 선대화', 'AVATAR_FIRST_TALK', '아바타 선대화 1일 5회', 5, 4);

INSERT INTO `level` (`id`, `level`, `level_xp`, `level_name`) VALUES
(1, 1, 0, 'Intro'),
(2, 2, 100, 'Friend'),
(3, 3, 800, 'Close'),
(4, 4, 2000, 'Special');

INSERT INTO `affinity` (`id`, `cube_ownership_id`, `level_id`, `current_xp`) VALUES
(1, 1, 3, 1245),
(2, 2, 1, 0),
(3, 3, 1, 0),
(4, 4, 1, 0),
(5, 5, 1, 0),
(6, 6, 1, 0),
(7, 7, 1, 0);

INSERT INTO `mission` (`id`, `reward_item_id`, `mission_type`, `title`, `description`, `mission_info`, `target_action`, `target_count`, `start_at`, `end_at`, `is_active`) VALUES
(1, 2, 'DAILY', '홈 화면 방문하기', 'AR ZONE 접속', 'home_view=1', 'HOME_VIEW', 1, NULL, NULL, TRUE),
(2, 1, 'DAILY', '아바타와 대화하기', '텍스트 또는 음성 대화', 'avatar_chat=3', 'CONVERSATION', 3, NULL, NULL, TRUE),
(3, 2, 'DAILY', '음원 재생하기', '앨범에서 노래 한 곡 재생', 'play_music=1', 'ALBUM_PLAY', 1, NULL, NULL, TRUE),
(4, 5, 'DAILY', '아바타 현실 소환하기', 'AR 카메라 3회 사용', 'summon_avatar=3', 'SUMMON_AVATAR', 3, NULL, NULL, TRUE),
(5, 4, 'DAILY', '갤러리 둘러보기', '아무 사진 5회 열람', 'open_gallery=5', 'OPEN_GALLERY', 5, NULL, NULL, TRUE),
(6, 3, 'DAILY', '커뮤니티 글 업로드하기', '게시물 1회 업로드', 'write_post=1', 'COMMUNITY_POST', 1, NULL, NULL, TRUE),
(7, 14, 'EVENT', '[RUBY] 콘서트 인증 이벤트', '아무 뮤직 비디오 5회 시청', 'watch_music_video=5', 'PLAY_MUSIC_VIDEO', 5, '2026-06-12 00:00:00', '2026-09-18 23:59:59', TRUE);

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
(2, 1, 14, '2025-03-18 22:32:00'),
(3, 1, 5, '2025-03-24 21:11:00'),
(4, 1, 6, '2025-03-07 19:30:00'),
(5, 1, 10, '2025-03-07 19:30:00'),
(6, 1, 7, '2025-03-15 12:00:00'),
(7, 1, 11, '2025-03-15 12:00:00'),
(8, 1, 8, '2025-03-23 20:45:00'),
(9, 1, 12, '2025-03-23 20:45:00'),
(10, 1, 13, '2025-03-23 20:45:00'),
(11, 1, 15, '2025-03-23 20:45:00'),
(12, 2, 6, '2025-03-07 19:30:00'),
(13, 2, 10, '2025-03-07 19:30:00'),
(14, 3, 6, '2025-03-07 19:30:00'),
(15, 3, 10, '2025-03-07 19:30:00'),
(16, 4, 6, '2025-04-01 18:00:00'),
(17, 4, 10, '2025-04-01 18:00:00'),
(18, 5, 6, '2025-04-02 18:00:00'),
(19, 5, 10, '2025-04-02 18:00:00'),
(20, 6, 6, '2025-04-03 18:00:00'),
(21, 6, 10, '2025-04-03 18:00:00'),
(22, 7, 6, '2025-04-04 18:00:00'),
(23, 7, 10, '2025-04-04 18:00:00');

INSERT INTO `notification` (`id`, `user_id`, `notification_type`, `title`, `content`, `is_read`, `sent_at`, `read_at`) VALUES
(1, 1, 'MISSION', '미션 완료', '홈 화면 조회 미션 보상을 받았어요.', TRUE, '2025-03-24 10:01:00', '2025-03-24 10:02:00'),
(2, 1, 'EVENT', '이벤트 진행 중', '루비 앨범 이벤트가 진행 중이에요.', TRUE, '2025-03-18 09:00:00', '2025-03-18 09:15:00'),
(3, 1, 'MISSION', '친밀도 상승', '젠득이와의 친밀도가 Close 레벨이 되었어요.', TRUE, '2025-03-23 20:45:00', '2025-03-23 21:00:00'),
(4, 1, 'MARKET', '거래 알림', '거래 제안이 도착했어요.', FALSE, '2025-04-08 14:45:00', NULL);

INSERT INTO `user_setting` (`id`, `user_id`, `push_enabled`, `new_conversation_enabled`, `affinity_change_enabled`, `daily_mission_refresh_enabled`, `trade_completed_enabled`, `trade_offer_enabled`, `community_comment_notice_enabled`) VALUES
(1, 1, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(2, 2, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(3, 3, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(4, 4, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(5, 5, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(6, 6, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(7, 7, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(8, 8, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(9, 9, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
(10, 10, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE);

INSERT INTO `album` (`id`, `title`, `artist_name`, `artist_company`, `track_count`, `track_total_second`, `description`, `cover_image_url`, `release_date`) VALUES
(1, 'Ruby', 'Jennie', 'Odd Atelier', 15, 2498, '제니 정규 1집 루비 앨범', 'https://haniumstorage.blob.core.windows.net/hanium/album_cover_img/RUBY_cover_img.jpeg', '2025-03-07');

INSERT INTO `stage` (`id`, `album_id`, `title`, `description`, `video_url`, `video_type`, `thumbnail_url`, `duration_seconds`, `recorded_at`, `is_active`, `is_title_video`) VALUES
(1, 1, 'Mantra MV', 'Mantra 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_mantra.mp4', 'MUSIC_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/music_video_thumbnail/mv_mantra.jpg', 136, '2024-10-11 13:00:00', TRUE, FALSE),
(2, 1, 'ZEN MV', 'ZEN 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_zen.mp4', 'MUSIC_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/music_video_thumbnail/mv_zen.jpg', 201, '2025-01-25 13:00:00', TRUE, FALSE),
(3, 1, 'Love Hangover MV', 'Love Hangover (feat. Dominic Fike) 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_lovehangover.mp4', 'MUSIC_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/music_video_thumbnail/mv_lovehangover.jpg', 180, '2025-01-31 13:00:00', TRUE, FALSE),
(4, 1, 'ExtraL MV', 'ExtraL (feat. Doechii) 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_extral.mp4', 'MUSIC_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/music_video_thumbnail/mv_extral.jpg', 168, '2025-02-21 13:00:00', TRUE, FALSE),
(5, 1, 'like JENNIE MV', 'like JENNIE 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_likejennie.mp4', 'MUSIC_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/music_video_thumbnail/mv_likejennie.jpg', 124, '2025-03-07 13:00:00', TRUE, TRUE),
(6, 1, 'Handlebars MV', 'Handlebars (feat. Dua Lipa) 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_handlebars.mp4', 'MUSIC_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/music_video_thumbnail/mv_handlebars.jpg', 185, '2025-03-10 13:00:00', TRUE, FALSE),
(7, 1, 'Seoul City MV', 'Seoul City 뮤직비디오', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_music_video/mv_seoul city.mp4', 'MUSIC_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/music_video_thumbnail/mv_seoul%20city.jpg', 164, '2025-04-26 13:00:00', TRUE, FALSE),
(8, 1, 'start a war Live Performance', 'start a war 콘서트 영상', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_concert_video/concert_zen.mp4', 'CONCERT_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/concert_video_thumbnail/concert_zen.jpg', 165, '2025-03-28 13:00:00', TRUE, FALSE),
(9, 1, 'Love Hangover Live Performance', 'Love Hangover 콘서트 영상', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_concert_video/concert_lovehangover.mp4', 'CONCERT_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/concert_video_thumbnail/concert_mantra.jpg', 180, '2025-02-12 13:00:00', TRUE, FALSE),
(10, 1, 'like JENNIE Live Performance', 'like JENNIE 콘서트 영상', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_concert_video/concert_likejennie.mp4', 'CONCERT_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/concert_video_thumbnail/concert_likejennie.jpg', 124, '2025-03-12 13:00:00', TRUE, FALSE),
(11, 1, 'Handlebars Live Performance', 'Handlebars 콘서트 영상', 'https://haniumstorage.blob.core.windows.net/hanium/stage/stage_concert_video/concert_handlebars.mp4', 'CONCERT_VIDEO', 'https://haniumstorage.blob.core.windows.net/hanium/stage/concert_video_thumbnail/concert_handlebars.jpg', 185, '2025-03-12 13:00:00', TRUE, FALSE);

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


INSERT INTO `avatar_conversation_session` (`id`, `cube_ownership_id`, `conversation_type`, `started_at`, `ended_at`, `audio_url`, `audio_duration_seconds`, `conversation_title`, `status`) VALUES
(1, 1, 'TEXT', '2025-03-10 12:00:00', '2025-03-10 12:04:00', NULL, NULL, '오늘의 인사', 'NOT_ACTIVE'),
(2, 1, 'VOICE', '2025-03-29 21:10:00', '2025-03-29 21:14:00', 'https://haniumstorage.blob.core.windows.net/hanium/conversation_audio/1/6/e916cdb7-5ade-4ac2-b083-5c12fade1106.m4a', 240, '저녁 메뉴 추천', 'NOT_ACTIVE'),
(3, 1, 'TEXT', '2025-04-12 20:20:00', '2025-04-12 20:31:00', NULL, NULL, 'Ruby 앨범 이야기', 'NOT_ACTIVE'),
(4, 1, 'VOICE', '2025-04-18 18:30:00', '2025-04-18 18:35:00', 'https://haniumstorage.blob.core.windows.net/hanium/conversation_audio/1/4/7e3a479e-5727-47df-95d7-721671c972b7.m4a', 300, '자연과의 만남', 'NOT_ACTIVE'),
(5, 1, 'TEXT', '2025-04-22 14:00:00', '2025-04-22 14:06:00', NULL, NULL, '여행의 추억과 친구들', 'NOT_ACTIVE'),
(6, 1, 'VOICE', '2025-04-28 09:00:00', '2025-04-28 09:05:00', 'https://haniumstorage.blob.core.windows.net/hanium/conversation_audio/1/2/9cbca527-7970-4851-b3d2-bdb527356573.m4a', 300, '운동과 건강 관리', 'NOT_ACTIVE');

INSERT INTO `avatar_conversation_message` (`id`, `conversation_session_id`, `sender_type`, `content`, `sequence_number`, `is_text_saved`, `status`, `violation_type`, `sent_at`) VALUES
(1, 1, 'USER', '안녕, 오늘 기분 어때?', 1, FALSE, 'ALLOWED', NULL, '2025-03-10 12:00:10'),
(2, 1, 'AVATAR', '좋아! 오늘은 like JENNIE 들어볼까?', 2, TRUE, 'ALLOWED', NULL, '2025-03-10 12:00:12'),
(3, 1, 'USER', '좋아, 가장 추천하는 곡은 뭐야?', 3, FALSE, 'ALLOWED', NULL, '2025-03-10 12:01:00'),
(4, 1, 'AVATAR', '나는 Like JENNIE를 먼저 추천할게.', 4, TRUE, 'ALLOWED', NULL, '2025-03-10 12:01:05'),
(5, 1, 'USER', '그럼 지금 바로 들어볼게.', 5, FALSE, 'ALLOWED', NULL, '2025-03-10 12:02:00'),
(6, 1, 'AVATAR', '좋아! 듣고 나서 감상도 알려줘.', 6, FALSE, 'ALLOWED', NULL, '2025-03-10 12:02:05'),
(7, 2, 'USER', '오늘 저녁은 뭘 먹을까?', 1, FALSE, 'ALLOWED', NULL, '2025-03-29 21:10:10'),
(8, 2, 'AVATAR', '따뜻한 파스타는 어때?', 2, FALSE, 'ALLOWED', NULL, '2025-03-29 21:10:15'),
(9, 2, 'USER', '조금 더 매콤한 게 먹고 싶어.', 3, FALSE, 'ALLOWED', NULL, '2025-03-29 21:11:00'),
(10, 2, 'AVATAR', '그러면 매콤한 떡볶이를 추천할게.', 4, FALSE, 'ALLOWED', NULL, '2025-03-29 21:11:05'),
(11, 2, 'USER', '좋아, 튀김도 같이 먹어야겠다.', 5, FALSE, 'ALLOWED', NULL, '2025-03-29 21:12:00'),
(12, 2, 'AVATAR', '완벽한 조합이네. 맛있게 먹어!', 6, FALSE, 'ALLOWED', NULL, '2025-03-29 21:12:05'),
(13, 3, 'USER', 'Ruby 앨범 콘셉트 설명해줘.', 1, FALSE, 'ALLOWED', NULL, '2025-04-12 20:20:10'),
(14, 3, 'AVATAR', '강렬함과 솔직한 내 모습을 담은 앨범이야.', 2, TRUE, 'ALLOWED', NULL, '2025-04-12 20:20:15'),
(15, 3, 'USER', '가장 애착이 가는 곡은 뭐야?', 3, FALSE, 'ALLOWED', NULL, '2025-04-12 20:21:00'),
(16, 3, 'AVATAR', '모든 곡이 소중하지만 타이틀곡에 특히 애착이 가.', 4, FALSE, 'ALLOWED', NULL, '2025-04-12 20:21:05'),
(17, 3, 'USER', '무대도 정말 기대하고 있어.', 5, FALSE, 'ALLOWED', NULL, '2025-04-12 20:22:00'),
(18, 3, 'AVATAR', '기대해도 좋아. 멋진 모습 보여줄게!', 6, FALSE, 'ALLOWED', NULL, '2025-04-12 20:22:05'),
(19, 4, 'USER', '요즘 산책하기 좋은 곳이 있을까?', 1, FALSE, 'ALLOWED', NULL, '2025-04-18 18:30:10'),
(20, 4, 'AVATAR', '강변 공원에서 천천히 걷는 건 어때?', 2, FALSE, 'ALLOWED', NULL, '2025-04-18 18:30:15'),
(21, 4, 'USER', '노을도 볼 수 있으면 좋겠어.', 3, FALSE, 'ALLOWED', NULL, '2025-04-18 18:31:00'),
(22, 4, 'AVATAR', '해 질 무렵에 가면 멋진 노을도 볼 수 있어.', 4, FALSE, 'ALLOWED', NULL, '2025-04-18 18:31:05'),
(23, 4, 'USER', '이번 주말에 꼭 가봐야겠다.', 5, FALSE, 'ALLOWED', NULL, '2025-04-18 18:32:00'),
(24, 4, 'AVATAR', '좋은 생각이야. 사진도 많이 찍어 와!', 6, FALSE, 'ALLOWED', NULL, '2025-04-18 18:32:05'),
(25, 5, 'USER', '친구들과 갔던 여행이 생각나.', 1, FALSE, 'ALLOWED', NULL, '2025-04-22 14:00:10'),
(26, 5, 'AVATAR', '어떤 순간이 가장 기억에 남아?', 2, FALSE, 'ALLOWED', NULL, '2025-04-22 14:00:15'),
(27, 5, 'USER', '바닷가에서 함께 본 일몰이 기억나.', 3, FALSE, 'ALLOWED', NULL, '2025-04-22 14:01:00'),
(28, 5, 'AVATAR', '친구들과 본 일몰이라 더 특별했겠다.', 4, FALSE, 'ALLOWED', NULL, '2025-04-22 14:01:05'),
(29, 5, 'USER', '다음에도 다 같이 여행하고 싶어.', 5, FALSE, 'ALLOWED', NULL, '2025-04-22 14:02:00'),
(30, 5, 'AVATAR', '다음 여행도 분명 좋은 추억이 될 거야.', 6, FALSE, 'ALLOWED', NULL, '2025-04-22 14:02:05'),
(31, 6, 'USER', '요즘 운동을 시작해 보려고 해.', 1, FALSE, 'ALLOWED', NULL, '2025-04-28 09:00:10'),
(32, 6, 'AVATAR', '가벼운 걷기부터 시작해 보는 건 어때?', 2, FALSE, 'ALLOWED', NULL, '2025-04-28 09:00:15'),
(33, 6, 'USER', '일주일에 몇 번 정도가 좋을까?', 3, FALSE, 'ALLOWED', NULL, '2025-04-28 09:01:00'),
(34, 6, 'AVATAR', '처음에는 일주일에 세 번 정도가 좋아.', 4, FALSE, 'ALLOWED', NULL, '2025-04-28 09:01:05'),
(35, 6, 'USER', '무리하지 않고 꾸준히 해볼게.', 5, FALSE, 'ALLOWED', NULL, '2025-04-28 09:02:00'),
(36, 6, 'AVATAR', '좋아! 꾸준함이 가장 중요해.', 6, FALSE, 'ALLOWED', NULL, '2025-04-28 09:02:05');

INSERT INTO `conversation_report` (`id`, `conversation_message_id`, `reason`, `detail_reason`) VALUES
(1, 1, 'INCORRECT_PERSONA', '페르소나 응답이 부정확한 예시'),
(2, 2, 'HALLUCINATION', '존재하지 않는 이벤트 언급'),
(3, 3, 'INAPPROPRIATE_EXPRESSION', '부적절한 표현 감지');

INSERT INTO `avatar_interaction_session` (`id`, `cube_ownership_id`, `started_at`, `ended_at`, `status`) VALUES
(1, 1, '2025-03-10 13:00:00', '2025-03-10 13:05:00', 'COMPLETED'),
(2, 1, '2025-03-18 19:20:00', '2025-03-18 19:24:00', 'COMPLETED'),
(3, 1, '2025-03-20 21:00:00', '2025-03-20 21:05:00', 'COMPLETED');

-- INSERT INTO `avatar_interaction_picture` (`id`, `interaction_session_id`, `picture_img_url`, `pictured_at`) VALUES


INSERT INTO `post` (`id`, `user_id`, `board_type`, `title`, `content`, `status`, `created_at`) VALUES
(1, 1, 'FREE', 'Ruby 큐브 26번 등록했어요', '앨범 나오자마자 큐브 등록했습니다. AR로 like JENNIE 무대 보는데 진짜 눈앞에 있는 것 같아요.', 'ACTIVE', '2026-08-28 09:10:00'),
(2, 4, 'FREE', '리액트 상태 관리 질문 있습니다', '커뮤니티 화면을 만들면서 상태 관리 방식을 고민하고 있습니다. 다들 어떤 방식을 사용하시나요?', 'ACTIVE', '2026-08-28 10:20:00'),
(3, 6, 'FREE', '제니 다음 앨범이 기대돼요', '이번 Ruby 앨범을 계속 듣고 있는데 다음 앨범 소식도 빨리 듣고 싶어요.', 'ACTIVE', '2026-08-28 11:30:00'),
(4, 8, 'FREE', '갤러리 기능 사용 팁 공유해요', '스테이지와 트랙에서 저장한 캡처를 갤러리에서 다시 보는 방법을 정리해봤어요.', 'ACTIVE', '2026-08-28 12:40:00'),
(5, 10, 'FREE', '콘서트 갈 때 준비물 추천해주세요', '공연을 처음 보러 가는데 꼭 챙겨야 하는 준비물이 있다면 알려주세요.', 'ACTIVE', '2026-08-28 13:50:00'),
(6, 2, 'CERTIFICATION', '큐브 인증 완료했습니다', '발매일에 구매한 큐브를 오늘 등록했습니다. 인증 과정도 빠르고 간단했어요.', 'ACTIVE', '2026-08-28 14:10:00'),
(7, 3, 'CERTIFICATION', '콘서트 영상 5회 시청 인증', '이벤트 미션으로 콘서트 영상을 다섯 번 시청하고 보상까지 받았습니다.', 'ACTIVE', '2026-08-28 15:20:00'),
(8, 5, 'CERTIFICATION', '친밀도 Close 달성 인증', '매일 대화와 미션을 진행해서 드디어 친밀도 Close 단계에 도달했습니다.', 'ACTIVE', '2026-08-28 16:30:00'),
(9, 7, 'CERTIFICATION', '스페셜 재생 모드 해금 인증', '친밀도를 올린 뒤 스페셜 재생 모드가 정상적으로 해금된 것을 확인했습니다.', 'REPORTED', '2026-08-28 17:40:00'),
(10, 9, 'CERTIFICATION', '마켓 거래 완료 인증합니다', '마켓에서 찾던 큐브를 구매하고 구매 확정까지 정상적으로 완료했습니다.', 'ACTIVE', '2026-08-28 18:50:00');

-- INSERT INTO `post_media` (`id`, `post_id`, `post_image_url`) VALUES

INSERT INTO `comment` (`id`, `post_id`, `user_id`, `content`, `status`) VALUES
(1, 1, 2, '축하해요! 26번 큐브 정말 부럽네요.', 'ACTIVE'),
(2, 1, 4, 'AR 무대가 실제로 보는 것처럼 생생하더라고요.', 'ACTIVE'),
(3, 1, 6, '저도 같은 큐브 등록하고 싶어요.', 'ACTIVE'),
(4, 1, 9, '시리얼 번호가 멋집니다.', 'ACTIVE'),
(5, 2, 1, '저는 화면 단위 상태와 서버 상태를 나눠서 관리하고 있어요.', 'ACTIVE'),
(6, 2, 5, '규모가 작으면 기본 상태 관리만으로도 충분한 것 같아요.', 'ACTIVE'),
(7, 2, 8, 'API 캐시가 필요한지부터 확인해보는 걸 추천해요.', 'ACTIVE'),
(8, 3, 2, '저도 다음 앨범 소식 기다리고 있어요.', 'ACTIVE'),
(9, 3, 4, '이번 앨범 수록곡이 다 좋아서 매일 듣고 있습니다.', 'ACTIVE'),
(10, 3, 7, '다음 활동도 멋진 무대가 많았으면 좋겠어요.', 'ACTIVE'),
(11, 3, 9, '새로운 콘셉트도 기대됩니다.', 'ACTIVE'),
(12, 3, 10, '공식 소식 나오면 같이 공유해요.', 'ACTIVE'),
(13, 4, 1, '캡처를 다시 보는 방법이 궁금했는데 감사합니다.', 'ACTIVE'),
(14, 4, 3, '트랙 캡처도 같은 방식으로 볼 수 있나요?', 'ACTIVE'),
(15, 4, 5, '정리해주신 내용대로 하니 잘 됩니다.', 'ACTIVE'),
(16, 4, 7, '갤러리 필터도 함께 사용하면 편해요.', 'ACTIVE'),
(17, 5, 2, '보조 배터리는 꼭 챙기는 걸 추천해요.', 'ACTIVE'),
(18, 5, 3, '공연장 입장 시간을 미리 확인하세요.', 'ACTIVE'),
(19, 5, 4, '신분증과 예매 내역도 잊지 마세요.', 'ACTIVE'),
(20, 5, 6, '편한 신발을 신고 가는 게 좋아요.', 'ACTIVE'),
(21, 5, 8, '응원봉 배터리도 여분으로 챙기세요.', 'ACTIVE'),
(22, 5, 9, '물은 공연장 반입 규정을 확인해야 해요.', 'ACTIVE'),
(23, 6, 1, '인증 완료 축하드립니다.', 'ACTIVE'),
(24, 6, 3, '저도 코드 입력하니 바로 등록됐어요.', 'ACTIVE'),
(25, 6, 5, '큐브 디자인이 정말 예쁘네요.', 'ACTIVE'),
(26, 6, 7, '인증 과정이 간단해서 좋았습니다.', 'ACTIVE'),
(27, 6, 10, '등록 후 홈 화면도 잘 나오나요?', 'ACTIVE'),
(28, 7, 2, '이벤트 보상까지 받으셨군요.', 'ACTIVE'),
(29, 7, 6, '저도 오늘 남은 횟수 채워야겠어요.', 'ACTIVE'),
(30, 7, 8, '콘서트 영상이 멋져서 다섯 번도 금방이더라고요.', 'ACTIVE'),
(31, 8, 1, 'Close 달성 축하해요.', 'ACTIVE'),
(32, 8, 4, '매일 꾸준히 진행하신 게 대단합니다.', 'ACTIVE'),
(33, 8, 7, '저도 곧 Close 단계에 도달할 것 같아요.', 'ACTIVE'),
(34, 8, 9, '해금된 기능도 궁금하네요.', 'ACTIVE'),
(35, 9, 2, '스페셜 모드 해금 축하드립니다.', 'ACTIVE'),
(36, 9, 3, '기본 재생과 어떤 차이가 있나요?', 'ACTIVE'),
(37, 9, 5, '저도 친밀도를 더 올려야겠어요.', 'ACTIVE'),
(38, 9, 8, '해금 조건 정보 감사합니다.', 'ACTIVE'),
(39, 9, 10, '스페셜 모드 영상이 궁금합니다.', 'ACTIVE'),
(40, 10, 1, '거래 완료 축하드립니다.', 'ACTIVE'),
(41, 10, 2, '배송은 얼마나 걸렸나요?', 'ACTIVE'),
(42, 10, 4, '저도 같은 제품을 찾고 있어요.', 'ACTIVE'),
(43, 10, 6, '구매 확정 화면이 잘 나오는지 궁금해요.', 'ACTIVE'),
(44, 10, 7, '좋은 판매자를 만나셨네요.', 'ACTIVE'),
(45, 10, 8, '디지털 인증서도 확인해보세요.', 'ACTIVE');

INSERT INTO `post_like` (`id`, `post_id`, `user_id`, `is_liked`) VALUES
(1, 1, 1, TRUE),
(2, 1, 2, TRUE),
(3, 1, 4, TRUE),
(4, 1, 6, FALSE),
(5, 1, 8, TRUE),
(6, 2, 10, TRUE),
(7, 2, 3, TRUE),
(8, 2, 5, TRUE),
(9, 2, 7, TRUE),
(10, 2, 9, FALSE),
(11, 3, 1, TRUE),
(12, 3, 2, TRUE),
(13, 3, 4, FALSE),
(14, 3, 8, TRUE),
(15, 3, 10, TRUE),
(16, 4, 1, FALSE),
(17, 4, 3, TRUE),
(18, 4, 5, FALSE),
(19, 4, 6, TRUE),
(20, 4, 9, TRUE),
(21, 5, 1, TRUE),
(22, 5, 2, FALSE),
(23, 5, 4, TRUE),
(24, 5, 7, TRUE),
(25, 5, 10, TRUE),
(26, 6, 1, FALSE),
(27, 6, 3, TRUE),
(28, 6, 5, TRUE),
(29, 6, 8, TRUE),
(30, 6, 9, TRUE),
(31, 7, 1, TRUE),
(32, 7, 2, TRUE),
(33, 7, 4, TRUE),
(34, 7, 6, TRUE),
(35, 7, 10, FALSE),
(36, 8, 1, FALSE),
(37, 8, 3, TRUE),
(38, 8, 5, TRUE),
(39, 8, 7, FALSE),
(40, 8, 9, TRUE),
(41, 9, 1, TRUE),
(42, 9, 2, FALSE),
(43, 9, 4, TRUE),
(44, 9, 8, TRUE),
(45, 9, 10, TRUE),
(46, 10, 1, FALSE),
(47, 10, 3, TRUE),
(48, 10, 5, TRUE),
(49, 10, 6, TRUE),
(50, 10, 9, TRUE);

INSERT INTO `comment_like` (`id`, `comment_id`, `user_id`, `is_liked`) VALUES
(1, 1, 2, TRUE),
(2, 1, 4, TRUE),
(3, 2, 1, TRUE),
(4, 5, 3, TRUE),
(5, 8, 1, TRUE),
(6, 12, 7, TRUE),
(7, 23, 4, TRUE),
(8, 31, 9, TRUE),
(9, 40, 1, FALSE),
(10, 45, 6, TRUE);

INSERT INTO `market_product` (`id`, `cube_id`, `product_image_url`) VALUES
(1, 1, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/Icon%20Background.png'),
(2, 2, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png'),
(3, 3, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png'),
(4, 4, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/Icon%20Background.png'),
(5, 5, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png'),
(6, 6, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png'),
(7, 7, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/Icon%20Background.png'),
(8, 8, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png'),
(9, 9, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png'),
(10, 10, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/Icon%20Background.png');

INSERT INTO `sell_listing` (`id`, `market_product_id`, `user_id`, `product_status`, `title`, `description`, `price`, `status`) VALUES
(1, 2, 2, '좋음', '빅뱅 메이드 큐브 31번', '상태 좋은 큐브 판매합니다.', 35000, 'SOLD'),
(2, 3, 3, '좋음', '로제 큐브 판매', '상태 좋은 큐브 판매합니다.', 35000, 'ACTIVE'),
(3, 9, 6, '미개봉', '로제 ROISE 큐브 99번', '미개봉 상태로 보관한 로제 큐브입니다.', 42000, 'ACTIVE'),
(4, 10, 7, '새상품', '아이유 THE WINNING 큐브', '구성품을 모두 포함한 새상품입니다.', 45000, 'ACTIVE'),
(5, 7, 4, '좋음', '제니 루비 큐브 77번', '구성품을 모두 보관한 제니 루비 큐브입니다.', 39000, 'ACTIVE');

INSERT INTO `selling_list_like` (`id`, `selling_list_id`, `user_id`, `is_liked`) VALUES
(1, 1, 3, TRUE),
(2, 2, 1, TRUE),
(3, 3, 1, TRUE),
(4, 3, 2, FALSE),
(5, 4, 1, TRUE),
(6, 4, 3, TRUE);

INSERT INTO `trade` (`id`, `sell_listing_id`, `buyer_user_id`, `buyer_phone_number`, `buyer_address`, `total_price`, `paid_time`, `sent_time`, `shipped_time`, `delivered_time`, `completed_time`, `status`) VALUES
(1, 1, 1, '010-1234-5678', '서울특별시 강남구 테헤란로 1', 36750, '2025-04-08 14:30:00', '2025-04-09 10:00:00', '2025-04-09 15:30:00', '2025-05-09 15:30:00', NULL, 'DELIVERED');

INSERT INTO `listing_media` (`id`, `sell_listing_id`, `image_url`) VALUES
(1, 1, 'https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card-2.png');

-- INSERT INTO `digital_certificate` (`id`, `trade_id`, `network`, `token_standard`, `token_id`, `contract_address`, `tx_hash`, `metadata_url`) VALUES
