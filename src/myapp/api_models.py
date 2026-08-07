from datetime import date
from typing import Optional
from pydantic import BaseModel

class ExtensionJob(BaseModel):
    """
    Data received from the browser extension.
    """
    company: str
    position: str
    status: str

    company_website: str | None = None
    location: str | None = None

    source: str | None = None
    job_type: str | None = None

    date_applied: str | None = None

    contact_name: str | None = None
    contact_email: str | None = None

    salary_range: str | None = None

    work_arrangement: str | None = None
    office_days: int | None = None

    job_url: str | None = None
    job_description: str | None = None

    notes: str | None = None