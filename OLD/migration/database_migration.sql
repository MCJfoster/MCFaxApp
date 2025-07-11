-- MCFax Database Schema Migration
-- Run this T-SQL script to update the existing database with new columns

-- Add missing columns to FaxJobs table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'recipient_fax')
    ALTER TABLE FaxJobs ADD recipient_fax NVARCHAR(20) NOT NULL DEFAULT '';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'priority')
    ALTER TABLE FaxJobs ADD priority NVARCHAR(20) DEFAULT 'Medium';

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'max_attempts')
    ALTER TABLE FaxJobs ADD max_attempts INT DEFAULT 3;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'retry_interval')
    ALTER TABLE FaxJobs ADD retry_interval INT DEFAULT 5;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'xml_path')
    ALTER TABLE FaxJobs ADD xml_path NVARCHAR(255) NULL;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'page_count')
    ALTER TABLE FaxJobs ADD page_count INT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'file_size_mb')
    ALTER TABLE FaxJobs ADD file_size_mb DECIMAL(10,2) DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'completed_at')
    ALTER TABLE FaxJobs ADD completed_at DATETIME NULL;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'error_message')
    ALTER TABLE FaxJobs ADD error_message NVARCHAR(MAX) NULL;

-- Rename xml_content to xml_path if it exists
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'xml_content')
    AND NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaxJobs' AND COLUMN_NAME = 'xml_path')
BEGIN
    EXEC sp_rename 'FaxJobs.xml_content', 'xml_path', 'COLUMN';
END

-- Add timestamp columns to Contacts table if they don't exist
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Contacts' AND COLUMN_NAME = 'created_at')
    ALTER TABLE Contacts ADD created_at DATETIME DEFAULT GETDATE();

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Contacts' AND COLUMN_NAME = 'updated_at')
    ALTER TABLE Contacts ADD updated_at DATETIME DEFAULT GETDATE();

-- Create FaxContactHistory table if it doesn't exist
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'FaxContactHistory' AND TABLE_TYPE = 'BASE TABLE')
BEGIN
    CREATE TABLE FaxContactHistory (
        history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        fax_id BIGINT NOT NULL,
        contact_id BIGINT NOT NULL,
        action NVARCHAR(50) NOT NULL,
        timestamp DATETIME DEFAULT GETDATE(),
        details NVARCHAR(MAX) NULL,
        FOREIGN KEY (fax_id) REFERENCES FaxJobs(fax_id),
        FOREIGN KEY (contact_id) REFERENCES Contacts(contact_id)
    );
END

-- Create indexes for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Contacts_FaxNumber' AND object_id = OBJECT_ID('Contacts'))
    CREATE NONCLUSTERED INDEX IX_Contacts_FaxNumber ON Contacts(fax_number);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Contacts_Name' AND object_id = OBJECT_ID('Contacts'))
    CREATE NONCLUSTERED INDEX IX_Contacts_Name ON Contacts(name);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FaxJobs_Status' AND object_id = OBJECT_ID('FaxJobs'))
    CREATE NONCLUSTERED INDEX IX_FaxJobs_Status ON FaxJobs(status);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FaxJobs_CreatedAt' AND object_id = OBJECT_ID('FaxJobs'))
    CREATE NONCLUSTERED INDEX IX_FaxJobs_CreatedAt ON FaxJobs(created_at);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FaxJobs_RecipientFax' AND object_id = OBJECT_ID('FaxJobs'))
    CREATE NONCLUSTERED INDEX IX_FaxJobs_RecipientFax ON FaxJobs(recipient_fax);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FaxContactHistory_FaxId' AND object_id = OBJECT_ID('FaxContactHistory'))
    CREATE NONCLUSTERED INDEX IX_FaxContactHistory_FaxId ON FaxContactHistory(fax_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FaxContactHistory_ContactId' AND object_id = OBJECT_ID('FaxContactHistory'))
    CREATE NONCLUSTERED INDEX IX_FaxContactHistory_ContactId ON FaxContactHistory(contact_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FaxContactHistory_Timestamp' AND object_id = OBJECT_ID('FaxContactHistory'))
    CREATE NONCLUSTERED INDEX IX_FaxContactHistory_Timestamp ON FaxContactHistory(timestamp);

PRINT 'Database migration completed successfully!';
