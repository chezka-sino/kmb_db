import pandas as pd
from datetime import date
from datetime import timedelta
from datetime import datetime
import os
import json
from json import loads
from dotenv import load_dotenv
from supabase import create_client, Client

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

    # only for first run to remove test accounts
    # data = data.drop(data[data['first_name'] == 'Test'].index)
   
    # change to date
    data['created_at'] = pd.to_datetime(data['created_at']).dt.date

    # keeping needed columns
    cust_info = data[['id', 'first_name', 'last_name', 'email', 'created_at', 'dne']]

    # keeping only from date last pulled to yesterday
    cust_info = cust_info[(cust_info['created_at'] >= last_pull) & (cust_info['created_at'] <= yesterday)]
    
    return cust_info

def add_to_customers(supabase, file_path, last_pull):
    """
    Add new customer records to the Supabase database.
    
    Args:
        supabase (Client): Supabase client instance
        file_path (str): Path to customer CSV file
        last_pull (date): Date of last data pull
    
    Returns:
        int: Number of records added
    """
    customer_list = customers(file_path, last_pull)
    customer_list['created_at'] = pd.to_datetime(customer_list['created_at']).dt.strftime('%m-%d-%Y')
    cust_json = loads(customer_list.to_json(orient='records'))
    
    data = supabase.table('customers').insert(cust_json).execute()
    return data.count

def classes(file_path):
    """
    Process class data from CSV file.
    
    Args:
        file_path (str): Path to the CSV file containing class data
    
    Returns:
        DataFrame: Processed class information
    """
    data = pd.read_csv(file_path)

    # renaming columns to match table
    data = data.rename(columns={
        'Class': 'class_name',
        'Date': 'day',
        'Time': 'class_start'
    })

    # keeping needed columns
    class_info = data[['class_name', 'day', 'class_start']]

    return class_info

def add_class(supabase, file_path):
    """
    Add class records to the Supabase database.
    
    Args:
        supabase (Client): Supabase client instance
        file_path (str): Path to class CSV file
    
    Returns:
        int: Number of records added
    """
    class_list = classes(file_path)
    class_json = loads(class_list.to_json(orient='records'))
    
    data = supabase.table('classes').insert(class_json).execute()
    return data.count

def add_pass(supabase, file_path):
    """
    Add pass records to the Supabase database.
    
    Args:
        supabase (Client): Supabase client instance
        file_path (str): Path to pass CSV file
    
    Returns:
        tuple: (int, list) Number of records added and list of duplicate pass names
        
    Raises:
        ValueError: If all passes in the file already exist in the database
    """
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
    return data.count, duplicate_names

def purchases(file_path, supabase):
    """
    Process purchase data and merge with pass information.
    
    Args:
        file_path (str): Path to the CSV file containing purchase data
        supabase (Client): Supabase client instance
    
    Returns:
        DataFrame: Processed and merged purchase information
    """
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

    return merged_data

def add_purchases(supabase, file_path):
    """
    Add purchase records to the Supabase database.
    
    Args:
        supabase (Client): Supabase client instance
        file_path (str): Path to purchase CSV file
    
    Returns:
        int: Number of records added
    """
    purchase_list = purchases(file_path, supabase)
    purchase_json = loads(purchase_list.to_json(orient='records'))
    
    data = supabase.table('purchases').insert(purchase_json).execute()
    return data.count

def attendances(file_path, supabase):
    """
    Process attendance data and merge with class and pass information.
    
    Args:
        file_path (str): Path to the CSV file containing attendance data
        supabase (Client): Supabase client instance
    
    Returns:
        DataFrame: Processed and merged attendance information
        
    Raises:
        ValueError: If required columns are missing or if date parsing fails
    """
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

        # Convert dates safely
        try:
            date_range_min = pd.to_datetime(raw['Class Date']).min()
            date_range_max = pd.to_datetime(raw['Class Date']).max()
            
            raw['Class Date'] = pd.to_datetime(raw['Class Date']).dt.strftime('%Y-%m-%d')
        except Exception as e:
            raise ValueError("Error parsing 'Class Date' column. Please ensure dates are in a valid format (YYYY-MM-DD or MM/DD/YYYY)")

        # Convert times safely
        try:
            raw['Class Time'] = pd.to_datetime(raw['Class Time'], format='%I:%M %p').dt.strftime('%H:%M:%S')
        except Exception as e:
            raise ValueError("Error parsing 'Class Time' column. Please ensure times are in format 'HH:MM AM/PM'")

        # pulling class data first
        query = (
            supabase.table('classes')
            .select('*')
            .gte('day', date_range_min.strftime('%Y-%m-%d'))
            .lte('day', date_range_max.strftime('%Y-%m-%d'))
            .execute()
        )
        classes = pd.DataFrame.from_records(query.data)
        
        # Merge with classes first
        merged_data = raw.merge(
            classes,
            left_on=['Class Date', 'Class Time', 'Class'],
            right_on=['day', 'class_start', 'class_name'],
            how='left'
        )
        
        # Check if any classes weren't matched
        unmatched_classes = merged_data[merged_data['id'].isna()]
        if not unmatched_classes.empty:
            unmatched_details = unmatched_classes[['Class Date', 'Class Time', 'Class']].drop_duplicates()
            raise ValueError(f"Some classes were not found in the database:\n\n" + 
                           unmatched_details.to_string(index=False))

        # Rename class id column
        merged_data = merged_data.rename(columns={'id': 'class_id'})

        # pulling pass data to merge
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
        
        # Rename pass id column
        merged_data = merged_data.rename(columns={'id': 'purchase_pass'})

        # Final column renames and selection
        merged_data = merged_data.rename(columns={
            'CustomerID': 'user_id',
            'No Show': 'no_show'
        })

        # Select only the needed columns
        final_data = merged_data[['user_id', 'class_id', 'purchase_pass', 'no_show']]
        
        # Verify we have all required data
        if final_data['class_id'].isna().any():
            raise ValueError("Some classes could not be matched with the database")
        
        return final_data
        
    except pd.errors.EmptyDataError:
        raise ValueError("The CSV file is empty")
    except pd.errors.ParserError:
        raise ValueError("Error reading the CSV file. Please ensure it's a valid CSV format")

def add_attendances(supabase, file_path, progress_callback=None):
    """
    Add attendance records to the Supabase database.
    
    Args:
        supabase (Client): Supabase client instance
        file_path (str): Path to attendance CSV file
        progress_callback (callable, optional): Function to call with progress updates
    
    Returns:
        int: Number of records added
    """
    # Process the attendance data
    attendance_list = attendances(file_path, supabase)
    attendance_json = loads(attendance_list.to_json(orient='records'))
    total_records = len(attendance_json)
    
    # Insert records in batches to show progress
    batch_size = 100
    records_added = 0
    
    for i in range(0, total_records, batch_size):
        batch = attendance_json[i:i + batch_size]
        data = supabase.table('attendances').insert(batch).execute()
        records_added += len(batch)
        
        if progress_callback:
            progress_callback(records_added, total_records, "Adding attendance records")
    
    return total_records

if __name__ == "__main__":
    from ui import DatabaseUI
    import tkinter as tk
    
    root = tk.Tk()
    app = DatabaseUI(root)
    root.mainloop()