-- Seed data for Departments reference table
INSERT INTO departments (name, description, cost_center) VALUES
('Engineering', 'Software development, QA and operations', 'ENG-01'),
('Sales', 'Customer acquisition and account management', 'SAL-02'),
('Marketing', 'Brand awareness, product marketing and PR', 'MKT-03'),
('Human Resources', 'Talent acquisition, employee relations and culture', 'HR-04'),
('Finance', 'Accounting, budget planning and financial analysis', 'FIN-05'),
('Operations', 'Facility operations, logistics and support', 'OPS-06')
ON CONFLICT (name) DO NOTHING;

-- Seed data for Employees
INSERT INTO employees (id, name, email, department, position, salary, is_active, created_at, updated_at) VALUES
('9f1c2e8a-4b6d-4c2a-9f0e-3a1b2c3d4e5f', 'Ada Lovelace', 'ada@example.com', 'Engineering', 'Senior Backend Engineer', 142500.0, TRUE, '2026-06-01T08:00:00Z', '2026-06-01T08:00:00Z'),
('8f2c2e8a-4b6d-4c2a-9f0e-3a1b2c3d4e5e', 'Grace Hopper', 'grace@example.com', 'Engineering', 'Systems Architect', 155000.0, TRUE, '2026-06-02T09:00:00Z', '2026-06-02T09:00:00Z'),
('7f3c2e8a-4b6d-4c2a-9f0e-3a1b2c3d4e5d', 'Katherine Johnson', 'katherine@example.com', 'Finance', 'Financial Analyst', 92000.0, TRUE, '2026-06-03T10:15:00Z', '2026-06-03T10:15:00Z')
ON CONFLICT (email) DO NOTHING;
