# ===============================================
# Personalized Learning Platform Database
# ===============================================
#
# Objective:
# Create an SQLite database capable of storing:
# - User profiles
# - Uploaded courses
# - AI generations
# - User feedback
#
# The database is composed of four main tables:
# profiles, courses, generations and feedbacks.
#
# Relationships are managed using foreign keys.
# This allows us to connect users, learning
# resources, generated content and feedback.
#
# ===============================================

import sqlite3

# Create (or open) the SQLite database
conn = sqlite3.connect("learning_platform.db")

# Create a cursor to execute SQL commands
cursor = conn.cursor()

# ===============================================
# Profiles Table
# Stores user information and learning preferences
# ===============================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    learning_style TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ===============================================
# Courses Table
# Stores uploaded courses and course information
# ===============================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    course_name TEXT NOT NULL,
    file_path TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
)
""")

# ===============================================
# Generations Table
# Stores AI generated learning content
# ===============================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    course_id INTEGER,
    prompt TEXT,
    generated_content TEXT,
    generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
""")

# ===============================================
# Feedbacks Table
# Stores user ratings and comments on AI outputs
# ===============================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    generation_id INTEGER,
    rating INTEGER,
    comment TEXT,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (generation_id) REFERENCES generations(id)
)
""")

# Save all changes
conn.commit()

# Close the database
conn.close()

# Confirmation message
print("Database successfully created.")

# ===============================================
# Final Result
#
# The database now contains:
# - profiles
# - courses
# - generations
# - feedbacks
#
# It can store all information required for the
# personalized learning platform and supports
# future expansion if additional features are
# implemented.
# ===============================================