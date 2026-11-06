"""Regenerates the sample .docx files in this folder:  python sample_data/make_samples.py"""
from pathlib import Path

from docx import Document

OUT = Path(__file__).resolve().parent

DOCS = {
    "remote_work_policy.docx": {
        "title": "Acme Corp Remote Work Policy",
        "sections": [
            (
                "1. Eligibility",
                "All full-time employees who have completed their 90-day probation period may request remote work. "
                "Contractors and interns are not eligible for remote work unless their manager and HR approve an exception in writing.",
            ),
            (
                "2. Working Hours",
                "Remote employees must be available during core hours, 10:00 to 16:00 in their local time zone. "
                "Outside core hours, employees may arrange their schedule freely as long as they complete their contracted weekly hours of 40 hours.",
            ),
            (
                "3. Equipment and Allowances",
                "Acme Corp provides a laptop, a monitor and a headset to every remote employee. "
                "Employees also receive a one-time home office stipend of 500 USD and a monthly internet allowance of 40 USD. "
                "Receipts for the home office stipend must be submitted within 60 days of the employee's first remote workday.",
            ),
            (
                "4. In-Office Days",
                "Teams based within 50 km of an Acme office must come to the office at least two days per week. "
                "The Engineering department meets on Tuesdays and Thursdays. The Sales department meets on Mondays and Wednesdays.",
            ),
            (
                "5. Working From Abroad",
                "Employees may work from another country for up to 30 calendar days per year. "
                "Longer stays require approval from HR because of tax and legal implications. "
                "Employees must never work from a country under international sanctions.",
            ),
        ],
        "table": [
            ("Item", "Amount", "Frequency"),
            ("Home office stipend", "500 USD", "One time"),
            ("Internet allowance", "40 USD", "Monthly"),
            ("Co-working space budget", "150 USD", "Monthly, on request"),
        ],
    },
    "employee_onboarding_guide.docx": {
        "title": "Acme Corp Employee Onboarding Guide",
        "sections": [
            (
                "Before Day One",
                "HR sends the welcome email five business days before the start date. "
                "New hires must return the signed contract and the tax forms before their first day. "
                "IT ships the laptop to the employee's address so that it arrives at least two days before the start date.",
            ),
            (
                "Week One",
                "On the first day, every new hire attends the 9:30 orientation session led by the People team. "
                "Each new hire is assigned an onboarding buddy who answers day-to-day questions during the first 30 days. "
                "By the end of week one, the new hire must complete the mandatory security awareness training.",
            ),
            (
                "The First 90 Days",
                "The manager sets three goals for the first 90 days and reviews progress at day 30, day 60 and day 90. "
                "The probation period lasts 90 days. At the end of probation the manager and HR confirm the employment.",
            ),
            (
                "Benefits",
                "Employees receive 25 days of paid vacation per year, plus public holidays. "
                "Unused vacation days can be carried over to the next year, up to a maximum of 5 days. "
                "Health insurance starts on the first day of employment and also covers the employee's spouse and children.",
            ),
            (
                "Learning Budget",
                "Each employee has an annual learning budget of 1,200 USD for courses, books and conferences. "
                "Purchases above 300 USD need prior approval from the manager.",
            ),
        ],
        "table": [
            ("Milestone", "When", "Owner"),
            ("Welcome email", "5 business days before start", "HR"),
            ("Laptop delivered", "2 days before start", "IT"),
            ("Orientation session", "Day 1, 09:30", "People team"),
            ("Security training", "End of week 1", "Employee"),
            ("Probation review", "Day 90", "Manager and HR"),
        ],
    },
    "information_security_policy.docx": {
        "title": "Acme Corp Information Security Policy",
        "sections": [
            (
                "Passwords and Authentication",
                "Passwords must be at least 14 characters long and must be stored in the company password manager. "
                "Multi-factor authentication is mandatory for email, the VPN and all production systems. "
                "Passwords must be changed immediately if a compromise is suspected, and are otherwise rotated every 12 months.",
            ),
            (
                "Data Classification",
                "Company data is classified as Public, Internal, Confidential or Restricted. "
                "Customer personal data is always Restricted. Restricted data must be encrypted at rest and in transit "
                "and may only be shared with people who need it for their work.",
            ),
            (
                "Incident Reporting",
                "Any suspected security incident, such as a lost laptop or a phishing email that was clicked, must be reported "
                "to the Security team within one hour at security@acme.example. "
                "The Security team classifies the incident and informs affected customers within 72 hours when personal data is involved.",
            ),
            (
                "Devices",
                "Company laptops use full-disk encryption and automatic screen lock after 5 minutes of inactivity. "
                "Personal devices may only access company email through the managed mobile app. "
                "Installing unapproved software on company laptops is not allowed.",
            ),
            (
                "Backups",
                "Production databases are backed up every night and backups are kept for 35 days. "
                "A restore test is performed every quarter by the Infrastructure team.",
            ),
        ],
        "table": [
            ("Classification", "Example", "Encryption required"),
            ("Public", "Marketing website", "No"),
            ("Internal", "Meeting notes", "In transit"),
            ("Confidential", "Contracts", "At rest and in transit"),
            ("Restricted", "Customer personal data", "At rest and in transit"),
        ],
    },
}


def build(filename: str, spec: dict) -> None:
    doc = Document()
    doc.add_heading(spec["title"], level=0)
    for heading, body in spec["sections"]:
        doc.add_heading(heading, level=1)
        doc.add_paragraph(body)
    doc.add_heading("Summary Table", level=1)
    rows = spec["table"]
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            table.cell(r, c).text = value
    doc.save(OUT / filename)


if __name__ == "__main__":
    for name, spec in DOCS.items():
        build(name, spec)
        print("wrote", OUT / name)
