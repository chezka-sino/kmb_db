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
    customer_list['created_at'] = pd.to_datetime(customer_list['created_at']).dt.strftime('%Y-%m-%d')
    cust_json = loads(customer_list.to_json(orient='records'))
    
    data = supabase.table('customers').insert(cust_json).execute()

def add_pass(supabase):
    
    file = input('File path: ')
    pass_list = pd.read_csv(file)
    pass_json = loads(pass_list.to_json(orient='records'))
    
    data = supabase.table('passes').insert(pass_json).execute()

if __name__ == "__main__":
    
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SECRET_KEY")
    supabase: Client = create_client(url, key)

    print("Menu")
    print("1. Add customer data")
    print("2. Add pass")

    task = int(input('Select: ' ))

    if task == 1:
        add_to_customers(supabase)
    elif task == 2:
        add_pass(supabase)