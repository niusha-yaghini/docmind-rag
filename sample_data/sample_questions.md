# Sample questions

Load the sample documents first (`docker compose exec web python manage.py load_sample_data`), then try these
in `POST /api/ask/` (or Swagger at `/api/docs/`).

| # | Question | Expected answer (from) |
|---|----------|------------------------|
| 1 | How much is the home office stipend? | 500 USD, one time (remote work policy) |
| 2 | How many days per year can I work from abroad? | Up to 30 calendar days (remote work policy) |
| 3 | What are the core working hours for remote employees? | 10:00 to 16:00 local time (remote work policy) |
| 4 | How many vacation days do employees get and how many can be carried over? | 25 days, up to 5 carried over (onboarding guide) |
| 5 | How long does the probation period last? | 90 days (onboarding guide) |
| 6 | Who is assigned to answer questions in the first 30 days? | An onboarding buddy (onboarding guide) |
| 7 | How long must passwords be? | At least 14 characters (security policy) |
| 8 | Within what time must a security incident be reported? | Within one hour (security policy) |
| 9 | How long are database backups kept? | 35 days (security policy) |
| 10 | What is the CEO's favourite colour? | Not in the documents, so the answer should say it could not be found |

Keyword-style retrieval check (no LLM): `GET /api/search/?q=home office stipend`.
