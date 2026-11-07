"""SQL Server database access layer for Capitalism High School Management System."""

from __future__ import annotations

import datetime
import decimal
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator, Sequence

import pyodbc

from login_app.config import DB_CONFIG


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass(frozen=True, slots=True)
class EmployeeRecord:
    employee_id: int
    name: str
    email: str
    phone: str
    role: str
    salary: float


@dataclass(frozen=True, slots=True)
class InventoryRecord:
    inventory_id: int
    item_name: str
    category: str
    quantity: int
    price: float
    supplier: str


@dataclass(frozen=True, slots=True)
class StudentRecord:
    student_id: int
    admission_number: str
    name: str
    gender: str
    dob: str
    student_class: str
    parent_name: str
    parent_phone: str
    email: str
    address: str


@dataclass(frozen=True, slots=True)
class TeacherRecord:
    teacher_id: int
    name: str
    tsc_number: str
    email: str
    phone: str
    department: str
    subject1: str
    subject2: str
    salary: float


@dataclass(frozen=True, slots=True)
class SubjectRecord:
    subject_id: int
    name: str
    results_count: int = 0


@dataclass(frozen=True, slots=True)
class ResultRecord:
    result_id: int
    student_id: int
    student_name: str
    admission_number: str
    subject_id: int
    subject_name: str
    cat_marks: int
    exam_marks: int
    total_marks: int
    grade: str


@dataclass(frozen=True, slots=True)
class FeeRecord:
    fee_id: int
    student_id: int
    student_name: str
    admission_number: str
    student_class: str
    amount_required: float
    amount_paid: float
    balance: float
    status: str


@dataclass(frozen=True, slots=True)
class BursaryRecord:
    bursary_id: int
    student_id: int
    student_name: str
    admission_number: str
    sponsor_name: str
    amount_awarded: float
    date_awarded: str


@dataclass(frozen=True, slots=True)
class BoardingRecord:
    boarding_id: int
    student_id: int
    student_name: str
    admission_number: str
    student_class: str
    dormitory: str
    bed_number: str


@dataclass(frozen=True, slots=True)
class ClubRecord:
    club_id: int
    name: str
    patron: str
    meeting_day: str
    member_count: int = 0


@dataclass(frozen=True, slots=True)
class ClubMemberRecord:
    membership_id: int
    student_id: int
    student_name: str
    admission_number: str
    student_class: str
    club_id: int
    club_name: str


class DatabaseError(Exception):
    """Raised when a database operation fails."""


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

def build_connection_string() -> str:
    parts = [
        f"Driver={{{DB_CONFIG.driver}}};",
        f"Server={DB_CONFIG.server};",
        f"Database={DB_CONFIG.database};",
    ]
    if DB_CONFIG.trusted_connection:
        parts.append("Trusted_Connection=yes;")
    elif DB_CONFIG.uid and DB_CONFIG.pwd:
        parts.append(f"UID={DB_CONFIG.uid};")
        parts.append(f"PWD={DB_CONFIG.pwd};")
    if DB_CONFIG.timeout_seconds:
        parts.append(f"Connection Timeout={DB_CONFIG.timeout_seconds};")
    return "".join(parts)


@contextmanager
def connection() -> Generator[pyodbc.Connection, None, None]:
    conn: pyodbc.Connection | None = None
    try:
        conn = pyodbc.connect(build_connection_string(), autocommit=True)
        yield conn
        try:
            conn.commit()
        except Exception:
            pass
    except pyodbc.Error as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        raise DatabaseError(_friendly_odbc_message(exc)) from exc
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def ping() -> None:
    """Verify that SQL Server is reachable."""
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")


def _list_tables(conn: pyodbc.Connection) -> set[str]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = N'dbo' AND TABLE_TYPE = N'BASE TABLE'
        """
    )
    return {str(row[0]) for row in cursor.fetchall()}


def _table_columns(conn: pyodbc.Connection, table: str) -> set[str]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = N'dbo' AND TABLE_NAME = ?
        """,
        (table,),
    )
    return {str(row[0]) for row in cursor.fetchall()}


def _friendly_odbc_message(exc: pyodbc.Error) -> str:
    text = str(exc).strip()
    if "08001" in text or "connection" in text.lower():
        return (
            "Could not connect to SQL Server. Check that the SQL Server service is running "
            "and that the server name in config.py is correct."
        )
    if "42S02" in text or "Invalid object name" in text:
        return (
            "Required tables are missing. The system will attempt to recreate them."
        )
    if "2627" in text or "23000" in text or "UNIQUE" in text.upper():
        return "A record with those unique credentials (Email, Admission No, or Key) already exists."
    if "547" in text or "REFERENCE" in text.upper():
        return "Cannot complete operation because dependent records are linked to this item."
    return text or "An unexpected database error occurred."


# ============================================================================
# SCHEMA INITIALIZATION & SEEDING
# ============================================================================

def ensure_schema() -> None:
    """Ensure all 11 tables exist, with foreign keys and seed data."""
    ddl_statements = {
        "Employees": """
            CREATE TABLE dbo.Employees (
                EmployeeID   INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
                Name         NVARCHAR(120)      NOT NULL,
                Email        NVARCHAR(254)      NOT NULL,
                Phone        NVARCHAR(20)       NOT NULL,
                Role         NVARCHAR(80)       NOT NULL,
                Salary       DECIMAL(12, 2)     NOT NULL
                    CONSTRAINT CK_Employees_Salary CHECK (Salary >= 0)
            )
        """,
        "Inventory": """
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
            )
        """,
        "Students": """
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
                Address         NVARCHAR(255)      NULL
            )
        """,
        "TeachingStaff": """
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
            )
        """,
        "Subjects": """
            CREATE TABLE dbo.Subjects (
                SubjectID   INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
                SubjectName NVARCHAR(80)       NOT NULL
            )
        """,
        "Results": """
            CREATE TABLE dbo.Results (
                ResultID   INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
                StudentID  INT                NOT NULL,
                SubjectID  INT                NOT NULL,
                CATMarks   INT                NOT NULL,
                ExamMarks  INT                NOT NULL,
                TotalMarks INT                NOT NULL,
                Grade      NVARCHAR(5)        NOT NULL
            )
        """,
        "Fees": """
            CREATE TABLE dbo.Fees (
                FeeID          INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
                StudentID      INT                NOT NULL,
                AmountRequired DECIMAL(12, 2)     NOT NULL,
                AmountPaid     DECIMAL(12, 2)     NOT NULL,
                Balance        DECIMAL(12, 2)     NOT NULL
            )
        """,
        "Bursaries": """
            CREATE TABLE dbo.Bursaries (
                BursaryID     INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
                StudentID     INT                NOT NULL,
                SponsorName   NVARCHAR(120)      NOT NULL,
                AmountAwarded DECIMAL(12, 2)     NOT NULL,
                DateAwarded   DATE               NULL
            )
        """,
        "Boarding": """
            CREATE TABLE dbo.Boarding (
                BoardingID INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
                StudentID  INT                NOT NULL,
                Dormitory  NVARCHAR(60)       NOT NULL,
                BedNumber  NVARCHAR(30)       NOT NULL
            )
        """,
        "Clubs": """
            CREATE TABLE dbo.Clubs (
                ClubID     INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
                ClubName   NVARCHAR(120)      NOT NULL,
                Patron     NVARCHAR(120)      NULL,
                MeetingDay NVARCHAR(40)       NULL
            )
        """,
        "ClubMembers": """
            CREATE TABLE dbo.ClubMembers (
                MembershipID INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
                StudentID    INT                NOT NULL,
                ClubID       INT                NOT NULL
            )
        """,
    }

    with connection() as conn:
        tables = _list_tables(conn)
        cursor = conn.cursor()

        for table_name, ddl in ddl_statements.items():
            if table_name not in tables:
                cursor.execute(ddl)

        # Re-check tables
        tables = _list_tables(conn)

        # Seed Subjects if empty
        if "Subjects" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.Subjects")
            if cursor.fetchone()[0] == 0:
                subjects = [
                    "Mathematics", "English", "Kiswahili", "Biology", "Chemistry",
                    "Physics", "History & Government", "Geography",
                    "CRE (Christian Religious Ed.)", "Business Studies",
                    "Agriculture", "Computer Studies"
                ]
                for s in subjects:
                    cursor.execute("INSERT INTO dbo.Subjects (SubjectName) VALUES (?)", (s,))

        # Seed Clubs if empty
        if "Clubs" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.Clubs")
            if cursor.fetchone()[0] == 0:
                clubs = [
                    ("Science & Robotics Club", "Mr. Ruben Ondiek", "Wednesday 4:00 PM"),
                    ("Debating & Public Speaking Society", "Mrs. Alice Wanjiru", "Thursday 4:00 PM"),
                    ("Drama & Music Society", "Mr. John Mwangi", "Tuesday 4:00 PM"),
                    ("Kenya Scouts Movement", "Mr. David Otieno", "Friday 4:30 PM"),
                    ("Red Cross Society", "Ms. Mercy Joy", "Monday 4:00 PM"),
                    ("Journalism & Media Club", "Mr. Peter Karanja", "Wednesday 4:00 PM"),
                    ("Environmental & Green Club", "Mrs. Faith Mutua", "Thursday 4:00 PM"),
                ]
                for name, patron, day in clubs:
                    cursor.execute("INSERT INTO dbo.Clubs (ClubName, Patron, MeetingDay) VALUES (?, ?, ?)", (name, patron, day))

        # Check for empty/dummy Student record (e.g. Admission == '') and update it to a valid sample student
        if "Students" in tables:
            cursor.execute("SELECT StudentID, AdmissionNumber FROM dbo.Students WHERE AdmissionNumber = '' OR AdmissionNumber IS NULL")
            dummy_rows = cursor.fetchall()
            for r in dummy_rows:
                cursor.execute(
                    """
                    UPDATE dbo.Students
                    SET AdmissionNumber = ?, FullName = ?, Gender = ?, DateOfBirth = ?,
                        Class = ?, ParentName = ?, ParentPhone = ?, Email = ?, Address = ?
                    WHERE StudentID = ?
                    """,
                    (
                        "CHS/2026/001",
                        "Brian Kiprono",
                        "Male",
                        "2008-04-12",
                        "Form 3 Alpha",
                        "David Kiprono",
                        "0712345678",
                        "brian.kiprono@gmail.com",
                        "Nairobi, Kenya",
                        r[0],
                    )
                )


# ============================================================================
# HELPER PARSERS
# ============================================================================

def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, decimal.Decimal):
        return float(value)
    try:
        return float(str(value).strip().replace(",", ""))
    except ValueError:
        return 0.0


def _to_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return 0


def _to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def calculate_grade(total_marks: int) -> str:
    """Calculate letter grade from total marks (0-100)."""
    if total_marks >= 80:
        return "A"
    elif total_marks >= 70:
        return "B"
    elif total_marks >= 60:
        return "C"
    elif total_marks >= 50:
        return "D"
    else:
        return "E"


# ============================================================================
# EMPLOYEES MODULE
# ============================================================================

def list_employees(search_term: str = "") -> list[EmployeeRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        if search_term.strip():
            wildcard = f"%{search_term.strip()}%"
            cursor.execute(
                """
                SELECT EmployeeID, Name, Email, Phone, Role, Salary
                FROM dbo.Employees
                WHERE Name LIKE ? OR Role LIKE ? OR Email LIKE ? OR Phone LIKE ?
                ORDER BY Name
                """,
                (wildcard, wildcard, wildcard, wildcard),
            )
        else:
            cursor.execute(
                "SELECT EmployeeID, Name, Email, Phone, Role, Salary FROM dbo.Employees ORDER BY Name"
            )

        return [
            EmployeeRecord(
                employee_id=_to_int(row[0]),
                name=_to_str(row[1]),
                email=_to_str(row[2]),
                phone=_to_str(row[3]),
                role=_to_str(row[4]),
                salary=_to_float(row[5]),
            )
            for row in cursor.fetchall()
        ]


def insert_employee(name: str, email: str, phone: str, role: str, salary: float) -> int:
    with connection() as conn:
        cursor = conn.cursor()
        phone_digits = re.sub(r"[\s\-()+]", "", phone.strip())
        cursor.execute(
            """
            INSERT INTO dbo.Employees (Name, Email, Phone, Role, Salary)
            OUTPUT INSERTED.EmployeeID
            VALUES (?, ?, ?, ?, ?)
            """,
            (name.strip(), email.strip(), phone_digits, role.strip(), salary),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def update_employee(employee_id: int, name: str, email: str, phone: str, role: str, salary: float) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        phone_digits = re.sub(r"[\s\-()+]", "", phone.strip())
        cursor.execute(
            """
            UPDATE dbo.Employees
            SET Name = ?, Email = ?, Phone = ?, Role = ?, Salary = ?
            WHERE EmployeeID = ?
            """,
            (name.strip(), email.strip(), phone_digits, role.strip(), salary, employee_id),
        )
        if cursor.rowcount == 0:
            raise DatabaseError("Employee record was not found.")


def delete_employee(employee_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.Employees WHERE EmployeeID = ?", (employee_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Employee record was not found.")


# ============================================================================
# INVENTORY MODULE
# ============================================================================

def _inventory_pk(conn: pyodbc.Connection) -> str:
    cols = _table_columns(conn, "Inventory")
    return "ItemID" if "ItemID" in cols else "InventoryID"


def list_inventory(search_term: str = "") -> list[InventoryRecord]:
    with connection() as conn:
        pk = _inventory_pk(conn)
        cursor = conn.cursor()
        if search_term.strip():
            wildcard = f"%{search_term.strip()}%"
            cursor.execute(
                f"""
                SELECT {pk}, ItemName, Category, Quantity, Price, Supplier
                FROM dbo.Inventory
                WHERE ItemName LIKE ? OR Category LIKE ? OR Supplier LIKE ?
                ORDER BY ItemName
                """,
                (wildcard, wildcard, wildcard),
            )
        else:
            cursor.execute(
                f"SELECT {pk}, ItemName, Category, Quantity, Price, Supplier FROM dbo.Inventory ORDER BY ItemName"
            )

        return [
            InventoryRecord(
                inventory_id=_to_int(row[0]),
                item_name=_to_str(row[1]),
                category=_to_str(row[2]),
                quantity=_to_int(row[3]),
                price=_to_float(row[4]),
                supplier=_to_str(row[5]),
            )
            for row in cursor.fetchall()
        ]


def insert_inventory_item(item_name: str, category: str, quantity: int, price: float, supplier: str) -> int:
    with connection() as conn:
        pk = _inventory_pk(conn)
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO dbo.Inventory (ItemName, Category, Quantity, Price, Supplier)
            OUTPUT INSERTED.{pk}
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_name.strip(), category.strip(), quantity, price, supplier.strip()),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def update_inventory_item(inventory_id: int, item_name: str, category: str, quantity: int, price: float, supplier: str) -> None:
    with connection() as conn:
        pk = _inventory_pk(conn)
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE dbo.Inventory
            SET ItemName = ?, Category = ?, Quantity = ?, Price = ?, Supplier = ?
            WHERE {pk} = ?
            """,
            (item_name.strip(), category.strip(), quantity, price, supplier.strip(), inventory_id),
        )
        if cursor.rowcount == 0:
            raise DatabaseError("Inventory record was not found.")


def delete_inventory_item(inventory_id: int) -> None:
    with connection() as conn:
        pk = _inventory_pk(conn)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM dbo.Inventory WHERE {pk} = ?", (inventory_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Inventory item was not found.")


# ============================================================================
# STUDENTS MODULE
# ============================================================================

def list_students(search_term: str = "", class_filter: str = "") -> list[StudentRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT StudentID, AdmissionNumber, FullName, Gender, DateOfBirth,
                   Class, ParentName, ParentPhone, Email, Address
            FROM dbo.Students
            WHERE 1=1
        """
        params: list[Any] = []

        if search_term.strip():
            sql += " AND (AdmissionNumber LIKE ? OR FullName LIKE ? OR ParentName LIKE ? OR ParentPhone LIKE ?)"
            wildcard = f"%{search_term.strip()}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        if class_filter.strip() and class_filter.strip() != "All Classes":
            sql += " AND Class = ?"
            params.append(class_filter.strip())

        sql += " ORDER BY AdmissionNumber"
        cursor.execute(sql, params)

        return [
            StudentRecord(
                student_id=_to_int(row[0]),
                admission_number=_to_str(row[1]),
                name=_to_str(row[2]),
                gender=_to_str(row[3]),
                dob=_to_str(row[4]),
                student_class=_to_str(row[5]),
                parent_name=_to_str(row[6]),
                parent_phone=_to_str(row[7]),
                email=_to_str(row[8]),
                address=_to_str(row[9]),
            )
            for row in cursor.fetchall()
        ]


def get_student_choices() -> list[tuple[int, str, str, str]]:
    """Return [(StudentID, AdmissionNumber, FullName, Class)] for dropdowns."""
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT StudentID, AdmissionNumber, FullName, Class FROM dbo.Students ORDER BY FullName")
        return [
            (_to_int(r[0]), _to_str(r[1]), _to_str(r[2]), _to_str(r[3]))
            for r in cursor.fetchall()
        ]


def insert_student(
    admission: str,
    name: str,
    gender: str,
    dob: str,
    student_class: str,
    parent: str,
    parent_phone: str,
    email: str,
    address: str,
) -> int:
    with connection() as conn:
        cursor = conn.cursor()
        dob_val = dob.strip() if dob.strip() else None
        cursor.execute(
            """
            INSERT INTO dbo.Students
            (AdmissionNumber, FullName, Gender, DateOfBirth, Class, ParentName, ParentPhone, Email, Address)
            OUTPUT INSERTED.StudentID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                admission.strip(),
                name.strip(),
                gender.strip(),
                dob_val,
                student_class.strip(),
                parent.strip(),
                parent_phone.strip(),
                email.strip(),
                address.strip(),
            ),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def update_student(
    student_id: int,
    admission: str,
    name: str,
    gender: str,
    dob: str,
    student_class: str,
    parent: str,
    parent_phone: str,
    email: str,
    address: str,
) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        dob_val = dob.strip() if dob.strip() else None
        cursor.execute(
            """
            UPDATE dbo.Students
            SET AdmissionNumber = ?, FullName = ?, Gender = ?, DateOfBirth = ?,
                Class = ?, ParentName = ?, ParentPhone = ?, Email = ?, Address = ?
            WHERE StudentID = ?
            """,
            (
                admission.strip(),
                name.strip(),
                gender.strip(),
                dob_val,
                student_class.strip(),
                parent.strip(),
                parent_phone.strip(),
                email.strip(),
                address.strip(),
                student_id,
            ),
        )
        if cursor.rowcount == 0:
            raise DatabaseError("Student record was not found.")


def delete_student(student_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        # Clean up related records if foreign key cascades are not enabled
        for child_table in ("Results", "Fees", "Bursaries", "Boarding", "ClubMembers"):
            if child_table in _list_tables(conn):
                cursor.execute(f"DELETE FROM dbo.{child_table} WHERE StudentID = ?", (student_id,))
        cursor.execute("DELETE FROM dbo.Students WHERE StudentID = ?", (student_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Student record was not found.")


# ============================================================================
# TEACHING STAFF MODULE
# ============================================================================

def list_teachers(search_term: str = "", dept_filter: str = "") -> list[TeacherRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT TeacherID, FullName, TSCNumber, Email, Phone, Department, Subject1, Subject2, Salary
            FROM dbo.TeachingStaff
            WHERE 1=1
        """
        params: list[Any] = []

        if search_term.strip():
            sql += " AND (FullName LIKE ? OR TSCNumber LIKE ? OR Subject1 LIKE ? OR Subject2 LIKE ?)"
            wildcard = f"%{search_term.strip()}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        if dept_filter.strip() and dept_filter.strip() != "All Departments":
            sql += " AND Department = ?"
            params.append(dept_filter.strip())

        sql += " ORDER BY FullName"
        cursor.execute(sql, params)

        return [
            TeacherRecord(
                teacher_id=_to_int(row[0]),
                name=_to_str(row[1]),
                tsc_number=_to_str(row[2]),
                email=_to_str(row[3]),
                phone=_to_str(row[4]),
                department=_to_str(row[5]),
                subject1=_to_str(row[6]),
                subject2=_to_str(row[7]),
                salary=_to_float(row[8]),
            )
            for row in cursor.fetchall()
        ]


def insert_teacher(
    name: str,
    tsc_number: str,
    email: str,
    phone: str,
    department: str,
    subject1: str,
    subject2: str,
    salary: float,
) -> int:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.TeachingStaff (FullName, TSCNumber, Email, Phone, Department, Subject1, Subject2, Salary)
            OUTPUT INSERTED.TeacherID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                tsc_number.strip(),
                email.strip(),
                phone.strip(),
                department.strip(),
                subject1.strip(),
                subject2.strip(),
                salary,
            ),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def update_teacher(
    teacher_id: int,
    name: str,
    tsc_number: str,
    email: str,
    phone: str,
    department: str,
    subject1: str,
    subject2: str,
    salary: float,
) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE dbo.TeachingStaff
            SET FullName = ?, TSCNumber = ?, Email = ?, Phone = ?,
                Department = ?, Subject1 = ?, Subject2 = ?, Salary = ?
            WHERE TeacherID = ?
            """,
            (
                name.strip(),
                tsc_number.strip(),
                email.strip(),
                phone.strip(),
                department.strip(),
                subject1.strip(),
                subject2.strip(),
                salary,
                teacher_id,
            ),
        )
        if cursor.rowcount == 0:
            raise DatabaseError("Teacher record was not found.")


def delete_teacher(teacher_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.TeachingStaff WHERE TeacherID = ?", (teacher_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Teacher record was not found.")


# ============================================================================
# ACADEMICS (SUBJECTS & EXAM RESULTS) MODULE
# ============================================================================

def list_subjects() -> list[SubjectRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.SubjectID, s.SubjectName,
                   (SELECT COUNT(*) FROM dbo.Results r WHERE r.SubjectID = s.SubjectID) AS ResultCount
            FROM dbo.Subjects s
            ORDER BY s.SubjectName
            """
        )
        return [
            SubjectRecord(
                subject_id=_to_int(row[0]),
                name=_to_str(row[1]),
                results_count=_to_int(row[2]),
            )
            for row in cursor.fetchall()
        ]


def insert_subject(subject_name: str) -> int:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.Subjects (SubjectName)
            OUTPUT INSERTED.SubjectID
            VALUES (?)
            """,
            (subject_name.strip(),),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def delete_subject(subject_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.Results WHERE SubjectID = ?", (subject_id,))
        cursor.execute("DELETE FROM dbo.Subjects WHERE SubjectID = ?", (subject_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Subject record was not found.")


def list_results(search_term: str = "", subject_id: int | None = None) -> list[ResultRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT r.ResultID, r.StudentID, s.FullName, s.AdmissionNumber,
                   r.SubjectID, sub.SubjectName, r.CATMarks, r.ExamMarks, r.TotalMarks, r.Grade
            FROM dbo.Results r
            INNER JOIN dbo.Students s ON r.StudentID = s.StudentID
            INNER JOIN dbo.Subjects sub ON r.SubjectID = sub.SubjectID
            WHERE 1=1
        """
        params: list[Any] = []

        if search_term.strip():
            sql += " AND (s.FullName LIKE ? OR s.AdmissionNumber LIKE ?)"
            wildcard = f"%{search_term.strip()}%"
            params.extend([wildcard, wildcard])

        if subject_id and subject_id > 0:
            sql += " AND r.SubjectID = ?"
            params.append(subject_id)

        sql += " ORDER BY s.FullName, sub.SubjectName"
        cursor.execute(sql, params)

        return [
            ResultRecord(
                result_id=_to_int(row[0]),
                student_id=_to_int(row[1]),
                student_name=_to_str(row[2]),
                admission_number=_to_str(row[3]),
                subject_id=_to_int(row[4]),
                subject_name=_to_str(row[5]),
                cat_marks=_to_int(row[6]),
                exam_marks=_to_int(row[7]),
                total_marks=_to_int(row[8]),
                grade=_to_str(row[9]),
            )
            for row in cursor.fetchall()
        ]


def insert_result(student_id: int, subject_id: int, cat_marks: int, exam_marks: int) -> int:
    total_marks = cat_marks + exam_marks
    grade = calculate_grade(total_marks)
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ResultID FROM dbo.Results WHERE StudentID = ? AND SubjectID = ?",
            (student_id, subject_id),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE dbo.Results
                SET CATMarks = ?, ExamMarks = ?, TotalMarks = ?, Grade = ?
                WHERE ResultID = ?
                """,
                (cat_marks, exam_marks, total_marks, grade, existing[0]),
            )
            return int(existing[0])
        else:
            cursor.execute(
                """
                INSERT INTO dbo.Results (StudentID, SubjectID, CATMarks, ExamMarks, TotalMarks, Grade)
                OUTPUT INSERTED.ResultID
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (student_id, subject_id, cat_marks, exam_marks, total_marks, grade),
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0


def update_result(result_id: int, cat_marks: int, exam_marks: int) -> None:
    total_marks = cat_marks + exam_marks
    grade = calculate_grade(total_marks)
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE dbo.Results
            SET CATMarks = ?, ExamMarks = ?, TotalMarks = ?, Grade = ?
            WHERE ResultID = ?
            """,
            (cat_marks, exam_marks, total_marks, grade, result_id),
        )
        if cursor.rowcount == 0:
            raise DatabaseError("Result record was not found.")


def delete_result(result_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.Results WHERE ResultID = ?", (result_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Result record was not found.")


# ============================================================================
# FEES & BURSARIES MODULE
# ============================================================================

def list_fees(search_term: str = "", status_filter: str = "") -> list[FeeRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT f.FeeID, f.StudentID, s.FullName, s.AdmissionNumber, s.Class,
                   f.AmountRequired, f.AmountPaid, f.Balance
            FROM dbo.Fees f
            INNER JOIN dbo.Students s ON f.StudentID = s.StudentID
            WHERE 1=1
        """
        params: list[Any] = []

        if search_term.strip():
            sql += " AND (s.FullName LIKE ? OR s.AdmissionNumber LIKE ? OR s.Class LIKE ?)"
            wildcard = f"%{search_term.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        if status_filter == "Fully Paid":
            sql += " AND f.Balance <= 0"
        elif status_filter == "Has Balance":
            sql += " AND f.Balance > 0"

        sql += " ORDER BY s.FullName"
        cursor.execute(sql, params)

        records: list[FeeRecord] = []
        for row in cursor.fetchall():
            req = _to_float(row[5])
            paid = _to_float(row[6])
            bal = _to_float(row[7])
            status = "Fully Paid" if bal <= 0 else "Pending"
            records.append(
                FeeRecord(
                    fee_id=_to_int(row[0]),
                    student_id=_to_int(row[1]),
                    student_name=_to_str(row[2]),
                    admission_number=_to_str(row[3]),
                    student_class=_to_str(row[4]),
                    amount_required=req,
                    amount_paid=paid,
                    balance=bal,
                    status=status,
                )
            )
        return records


def upsert_fee(student_id: int, amount_required: float, amount_paid: float) -> int:
    balance = amount_required - amount_paid
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT FeeID FROM dbo.Fees WHERE StudentID = ?", (student_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                """
                UPDATE dbo.Fees
                SET AmountRequired = ?, AmountPaid = ?, Balance = ?
                WHERE FeeID = ?
                """,
                (amount_required, amount_paid, balance, row[0]),
            )
            return int(row[0])
        else:
            cursor.execute(
                """
                INSERT INTO dbo.Fees (StudentID, AmountRequired, AmountPaid, Balance)
                OUTPUT INSERTED.FeeID
                VALUES (?, ?, ?, ?)
                """,
                (student_id, amount_required, amount_paid, balance),
            )
            res = cursor.fetchone()
            return int(res[0]) if res else 0


def delete_fee(fee_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.Fees WHERE FeeID = ?", (fee_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Fee record was not found.")


def list_bursaries(search_term: str = "") -> list[BursaryRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT b.BursaryID, b.StudentID, s.FullName, s.AdmissionNumber,
                   b.SponsorName, b.AmountAwarded, b.DateAwarded
            FROM dbo.Bursaries b
            INNER JOIN dbo.Students s ON b.StudentID = s.StudentID
            WHERE 1=1
        """
        params: list[Any] = []
        if search_term.strip():
            sql += " AND (s.FullName LIKE ? OR s.AdmissionNumber LIKE ? OR b.SponsorName LIKE ?)"
            wildcard = f"%{search_term.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        sql += " ORDER BY b.BursaryID DESC"
        cursor.execute(sql, params)

        return [
            BursaryRecord(
                bursary_id=_to_int(row[0]),
                student_id=_to_int(row[1]),
                student_name=_to_str(row[2]),
                admission_number=_to_str(row[3]),
                sponsor_name=_to_str(row[4]),
                amount_awarded=_to_float(row[5]),
                date_awarded=_to_str(row[6]),
            )
            for row in cursor.fetchall()
        ]


def insert_bursary(student_id: int, sponsor_name: str, amount_awarded: float, date_awarded: str) -> int:
    date_val = date_awarded.strip() if date_awarded.strip() else None
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.Bursaries (StudentID, SponsorName, AmountAwarded, DateAwarded)
            OUTPUT INSERTED.BursaryID
            VALUES (?, ?, ?, ?)
            """,
            (student_id, sponsor_name.strip(), amount_awarded, date_val),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def update_bursary(bursary_id: int, sponsor_name: str, amount_awarded: float, date_awarded: str) -> None:
    date_val = date_awarded.strip() if date_awarded.strip() else None
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE dbo.Bursaries
            SET SponsorName = ?, AmountAwarded = ?, DateAwarded = ?
            WHERE BursaryID = ?
            """,
            (sponsor_name.strip(), amount_awarded, date_val, bursary_id),
        )
        if cursor.rowcount == 0:
            raise DatabaseError("Bursary record was not found.")


def delete_bursary(bursary_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.Bursaries WHERE BursaryID = ?", (bursary_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Bursary record was not found.")


# ============================================================================
# BOARDING MODULE
# ============================================================================

def list_boarding(search_term: str = "", dorm_filter: str = "") -> list[BoardingRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT bd.BoardingID, bd.StudentID, s.FullName, s.AdmissionNumber,
                   s.Class, bd.Dormitory, bd.BedNumber
            FROM dbo.Boarding bd
            INNER JOIN dbo.Students s ON bd.StudentID = s.StudentID
            WHERE 1=1
        """
        params: list[Any] = []

        if search_term.strip():
            sql += " AND (s.FullName LIKE ? OR s.AdmissionNumber LIKE ? OR bd.BedNumber LIKE ?)"
            wildcard = f"%{search_term.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        if dorm_filter.strip() and dorm_filter.strip() != "All Dormitories":
            sql += " AND bd.Dormitory = ?"
            params.append(dorm_filter.strip())

        sql += " ORDER BY bd.Dormitory, bd.BedNumber"
        cursor.execute(sql, params)

        return [
            BoardingRecord(
                boarding_id=_to_int(row[0]),
                student_id=_to_int(row[1]),
                student_name=_to_str(row[2]),
                admission_number=_to_str(row[3]),
                student_class=_to_str(row[4]),
                dormitory=_to_str(row[5]),
                bed_number=_to_str(row[6]),
            )
            for row in cursor.fetchall()
        ]


def assign_boarding(student_id: int, dormitory: str, bed_number: str) -> int:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT BoardingID FROM dbo.Boarding WHERE StudentID = ?", (student_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                """
                UPDATE dbo.Boarding
                SET Dormitory = ?, BedNumber = ?
                WHERE BoardingID = ?
                """,
                (dormitory.strip(), bed_number.strip(), row[0]),
            )
            return int(row[0])
        else:
            cursor.execute(
                """
                INSERT INTO dbo.Boarding (StudentID, Dormitory, BedNumber)
                OUTPUT INSERTED.BoardingID
                VALUES (?, ?, ?)
                """,
                (student_id, dormitory.strip(), bed_number.strip()),
            )
            res = cursor.fetchone()
            return int(res[0]) if res else 0


def update_boarding(boarding_id: int, dormitory: str, bed_number: str) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE dbo.Boarding
            SET Dormitory = ?, BedNumber = ?
            WHERE BoardingID = ?
            """,
            (dormitory.strip(), bed_number.strip(), boarding_id),
        )
        if cursor.rowcount == 0:
            raise DatabaseError("Boarding record was not found.")


def delete_boarding(boarding_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.Boarding WHERE BoardingID = ?", (boarding_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Boarding record was not found.")


# ============================================================================
# CLUBS & SOCIETIES MODULE
# ============================================================================

def list_clubs() -> list[ClubRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.ClubID, c.ClubName, c.Patron, c.MeetingDay,
                   (SELECT COUNT(*) FROM dbo.ClubMembers cm WHERE cm.ClubID = c.ClubID) AS MemberCount
            FROM dbo.Clubs c
            ORDER BY c.ClubName
            """
        )
        return [
            ClubRecord(
                club_id=_to_int(row[0]),
                name=_to_str(row[1]),
                patron=_to_str(row[2]),
                meeting_day=_to_str(row[3]),
                member_count=_to_int(row[4]),
            )
            for row in cursor.fetchall()
        ]


def insert_club(club_name: str, patron: str, meeting_day: str) -> int:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.Clubs (ClubName, Patron, MeetingDay)
            OUTPUT INSERTED.ClubID
            VALUES (?, ?, ?)
            """,
            (club_name.strip(), patron.strip(), meeting_day.strip()),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def update_club(club_id: int, club_name: str, patron: str, meeting_day: str) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE dbo.Clubs
            SET ClubName = ?, Patron = ?, MeetingDay = ?
            WHERE ClubID = ?
            """,
            (club_name.strip(), patron.strip(), meeting_day.strip(), club_id),
        )
        if cursor.rowcount == 0:
            raise DatabaseError("Club record was not found.")


def delete_club(club_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.ClubMembers WHERE ClubID = ?", (club_id,))
        cursor.execute("DELETE FROM dbo.Clubs WHERE ClubID = ?", (club_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Club record was not found.")


def list_club_members(club_id: int | None = None) -> list[ClubMemberRecord]:
    with connection() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT cm.MembershipID, cm.StudentID, s.FullName, s.AdmissionNumber,
                   s.Class, cm.ClubID, c.ClubName
            FROM dbo.ClubMembers cm
            INNER JOIN dbo.Students s ON cm.StudentID = s.StudentID
            INNER JOIN dbo.Clubs c ON cm.ClubID = c.ClubID
            WHERE 1=1
        """
        params: list[Any] = []
        if club_id and club_id > 0:
            sql += " AND cm.ClubID = ?"
            params.append(club_id)

        sql += " ORDER BY c.ClubName, s.FullName"
        cursor.execute(sql, params)

        return [
            ClubMemberRecord(
                membership_id=_to_int(row[0]),
                student_id=_to_int(row[1]),
                student_name=_to_str(row[2]),
                admission_number=_to_str(row[3]),
                student_class=_to_str(row[4]),
                club_id=_to_int(row[5]),
                club_name=_to_str(row[6]),
            )
            for row in cursor.fetchall()
        ]


def add_club_member(student_id: int, club_id: int) -> int:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MembershipID FROM dbo.ClubMembers WHERE StudentID = ? AND ClubID = ?",
            (student_id, club_id),
        )
        if cursor.fetchone():
            raise DatabaseError("This student is already a registered member of this club.")
        cursor.execute(
            """
            INSERT INTO dbo.ClubMembers (StudentID, ClubID)
            OUTPUT INSERTED.MembershipID
            VALUES (?, ?)
            """,
            (student_id, club_id),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def remove_club_member(membership_id: int) -> None:
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.ClubMembers WHERE MembershipID = ?", (membership_id,))
        if cursor.rowcount == 0:
            raise DatabaseError("Club membership record was not found.")


# ============================================================================
# COMPREHENSIVE DASHBOARD STATS
# ============================================================================

def dashboard_stats() -> dict[str, Any]:
    """Calculate aggregate statistics across all operational modules."""
    with connection() as conn:
        tables = _list_tables(conn)
        cursor = conn.cursor()

        # Students
        student_count = 0
        if "Students" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.Students")
            student_count = int(cursor.fetchone()[0])

        # Teachers
        teacher_count = 0
        if "TeachingStaff" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.TeachingStaff")
            teacher_count = int(cursor.fetchone()[0])

        # Employees (Support Staff)
        employee_count = 0
        if "Employees" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.Employees")
            employee_count = int(cursor.fetchone()[0])

        # Inventory
        inventory_count = 0
        inventory_value = 0.0
        low_stock = 0
        if "Inventory" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.Inventory")
            inventory_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT ISNULL(SUM(CAST(Quantity AS BIGINT) * Price), 0) FROM dbo.Inventory")
            inventory_value = _to_float(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM dbo.Inventory WHERE Quantity <= 5")
            low_stock = int(cursor.fetchone()[0])

        # Fees
        fees_required = 0.0
        fees_paid = 0.0
        fees_balance = 0.0
        if "Fees" in tables:
            cursor.execute(
                """
                SELECT ISNULL(SUM(AmountRequired), 0), ISNULL(SUM(AmountPaid), 0), ISNULL(SUM(Balance), 0)
                FROM dbo.Fees
                """
            )
            row = cursor.fetchone()
            fees_required = _to_float(row[0])
            fees_paid = _to_float(row[1])
            fees_balance = _to_float(row[2])

        # Boarding
        boarder_count = 0
        if "Boarding" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.Boarding")
            boarder_count = int(cursor.fetchone()[0])

        # Clubs
        club_count = 0
        club_members_count = 0
        if "Clubs" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.Clubs")
            club_count = int(cursor.fetchone()[0])
        if "ClubMembers" in tables:
            cursor.execute("SELECT COUNT(*) FROM dbo.ClubMembers")
            club_members_count = int(cursor.fetchone()[0])

        # Exams / Results
        results_count = 0
        avg_score = 0.0
        if "Results" in tables:
            cursor.execute("SELECT COUNT(*), ISNULL(AVG(CAST(TotalMarks AS FLOAT)), 0) FROM dbo.Results")
            row = cursor.fetchone()
            results_count = int(row[0])
            avg_score = round(_to_float(row[1]), 1)

    return {
        "student_count": student_count,
        "teacher_count": teacher_count,
        "employee_count": employee_count,
        "inventory_count": inventory_count,
        "inventory_value": inventory_value,
        "low_stock": low_stock,
        "fees_required": fees_required,
        "fees_paid": fees_paid,
        "fees_balance": fees_balance,
        "boarder_count": boarder_count,
        "club_count": club_count,
        "club_members_count": club_members_count,
        "results_count": results_count,
        "avg_score": avg_score,
    }
