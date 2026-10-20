-- test_new_checks_valid.sql
-- Tests for negative literals and new semantic checks

CREATE TABLE readings (
    sensor_id   INT,
    temp        FLOAT,
    label       VARCHAR(30)
);

-- Negative integer literal
SELECT * FROM readings
WHERE sensor_id > -100;

-- Negative float literal
SELECT * FROM readings
WHERE temp <= -0.5;

-- IN with matching types (INT column, int literals)
SELECT * FROM readings
WHERE sensor_id IN (1, 2, -3);

-- NOT IN with matching types (VARCHAR column, string literals)
SELECT * FROM readings
WHERE label NOT IN ('bad', 'error');

-- IN with FLOAT column and mixed int/float literals (both valid)
SELECT * FROM readings
WHERE temp IN (1, 2.5, -3.14);
