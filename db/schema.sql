-- Hand-written DDL for Employee Management System

-- Drop tables if they exist (clean setup)
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

-- 1. Departments Reference Table
CREATE TABLE departments (
    name VARCHAR(50) PRIMARY KEY,
    description VARCHAR(255),
    cost_center VARCHAR(20)
);

-- 2. Employees Table
CREATE TABLE employees (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department VARCHAR(50) NOT NULL REFERENCES departments(name),
    position VARCHAR(100) NOT NULL,
    salary DOUBLE PRECISION NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT check_positive_salary CHECK (salary > 0)
);

-- 3. Indexes for Optimized Queries
CREATE INDEX idx_employees_department ON employees(department);
CREATE INDEX idx_employees_is_active ON employees(is_active);
CREATE INDEX idx_employees_name ON employees(name);
