import pandas as pd
from datetime import date
from datetime import timedelta
from datetime import datetime
import os
import json
from json import loads
from dotenv import load_dotenv
from supabase import create_client, Client

def customers():
    last_pull = datetime.strptime(input('Last pull date: '), '%Y-%m-%d').date()
    yesterday = date.today() - timedelta(days=1)
    file = input('File path: ')
    data = pd.read_csv(file)

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

def add_to_customers(supabase):
    customer_list = customers()
    customer_list['created_at'] = pd.to_datetime(customer_list['created_at']).dt.strftime('%m-%d-%Y')
    cust_json = loads(customer_list.to_json(orient='records'))
    
    data = supabase.table('customers').insert(cust_json).execute()
    print('Added rows to customers', data.count)

def classes():
    file = input('File path: ')
    data = pd.read_csv(file)

    # renaming columns to match table
    data = data.rename(columns={
        'Class': 'class_name',
        'Date': 'day',
        'Time': 'class_start'
    })

    # keeping needed columns
    class_info = data[['class_name', 'day', 'class_start']]

    return class_info

def add_class(supabase):
    class_list = classes()
    class_json = loads(class_list.to_json(orient='records'))
    
    data = supabase.table('classes').insert(class_json).execute()

def add_pass(supabase):
    
    file = input('File path: ')
    pass_list = pd.read_csv(file)
    pass_json = loads(pass_list.to_json(orient='records'))
    
    data = supabase.table('passes').insert(pass_json).execute()

def purchases():
    file = input('File path: ')
    data = pd.read_csv(file)

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

def add_purchases(supabase):

    purchase_list = purchases()
    purchase_json = loads(purchase_list.to_json(orient='records'))
    
    data = supabase.table('purchases').insert(purchase_json).execute()

def attendances():
    file = input('File path: ')
    raw = pd.read_csv(file)

    date_range_min = raw['Class Date'].min()
    date_range_max = raw['Class Date'].max()
    
    raw['Class Date'] = pd.to_datetime(
        raw['Class Date'], format='%Y-%m-%d').dt.strftime('%Y-%m-%d')
    
    raw['Class Time'] = pd.to_datetime(
        raw['Class Time'], format='%I:%M %p').dt.strftime('%H:%M:%S')

    # pulling pass data to merge
    passes = pd.DataFrame.from_records(
        supabase.table('passes').select('*').execute().data)

    # pulling class data to merge
    query = (
        supabase.table('classes')
        .select('*')
        .gte('day', date_range_min)
        .lte('day', date_range_max)
        .execute()
        )
    
    classes = pd.DataFrame.from_records(query.data)

    # merging with pass data
    merged_data = raw.merge(passes, left_on='Pass Used', right_on='pass_name',
                                      how='left')
    # rename id to class_id
    merged_data = merged_data.rename(columns={
        'id': 'purchase_pass'
    })

    # merging with class data
    merged_data = merged_data.merge(classes, 
                                    left_on=['Class Date', 'Class Time', 'Class'],
                                    right_on=['day','class_start', 'class_name'],
                                    how='left')
    
    # rename remaining columns
    merged_data = merged_data.rename(columns={
        'id': 'class_id',
        'CustomerID': 'user_id',
        'No Show': 'no_show'
    })

    return merged_data[['user_id', 'class_id', 'purchase_pass', 'no_show']]

def add_attendances(supabase):
    attendance_list = attendances()
    attendance_json = loads(attendance_list.to_json(orient='records'))
    
    data = supabase.table('attendances').insert(attendance_json).execute()

if __name__ == "__main__":
    
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SECRET_KEY")
    supabase: Client = create_client(url, key)

    print("Menu")
    print("1. Add customer data")
    print("2. Add pass")
    print("3. Add classes")
    print("4. Add purchases")
    print("5. Add attendances")

    task = int(input('Select: ' ))

    if task == 1:
        add_to_customers(supabase)
    elif task == 2:
        add_pass(supabase)
    elif task == 3:
        add_class(supabase)
    elif task == 4:
        add_purchases(supabase)
    elif task == 5:
        add_attendances(supabase)