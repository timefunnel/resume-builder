ALTER TABLE interview_sessions ADD COLUMN resume_id BIGINT NULL COMMENT '关联简历 ID';
CREATE INDEX idx_interview_sessions_user_resume_updated_at ON interview_sessions(user_id, resume_id, updated_at);
