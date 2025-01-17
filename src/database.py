import pandas as pd
from datetime import date, timedelta, datetime
import json
from json import loads
from supabase import Client

def customers(file_path, last_pull):
    """
    Process customer data from CSV file and filter by date range.
    
    Args:
        file_path (str): Path to the CSV file containing customer data
        last_pull (date): Date of last data pull to filter new records
    
    Returns:
        DataFrame: Processed customer information filtered by date range
    """
    yesterday = date.today() - timedelta(days=1)
    data = pd.read_csv(file_path)

    # renaming columns to match table
    data = data.rename(columns={
        'Customer Id': 'id',
        'First Name': 'first_name',
        'Last Name': 'last_name',
        'Email': 'email',
        'Date Added': 'created_at',
        'Do Not Email': 'dne'
    })
   
    # change to date
    data['created_at'] = pd.to_datetime(data['created_at']).dt.date

    # keeping needed columns
    cust_info = data[['id', 'first_name', 'last_name', 'email', 'created_at', 'dne']]

    # keeping only from date last pulled to yesterday
    cust_info = cust_info[(cust_info['created_at'] >= last_pull) & (cust_info['created_at'] <= yesterday)]
    
    return cust_info

def add_to_customers(supabase: Client, file_path: str, last_pull: date) -> int:
    """Add new customer records to the Supabase database."""
    customer_list = customers(file_path, last_pull)
    customer_list['created_at'] = pd.to_datetime(customer_list['created_at']).dt.strftime('%m-%d-%Y')
    cust_json = loads(customer_list.to_json(orient='records'))
    
    data = supabase.table('customers').insert(cust_json).execute()
    return len(cust_json)

def add_pass(supabase: Client, file_path: str) -> tuple[int, list]:
    """Add pass records to the Supabase database."""
    # Read new passes
    pass_list = pd.read_csv(file_path)
    
    # Get existing passes from database
    existing_passes = pd.DataFrame.from_records(
        supabase.table('passes').select('pass_name').execute().data
    )
    
    # Find duplicates and new passes
    duplicates = pass_list[pass_list['pass_name'].isin(existing_passes['pass_name'])]
    new_passes = pass_list[~pass_list['pass_name'].isin(existing_passes['pass_name'])]
    
    # If all passes are duplicates, raise error
    if new_passes.empty:
        duplicate_names = duplicates['pass_name'].tolist()
        raise ValueError(f"All passes already exist in the database: {', '.join(duplicate_names)}")
    
    # Insert only the new passes
    pass_json = loads(new_passes.to_json(orient='records'))
    data = supabase.table('passes').insert(pass_json).execute()
    
    # Return count of added passes and list of duplicates that were skipped
    duplicate_names = duplicates['pass_name'].tolist() if not duplicates.empty else []
    return len(pass_json), duplicate_names

def add_class(supabase: Client, file_path: str) -> int:
    """Add class records to the Supabase database."""
    data = pd.read_csv(file_path)

    # renaming columns to match table
    data = data.rename(columns={
        'Class': 'class_name',
        'Date': 'day',
        'Time': 'class_start'
    })

    # keeping needed columns
    class_info = data[['class_name', 'day', 'class_start']]
    class_json = loads(class_info.to_json(orient='records'))
    
    data = supabase.table('classes').insert(class_json).execute()
    return len(class_json)

def add_purchases(supabase: Client, file_path: str) -> int:
    """Add purchase records to the Supabase database."""
    data = pd.read_csv(file_path)

    data = data.rename(columns={
        'Customer ID': 'user_id',
        'Pass': 'pass_name',
        'Purchased': 'purchase_date',
        'Paid with': 'method'
    })

    purchase_info = data[['user_id', 'pass_name', 'purchase_date', 'method']]

    # pulling pass data to merge
    passes = pd.DataFrame.from_records(
        supabase.table('passes').select('*').execute().data)
    
    merged_data = purchase_info.merge(passes, left_on='pass_name', right_on='pass_name',
                                      how='left')
    merged_data = merged_data.drop(['pass_name','punches','price'], axis=1)
    merged_data = merged_data.rename(columns={'id':'pass_id'})

    purchase_json = loads(merged_data.to_json(orient='records'))
    data = supabase.table('purchases').insert(purchase_json).execute()
    return len(purchase_json)

def add_attendances(supabase: Client, file_path: str) -> int:
    """Add attendance records to the Supabase database."""
    try:
        raw = pd.read_csv(file_path)
        
        # Verify required columns exist (case-insensitive)
        required_columns = ['Class Date', 'Class Time', 'Class', 'CustomerID', 'Pass Used', 'No Show']
        actual_columns = raw.columns.tolist()
        
        # Check for missing columns (case-insensitive)
        missing_columns = []
        for required_col in required_columns:
            if required_col.lower() not in [col.lower() for col in actual_columns]:
                missing_columns.append(required_col)
        
        if missing_columns:
            error_message = (
                f"Missing required columns: {', '.join(missing_columns)}\n\n"
                f"Required columns are: {', '.join(required_columns)}\n\n"
                f"Found columns are: {', '.join(actual_columns)}"
            )
            raise ValueError(error_message)

        # Convert dates and times
        raw['Class Date'] = pd.to_datetime(raw['Class Date']).dt.strftime('%Y-%m-%d')
        raw['Class Time'] = pd.to_datetime(raw['Class Time'], format='%I:%M %p').dt.strftime('%H:%M:%S')

        # Get date range for classes query
        date_range_min = pd.to_datetime(raw['Class Date']).min()
        date_range_max = pd.to_datetime(raw['Class Date']).max()

        # Get relevant classes
        query = (
            supabase.table('classes')
            .select('*')
            .gte('day', date_range_min.strftime('%Y-%m-%d'))
            .lte('day', date_range_max.strftime('%Y-%m-%d'))
            .execute()
        )
        classes = pd.DataFrame.from_records(query.data)
        
        # Merge with classes
        merged_data = raw.merge(
            classes,
            left_on=['Class Date', 'Class Time', 'Class'],
            right_on=['day', 'class_start', 'class_name'],
            how='left'
        )
        
        # Check for unmatched classes
        unmatched_classes = merged_data[merged_data['id'].isna()]
        if not unmatched_classes.empty:
            unmatched_details = unmatched_classes[['Class Date', 'Class Time', 'Class']].drop_duplicates()
            raise ValueError(f"Some classes were not found in the database:\n\n" + 
                           unmatched_details.to_string(index=False))

        # Rename and process columns
        merged_data = merged_data.rename(columns={
            'id': 'class_id',
            'CustomerID': 'user_id',
            'No Show': 'no_show'
        })

        # Get pass data
        passes = pd.DataFrame.from_records(
            supabase.table('passes').select('*').execute().data
        )

        # Merge with passes
        merged_data = merged_data.merge(
            passes,
            left_on='Pass Used',
            right_on='pass_name',
            how='left'
        )
        
        merged_data = merged_data.rename(columns={'id': 'purchase_pass'})

        # Prepare final data
        final_data = merged_data[['user_id', 'class_id', 'purchase_pass', 'no_show']]
        
        # Insert data
        attendance_json = loads(final_data.to_json(orient='records'))
        data = supabase.table('attendances').insert(attendance_json).execute()
        return len(attendance_json)
        
    except pd.errors.EmptyDataError:
        raise ValueError("The CSV file is empty")
    except pd.errors.ParserError:
        raise ValueError("Error reading the CSV file. Please ensure it's a valid CSV format") 