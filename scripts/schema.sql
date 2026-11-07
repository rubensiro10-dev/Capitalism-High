-- ============================================================================
-- CAPITALISM HIGH SCHOOL MANAGEMENT SYSTEM
-- Comprehensive Database Schema & Seed Data for Microsoft SQL Server
-- ============================================================================

IF DB_ID(N'ManagementSystem') IS NULL
BEGIN
    CREATE DATABASE ManagementSystem;
END
GO

USE ManagementSystem;
GO

-- 1. SUPPORT & ADMINISTRATIVE WORKFORCE (Employees)
IF OBJECT_ID(N'dbo.Employees', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Employees (
        EmployeeID   INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        Name         NVARCHAR(120)      NOT NULL,
        Email        NVARCHAR(254)      NOT NULL,
        Phone        NVARCHAR(20)       NOT NULL,
        Role         NVARCHAR(80)       NOT NULL,
        Salary       DECIMAL(12, 2)     NOT NULL
            CONSTRAINT CK_Employees_Salary CHECK (Salary >= 0),
        CreatedAt    DATETIME2(0)       NOT NULL
            CONSTRAINT DF_Employees_CreatedAt DEFAULT SYSUTCDATETIME()
    );
END
GO

-- 2. INVENTORY & SCHOOL SUPPLIES
IF OBJECT_ID(N'dbo.Inventory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Inventory (
        ItemID             INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        ItemName           NVARCHAR(160)      NOT NULL,
        Category           NVARCHAR(80)       NOT NULL,
        Quantity           INT                NOT NULL
            CONSTRAINT CK_Inventory_Quantity CHECK (Quantity >= 0),
        Price              DECIMAL(12, 2)     NOT NULL
            CONSTRAINT CK_Inventory_Price CHECK (Price >= 0),
        Supplier           NVARCHAR(120)      NOT NULL,
        AssignedEmployeeID INT                NULL
            CONSTRAINT FK_Inventory_Employee FOREIGN KEY REFERENCES dbo.Employees(EmployeeID) ON DELETE SET NULL,
        UpdatedAt          DATETIME2(0)       NOT NULL
            CONSTRAINT DF_Inventory_UpdatedAt DEFAULT SYSUTCDATETIME()
    );
END
GO

-- 3. STUDENTS DIRECTORY
IF OBJECT_ID(N'dbo.Students', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Students (
        StudentID       INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        AdmissionNumber NVARCHAR(30)       NOT NULL,
        FullName        NVARCHAR(120)      NOT NULL,
        Gender          NVARCHAR(10)       NULL,
        DateOfBirth     DATE               NULL,
        Class           NVARCHAR(40)       NULL,
        ParentName      NVARCHAR(120)      NULL,
        ParentPhone     NVARCHAR(25)       NULL,
        Email           NVARCHAR(120)      NULL,
        Address         NVARCHAR(255)      NULL,
        CreatedAt       DATETIME2(0)       NOT NULL
            CONSTRAINT DF_Students_CreatedAt DEFAULT SYSUTCDATETIME()
    );
END
GO

-- 4. TEACHING FACULTY & STAFF
IF OBJECT_ID(N'dbo.TeachingStaff', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TeachingStaff (
        TeacherID   INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        FullName    NVARCHAR(120)      NOT NULL,
        TSCNumber   NVARCHAR(50)       NULL,
        Email       NVARCHAR(120)      NULL,
        Phone       NVARCHAR(25)       NULL,
        Department  NVARCHAR(60)       NULL,
        Subject1    NVARCHAR(60)       NULL,
        Subject2    NVARCHAR(60)       NULL,
        Salary      DECIMAL(12, 2)     NULL
            CONSTRAINT CK_Teachers_Salary CHECK (Salary >= 0),
        CreatedAt   DATETIME2(0)       NOT NULL
            CONSTRAINT DF_TeachingStaff_CreatedAt DEFAULT SYSUTCDATETIME()
    );
END
GO

-- 5. ACADEMIC SUBJECTS CATALOG
IF OBJECT_ID(N'dbo.Subjects', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Subjects (
        SubjectID   INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        SubjectName NVARCHAR(80)       NOT NULL
    );
END
GO

-- 6. EXAMINATIONS & ACADEMIC RESULTS
IF OBJECT_ID(N'dbo.Results', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Results (
        ResultID   INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        StudentID  INT                NOT NULL
            CONSTRAINT FK_Results_Student FOREIGN KEY REFERENCES dbo.Students(StudentID) ON DELETE CASCADE,
        SubjectID  INT                NOT NULL
            CONSTRAINT FK_Results_Subject FOREIGN KEY REFERENCES dbo.Subjects(SubjectID) ON DELETE CASCADE,
        CATMarks   INT                NOT NULL
            CONSTRAINT CK_Results_CAT CHECK (CATMarks >= 0 AND CATMarks <= 30),
        ExamMarks  INT                NOT NULL
            CONSTRAINT CK_Results_Exam CHECK (ExamMarks >= 0 AND ExamMarks <= 70),
        TotalMarks INT                NOT NULL
            CONSTRAINT CK_Results_Total CHECK (TotalMarks >= 0 AND TotalMarks <= 100),
        Grade      NVARCHAR(5)        NOT NULL
    );
END
GO

-- 7. FEES MANAGEMENT & INVOICING
IF OBJECT_ID(N'dbo.Fees', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Fees (
        FeeID          INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        StudentID      INT                NOT NULL
            CONSTRAINT FK_Fees_Student FOREIGN KEY REFERENCES dbo.Students(StudentID) ON DELETE CASCADE,
        AmountRequired DECIMAL(12, 2)     NOT NULL
            CONSTRAINT CK_Fees_Required CHECK (AmountRequired >= 0),
        AmountPaid     DECIMAL(12, 2)     NOT NULL
            CONSTRAINT CK_Fees_Paid CHECK (AmountPaid >= 0),
        Balance        DECIMAL(12, 2)     NOT NULL
    );
END
GO

-- 8. BURSARIES & SCHOLARSHIPS
IF OBJECT_ID(N'dbo.Bursaries', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Bursaries (
        BursaryID     INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        StudentID     INT                NOT NULL
            CONSTRAINT FK_Bursaries_Student FOREIGN KEY REFERENCES dbo.Students(StudentID) ON DELETE CASCADE,
        SponsorName   NVARCHAR(120)      NOT NULL,
        AmountAwarded DECIMAL(12, 2)     NOT NULL
            CONSTRAINT CK_Bursary_Amount CHECK (AmountAwarded >= 0),
        DateAwarded   DATE               NULL
    );
END
GO

-- 9. BOARDING & DORMITORIES
IF OBJECT_ID(N'dbo.Boarding', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Boarding (
        BoardingID INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        StudentID  INT                NOT NULL
            CONSTRAINT FK_Boarding_Student FOREIGN KEY REFERENCES dbo.Students(StudentID) ON DELETE CASCADE,
        Dormitory  NVARCHAR(60)       NOT NULL,
        BedNumber  NVARCHAR(30)       NOT NULL
    );
END
GO

-- 10. CLUBS & EXTRA-CURRICULAR SOCIETIES
IF OBJECT_ID(N'dbo.Clubs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Clubs (
        ClubID     INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        ClubName   NVARCHAR(120)      NOT NULL,
        Patron     NVARCHAR(120)      NULL,
        MeetingDay NVARCHAR(40)       NULL
    );
END
GO

-- 11. CLUB MEMBERSHIPS
IF OBJECT_ID(N'dbo.ClubMembers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ClubMembers (
        MembershipID INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        StudentID    INT                NOT NULL
            CONSTRAINT FK_ClubMembers_Student FOREIGN KEY REFERENCES dbo.Students(StudentID) ON DELETE CASCADE,
        ClubID       INT                NOT NULL
            CONSTRAINT FK_ClubMembers_Club FOREIGN KEY REFERENCES dbo.Clubs(ClubID) ON DELETE CASCADE
    );
END
GO

-- ============================================================================
-- SEED ESSENTIAL DATA IF MISSING
-- ============================================================================

-- Seed Default Subjects
IF NOT EXISTS (SELECT 1 FROM dbo.Subjects)
BEGIN
    INSERT INTO dbo.Subjects (SubjectName) VALUES
        (N'Mathematics'),
        (N'English'),
        (N'Kiswahili'),
        (N'Biology'),
        (N'Chemistry'),
        (N'Physics'),
        (N'History & Government'),
        (N'Geography'),
        (N'CRE (Christian Religious Ed.)'),
        (N'Business Studies'),
        (N'Agriculture'),
        (N'Computer Studies');
END
GO

-- Seed Default Clubs
IF NOT EXISTS (SELECT 1 FROM dbo.Clubs)
BEGIN
    INSERT INTO dbo.Clubs (ClubName, Patron, MeetingDay) VALUES
        (N'Science & Robotics Club', N'Mr. Ruben Ondiek', N'Wednesday 4:00 PM'),
        (N'Debating & Public Speaking Society', N'Mrs. Alice Wanjiru', N'Thursday 4:00 PM'),
        (N'Drama & Music Club', N'Mr. John Mwangi', N'Tuesday 4:00 PM'),
        (N'Kenya Scouts Movement', N'Mr. David Otieno', N'Friday 4:30 PM'),
        (N'Red Cross Society', N'Ms. Mercy Joy', N'Monday 4:00 PM'),
        (N'Journalism & Media Club', N'Mr. Peter Karanja', N'Wednesday 4:00 PM'),
        (N'Environmental & Green Club', N'Mrs. Faith Mutua', N'Thursday 4:00 PM');
END
GO
