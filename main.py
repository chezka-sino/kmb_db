import pandas as pd
from datetime import date
from datetime import timedelta
from datetime import datetime
from sqlalchemy import create_engine

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

    # only for first run. remove test 
    data = data.drop(data[data['first_name'] == 'Test'].index)
   
    # change to date
    data['created_at'] = pd.to_datetime(data['created_at']).dt.date

    # keeping needed columns
    cust_info = data[['id', 'first_name', 'last_name', 'email', 'created_at', 'dne']]

    # keeping only from date last pulled to yesterday
    cust_info = cust_info[(cust_info['created_at'] >= last_pull) & (cust_info['created_at'] <= yesterday)]

    return

if __name__ == "__main__":
    print("Menu")
    print("1. Add customer data")
    task = int(input('Select: ' ))
    if task == 1:
        customers()