# DB from Punchpass Reports

Creating a database from Punchpass reports for analytics.

[ERD](https://dbdocs.io/chezka/KMB-classes?view=relationships)

## Data Sources

### Customers Table
- **Source:** Customers -> Active Customers
- **Required Columns:**
  - Customer Id
  - First Name
  - Last Name
  - Email
  - Date Added
  - Do Not Email

### Classes Table
- **Source:** Reports -> Classes -> Individual Class Details
- **Required Columns:**
  - Class
  - Date
  - Time

### Passes Table
- **Source:** Manually maintained
- **Required Columns:**
  - pass_name
  - punches
  - price

### Purchases Table
- **Source:** Reports -> Passes -> Sales Details -> Pass Purchases
- **Required Columns:**
  - Customer ID
  - Pass
  - Purchased
  - Paid with

### Attendances Table
- **Source:** Reports -> Attendances -> Attendances by date range
- **Required Columns:**
  - Class Date
  - Class Time
  - Class
  - CustomerID
  - Pass Used
  - No Show

## Features

### Data Validation
- Automatic column validation
- Date format verification
- Class existence checking
- Duplicate pass detection

### Progress Tracking
- Real-time progress bars
- Operation status updates
- Batch processing for large datasets

### Error Handling
- Detailed error logging
- User-friendly error messages
- Daily log rotation

## Prerequisites

- Python 3.8+
- Supabase account and project
- Required Python packages:
  - pandas
  - python-dotenv
  - supabase
  - tkinter (usually comes with Python)

## Setup

1. Create a `.env` file with your Supabase credentials:
SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_key

2. Run the application:
python src/main.py

## Common Issues

### Missing Columns
- Ensure CSV files contain all required columns
- Column names are case-sensitive
- Check for extra spaces in column names

### Date Formats
- Customer dates: YYYY-MM-DD
- Class times: HH:MM AM/PM

### Duplicate Handling
- Passes: System skips existing passes and reports duplicates
- Classes: Must exist before adding attendance records

## Error Logs

Logs are stored in `logs/error_log_YYYYMMDD.log` with the format:
```
YYYY-MM-DD HH:MM:SS,SSS - ERROR - Operation: [operation_name]
Error: [error_message]
Details: {
    "file": "path/to/file",
    "context": "additional_information",
    "traceback": "stack_trace"
}
```

## Support

If you encounter any issues:
1. Check the Common Issues section above
2. Review the error logs in the `logs` directory
3. Create an issue with:
   - Description of the problem
   - Relevant error messages
   - Steps to reproduce the issue
