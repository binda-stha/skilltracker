-- SkillTracker Database Schema
-- BCA 6th Semester Project II - Tribhuvan University
-- Author: Binda Shrestha
-- Created: March 27, 2026

-- Create database
CREATE DATABASE IF NOT EXISTS skilltracker;
USE skilltracker;

-- Roles table (Admin=1, User=2)
CREATE TABLE IF NOT EXISTS roles (
    role_ID INT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role_ID INT NOT NULL DEFAULT 2,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    bio TEXT,
    profile_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_ID) REFERENCES roles(role_ID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Skills table
CREATE TABLE IF NOT EXISTS skills (
    skill_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    skill_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    current_progress DECIMAL(5,2) DEFAULT 0.00 CHECK (current_progress >= 0 AND current_progress <= 100),
    target_hours DECIMAL(8,2) DEFAULT 0.00,
    proficiency_level ENUM('Beginner', 'Intermediate', 'Advanced', 'Expert') DEFAULT 'Beginner',
    priority ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
    target_date DATE,
    status ENUM('Active', 'Completed', 'Paused', 'Archived') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_skill (user_id, skill_name),
    INDEX idx_category (category),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Progress log table (for tracking skill progress history)
CREATE TABLE IF NOT EXISTS progress_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    skill_id INT NOT NULL,
    user_id INT NOT NULL,
    previous_progress DECIMAL(5,2),
    new_progress DECIMAL(5,2) NOT NULL,
    hours_spent DECIMAL(5,2) DEFAULT 0.00,
    notes TEXT,
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_skill_date (skill_id, log_date),
    INDEX idx_user_date (user_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Skill logs table (daily learning logs)
CREATE TABLE IF NOT EXISTS skill_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    hours_spent DECIMAL(5,2) NOT NULL,
    log_date DATE NOT NULL,
    reflection_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, log_date),
    INDEX idx_skill_date (skill_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- User profile table (extended profile information)
CREATE TABLE IF NOT EXISTS user_profile (
    profile_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    linkedin VARCHAR(255),
    github VARCHAR(255),
    professional_summary TEXT,
    linkedin_url VARCHAR(255),
    github_url VARCHAR(255),
    portfolio_url VARCHAR(255),
    resume_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Education table
CREATE TABLE IF NOT EXISTS education (
    education_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    degree VARCHAR(255) NOT NULL,
    institution VARCHAR(255) NOT NULL,
    field_of_study VARCHAR(255),
    start_year INT,
    end_year INT,
    gpa VARCHAR(10),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_education (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Experience table
CREATE TABLE IF NOT EXISTS experience (
    experience_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_experience (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    technologies VARCHAR(255),
    github_link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_projects (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Certifications table
CREATE TABLE IF NOT EXISTS certifications (
    certification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    certification_name VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255) NOT NULL,
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_certifications (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default roles
INSERT IGNORE INTO roles (role_ID, role_name, description) VALUES
(1, 'Admin', 'System administrator with full access'),
(2, 'User', 'Regular user with skill tracking access');

-- Insert test admin user (password: admin123)
INSERT IGNORE INTO users (email, password, role_ID, first_name, last_name) VALUES
('admin@skilltracker.com', 'pbkdf2:sha256:600000$ekUJppLAJqtzXqMs$7fece26823b5df9cb8d6dcb2e48b0d574b7d5b1f95d2e95533a7431d59ebc6b5', 1, 'System', 'Administrator');

-- Insert test regular user (password: password123)
INSERT IGNORE INTO users (email, password, role_ID, first_name, last_name) VALUES
('student@skilltracker.com', 'pbkdf2:sha256:600000$enUKUJukb57m7ihe$074e7ee86c72bb2f25195bbc6299cfcfb00a635320dbde99912ae5834cb73bab', 2, 'John', 'Doe');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_ID);
CREATE INDEX IF NOT EXISTS idx_skills_user_progress ON skills(user_id, current_progress);
CREATE INDEX IF NOT EXISTS idx_progress_log_skill_date ON progress_log(skill_id, log_date DESC);
CREATE INDEX IF NOT EXISTS idx_skill_logs_user_date ON skill_logs(user_id, log_date DESC);

-- Create view for user statistics
CREATE OR REPLACE VIEW user_skill_stats AS
SELECT
    u.id as user_id,
    u.email,
    u.first_name,
    u.last_name,
    COUNT(s.skill_id) as total_skills,
    AVG(s.current_progress) as avg_progress,
    SUM(s.target_hours) as total_target_hours,
    COUNT(CASE WHEN s.status = 'Completed' THEN 1 END) as completed_skills,
    COUNT(CASE WHEN s.proficiency_level = 'Expert' THEN 1 END) as expert_skills
FROM users u
LEFT JOIN skills s ON u.id = s.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name;

-- Create view for skill categories
CREATE OR REPLACE VIEW skill_category_stats AS
SELECT
    category,
    COUNT(*) as skill_count,
    AVG(current_progress) as avg_progress,
    COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed_count
FROM skills
WHERE category IS NOT NULL AND category != ''
GROUP BY category
ORDER BY skill_count DESC;

COMMIT;