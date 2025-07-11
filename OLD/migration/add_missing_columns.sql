-- Add missing columns to FaxJobs table
ALTER TABLE FaxJobs ADD recipient_fax NVARCHAR(20) NOT NULL DEFAULT '';
ALTER TABLE FaxJobs ADD priority NVARCHAR(20) DEFAULT 'Medium';
ALTER TABLE FaxJobs ADD max_attempts INT DEFAULT 3;
ALTER TABLE FaxJobs ADD retry_interval INT DEFAULT 5;
ALTER TABLE FaxJobs ADD xml_path NVARCHAR(255) NULL;
ALTER TABLE FaxJobs ADD page_count INT DEFAULT 0;
ALTER TABLE FaxJobs ADD file_size_mb DECIMAL(10,2) DEFAULT 0;
ALTER TABLE FaxJobs ADD completed_at DATETIME NULL;
ALTER TABLE FaxJobs ADD error_message NVARCHAR(MAX) NULL;

-- Add timestamp columns to Contacts table
ALTER TABLE Contacts ADD created_at DATETIME DEFAULT GETDATE();
ALTER TABLE Contacts ADD updated_at DATETIME DEFAULT GETDATE();
