ALTER TABLE rag_document_chunks ADD COLUMN IF NOT EXISTS user_id BIGINT NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_user_id ON rag_document_chunks (user_id);
