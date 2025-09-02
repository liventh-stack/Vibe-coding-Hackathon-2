-- Run this in your MySQL instance
CREATE DATABASE IF NOT EXISTS medicounsel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medicounsel;

CREATE TABLE IF NOT EXISTS entries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_alias VARCHAR(64) DEFAULT NULL,
  entry_text TEXT NOT NULL,
  emotion_label VARCHAR(32) NOT NULL,
  emotion_scores TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
