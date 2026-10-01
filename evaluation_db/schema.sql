-- ===============================================
-- Personalized Learning Platform — SQLite schema
-- ===============================================
--
-- Four tables: profiles, courses, generations, feedbacks.
-- Executed by create_database.py; safe to re-run (IF NOT EXISTS).

PRAGMA foreign_keys = ON;

-- -----------------------------------------------
-- Profiles
-- User information and learning preferences.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    learning_style TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------
-- Courses
-- Uploaded course files, linked to a profile.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    course_name TEXT NOT NULL,
    file_path TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

-- -----------------------------------------------
-- Generations
-- AI-generated study material for a course.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    course_id INTEGER,
    prompt TEXT,
    generated_content TEXT,
    generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- -----------------------------------------------
-- Feedbacks
-- User ratings (1-5) and comments on a generation.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    generation_id INTEGER,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (generation_id) REFERENCES generations(id)
);
