-- 1. Free-text search (case-insensitive) on name or email
SELECT * FROM employees 
WHERE LOWER(name) LIKE '%ada%' OR LOWER(email) LIKE '%ada%';

-- 2. Filter by department and active status with pagination
SELECT * FROM employees 
WHERE department = 'Engineering' AND is_active = TRUE 
ORDER BY LOWER(name) 
LIMIT 10 OFFSET 0;

-- 3. JOIN query: Retrieve employees with their department's details
SELECT e.id, e.name, e.email, e.position, e.salary, d.name AS department_name, d.description, d.cost_center
FROM employees e
INNER JOIN departments d ON e.department = d.name;

-- 4. Aggregation query: Average, total salaries, and employee count per department
SELECT department, COUNT(*) AS employee_count, AVG(salary) AS average_salary, SUM(salary) AS total_salary
FROM employees
GROUP BY department
HAVING COUNT(*) > 0
ORDER BY average_salary DESC;

-- 5. Atomic Transaction: Apply 5% raise to all Engineering employees
BEGIN;

UPDATE employees
SET salary = salary * 1.05,
    updated_at = NOW()
WHERE department = 'Engineering';

COMMIT;

-- 6. Query Plan Analysis (EXPLAIN ANALYZE)
EXPLAIN ANALYZE 
SELECT * FROM employees 
WHERE department = 'Engineering' AND is_active = TRUE;
