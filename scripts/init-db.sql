-- Database initialization script for AI Consultancy Platform
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE agentic_platform'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'agentic_platform')\gexec

-- Connect to the database
\c agentic_platform;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we can prepare the database

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE agentic_platform TO postgres;

-- Create application user (optional, for better security)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'agentic_app') THEN
        CREATE ROLE agentic_app WITH LOGIN PASSWORD 'app_password_change_in_production';
    END IF;
END
$$;

-- Grant necessary permissions to application user
GRANT CONNECT ON DATABASE agentic_platform TO agentic_app;
GRANT USAGE ON SCHEMA public TO agentic_app;
GRANT CREATE ON SCHEMA public TO agentic_app;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO agentic_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO agentic_app;
