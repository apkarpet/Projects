-- test_alias_valid.sql
-- Expected: no errors, "Syntactic analysis successful."

CREATE TABLE employees (
    emp_id   INT,
    emp_name VARCHAR(60),
    dept_id  INT,
    salary   FLOAT
);

CREATE TABLE departments (
    dept_id   INT,
    dept_name VARCHAR(80)
);

CREATE TABLE customers (
    cust_id INT
);

-- Table aliases via AS
SELECT e.emp_name, d.dept_name
FROM employees AS e
JOIN departments AS d ON e.dept_id = d.dept_id;

-- Alias in WHERE
SELECT e.emp_name
FROM employees AS e
WHERE e.salary > 50000;

-- Multiple joins with aliases
SELECT e.emp_name, d.dept_name
FROM employees AS e
JOIN customers ON e.emp_id = customers.cust_id
JOIN departments AS d ON e.dept_id = d.dept_id
WHERE e.salary >= 40000
ORDER BY e.emp_name
LIMIT 20;
