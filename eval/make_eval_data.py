"""Regenerates eval/corpus.json and eval/questions.json:  python eval/make_eval_data.py

The corpus is deliberately full of look-alike facts (several "within 24 hours", "within 30 days", "within 14 days"
in different policies) so that finding the right passage is not trivial. Each question names a `expect` phrase that
appears in exactly one passage; a retrieved chunk counts as a hit when it contains that phrase.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

CORPUS = {
    "Leave Policy": [
        ("Acme Corp Leave Policy", None),
        ("Annual Leave", "Every full-time employee receives 25 days of paid annual leave per calendar year. Part-time employees receive a proportional amount. Leave accrues monthly and may be taken from the first month of employment."),
        ("Carry Over", "Up to 5 unused annual leave days can be carried over into the next year. Carried-over days expire on 31 March, and days not taken by then are lost without compensation."),
        ("Requesting Leave", "Leave requests are submitted in the HR portal at least 14 days before the first day of absence. Managers answer within 3 working days. Requests for more than 10 consecutive days need approval from the department director."),
        ("Sick Leave", "Employees receive 10 days of paid sick leave per year. A medical certificate is required after 3 consecutive days of absence. Employees must inform their manager before 10:00 on the first day of illness."),
        ("Parental Leave", "The primary caregiver receives 16 weeks of fully paid parental leave, and the second parent receives 6 weeks. Parental leave can be taken in one block or split into two blocks within the first 12 months after the birth or adoption."),
        ("Unpaid Leave", "Employees with at least two years of service may request unpaid leave of up to 3 months. The request needs written approval from the department director and HR. Benefits are suspended during unpaid leave."),
        ("Public Holidays", "Acme observes the public holidays of the country in which the employee's contract is based. If a public holiday falls on a weekend, no replacement day is granted. Employees who work on a public holiday receive a day off in lieu within 60 days."),
        ("Bereavement Leave", "Employees receive 5 paid days after the death of a spouse, child or parent, and 2 paid days after the death of another close relative. Additional unpaid time can be agreed with the manager."),
    ],
    "Expense Reimbursement Policy": [
        ("Acme Corp Expense Reimbursement Policy", None),
        ("Submitting Claims", "Expense claims must be submitted in the finance portal within 30 days of the expense date. Late claims are only paid with written approval from the Finance Director."),
        ("Receipts", "An itemised receipt is required for every expense above 25 USD. For expenses of 25 USD or less, a short description in the claim is enough."),
        ("Meals", "While travelling, meals are reimbursed up to 60 USD per day. Alcohol is never reimbursed, even when it is part of a client dinner."),
        ("Approval Limits", "Managers approve claims up to 500 USD. Claims above 500 USD also need approval from the department director before payment."),
        ("Payment", "Approved claims are paid with the next payroll run, and no later than 10 business days after approval. Employees can follow the status of each claim in the finance portal."),
        ("Mileage", "Business use of a private car is reimbursed at 0.45 USD per kilometre. Employees must record the start and end point of each trip and the purpose of the visit."),
        ("Phone Allowance", "Employees who need a mobile phone for their work receive a flat allowance of 30 USD per month. The allowance is paid with the salary and is not part of the expense claim process."),
        ("Client Entertainment", "Client dinners need prior approval from a director and a list of attendees. The limit is 100 USD per person, including tip."),
        ("Corporate Cards", "Corporate cards are issued to managers and above. Cardholders must reconcile their statement within 15 days of the statement date, otherwise the card is suspended."),
        ("Foreign Currency", "Expenses in a foreign currency are converted at the exchange rate on the payment date shown on the bank or card statement."),
    ],
    "Business Travel Policy": [
        ("Acme Corp Business Travel Policy", None),
        ("Booking", "All flights and hotels are booked through the Acme travel portal at least 14 days before departure. Late bookings need approval from the traveller's manager."),
        ("Flights", "Economy class is used for flights shorter than 6 hours. For flights of 6 hours or longer, premium economy is allowed. Business class is only available to directors."),
        ("Hotels", "Hotel stays are capped at 180 USD per night, or 250 USD per night in cities on the high-cost list: London, New York, Tokyo and Zurich. Breakfast is included in the cap."),
        ("Rental Cars", "Rental cars are allowed only with manager approval and only when public transport is not practical. Insurance is included in the company rental rate."),
        ("Travel Insurance", "Every business trip is automatically covered by the company travel insurance. Employees do not need to buy extra cover for medical costs or cancelled flights."),
        ("Incidents", "Travel incidents such as a lost passport or a medical emergency must be reported to the Travel Desk within 24 hours on +1 555 0100. The Travel Desk arranges replacement documents and medical help."),
        ("Extending a Trip", "Employees may extend a business trip with personal days at their own cost, as long as the extra days do not raise the ticket price."),
        ("Visas", "The Travel Desk starts visa applications once the trip is approved. For countries that require a visa, employees must hand in their passport at least 20 working days before departure."),
        ("Loyalty Programmes", "Employees keep the frequent flyer miles and hotel points they collect on business trips."),
    ],
    "IT Equipment and Software Policy": [
        ("Acme Corp IT Equipment and Software Policy", None),
        ("Laptop Replacement", "Laptops are replaced every 36 months. Developers may request a higher specification with their manager's approval."),
        ("Lost or Stolen Devices", "A lost or stolen device must be reported to the IT Service Desk within 24 hours. IT locks and wipes the device remotely and issues a replacement within 2 business days."),
        ("Software Requests", "Software requests are submitted as a ticket and answered within 5 business days. Open source tools on the approved list can be installed without a ticket."),
        ("Peripherals", "Each employee may choose one 27-inch monitor, a keyboard and a mouse. Ergonomic chairs are ordered through Facilities, not through IT."),
        ("Removable Storage", "Personal USB storage devices must not be connected to company laptops. Files are shared through the company cloud storage."),
        ("Leaving the Company", "Equipment must be returned within 7 days after the last working day. Equipment that is not returned is deducted from the final salary at its remaining book value."),
        ("Networks", "The VPN must be used on all public networks. Visitors may only use the guest Wi-Fi, which has no access to internal systems."),
        ("Support Hours", "The IT Service Desk is open from 8:00 to 18:00 on working days. Critical outages are handled around the clock through the on-call phone line."),
    ],
    "Code of Conduct": [
        ("Acme Corp Code of Conduct", None),
        ("Gifts", "Gifts worth more than 50 USD must be declared to Compliance within 5 working days. Cash gifts are never accepted, whatever the amount."),
        ("Conflicts of Interest", "A conflict of interest must be disclosed to the Compliance team in writing as soon as it arises. Employees must not take part in decisions where they have a personal interest."),
        ("Raising Concerns", "Employees can report a concern anonymously through the ethics hotline, which is open 24 hours a day. Reports can also be made in person to Compliance or HR."),
        ("No Retaliation", "Retaliation against anyone who reports a concern in good faith is prohibited and leads to disciplinary action, up to dismissal."),
        ("Investigations", "Compliance acknowledges every report within 2 working days and aims to close the investigation within 30 working days. The person who reported the concern is told the outcome."),
        ("Outside Employment", "Outside employment requires written approval from the manager and HR. Work for a competitor is not permitted."),
        ("Social Media", "Employees must not share confidential information on social media and must make clear that personal opinions are their own."),
        ("Annual Training", "All employees complete the code of conduct training before 31 January every year. Managers receive a list of colleagues who have not finished it."),
    ],
    "Performance Review Policy": [
        ("Acme Corp Performance Review Policy", None),
        ("Review Cycle", "Performance reviews take place twice a year, in June and December. Each review covers the goals agreed at the start of the period."),
        ("Rating Scale", "Employees are rated on a scale from 1 to 5, where 3 means fully meets expectations. Ratings of 5 are limited to about 10 percent of a team."),
        ("Peer Feedback", "Every review includes written feedback from at least 3 colleagues chosen by the employee and the manager."),
        ("Appeals", "Employees may appeal their rating within 14 days of the review meeting. The appeal is decided by the next-level manager together with HR."),
        ("Promotions", "Promotions are decided once a year, in the January cycle, and take effect on 1 February. A promotion needs two consecutive ratings of 4 or higher."),
        ("Improvement Plans", "An employee rated 1 or 2 receives a performance improvement plan that lasts 60 days. Progress is reviewed every two weeks with the manager."),
        ("Goal Setting", "Goals are written in the HR portal in the first month of each period. Each employee has between three and five goals, and at least one is about personal development."),
    ],
    "Payroll and Compensation Policy": [
        ("Acme Corp Payroll and Compensation Policy", None),
        ("Pay Day", "Salaries are paid on the 25th of each month. When the 25th is a weekend or a public holiday, payment is made on the last working day before it."),
        ("Payslips", "Payslips are published in the HR portal on the day of payment. Employees can download the payslips of the last 36 months."),
        ("Overtime", "Overtime is paid at 1.5 times the normal hourly rate for hours above 40 per week. Overtime must be approved in advance by the manager."),
        ("Annual Bonus", "The annual bonus is paid in March together with the salary. The amount depends on the company result and the employee's last rating."),
        ("Salary Review", "Salaries are reviewed once a year in January. Increases take effect on 1 February and are announced by the manager in a personal meeting."),
        ("Payroll Errors", "Errors in a payslip must be reported to Payroll within 30 days of the payment. Underpayments are corrected in the next payroll run."),
        ("Pension", "Acme pays 5 percent of the gross salary into the employee's pension plan. Employees may add a further contribution of up to 10 percent."),
        ("Tax Documents", "Annual tax statements are available in the HR portal by 31 January."),
    ],
    "Health and Safety Policy": [
        ("Acme Corp Health and Safety Policy", None),
        ("Reporting Injuries", "Workplace injuries must be reported to the safety officer within 24 hours, even when the injury seems minor. The safety officer records the incident and decides whether an investigation is needed."),
        ("First Aid", "Acme has one trained first aider for every 25 employees. Their names and phone numbers are posted next to the first aid boxes on each floor."),
        ("Fire Drills", "Fire drills are held every 6 months. Employees must leave the building by the nearest marked exit and must not use the lifts."),
        ("Evacuation", "After an evacuation, everyone gathers at the assembly point, which is car park B. The floor warden counts the team and reports missing colleagues to the safety officer."),
        ("Ergonomics", "Employees can ask for an ergonomic assessment of their workplace. The assessment takes place within 10 business days of the request."),
        ("Emergency Number", "The internal emergency number is 555. For life-threatening situations call the public emergency number first."),
        ("Working From Home", "Employees working from home are covered by the same safety rules. They must report accidents that happen during working hours within 24 hours."),
        ("Hazard Reports", "Hazards such as wet floors or damaged cables should be reported to Facilities immediately through the helpdesk."),
    ],
    "Procurement Policy": [
        ("Acme Corp Procurement Policy", None),
        ("Quotes", "Purchases above 5,000 USD require three written quotes from different vendors. The cheapest quote does not have to win, but the choice must be explained in writing."),
        ("Approval Limits", "Purchases above 25,000 USD require approval from the CFO. Purchases above 100,000 USD also require approval from the management board."),
        ("Approved Vendors", "Orders should be placed with vendors on the approved vendor list. New vendors are added after a check by Procurement and Legal, which takes about 10 business days."),
        ("Contract Review", "Legal reviews every contract within 5 business days of receiving it. Contracts must be signed before work starts."),
        ("Payment Terms", "The standard payment term for suppliers is net 45 days from the invoice date. Shorter terms need approval from Finance."),
        ("Purchase Orders", "A purchase order is required for every purchase above 1,000 USD. Invoices without a purchase order are returned to the supplier."),
        ("Sustainability", "Procurement asks suppliers about their environmental policy. Suppliers with a recognised certification are preferred when quotes are similar."),
    ],
    "Data Retention and Privacy Policy": [
        ("Acme Corp Data Retention and Privacy Policy", None),
        ("Customer Data", "Customer data is kept for 7 years after the contract ends, because of tax and accounting rules. After that period it is deleted or anonymised."),
        ("Employee Records", "Employee records are kept for 6 years after the employee leaves Acme. Application documents of candidates who were not hired are deleted after 6 months."),
        ("Access Logs", "Access logs of production systems are kept for 12 months. Logs are only inspected when there is a security incident or a legal request."),
        ("Deletion Requests", "Acme answers customer deletion requests within 30 days. The Privacy Officer confirms by email once the data has been erased."),
        ("Data Breaches", "A personal data breach must be reported to the regulator within 72 hours of Acme becoming aware of it. Affected customers are told without undue delay."),
        ("Data Protection Officer", "The Data Protection Officer can be reached at privacy@acme.example. Employees with privacy questions should contact the officer before sharing personal data with third parties."),
        ("Backups", "Backups are encrypted and kept for 35 days. Deleted data may remain in backups until they expire."),
    ],
}

QUESTIONS = [
    ("How many vacation days do I get per year?", "25 days of paid annual leave"),
    ("How many unused holiday days can I take into next year?", "Up to 5 unused annual leave days"),
    ("Do I need a doctor's note when I am ill?", "A medical certificate is required after 3 consecutive days"),
    ("How long is parental leave for the second parent?", "the second parent receives 6 weeks"),
    ("By when must I hand in an expense claim?", "within 30 days of the expense date"),
    ("From what amount do I need to attach a receipt?", "itemised receipt is required for every expense above 25 USD"),
    ("What is the daily food allowance on business trips?", "meals are reimbursed up to 60 USD per day"),
    ("Who has to approve expense claims over 500 USD?", "Claims above 500 USD also need approval from the department director"),
    ("How far ahead do I have to book flights?", "at least 14 days before departure"),
    ("What is the maximum price per night for a hotel in London?", "250 USD per night in cities on the high-cost list"),
    ("When am I allowed to fly premium economy?", "For flights of 6 hours or longer"),
    ("How quickly must a lost laptop be reported?", "must be reported to the IT Service Desk within 24 hours"),
    ("How often do laptops get replaced?", "Laptops are replaced every 36 months"),
    ("How long do I have to give back my equipment after I quit?", "returned within 7 days after the last working day"),
    ("From what value do I have to declare a gift?", "Gifts worth more than 50 USD"),
    ("Can I report misconduct without giving my name?", "report a concern anonymously through the ethics hotline"),
    ("How many times a year are performance reviews held?", "twice a year, in June and December"),
    ("How long do I have to appeal my rating?", "appeal their rating within 14 days"),
    ("On which day of the month is the salary paid?", "Salaries are paid on the 25th of each month"),
    ("How much extra is overtime paid?", "1.5 times the normal hourly rate"),
    ("How soon must a workplace injury be reported?", "Workplace injuries must be reported to the safety officer within 24 hours"),
    ("Where do we meet after the building is evacuated?", "assembly point, which is car park B"),
    ("How many quotes do I need for a purchase of 8,000 dollars?", "three written quotes from different vendors"),
    ("How long is customer data stored after the contract ends?", "kept for 7 years after the contract ends"),
    ("How fast must a data breach be reported to the authorities?", "within 72 hours of Acme becoming aware"),
    ("How quickly do you answer a customer's request to erase their data?", "customer deletion requests within 30 days"),
]


def build() -> None:
    corpus = []
    for title, parts in CORPUS.items():
        blocks = []
        for heading, body in parts:
            blocks.append(heading if body is None else f"{heading}\n\n{body}")
        corpus.append({"title": title, "text": "\n\n".join(blocks)})
    (OUT / "corpus.json").write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    questions = [{"question": q, "expect": e} for q, e in QUESTIONS]
    (OUT / "questions.json").write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
