-- test_join_valid.sql
-- Expected: no errors, "Syntactic analysis successful."

CREATE TABLE authors (
    author_id INT,
    full_name VARCHAR(80)
);

CREATE TABLE books (
    book_id   INT,
    title     VARCHAR(120),
    author_id INT,
    price     FLOAT
);

-- Inner join on shared key
SELECT authors.full_name, books.title
FROM authors
JOIN books ON authors.author_id = books.author_id;

-- Join with WHERE filter
SELECT authors.full_name, books.title
FROM authors
JOIN books ON authors.author_id = books.author_id
WHERE books.price < 30;

-- Join with ORDER BY and LIMIT
SELECT authors.full_name, books.title, books.price
FROM authors
JOIN books ON authors.author_id = books.author_id
ORDER BY books.price
LIMIT 5;
