# DB from Punchpass Reports

Creating a database from Punchpass reports for analytics.

[ERD](https://dbdocs.io/chezka/KMB-classes?view=relationships)

## Data Sources in Punchpass

Each table requires data from specific Punchpass reports:

### Customers
- Location: Customers -> Active Customers
- Required columns:
  - Customer Id
  - First Name
  - Last Name
  - Email
  - Date Added
  - Do Not Email

### Classes
- Location: Reports -> Classes -> Individual Class Details
- Required columns:
  - Class
  - Date
  - Time

### Passes
- Manually maintained
- Required columns:
  - pass_name
  - punches
  - price

### Purchases
- Location: Reports -> Passes -> Sales Details -> Pass Purchases
- Required columns:
  - Customer ID
  - Pass
  - Purchased
  - Paid with

### Attendances
- Location: Reports -> Attendances -> Attendances by date range
- Required columns:
  - Class Date
  - Class Time
  - Class
  - CustomerID
  - Pass Used
  - No Show

## Features

- Add and manage customer data
- Handle class schedules
- Manage pass types
- Track purchases
- Record class attendance
- Progress tracking for data operations
- Error logging system
- Duplicate detection for passes

## Prerequisites

- Python 3.8 or higher
- Supabase account and project
- Required Python packages:
  - pandas
  - python-dotenv
  - supabase
  - tkinter (usually comes with Python)

## Project Structure
