CREATE TABLE IF NOT EXISTS users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100) NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

ALTER TABLE interview_sessions
    ADD COLUMN IF NOT EXISTS user_id BIGINT NULL COMMENT '所属用户 ID';

ALTER TABLE interview_session_messages
    ADD COLUMN IF NOT EXISTS user_id BIGINT NULL COMMENT '所属用户 ID';

CREATE INDEX idx_interview_sessions_user_updated_at ON interview_sessions(user_id, updated_at);
CREATE INDEX idx_interview_session_messages_user_created_at ON interview_session_messages(user_id, created_at);
