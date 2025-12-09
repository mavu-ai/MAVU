-- Database initialization script for MavuAI
-- This script runs automatically when PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- The tables will be created by SQLAlchemy, but we can add
-- indexes and constraints here if needed

-- Create indexes for performance (these will be created if tables exist)
-- These are precautionary; SQLAlchemy will create the main tables

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'MavuAI database initialized successfully';
END $$;
