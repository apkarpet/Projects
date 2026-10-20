-- test_new_checks_invalid.sql
-- Tests for new semantic error detection

CREATE TABLE items (
    item_id     INT,
    price       FLOAT,
    name        VARCHAR(50)
);

-- Error: IN type mismatch — INT column with string literals
SELECT * FROM items
WHERE item_id IN ('a', 'b');

-- Error: NOT IN type mismatch — VARCHAR column with int literals
SELECT * FROM items
WHERE name NOT IN (1, 2, 3);

-- Error: GROUP BY with nonexistent column
SELECT item_id FROM items
GROUP BY nonexistent_col;

-- Error: ORDER BY with nonexistent column
SELECT item_id FROM items
ORDER BY fake_col;

-- Error: INT column compared with float literal (not allowed per spec)
SELECT * FROM items
WHERE item_id = 3.14;
