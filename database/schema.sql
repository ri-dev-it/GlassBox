-- MySQL schema for the Explainable AI Loan Approval System (Milestone 3).
-- Flask-Migrate manages this in normal operation (see backend/README
-- section on `flask db upgrade`); this file is the reproducible reference
-- schema / can be run directly for a fresh setup.

CREATE DATABASE IF NOT EXISTS xai_loan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE xai_loan_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'applicant',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS applicants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_applicants_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    public_id VARCHAR(20) UNIQUE,
    applicant_id INT NOT NULL,
    features_json TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES applicants(id) ON DELETE CASCADE,
    INDEX idx_applications_applicant (applicant_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL UNIQUE,
    decision VARCHAR(20) NOT NULL,
    probability FLOAT NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS explanations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prediction_id INT NOT NULL,
    method VARCHAR(10) NOT NULL,
    contributions_json TEXT NOT NULL,
    plain_english TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE,
    UNIQUE KEY uq_prediction_method (prediction_id, method),
    INDEX idx_explanations_prediction (prediction_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS counterfactuals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prediction_id INT NOT NULL,
    found BOOLEAN NOT NULL DEFAULT FALSE,
    message TEXT,
    alternatives_json TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE,
    INDEX idx_counterfactuals_prediction (prediction_id)
) ENGINE=InnoDB;
