-- test_select_valid.sql
-- Expected: no errors, "Syntactic analysis successful."

CREATE TABLE students (
    student_id INT,
    first_name VARCHAR(40),
    last_name  VARCHAR(40),
    gpa        FLOAT
);

-- Simple select all
SELECT * FROM students;

-- Select with WHERE comparison
SELECT first_name, last_name FROM students
WHERE gpa >= 3.5;

-- Select with WHERE string comparison
SELECT student_id, first_name FROM students
WHERE last_name = 'Smith';

-- Select with IN list
SELECT * FROM students
WHERE student_id IN (1, 2, 3);

-- Select with GROUP BY and ORDER BY
SELECT first_name FROM students
GROUP BY first_name
ORDER BY first_name
LIMIT 10;
