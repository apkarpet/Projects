-- test_create_invalid.sql
-- Expected: semantic error - duplicate table name

CREATE TABLE products (
    product_id   INT,
    product_name VARCHAR(80),
    price        FLOAT
);

-- Second definition of the same table semantic error
CREATE TABLE products (
    product_id INT,
    price      FLOAT
);
