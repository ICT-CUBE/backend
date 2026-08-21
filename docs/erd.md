```mermaid
erDiagram
    USER {
        bigint id PK
        varchar_255 email "NOT NULL, UNIQUE"
        varchar_255 password_hash "NULL"
        varchar_20 login_provider "NOT NULL, Enum: EMAIL | GOOGLE | APPLE"
        varchar_255 provider_user_id "NULL"
        varchar_8 nickname "NULL"
        varchar_50 profile_character_img_url "NULL"
        int chat_violation_count "NOT NULL, DEFAULT: 0"
        varchar_20 status "NOT NULL, Enum: ACTIVE | WITHDRAWN | SUSPENDED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    AUTH_SESSION {
        bigint id PK
        bigint user_id FK "NOT NULL"
        varchar_64 token_jti "NOT NULL, UNIQUE"
        varchar_20 status "NOT NULL, Enum: ACTIVE | REVOKED"
        datetime issued_at "NOT NULL"
        datetime expires_at "NOT NULL"
        datetime revoked_at "NULL"
        varchar_255 device_id "NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    CUBE {
        bigint id PK
        varchar_100 serial_number "NOT NULL, UNIQUE"
        varchar_150 product_name "NOT NULL"
        varchar_255 ownership_code_hash "NOT NULL"
        varchar_20 artist_name "NOT NULL"
        varchar_20 status "NOT NULL, Enum: UNREGISTERED | OWNED | TRADE_PENDING | DISABLED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    CUBE_VERIFICATION {
        bigint id PK
        bigint user_id FK "NOT NULL"
        bigint cube_id FK "NOT NULL"
        varchar_20 verification_status "NOT NULL, Enum: PENDING | SUCCESS | FAILED | EXPIRED"
        datetime code_expires_at "NULL"
        datetime verified_at "NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    CUBE_OWNERSHIP {
        bigint id PK
        bigint user_id FK "NOT NULL"
        bigint cube_id FK "NOT NULL"
        varchar_30 avatar_nickname "NULL"
        varchar_20 ownership_status "NOT NULL, Enum: ACTIVE | TRANSFERRED | REVOKED"
        boolean is_last_accessed "NOT NULL, DEFAULT: false"
        datetime acquired_at "NOT NULL"
        datetime transferred_at "NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    AFFINITY {
        bigint id PK
        bigint cube_ownership_id FK "NOT NULL, UNIQUE"
        bigint level_id FK "NOT NULL"
        int current_xp "NOT NULL, DEFAULT: 0"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    LEVEL {
        bigint id PK
        bigint reward_item_id FK "NOT NULL"
        int level "NOT NULL"
        int level_xp "NOT NULL"
        varchar_30 level_name "NOT NULL, Enum: Intro | Friend | Close | Special"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    REWARD_ITEM {
        bigint id PK
        varchar_100 name "NOT NULL"
        varchar_30 reward_type "NOT NULL, Enum: AFFINITY_POINT | CONVERSATION_COUNT | COMMENT_TYPE | SPECIAL_COMMENT | AVATAR_FIRST_TALK | BADGE"
        varchar_255 description "NULL"
        int reward_count "NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    MISSION {
        bigint id PK
        bigint reward_item_id FK "NOT NULL"
        varchar_20 mission_type "NOT NULL, Enum: DAILY | EVENT"
        varchar_100 title "NOT NULL"
        varchar_255 description "NULL"
        varchar_500 mission_info "NULL"
        varchar_50 target_action "NOT NULL, Enum: HOME_VIEW | CONVERSATION | ALBUM_PLAY | OPEN_GALLERY | COMMUNITY_POST | SUMMON_AVATAR | PLAY_MUSIC_VIDEO"
        int target_count "NOT NULL"
        datetime start_at "NULL"
        datetime end_at "NULL"
        boolean is_active "NOT NULL, DEFAULT: true"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    MISSION_PROGRESS {
        bigint id PK
        bigint cube_ownership_id FK "NOT NULL, COMPOSITE UNIQUE: cube_ownership_id | mission_id"
        bigint mission_id FK "NOT NULL, COMPOSITE UNIQUE: cube_ownership_id | mission_id"
        int current_count "NOT NULL, DEFAULT: 0"
        varchar_20 status "NOT NULL, DEFAULT: IN_PROGRESS, Enum: IN_PROGRESS | COMPLETED | REWARDED"
        boolean reward_claimed "NOT NULL, DEFAULT: false"
        datetime completed_at "NULL"
        datetime claimed_at "NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    USER_REWARD {
        bigint id PK
        bigint cube_ownership_id FK "NOT NULL, COMPOSITE UNIQUE: cube_ownership_id | reward_item_id"
        bigint reward_item_id FK "NOT NULL, COMPOSITE UNIQUE: cube_ownership_id | reward_item_id"
        datetime acquired_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    NOTIFICATION {
        bigint id PK
        bigint user_id FK "NOT NULL"
        varchar_30 notification_type "NOT NULL, Enum: ALL | MISSION | EVENT | MARKET"
        varchar_100 title "NOT NULL"
        varchar_500 content "NOT NULL"
        boolean is_read "NOT NULL, DEFAULT: false"
        datetime sent_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime read_at "NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    USER_SETTING {
        bigint id PK
        bigint user_id FK "NOT NULL, UNIQUE"
        boolean push_enabled "NOT NULL, DEFAULT: true"
        boolean new_conversation_enabled "NOT NULL, DEFAULT: true"
        boolean affinity_change_enabled "NOT NULL, DEFAULT: true"
        boolean daily_mission_refresh_enabled "NOT NULL, DEFAULT: true"
        boolean trade_completed_enabled "NOT NULL, DEFAULT: true"
        boolean trade_offer_enabled "NOT NULL, DEFAULT: true"
        boolean community_comment_notice_enabled "NOT NULL, DEFAULT: true"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    ALBUM {
        bigint id PK
        varchar_150 title "NOT NULL"
        varchar_100 artist_name "NOT NULL"
        varchar_100 artist_company "NOT NULL"
        int track_count "NOT NULL"
        int track_total_second "NOT NULL"
        text description "NULL"
        varchar_500 cover_image_url "NOT NULL"
        date release_date "NOT NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    STAGE {
        bigint id PK
        bigint album_id FK "NOT NULL"
        varchar_150 title "NOT NULL"
        text description "NULL"
        varchar_500 video_url "NOT NULL"
        varchar_20 video_type "NOT NULL, Enum: MUSIC_VIDEO | CONCERT_VIDEO"
        varchar_500 thumbnail_url "NULL"
        int duration_seconds "NOT NULL"
        datetime recorded_at "NOT NULL"
        boolean is_active "NOT NULL, DEFAULT: true"
        boolean is_title_video "NOT NULL, DEFAULT: false"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    STAGE_SESSION {
        bigint id PK
        bigint cube_ownership_id FK "NOT NULL"
        bigint stage_id FK "NOT NULL"
        datetime started_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime ended_at "NULL"
        int last_position_seconds "NOT NULL, DEFAULT: 0"
        int viewed_seconds "NULL, DEFAULT: 0"
        varchar_20 view_mode "NOT NULL, Enum: NORMAL | AR"
        varchar_20 status "NOT NULL, DEFAULT: PLAYING, Enum: PLAYING | COMPLETED | CANCELLED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    STAGE_CAPTURE {
        bigint id PK
        bigint stage_session_id FK "NOT NULL"
        varchar_500 stage_capture_img_url "NOT NULL"
        int captured_position_seconds "NULL"
        datetime captured_at "NOT NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    TRACK {
        bigint id PK
        bigint album_id FK "NOT NULL"
        varchar_150 title "NOT NULL"
        varchar_100 artist_name "NOT NULL"
        varchar_500 audio_url "NOT NULL"
        int duration_seconds "NOT NULL"
        varchar_5000 lyrics "NOT NULL"
        int track_number "NOT NULL"
        boolean is_title_track "NOT NULL, DEFAULT: false"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    TRACK_SESSION {
        bigint id PK
        bigint cube_ownership_id FK "NOT NULL"
        bigint track_id FK "NOT NULL"
        datetime started_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime ended_at "NULL"
        int last_position_seconds "NOT NULL, DEFAULT: 0"
        int viewed_seconds "NOT NULL, DEFAULT: 0"
        varchar_20 play_mode "NOT NULL, Enum: NORMAL | SPECIAL"
        varchar_20 status "NOT NULL, DEFAULT: PLAYING, Enum: PLAYING | COMPLETED | CANCELLED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    TRACK_CAPTURE {
        bigint id PK
        bigint track_session_id FK "NOT NULL"
        varchar_500 track_capture_img_url "NOT NULL"
        int captured_position_seconds "NULL"
        datetime captured_at "NOT NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    ALBUM_IMAGE {
        bigint id PK
        bigint album_id FK "NOT NULL"
        varchar_150 title "NULL"
        varchar_30 image_type "NOT NULL, Enum: ALBUM_IMAGE | CONCERT_STILLCUT | YEZUL_FRAME"
        varchar_500 album_contents_img_url "NOT NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    AVATAR_CONVERSATION_SESSION {
        bigint id PK
        bigint cube_ownership_id FK "NOT NULL"
        varchar_20 conversation_type "NOT NULL, Enum: TEXT | VOICE"
        datetime started_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime ended_at "NULL"
        varchar_500 audio_url "NULL"
        int audio_duration_seconds "NULL"
        varchar_50 conversation_title "NULL"
        varchar_20 status "NOT NULL, DEFAULT: ACTIVE, Enum: ACTIVE | NOT_ACTIVE"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    AVATAR_CONVERSATION_MESSAGE {
        bigint id PK
        bigint conversation_session_id FK "NOT NULL"
        varchar_20 sender_type "NOT NULL, Enum: USER | AVATAR"
        text content "NOT NULL"
        int sequence_number "NOT NULL"
        boolean is_text_saved "NOT NULL, DEFAULT: false"
        varchar_20 status "NOT NULL, DEFAULT: ALLOWED, Enum: ALLOWED | BLOCKED"
        varchar_20 violation_type "NULL, Enum: PROFANITY | SEXUAL | THREAT"
        datetime sent_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    CONVERSATION_REPORT {
        bigint id PK
        bigint conversation_message_id FK "NOT NULL"
        varchar_50 reason "NOT NULL, Enum: INCORRECT_PERSONA | HALLUCINATION | INAPPROPRIATE_EXPRESSION | IMPERSONATION_OR_PRIVATE"
        varchar_500 detail_reason "NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    AVATAR_INTERACTION_SESSION {
        bigint id PK
        bigint cube_ownership_id FK "NOT NULL"
        datetime started_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime ended_at "NULL"
        varchar_20 status "NOT NULL, DEFAULT: ACTIVE, Enum: ACTIVE | COMPLETED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    AVATAR_INTERACTION_PICTURE {
        bigint id PK
        bigint interaction_session_id FK "NOT NULL"
        varchar_500 picture_img_url "NOT NULL"
        datetime pictured_at "NOT NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    POST {
        bigint id PK
        bigint user_id FK "NOT NULL"
        bigint board_type FK "NOT NULL, Enum: FREE | CERTIFICATION"
        varchar_150 title "NOT NULL"
        text content "NOT NULL"
        varchar_20 status "NOT NULL, DEFAULT: ACTIVE, Enum: ACTIVE | DELETED | REPORTED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    POST_MEDIA {
        bigint id PK
        bigint post_id FK "NOT NULL"
        varchar_500 post_image_url "NOT NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    COMMENT {
        bigint id PK
        bigint post_id FK "NOT NULL"
        bigint user_id FK "NOT NULL"
        text content "NOT NULL"
        varchar_20 status "NOT NULL, DEFAULT: ACTIVE, Enum: ACTIVE | DELETED | REPORTED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    POST_LIKE {
        bigint id PK
        bigint post_id FK "NOT NULL, UNIQUE"
        bigint user_id FK "NOT NULL, UNIQUE"
        boolean is_liked "NOT NULL, DEFAULT: true"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    COMMENT_LIKE {
        bigint id PK
        bigint comment_id FK "NOT NULL, UNIQUE"
        bigint user_id FK "NOT NULL, UNIQUE"
        boolean is_liked "NOT NULL, DEFAULT: true"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    SELL_LISTING {
        bigint id PK
        bigint market_product_id FK "NOT NULL"
        bigint user_id FK "NOT NULL"
        varchar_30 product_status "NULL"
        varchar_20 title "NOT NULL"
        varchar_500 description "NOT NULL"
        int price "NOT NULL"
        varchar_20 status "NOT NULL, DEFAULT: ACTIVE, Enum: ACTIVE | SOLD | DELETED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    TRADE {
        bigint id PK
        bigint sell_listing_id FK "NOT NULL"
        bigint buyer_user_id FK "NOT NULL"
        varchar_20 buyer_phone_number "NOT NULL"
        varchar_100 buyer_address "NOT NULL"
        int total_price "NOT NULL"
        datetime paid_time "NULL"
        datetime sent_time "NULL"
        datetime shipped_time "NULL"
        datetime delivered_time "NULL"
        datetime completed_time "NULL"        
        varchar_30 status "NOT NULL, DEFAULT: PAID, Enum: PAID | SENT | SHIPPING | DELIVERED | COMPLETED"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
    }

    DIGITAL_CERTIFICATE {
        bigint id PK
        bigint trade_id FK "NOT NULL"
        varchar_200 network "NOT NULL"
        varchar_200 token_standard "NOT NULL"
        varchar_200 token_id "NOT NULL"
        varchar_200 contract_address "NOT NULL"
        varchar_200 tx_hash "NOT NULL"
        varchar_200 metadata_url "NOT NULL"
    }

    MARKET_PRODUCT {
        bigint id PK
        bigint cube_id FK "NOT NULL"
        varchar_500 product_image_url "NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }

    LISTING_MEDIA {
        bigint id PK
        bigint sell_listing_id FK "NOT NULL"
        varchar_500 image_url "NOT NULL"
        datetime created_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime updated_at "NOT NULL, DEFAULT: CURRENT_TIMESTAMP"
        datetime deleted_at "NULL"
    }


    USER ||--o{ AUTH_SESSION : "has"
    USER ||--o{ CUBE_VERIFICATION : "requests"
    CUBE ||--o{ CUBE_VERIFICATION : "is verified through"
    USER ||--o{ CUBE_OWNERSHIP : "owns"
    CUBE ||--o{ CUBE_OWNERSHIP : "has ownership records"
    CUBE_OWNERSHIP ||--|| AFFINITY : "has"
    LEVEL ||--o{ AFFINITY : "current level"
    REWARD_ITEM ||--o{ LEVEL : "level reward"
    REWARD_ITEM ||--o{ MISSION : "mission reward"
    MISSION ||--o{ MISSION_PROGRESS : "has progress"
    CUBE_OWNERSHIP ||--o{ MISSION_PROGRESS : "performs"
    REWARD_ITEM ||--o{ USER_REWARD : "is acquired as"
    CUBE_OWNERSHIP ||--o{ USER_REWARD : "owns"
    USER ||--o{ NOTIFICATION : "receives"
    USER ||--o| USER_SETTING : "has"
    ALBUM ||--o{ STAGE : "contains"
    ALBUM ||--|{ TRACK : "contains"
    ALBUM ||--o{ ALBUM_IMAGE : "contains"
    CUBE_OWNERSHIP ||--o{ STAGE_SESSION : "creates"
    STAGE ||--o{ STAGE_SESSION : "played_in"
    STAGE_SESSION ||--o{ STAGE_CAPTURE : "contains"
    CUBE_OWNERSHIP ||--o{ TRACK_SESSION : "creates"
    TRACK ||--o{ TRACK_SESSION : "played_in"
    TRACK_SESSION ||--o{ TRACK_CAPTURE : "contains"
    CUBE_OWNERSHIP ||--o{ AVATAR_CONVERSATION_SESSION : "creates"
    AVATAR_CONVERSATION_SESSION ||--|{ AVATAR_CONVERSATION_MESSAGE : "contains"
    AVATAR_CONVERSATION_MESSAGE ||--o| CONVERSATION_REPORT : "reported_as"
    CUBE_OWNERSHIP ||--o{ AVATAR_INTERACTION_SESSION : "creates"
    AVATAR_INTERACTION_SESSION ||--o{ AVATAR_INTERACTION_PICTURE : "contains"
    USER ||--o{ POST : "writes"
    POST ||--o{ POST_MEDIA : "contains"
    POST ||--o{ COMMENT : "has"
    USER ||--o{ COMMENT : "writes"
    POST ||--o{ POST_LIKE : "receives"
    USER ||--o{ POST_LIKE : "creates"
    COMMENT ||--o{ COMMENT_LIKE : "receives"
    USER ||--o{ COMMENT_LIKE : "creates"
    SELL_LISTING ||--o| TRADE : "creates"
    CUBE ||--o{ MARKET_PRODUCT : "upload"
    SELL_LISTING ||--o{ LISTING_MEDIA : "contains"
    TRADE ||--o| DIGITAL_CERTIFICATE : "contains"
```
