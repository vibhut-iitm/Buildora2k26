-- Buildora Hackathon 2026 - Participant Registration & Attendance Schema

-- Create trigger function for automatic updated_at handling (PostgreSQL / Supabase)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_id TEXT UNIQUE NOT NULL,
    team_id TEXT NOT NULL,
    team_name TEXT NOT NULL,
    participant_name TEXT NOT NULL,
    participant_email TEXT,
    participant_phone TEXT,
    college_name TEXT DEFAULT 'N/A',
    participant_role TEXT DEFAULT 'Participant',
    qr_token TEXT UNIQUE NOT NULL,
    registration_status TEXT NOT NULL DEFAULT 'Confirmed',
    attendance_status TEXT NOT NULL DEFAULT 'Pending',
    check_in_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for lightning-fast QR verification & dashboard lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_qr_token ON projects(qr_token);
CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_registration_id ON projects(registration_id);
CREATE INDEX IF NOT EXISTS idx_projects_team_id ON projects(team_id);
CREATE INDEX IF NOT EXISTS idx_projects_attendance_status ON projects(attendance_status);

-- Auto-update updated_at timestamp on row update
DROP TRIGGER IF EXISTS set_projects_updated_at ON projects;
CREATE TRIGGER set_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();