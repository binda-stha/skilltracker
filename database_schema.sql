-- ============================================================
-- SkillTracker Database Schema
-- BCA 6th Semester Project II - Tribhuvan University
-- Author: Binda Shrestha
-- Database: skilltracker
-- ============================================================

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS skilltracker;
USE skilltracker;

-- ============================================================
-- TABLE: roles
-- Purpose: Store role definitions for users
-- ============================================================
CREATE TABLE roles (
    role_ID INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default roles
INSERT INTO roles (role_name, description) VALUES
('admin', 'Administrator with full system access'),
('user', 'Regular user with limited access');

-- ============================================================
-- TABLE: users
-- Purpose: Store user account information
-- Security: Passwords are hashed using werkzeug.security
-- ============================================================
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role_ID INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_ID) REFERENCES roles(role_ID),
    INDEX idx_email (email),
    INDEX idx_role (role_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: skills
-- Purpose: Store skill information for users
-- Relationships: Each skill belongs to one user
-- ============================================================
CREATE TABLE skills (
    skill_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    skill_name VARCHAR(150) NOT NULL,
    description TEXT,
    current_progress INT DEFAULT 0 CHECK (current_progress >= 0 AND current_progress <= 100),
    target_hours INT DEFAULT 0,
    target_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_progress (current_progress),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: user_profile
-- Purpose: Store personal information for CV generation
-- ============================================================
CREATE TABLE user_profile (
    profile_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    linkedin VARCHAR(255),
    github VARCHAR(255),
    professional_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_profile (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: education
-- Purpose: Store education details for CV
-- ============================================================
CREATE TABLE education (
    education_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    degree VARCHAR(100) NOT NULL,
    institution VARCHAR(100) NOT NULL,
    start_year YEAR NOT NULL,
    end_year YEAR,
    gpa DECIMAL(3,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: experience
-- Purpose: Store work experience for CV
-- ============================================================
CREATE TABLE experience (
    experience_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    company VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: projects
-- Purpose: Store project details for CV
-- ============================================================
CREATE TABLE projects (
    project_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    project_name VARCHAR(100) NOT NULL,
    description TEXT,
    technologies VARCHAR(255),
    github_link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: certifications
-- Purpose: Store certification details for CV
-- ============================================================
CREATE TABLE certifications (
    certification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    certification_name VARCHAR(100) NOT NULL,
    issuing_organization VARCHAR(100) NOT NULL,
    issue_date DATE NOT NULL,
    expiry_date DATE,
    credential_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: skill_logs
-- Purpose: Store skill practice logs and hours tracking
-- ============================================================
CREATE TABLE skill_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    hours_spent DECIMAL(5,2) NOT NULL,
    log_date DATE NOT NULL,
    reflection_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
    INDEX idx_user_skill (user_id, skill_id),
    INDEX idx_log_date (log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User progress summary
CREATE VIEW user_progress_summary AS
SELECT 
    u.id,
    u.email,
    COUNT(s.skill_id) as total_skills,
    AVG(s.current_progress) as average_progress,
    sum(CASE WHEN s.current_progress = 100 THEN 1 ELSE 0 END) as completed_skills,
    MIN(s.created_at) as first_skill_date,
    MAX(s.updated_at) as last_updated
FROM users u
LEFT JOIN skills s ON u.id = s.user_id
WHERE u.role_ID = 2
GROUP BY u.id, u.email;

-- Skill categories summary
CREATE VIEW skill_category_summary AS
SELECT 
    s.skill_name,
    COUNT(*) as users_with_skill,
    AVG(s.current_progress) as average_progress,
    MIN(s.current_progress) as min_progress,
    MAX(s.current_progress) as max_progress
FROM skills s
GROUP BY s.skill_name;

-- ============================================================
-- INDICES for Performance Optimization
-- ============================================================

CREATE INDEX idx_skills_user_skill ON skills(user_id, skill_id);
CREATE INDEX idx_users_role_created ON users(role_ID, created_at);

-- ============================================================
-- SAMPLE DATA (For Testing - Optional)
-- ============================================================

-- Sample Users (Passwords are hashed - these are examples)
-- INSERT INTO users (email, password, role_ID) VALUES
-- ('admin@skilltracker.com', 'hashed_password_here', 1),
-- ('student@skilltracker.com', 'hashed_password_here', 2);

-- ============================================================
-- END OF SCHEMA
-- ============================================================
