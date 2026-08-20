-- MySQL 8 representation of the ThreadFlow domain schema for MySQL Workbench.
-- PostgreSQL remains the runtime source of truth; see schema.sql for exact DDL.

CREATE SCHEMA IF NOT EXISTS threadflow;
USE threadflow;

CREATE TABLE accounts_user (
    id CHAR(36) PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP(6) NULL,
    created_at TIMESTAMP(6) NOT NULL,
    is_active BOOLEAN NOT NULL,
    is_staff BOOLEAN NOT NULL,
    is_superuser BOOLEAN NOT NULL
);

CREATE TABLE comments_comment (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NULL,
    parent_id CHAR(36) NULL,
    root_id CHAR(36) NULL,
    author_name VARCHAR(150) NOT NULL,
    author_email VARCHAR(254) NOT NULL,
    homepage VARCHAR(200) NOT NULL,
    html_text LONGTEXT NOT NULL,
    search_text LONGTEXT NOT NULL,
    depth INT UNSIGNED NOT NULL,
    score INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL,
    updated_at TIMESTAMP(6) NOT NULL,
    CONSTRAINT root_comment_depth_zero CHECK (parent_id IS NOT NULL OR depth = 0),
    CONSTRAINT comments_user_fk FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE SET NULL,
    CONSTRAINT comments_parent_fk FOREIGN KEY (parent_id) REFERENCES comments_comment(id) ON DELETE CASCADE,
    CONSTRAINT comments_root_fk FOREIGN KEY (root_id) REFERENCES comments_comment(id) ON DELETE CASCADE,
    INDEX comments_parent_created_idx (parent_id, created_at),
    INDEX comments_root_created_idx (root_id, created_at),
    INDEX comment_root_date_idx (created_at DESC, id DESC),
    INDEX comment_root_name_idx (author_name, id),
    INDEX comment_root_email_idx (author_email, id)
);

CREATE TABLE attachments_attachment (
    id CHAR(36) PRIMARY KEY,
    comment_id CHAR(36) NULL,
    owner_id CHAR(36) NULL,
    purpose VARCHAR(16) NOT NULL,
    kind VARCHAR(16) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file VARCHAR(100) NOT NULL,
    content_type VARCHAR(64) NOT NULL,
    size INT UNSIGNED NOT NULL,
    width INT UNSIGNED NULL,
    height INT UNSIGNED NULL,
    claim_token_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL,
    CONSTRAINT attachments_comment_fk FOREIGN KEY (comment_id) REFERENCES comments_comment(id) ON DELETE CASCADE,
    CONSTRAINT attachments_owner_fk FOREIGN KEY (owner_id) REFERENCES accounts_user(id) ON DELETE SET NULL,
    INDEX attachments_comment_created_idx (comment_id, created_at),
    INDEX attachments_owner_idx (owner_id)
);

CREATE TABLE comments_commentvote (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    comment_id CHAR(36) NOT NULL,
    identity VARCHAR(100) NOT NULL,
    value SMALLINT NOT NULL,
    created_at TIMESTAMP(6) NOT NULL,
    updated_at TIMESTAMP(6) NOT NULL,
    CONSTRAINT comment_vote_value_valid CHECK (value IN (-1, 1)),
    CONSTRAINT comment_votes_comment_fk FOREIGN KEY (comment_id) REFERENCES comments_comment(id) ON DELETE CASCADE,
    CONSTRAINT unique_vote_per_identity UNIQUE (comment_id, identity)
);

CREATE TABLE events_outboxevent (
    id CHAR(36) PRIMARY KEY,
    event_type VARCHAR(80) NOT NULL,
    aggregate_id CHAR(36) NOT NULL,
    payload JSON NOT NULL,
    created_at TIMESTAMP(6) NOT NULL,
    published_at TIMESTAMP(6) NULL,
    attempts INT UNSIGNED NOT NULL DEFAULT 0,
    last_error LONGTEXT NOT NULL,
    INDEX outbox_pending_created_idx (published_at, created_at)
);

CREATE TABLE events_processedevent (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    event_id CHAR(36) NOT NULL,
    consumer_name VARCHAR(80) NOT NULL,
    processed_at TIMESTAMP(6) NOT NULL,
    CONSTRAINT unique_event_per_consumer UNIQUE (event_id, consumer_name)
);
