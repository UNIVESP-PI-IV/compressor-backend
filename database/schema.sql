CREATE DATABASE IF NOT EXISTS compressor_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE compressor_db;

CREATE TABLE IF NOT EXISTS readings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  temperature DECIMAL(12, 6) NOT NULL,
  `timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_readings_timestamp (`timestamp`)
);
