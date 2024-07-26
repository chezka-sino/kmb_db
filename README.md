# DB from Punchpass reports

Creating a database from Punchpass reports for anaytics

[ERD](https://dbdocs.io/chezka/KMB-classes?view=relationships)

### Which reports are needed for each table?
_Note: reports will have to be preprocessed before inserting to the database_
- customers: Customers -> Active Customers
- classes: Reports -> Classes -> Individual Class Details
- passes: manually maintained
- purchases: Reports -> Passes -> Sales Details -> Pass Purchases
- attendances: Reports -> Attendances -> Attendances by date range
