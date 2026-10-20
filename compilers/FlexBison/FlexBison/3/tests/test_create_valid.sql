-- test_create_valid.sql
-- Expected: no errors, "Syntactic analysis successful."

CREATE TABLE employees (
    id      INT,
    name    VARCHAR(50),
    salary  FLOAT
);

CREATE TABLE departments (
    dept_id   INT,
    dept_name VARCHAR(100)
);
