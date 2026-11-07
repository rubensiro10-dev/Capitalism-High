"""Input validation for all forms and models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from login_app.config import EMAIL_PATTERN, PHONE_LENGTH, PHONE_PREFIXES


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    message: str = ""

    @classmethod
    def success(cls) -> ValidationResult:
        return cls(ok=True)

    @classmethod
    def failure(cls, message: str) -> ValidationResult:
        return cls(ok=False, message=message)


@dataclass(frozen=True, slots=True)
class SignUpData:
    username: str
    password: str
    confirm_password: str
    email: str
    phone: str


@dataclass(frozen=True, slots=True)
class SignInData:
    username: str
    password: str


def validate_non_empty(value: str, field_name: str) -> ValidationResult:
    if not value.strip():
        return ValidationResult.failure(f"{field_name} is required.")
    return ValidationResult.success()


def validate_password_match(password: str, confirm: str) -> ValidationResult:
    if password != confirm:
        return ValidationResult.failure("Passwords do not match.")
    return ValidationResult.success()


def validate_password_strength(password: str) -> ValidationResult:
    if len(password) < 8:
        return ValidationResult.failure("Password must be at least 8 characters.")
    return ValidationResult.success()


def validate_email(email: str, optional: bool = False) -> ValidationResult:
    raw = email.strip()
    if not raw:
        if optional:
            return ValidationResult.success()
        return ValidationResult.failure("Email address is required.")
    if not re.match(EMAIL_PATTERN, raw):
        return ValidationResult.failure("Enter a valid email address (e.g. name@example.com).")
    return ValidationResult.success()


def validate_phone(phone: str) -> ValidationResult:
    digits = phone.strip()
    if not digits.isdigit():
        return ValidationResult.failure("Phone number must contain digits only.")
    if len(digits) != PHONE_LENGTH:
        return ValidationResult.failure(f"Phone number must be {PHONE_LENGTH} digits.")
    if not digits.startswith(PHONE_PREFIXES):
        return ValidationResult.failure("Phone number must start with 07 or 01.")
    return ValidationResult.success()


def validate_work_phone(phone: str, field_name: str = "Phone", optional: bool = False) -> ValidationResult:
    """Contacts for staff/parents/suppliers — supports spaces, dashes, + prefix."""
    raw = phone.strip()
    if not raw:
        if optional:
            return ValidationResult.success()
        return ValidationResult.failure(f"{field_name} is required.")
    digits = re.sub(r"[\s\-()+]", "", raw)
    if not digits.isdigit():
        return ValidationResult.failure(f"{field_name} must contain digits (spaces and dashes are allowed).")
    if len(digits) < 7 or len(digits) > 15:
        return ValidationResult.failure(f"{field_name} must be between 7 and 15 digits.")
    return ValidationResult.success()


def validate_date_string(date_text: str, field_name: str = "Date", optional: bool = True) -> ValidationResult:
    raw = date_text.strip()
    if not raw:
        if optional:
            return ValidationResult.success()
        return ValidationResult.failure(f"{field_name} is required (YYYY-MM-DD).")
    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return ValidationResult.success()
    except ValueError:
        return ValidationResult.failure(f"{field_name} must be in YYYY-MM-DD format (e.g. 2008-04-15).")


def validate_sign_in(data: SignInData) -> ValidationResult:
    for value, name in ((data.username, "Username"), (data.password, "Password")):
        result = validate_non_empty(value, name)
        if not result.ok:
            return result
    return ValidationResult.success()


def validate_sign_up(data: SignUpData) -> ValidationResult:
    checks = (
        validate_non_empty(data.username, "Username"),
        validate_non_empty(data.password, "Password"),
        validate_non_empty(data.confirm_password, "Confirm password"),
        validate_non_empty(data.email, "Email"),
        validate_non_empty(data.phone, "Phone number"),
        validate_password_match(data.password, data.confirm_password),
        validate_password_strength(data.password),
        validate_email(data.email),
        validate_phone(data.phone),
    )
    for result in checks:
        if not result.ok:
            return result
    return ValidationResult.success()


def validate_employee_fields(
    name: str,
    email: str,
    phone: str,
    role: str,
    salary_text: str,
) -> tuple[ValidationResult, float | None]:
    for value, label in (
        (name, "Name"),
        (email, "Email"),
        (phone, "Phone"),
        (role, "Role"),
        (salary_text, "Salary"),
    ):
        result = validate_non_empty(value, label)
        if not result.ok:
            return result, None
    email_result = validate_email(email)
    if not email_result.ok:
        return email_result, None
    phone_result = validate_work_phone(phone, "Phone")
    if not phone_result.ok:
        return phone_result, None
    try:
        salary = float(salary_text.strip().replace(",", ""))
    except ValueError:
        return ValidationResult.failure("Salary must be a valid number."), None
    if salary < 0:
        return ValidationResult.failure("Salary cannot be negative."), None
    return ValidationResult.success(), salary


def validate_inventory_fields(
    item_name: str,
    category: str,
    quantity_text: str,
    price_text: str,
    supplier: str,
) -> tuple[ValidationResult, int | None, float | None]:
    for value, label in (
        (item_name, "Item name"),
        (category, "Category"),
        (quantity_text, "Quantity"),
        (price_text, "Price"),
        (supplier, "Supplier"),
    ):
        result = validate_non_empty(value, label)
        if not result.ok:
            return result, None, None
    try:
        quantity = int(quantity_text.strip())
    except ValueError:
        return ValidationResult.failure("Quantity must be a whole number."), None, None
    if quantity < 0:
        return ValidationResult.failure("Quantity cannot be negative."), None, None
    try:
        price = float(price_text.strip().replace(",", ""))
    except ValueError:
        return ValidationResult.failure("Price must be a valid number."), None, None
    if price < 0:
        return ValidationResult.failure("Price cannot be negative."), None, None
    return ValidationResult.success(), quantity, price


def validate_student_fields(
    admission: str,
    name: str,
    gender: str,
    dob: str,
    student_class: str,
    parent: str,
    parent_phone: str,
    email: str,
    address: str,
) -> ValidationResult:
    for value, label in (
        (admission, "Admission Number"),
        (name, "Full Name"),
        (gender, "Gender"),
        (student_class, "Class"),
        (parent, "Parent/Guardian Name"),
        (parent_phone, "Parent Phone"),
    ):
        result = validate_non_empty(value, label)
        if not result.ok:
            return result

    phone_result = validate_work_phone(parent_phone, "Parent Phone")
    if not phone_result.ok:
        return phone_result

    email_result = validate_email(email, optional=True)
    if not email_result.ok:
        return email_result

    dob_result = validate_date_string(dob, "Date of Birth", optional=True)
    if not dob_result.ok:
        return dob_result

    return ValidationResult.success()


def validate_teacher_fields(
    name: str,
    tsc_number: str,
    email: str,
    phone: str,
    department: str,
    subject1: str,
    subject2: str,
    salary_text: str,
) -> tuple[ValidationResult, float | None]:
    for value, label in (
        (name, "Teacher Name"),
        (tsc_number, "TSC Number"),
        (email, "Email"),
        (phone, "Phone"),
        (department, "Department"),
        (subject1, "Primary Subject"),
    ):
        result = validate_non_empty(value, label)
        if not result.ok:
            return result, None

    email_result = validate_email(email)
    if not email_result.ok:
        return email_result, None

    phone_result = validate_work_phone(phone, "Phone")
    if not phone_result.ok:
        return phone_result, None

    salary = 0.0
    if salary_text.strip():
        try:
            salary = float(salary_text.strip().replace(",", ""))
            if salary < 0:
                return ValidationResult.failure("Salary cannot be negative."), None
        except ValueError:
            return ValidationResult.failure("Salary must be a valid number."), None

    return ValidationResult.success(), salary


def validate_subject_fields(subject_name: str) -> ValidationResult:
    return validate_non_empty(subject_name, "Subject Name")


def validate_result_fields(
    student_id: int | None,
    subject_id: int | None,
    cat_text: str,
    exam_text: str,
) -> tuple[ValidationResult, int | None, int | None]:
    if not student_id or student_id <= 0:
        return ValidationResult.failure("Please select a student."), None, None
    if not subject_id or subject_id <= 0:
        return ValidationResult.failure("Please select a subject."), None, None

    try:
        cat_marks = int(cat_text.strip())
        if not (0 <= cat_marks <= 30):
            return ValidationResult.failure("Continuous Assessment (CAT) marks must be between 0 and 30."), None, None
    except ValueError:
        return ValidationResult.failure("CAT marks must be a whole number between 0 and 30."), None, None

    try:
        exam_marks = int(exam_text.strip())
        if not (0 <= exam_marks <= 70):
            return ValidationResult.failure("Main Exam marks must be between 0 and 70."), None, None
    except ValueError:
        return ValidationResult.failure("Exam marks must be a whole number between 0 and 70."), None, None

    return ValidationResult.success(), cat_marks, exam_marks


def validate_fee_fields(
    student_id: int | None,
    amount_required_text: str,
    amount_paid_text: str,
) -> tuple[ValidationResult, float | None, float | None]:
    if not student_id or student_id <= 0:
        return ValidationResult.failure("Please select a student."), None, None

    try:
        req = float(amount_required_text.strip().replace(",", ""))
        if req < 0:
            return ValidationResult.failure("Amount required cannot be negative."), None, None
    except ValueError:
        return ValidationResult.failure("Amount required must be a valid number."), None, None

    try:
        paid = float(amount_paid_text.strip().replace(",", ""))
        if paid < 0:
            return ValidationResult.failure("Amount paid cannot be negative."), None, None
    except ValueError:
        return ValidationResult.failure("Amount paid must be a valid number."), None, None

    return ValidationResult.success(), req, paid


def validate_bursary_fields(
    student_id: int | None,
    sponsor_name: str,
    amount_text: str,
    date_awarded: str,
) -> tuple[ValidationResult, float | None]:
    if not student_id or student_id <= 0:
        return ValidationResult.failure("Please select a student."), None
    if not sponsor_name.strip():
        return ValidationResult.failure("Sponsor Name is required."), None

    try:
        amount = float(amount_text.strip().replace(",", ""))
        if amount <= 0:
            return ValidationResult.failure("Amount awarded must be greater than zero."), None
    except ValueError:
        return ValidationResult.failure("Amount awarded must be a valid number."), None

    date_res = validate_date_string(date_awarded, "Date Awarded", optional=True)
    if not date_res.ok:
        return date_res, None

    return ValidationResult.success(), amount


def validate_boarding_fields(
    student_id: int | None,
    dormitory: str,
    bed_number: str,
) -> ValidationResult:
    if not student_id or student_id <= 0:
        return ValidationResult.failure("Please select a student.")
    if not dormitory.strip():
        return ValidationResult.failure("Please select or enter a Dormitory.")
    if not bed_number.strip():
        return ValidationResult.failure("Bed / Cubicle number is required.")
    return ValidationResult.success()


def validate_club_fields(
    club_name: str,
    patron: str,
    meeting_day: str,
) -> ValidationResult:
    for val, name in ((club_name, "Club Name"), (patron, "Patron Name"), (meeting_day, "Meeting Schedule")):
        res = validate_non_empty(val, name)
        if not res.ok:
            return res
    return ValidationResult.success()
