SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `listing_media`;
DROP TABLE IF EXISTS `digital_certificate`;
DROP TABLE IF EXISTS `trade`;
DROP TABLE IF EXISTS `sell_listing`;
DROP TABLE IF EXISTS `market_product`;
DROP TABLE IF EXISTS `comment_like`;
DROP TABLE IF EXISTS `post_like`;
DROP TABLE IF EXISTS `comment`;
DROP TABLE IF EXISTS `post_media`;
DROP TABLE IF EXISTS `post`;
DROP TABLE IF EXISTS `avatar_interaction_picture`;
DROP TABLE IF EXISTS `avatar_interaction_session`;
DROP TABLE IF EXISTS `conversation_report`;
DROP TABLE IF EXISTS `avatar_conversation_message`;
DROP TABLE IF EXISTS `avatar_conversation_session`;
DROP TABLE IF EXISTS `album_image`;
DROP TABLE IF EXISTS `track_capture`;
DROP TABLE IF EXISTS `track_session`;
DROP TABLE IF EXISTS `track`;
DROP TABLE IF EXISTS `stage_capture`;
DROP TABLE IF EXISTS `stage_session`;
DROP TABLE IF EXISTS `stage`;
DROP TABLE IF EXISTS `album`;
DROP TABLE IF EXISTS `user_setting`;
DROP TABLE IF EXISTS `notification`;
DROP TABLE IF EXISTS `user_reward`;
DROP TABLE IF EXISTS `mission_progress`;
DROP TABLE IF EXISTS `mission`;
DROP TABLE IF EXISTS `affinity`;
DROP TABLE IF EXISTS `level`;
DROP TABLE IF EXISTS `reward_item`;
DROP TABLE IF EXISTS `cube_ownership`;
DROP TABLE IF EXISTS `cube_verification`;
DROP TABLE IF EXISTS `cube`;
DROP TABLE IF EXISTS `auth_session`;
DROP TABLE IF EXISTS `user`;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL,
    `password_hash` VARCHAR(255) NULL,
    `login_provider` VARCHAR(20) NOT NULL,
    `provider_user_id` VARCHAR(255) NULL,
    `nickname` VARCHAR(8) NULL,
    `profile_character_img_url` VARCHAR(50) NULL,
    `chat_violation_count` INT NOT NULL DEFAULT 0,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_email` (`email`),
    KEY `idx_user_status` (`status`),
    CONSTRAINT `ck_user_login_provider` CHECK (`login_provider` IN ('EMAIL', 'GOOGLE', 'APPLE')),
    CONSTRAINT `ck_user_status` CHECK (`status` IN ('ACTIVE', 'WITHDRAWN', 'SUSPENDED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `auth_session` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `token_jti` VARCHAR(64) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `issued_at` DATETIME NOT NULL,
    `expires_at` DATETIME NOT NULL,
    `revoked_at` DATETIME NULL,
    `device_id` VARCHAR(255) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_auth_session_token_jti` (`token_jti`),
    KEY `idx_auth_session_user_id` (`user_id`),
    CONSTRAINT `fk_auth_session_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `ck_auth_session_status` CHECK (`status` IN ('ACTIVE', 'REVOKED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `cube` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `serial_number` VARCHAR(100) NOT NULL,
    `product_name` VARCHAR(150) NOT NULL,
    `ownership_code_hash` VARCHAR(255) NOT NULL,
    `artist_name` VARCHAR(20) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'UNREGISTERED',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_cube_serial_number` (`serial_number`),
    CONSTRAINT `ck_cube_status` CHECK (`status` IN ('UNREGISTERED', 'OWNED', 'TRADE_PENDING', 'DISABLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `cube_verification` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `cube_id` BIGINT NOT NULL,
    `verification_status` VARCHAR(20) NOT NULL,
    `code_expires_at` DATETIME NULL,
    `verified_at` DATETIME NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_cube_verification_user_id` (`user_id`),
    KEY `idx_cube_verification_cube_id` (`cube_id`),
    CONSTRAINT `fk_cube_verification_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `fk_cube_verification_cube` FOREIGN KEY (`cube_id`) REFERENCES `cube` (`id`),
    CONSTRAINT `ck_cube_verification_status` CHECK (`verification_status` IN ('PENDING', 'SUCCESS', 'FAILED', 'EXPIRED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `cube_ownership` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `cube_id` BIGINT NOT NULL,
    `avatar_nickname` VARCHAR(30) NULL,
    `ownership_status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `is_last_accessed` BOOLEAN NOT NULL DEFAULT FALSE,
    `acquired_at` DATETIME NOT NULL,
    `transferred_at` DATETIME NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_cube_ownership_user_id` (`user_id`),
    KEY `idx_cube_ownership_cube_id` (`cube_id`),
    CONSTRAINT `fk_cube_ownership_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `fk_cube_ownership_cube` FOREIGN KEY (`cube_id`) REFERENCES `cube` (`id`),
    CONSTRAINT `ck_cube_ownership_status` CHECK (`ownership_status` IN ('ACTIVE', 'TRANSFERRED', 'REVOKED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `reward_item` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `reward_type` VARCHAR(30) NOT NULL,
    `description` VARCHAR(255) NULL,
    `reward_count` INT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `ck_reward_item_type` CHECK (`reward_type` IN ('AFFINITY_POINT', 'CONVERSATION_COUNT', 'COMMENT_TYPE', 'SPECIAL_COMMENT', 'AVATAR_FIRST_TALK', 'BADGE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `level` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `reward_item_id` BIGINT NOT NULL,
    `level` INT NOT NULL,
    `level_xp` INT NOT NULL,
    `level_name` VARCHAR(30) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_level_reward_item_id` (`reward_item_id`),
    UNIQUE KEY `uk_level_level` (`level`),
    CONSTRAINT `fk_level_reward_item` FOREIGN KEY (`reward_item_id`) REFERENCES `reward_item` (`id`),
    CONSTRAINT `ck_level_name` CHECK (`level_name` IN ('Intro', 'Friend', 'Close', 'Special'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `affinity` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `cube_ownership_id` BIGINT NOT NULL,
    `level_id` BIGINT NOT NULL,
    `current_xp` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_affinity_cube_ownership_id` (`cube_ownership_id`),
    KEY `idx_affinity_level_id` (`level_id`),
    CONSTRAINT `fk_affinity_cube_ownership` FOREIGN KEY (`cube_ownership_id`) REFERENCES `cube_ownership` (`id`),
    CONSTRAINT `fk_affinity_level` FOREIGN KEY (`level_id`) REFERENCES `level` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `mission` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `reward_item_id` BIGINT NOT NULL,
    `mission_type` VARCHAR(20) NOT NULL,
    `title` VARCHAR(100) NOT NULL,
    `description` VARCHAR(255) NULL,
    `mission_info` VARCHAR(500) NULL,
    `target_action` VARCHAR(50) NOT NULL,
    `target_count` INT NOT NULL,
    `start_at` DATETIME NULL,
    `end_at` DATETIME NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_mission_reward_item_id` (`reward_item_id`),
    CONSTRAINT `fk_mission_reward_item` FOREIGN KEY (`reward_item_id`) REFERENCES `reward_item` (`id`),
    CONSTRAINT `ck_mission_type` CHECK (`mission_type` IN ('DAILY', 'EVENT')),
    CONSTRAINT `ck_mission_target_action` CHECK (`target_action` IN ('HOME_VIEW', 'CONVERSATION', 'ALBUM_PLAY', 'OPEN_GALLERY', 'COMMUNITY_POST', 'SUMMON_AVATAR', 'PLAY_MUSIC_VIDEO'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `mission_progress` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `cube_ownership_id` BIGINT NOT NULL,
    `mission_id` BIGINT NOT NULL,
    `current_count` INT NOT NULL DEFAULT 0,
    `status` VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS',
    `reward_claimed` BOOLEAN NOT NULL DEFAULT FALSE,
    `completed_at` DATETIME NULL,
    `claimed_at` DATETIME NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_mission_progress_ownership_mission` (`cube_ownership_id`, `mission_id`),
    KEY `idx_mission_progress_mission_id` (`mission_id`),
    CONSTRAINT `fk_mission_progress_cube_ownership` FOREIGN KEY (`cube_ownership_id`) REFERENCES `cube_ownership` (`id`),
    CONSTRAINT `fk_mission_progress_mission` FOREIGN KEY (`mission_id`) REFERENCES `mission` (`id`),
    CONSTRAINT `ck_mission_progress_status` CHECK (`status` IN ('IN_PROGRESS', 'COMPLETED', 'REWARDED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `user_reward` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `cube_ownership_id` BIGINT NOT NULL,
    `reward_item_id` BIGINT NOT NULL,
    `acquired_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_reward_ownership_reward` (`cube_ownership_id`, `reward_item_id`),
    KEY `idx_user_reward_reward_item_id` (`reward_item_id`),
    CONSTRAINT `fk_user_reward_cube_ownership` FOREIGN KEY (`cube_ownership_id`) REFERENCES `cube_ownership` (`id`),
    CONSTRAINT `fk_user_reward_reward_item` FOREIGN KEY (`reward_item_id`) REFERENCES `reward_item` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `notification` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `notification_type` VARCHAR(30) NOT NULL,
    `title` VARCHAR(100) NOT NULL,
    `content` VARCHAR(500) NOT NULL,
    `is_read` BOOLEAN NOT NULL DEFAULT FALSE,
    `sent_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `read_at` DATETIME NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_notification_user_id` (`user_id`),
    CONSTRAINT `fk_notification_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `ck_notification_type` CHECK (`notification_type` IN ('ALL', 'MISSION', 'EVENT', 'MARKET'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `user_setting` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `push_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `new_conversation_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `affinity_change_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `daily_mission_refresh_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `trade_completed_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `trade_offer_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `community_comment_notice_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_setting_user_id` (`user_id`),
    CONSTRAINT `fk_user_setting_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `album` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(150) NOT NULL,
    `artist_name` VARCHAR(100) NOT NULL,
    `artist_company` VARCHAR(100) NOT NULL,
    `track_count` INT NOT NULL,
    `track_total_second` INT NOT NULL,
    `description` TEXT NULL,
    `cover_image_url` VARCHAR(500) NOT NULL,
    `release_date` DATE NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `stage` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `album_id` BIGINT NOT NULL,
    `title` VARCHAR(150) NOT NULL,
    `description` TEXT NULL,
    `video_url` VARCHAR(500) NOT NULL,
    `video_type` VARCHAR(20) NOT NULL,
    `thumbnail_url` VARCHAR(500) NULL,
    `duration_seconds` INT NOT NULL,
    `recorded_at` DATETIME NOT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `is_title_video` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_stage_album_id` (`album_id`),
    CONSTRAINT `fk_stage_album` FOREIGN KEY (`album_id`) REFERENCES `album` (`id`),
    CONSTRAINT `ck_stage_video_type` CHECK (`video_type` IN ('MUSIC_VIDEO', 'CONCERT_VIDEO'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `stage_session` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `cube_ownership_id` BIGINT NOT NULL,
    `stage_id` BIGINT NOT NULL,
    `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `ended_at` DATETIME NULL,
    `last_position_seconds` INT NOT NULL DEFAULT 0,
    `viewed_seconds` INT NULL,
    `view_mode` VARCHAR(20) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PLAYING',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_stage_session_cube_ownership_id` (`cube_ownership_id`),
    KEY `idx_stage_session_stage_id` (`stage_id`),
    CONSTRAINT `fk_stage_session_cube_ownership` FOREIGN KEY (`cube_ownership_id`) REFERENCES `cube_ownership` (`id`),
    CONSTRAINT `fk_stage_session_stage` FOREIGN KEY (`stage_id`) REFERENCES `stage` (`id`),
    CONSTRAINT `ck_stage_session_view_mode` CHECK (`view_mode` IN ('NORMAL', 'AR')),
    CONSTRAINT `ck_stage_session_status` CHECK (`status` IN ('PLAYING', 'COMPLETED', 'CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `stage_capture` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `stage_session_id` BIGINT NOT NULL,
    `stage_capture_img_url` VARCHAR(500) NOT NULL,
    `captured_position_seconds` INT NULL,
    `captured_at` DATETIME NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_stage_capture_stage_session_id` (`stage_session_id`),
    CONSTRAINT `fk_stage_capture_stage_session` FOREIGN KEY (`stage_session_id`) REFERENCES `stage_session` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `track` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `album_id` BIGINT NOT NULL,
    `title` VARCHAR(150) NOT NULL,
    `artist_name` VARCHAR(100) NOT NULL,
    `audio_url` VARCHAR(500) NOT NULL,
    `duration_seconds` INT NOT NULL,
    `lyrics` VARCHAR(5000) NOT NULL,
    `track_number` INT NOT NULL,
    `is_title_track` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_track_album_id` (`album_id`),
    UNIQUE KEY `uk_track_album_number` (`album_id`, `track_number`),
    CONSTRAINT `fk_track_album` FOREIGN KEY (`album_id`) REFERENCES `album` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `track_session` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `cube_ownership_id` BIGINT NOT NULL,
    `track_id` BIGINT NOT NULL,
    `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `ended_at` DATETIME NULL,
    `last_position_seconds` INT NOT NULL DEFAULT 0,
    `viewed_seconds` INT NOT NULL DEFAULT 0,
    `play_mode` VARCHAR(20) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PLAYING',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_track_session_cube_ownership_id` (`cube_ownership_id`),
    KEY `idx_track_session_track_id` (`track_id`),
    CONSTRAINT `fk_track_session_cube_ownership` FOREIGN KEY (`cube_ownership_id`) REFERENCES `cube_ownership` (`id`),
    CONSTRAINT `fk_track_session_track` FOREIGN KEY (`track_id`) REFERENCES `track` (`id`),
    CONSTRAINT `ck_track_session_play_mode` CHECK (`play_mode` IN ('NORMAL', 'SPECIAL')),
    CONSTRAINT `ck_track_session_status` CHECK (`status` IN ('PLAYING', 'COMPLETED', 'CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `track_capture` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `track_session_id` BIGINT NOT NULL,
    `track_capture_img_url` VARCHAR(500) NOT NULL,
    `captured_position_seconds` INT NULL,
    `captured_at` DATETIME NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_track_capture_track_session_id` (`track_session_id`),
    CONSTRAINT `fk_track_capture_track_session` FOREIGN KEY (`track_session_id`) REFERENCES `track_session` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `album_image` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `album_id` BIGINT NOT NULL,
    `title` VARCHAR(150) NULL,
    `image_type` VARCHAR(30) NOT NULL,
    `album_contents_img_url` VARCHAR(500) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_album_image_album_id` (`album_id`),
    CONSTRAINT `fk_album_image_album` FOREIGN KEY (`album_id`) REFERENCES `album` (`id`),
    CONSTRAINT `ck_album_image_type` CHECK (`image_type` IN ('ALBUM_IMAGE', 'CONCERT_STILLCUT', 'YEZUL_FRAME'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `avatar_conversation_session` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `cube_ownership_id` BIGINT NOT NULL,
    `conversation_type` VARCHAR(20) NOT NULL,
    `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `ended_at` DATETIME NULL,
    `audio_url` VARCHAR(500) NULL,
    `audio_duration_seconds` INT NULL,
    `conversation_title` VARCHAR(50) NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_avatar_conversation_session_ownership_id` (`cube_ownership_id`),
    CONSTRAINT `fk_avatar_conversation_session_cube_ownership` FOREIGN KEY (`cube_ownership_id`) REFERENCES `cube_ownership` (`id`),
    CONSTRAINT `ck_avatar_conversation_session_type` CHECK (`conversation_type` IN ('TEXT', 'VOICE')),
    CONSTRAINT `ck_avatar_conversation_session_status` CHECK (`status` IN ('ACTIVE', 'NOT_ACTIVE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `avatar_conversation_message` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `conversation_session_id` BIGINT NOT NULL,
    `sender_type` VARCHAR(20) NOT NULL,
    `content` TEXT NOT NULL,
    `sequence_number` INT NOT NULL,
    `is_text_saved` BOOLEAN NOT NULL DEFAULT FALSE,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ALLOWED',
    `violation_type` VARCHAR(20) NULL,
    `sent_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_avatar_conversation_message_session_id` (`conversation_session_id`),
    UNIQUE KEY `uk_avatar_conversation_message_sequence` (`conversation_session_id`, `sequence_number`),
    CONSTRAINT `fk_avatar_conversation_message_session` FOREIGN KEY (`conversation_session_id`) REFERENCES `avatar_conversation_session` (`id`),
    CONSTRAINT `ck_avatar_conversation_message_sender` CHECK (`sender_type` IN ('USER', 'AVATAR')),
    CONSTRAINT `ck_avatar_conversation_message_status` CHECK (`status` IN ('ALLOWED', 'BLOCKED')),
    CONSTRAINT `ck_avatar_conversation_message_violation` CHECK (`violation_type` IS NULL OR `violation_type` IN ('PROFANITY', 'SEXUAL', 'THREAT'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `conversation_report` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `conversation_message_id` BIGINT NOT NULL,
    `reason` VARCHAR(50) NOT NULL,
    `detail_reason` VARCHAR(500) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_conversation_report_message_id` (`conversation_message_id`),
    CONSTRAINT `fk_conversation_report_message` FOREIGN KEY (`conversation_message_id`) REFERENCES `avatar_conversation_message` (`id`),
    CONSTRAINT `ck_conversation_report_reason` CHECK (`reason` IN ('INCORRECT_PERSONA', 'HALLUCINATION', 'INAPPROPRIATE_EXPRESSION', 'IMPERSONATION_OR_PRIVATE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `avatar_interaction_session` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `cube_ownership_id` BIGINT NOT NULL,
    `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `ended_at` DATETIME NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_avatar_interaction_session_ownership_id` (`cube_ownership_id`),
    CONSTRAINT `fk_avatar_interaction_session_cube_ownership` FOREIGN KEY (`cube_ownership_id`) REFERENCES `cube_ownership` (`id`),
    CONSTRAINT `ck_avatar_interaction_session_status` CHECK (`status` IN ('ACTIVE', 'COMPLETED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `avatar_interaction_picture` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `interaction_session_id` BIGINT NOT NULL,
    `picture_img_url` VARCHAR(500) NOT NULL,
    `pictured_at` DATETIME NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_avatar_interaction_picture_session_id` (`interaction_session_id`),
    CONSTRAINT `fk_avatar_interaction_picture_session` FOREIGN KEY (`interaction_session_id`) REFERENCES `avatar_interaction_session` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `post` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `board_type` VARCHAR(30) NOT NULL,
    `title` VARCHAR(150) NOT NULL,
    `content` TEXT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_post_board_type` (`board_type`),
    KEY `idx_post_user_id` (`user_id`),
    CONSTRAINT `fk_post_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `ck_post_board_type` CHECK (`board_type` IN ('FREE', 'CERTIFICATION')),
    CONSTRAINT `ck_post_status` CHECK (`status` IN ('ACTIVE', 'DELETED', 'REPORTED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `post_media` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `post_id` BIGINT NOT NULL,
    `post_image_url` VARCHAR(500) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_post_media_post_id` (`post_id`),
    CONSTRAINT `fk_post_media_post` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `comment` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `post_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `content` TEXT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_comment_post_id` (`post_id`),
    KEY `idx_comment_user_id` (`user_id`),
    CONSTRAINT `fk_comment_post` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`),
    CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `ck_comment_status` CHECK (`status` IN ('ACTIVE', 'DELETED', 'REPORTED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `post_like` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `post_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `is_liked` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_post_like_post_user` (`post_id`, `user_id`),
    KEY `idx_post_like_user_id` (`user_id`),
    CONSTRAINT `fk_post_like_post` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`),
    CONSTRAINT `fk_post_like_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `comment_like` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `comment_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `is_liked` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_comment_like_comment_user` (`comment_id`, `user_id`),
    KEY `idx_comment_like_user_id` (`user_id`),
    CONSTRAINT `fk_comment_like_comment` FOREIGN KEY (`comment_id`) REFERENCES `comment` (`id`),
    CONSTRAINT `fk_comment_like_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `market_product` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `cube_id` BIGINT NOT NULL,
    `product_image_url` VARCHAR(500) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_market_product_cube_id` (`cube_id`),
    CONSTRAINT `fk_market_product_cube` FOREIGN KEY (`cube_id`) REFERENCES `cube` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sell_listing` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `market_product_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `product_status` VARCHAR(30) NULL,
    `title` VARCHAR(20) NOT NULL,
    `description` VARCHAR(500) NOT NULL,
    `price` INT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_sell_listing_market_product_id` (`market_product_id`),
    KEY `idx_sell_listing_user_id` (`user_id`),
    CONSTRAINT `fk_sell_listing_market_product` FOREIGN KEY (`market_product_id`) REFERENCES `market_product` (`id`),
    CONSTRAINT `fk_sell_listing_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `ck_sell_listing_status` CHECK (`status` IN ('ACTIVE', 'SOLD', 'DELETED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `trade` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `sell_listing_id` BIGINT NOT NULL,
    `buyer_user_id` BIGINT NOT NULL,
    `buyer_phone_number` VARCHAR(20) NOT NULL,
    `buyer_address` VARCHAR(100) NOT NULL,
    `total_price` INT NOT NULL,
    `paid_time` DATETIME NULL,
    `sent_time` DATETIME NULL,
    `shipped_time` DATETIME NULL,
    `delivered_time` DATETIME NULL,
    `completed_time` DATETIME NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'PAID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_trade_sell_listing_id` (`sell_listing_id`),
    KEY `idx_trade_buyer_user_id` (`buyer_user_id`),
    CONSTRAINT `fk_trade_sell_listing` FOREIGN KEY (`sell_listing_id`) REFERENCES `sell_listing` (`id`),
    CONSTRAINT `fk_trade_buyer_user` FOREIGN KEY (`buyer_user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `ck_trade_status` CHECK (`status` IN ('PAID', 'SENT', 'SHIPPING', 'DELIVERED', 'COMPLETED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `listing_media` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `sell_listing_id` BIGINT NOT NULL,
    `image_url` VARCHAR(500) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_listing_media_sell_listing_id` (`sell_listing_id`),
    CONSTRAINT `fk_listing_media_sell_listing` FOREIGN KEY (`sell_listing_id`) REFERENCES `sell_listing` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `digital_certificate` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `trade_id` BIGINT NOT NULL,
    `network` VARCHAR(200) NOT NULL,
    `token_standard` VARCHAR(200) NOT NULL,
    `token_id` VARCHAR(200) NOT NULL,
    `contract_address` VARCHAR(200) NOT NULL,
    `tx_hash` VARCHAR(200) NOT NULL,
    `metadata_url` VARCHAR(200) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_digital_certificate_trade_id` (`trade_id`),
    CONSTRAINT `fk_digital_certificate_trade` FOREIGN KEY (`trade_id`) REFERENCES `trade` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
