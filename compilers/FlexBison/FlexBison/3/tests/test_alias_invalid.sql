-- test_alias_invalid.sql
-- Expected: semantic error — duplicate alias

CREATE TABLE customers (
    cust_id  INT,
    cust_name VARCHAR(80),
    country   VARCHAR(40)
);

CREATE TABLE orders (
    order_id  INT,
    cust_id   INT,
    amount    FLOAT
);

-- Error: same alias 'c' used twice
SELECT c.cust_name, c.amount
FROM customers AS c
JOIN orders AS c ON customers.cust_id = orders.cust_id;
