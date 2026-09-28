# Database Folder

This folder contains all files related to the SQLite database used by the Personalized Learning Platform.

## Contents

### create_database.py
Python script responsible for creating the SQLite database and all required tables.

Run:

```bash
python create_database.py
```

This automatically creates:

```text
learning_platform.db
```

### learning_platform.db
SQLite database file containing all application data.

Stored information includes:

- User profiles
- Uploaded courses
- AI generations
- User feedback

### DATABASE.md
Database documentation file.

This document contains:

- Database overview
- Database schema
- Table descriptions
- Relationships between tables
- Design choices
- Future improvements

## Database Structure

The database consists of four main tables:

```text
profiles
courses
generations
feedbacks
```

Together, these tables support the personalized learning system by storing user preferences, educational resources, AI-generated content, and feedback.

## Technology Stack

- SQLite
- Python (sqlite3 library)

## Purpose

The database provides persistent storage for the platform and enables:

- User profile management
- Learning style tracking
- Course management
- AI content generation history
- Feedback collection and analysis

The current database structure is lightweight, scalable, and suitable for the project's educational objectives.
