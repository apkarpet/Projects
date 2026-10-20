-- test_assignment_example.sql
-- The example from page 10 of Askisi2026.pdf

CREATE TABLE Students (
    student_id  int,
    first_name  varchar(50),
    last_name   varchar(50),
    gpa         float
);

CREATE TABLE Courses (
    course_id   int,
    title       varchar(100),
    credits     int
);

CREATE TABLE Enrollments (
    enrollment_id int,
    student_id    int,
    course_id     int,
    grade         varchar(2)
);

select * from Students;

SELECT s.student_id,
       s.first_name,
       s.last_name,
       c.title,
       e.grade,
       s.gpa
FROM Students       AS s
JOIN Enrollments    AS e ON s.student_id = e.student_id
JOIN Courses        AS c ON e.course_id = c.course_id
WHERE s.gpa >= 3.0
  AND c.credits IN (3, 4)
  AND e.grade NOT IN ('F','D')
GROUP BY s.student_id, c.course_id
ORDER BY s.gpa, c.title
LIMIT 20;
