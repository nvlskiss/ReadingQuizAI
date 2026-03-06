import sqlite3

database = 'notebook.db'
create_tables = ["""
    CREATE TABLE IF NOT EXISTS question_setting (
        id INTEGER PRIMARY KEY,
        file_input BLOB NULL,
        text_input TEXT NULL,
        multiple_choice_bool INTEGER NOT NULL CHECK (multiple_choice_bool IN (0, 1)),
        true_or_false_bool INTEGER NOT NULL CHECK (true_or_false_bool IN (0, 1)),
        identification_bool INTEGER NOT NULL CHECK (identification_bool IN (0, 1)),
        essay_bool INTEGER NOT NULL CHECK (essay_bool IN (0, 1)),
        multiple_choice_qty INTEGER NOT NULL,
        true_or_false_qty INTEGER NOT NULL,
        identification_qty INTEGER NOT NULL,
        essay_qty INTEGER NOT NULL,
        language TEXT NOT NULL CHECK (language IN ('English', 'Filipino'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS quiz (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS quiz_question (
        id INTEGER PRIMARY KEY,
        quiz_id INTEGER,
        question_type TEXT NOT NULL,
        content TEXT NOT NULL,
        FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS quiz_answer (
        id INTEGER PRIMARY KEY,
        quiz_id INTEGER,
        question_id INTEGER,
        quiz_question_answer_choice TEXT NOT NULL,
        quiz_question_answer_correct TEXT NOT NULL,
        FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES quiz_question(id) ON DELETE CASCADE

        
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS notebook (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        question_setting_id INTEGER,
        quiz_id INTEGER,
        FOREIGN KEY (question_setting_id) REFERENCES question_setting(id) ON DELETE CASCADE,
        FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE
    );
    """
    
    ]

try:
    with sqlite3.connect(database) as conn:
        # Create a cursor
        cursor = conn.cursor()

        # Execute create table statements stuff
        for statement in create_tables:
            cursor.execute(statement)

        # Commit the changes
        conn.commit()
        print("tables created successfully!")

except sqlite3.OperationalError as e:
    print("failed to create tables: ", e)