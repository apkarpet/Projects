-- test_join_invalid.sql
-- Expected: semantic errors (unknown table in JOIN, bad column in ON)

CREATE TABLE suppliers (
    supplier_id INT,
    company     VARCHAR(60)
);

CREATE TABLE parts (
    part_id     INT,
    description VARCHAR(100),
    supplier_id INT
);

-- Error: JOIN on unknown table
SELECT suppliers.company
FROM suppliers
JOIN nonexistent ON suppliers.supplier_id = nonexistent.supplier_id;

-- Error: ON condition references column that doesn't exist
SELECT parts.description
FROM parts
JOIN suppliers ON parts.supplier_id = suppliers.missing_col;
