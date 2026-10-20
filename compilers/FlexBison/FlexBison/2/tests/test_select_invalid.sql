-- test_select_invalid.sql
-- Expected: semantic errors (unknown table / type mismatch)

CREATE TABLE orders (
    order_id   INT,
    customer   VARCHAR(60),
    total      FLOAT
);

-- Error 1: querying non-existent table
SELECT * FROM invoices;

-- Error 2: type mismatch — comparing FLOAT column with string
SELECT order_id FROM orders
WHERE total = 'expensive';

-- Error 3: unknown column referenced
SELECT orders.nonexistent FROM orders;
