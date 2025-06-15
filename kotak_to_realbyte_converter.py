import csv
import re
import pandas as pd
from datetime import datetime
import sys
import os

def parse_kotak_statement(input_file):
    """
    Parse Kotak Mahindra Bank statement CSV file and extract transaction data
    """
    # Read the entire file content
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.readlines()
    
    # Find the line where transaction details start
    transaction_start = 0
    for i, line in enumerate(content):
        if 'Sl. No.,Transaction Date,Value Date,Description' in line:
            transaction_start = i
            break
    
    if transaction_start == 0:
        print("Error: Could not find transaction details header in the statement")
        return None
    
    # Create a list to store transaction data
    transactions = []
    
    # Process transaction lines
    for line in content[transaction_start+1:]:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Parse the CSV line
        try:
            row = next(csv.reader([line]))
            
            # Check if this is a valid transaction row
            if len(row) >= 8 and re.match(r'\d+', row[0]):
                # Extract transaction data
                sl_no = row[0]
                trans_date = row[1]
                value_date = row[2]
                description = row[3]
                ref_no = ''    #row[4]
                amount = row[5].replace(',', '') if row[5] else '0'
                dr_cr = row[6]
                balance = row[7]
                date_part = trans_date.split()[0] if ' ' in trans_date else trans_date
                category = categorize_transaction(description)
                subcategory = get_subcategory(category, description)

                # Process and add to transactions list
                transactions.append({
                    
                    'transaction_date': datetime.strptime(date_part, '%d-%m-%Y').strftime('%d/%m/%Y'),  # Convert to DD/MM/YYYY
                    'description': description,
                    'ref_no': ref_no,
                    'amount': float(amount.replace(',', '')),
                    'type': 'Expense' if dr_cr == 'DR' else 'Income',
                    'category': category,
                    'subcategory': subcategory,
                    'account': 'Kotak'  # Default account name
                })
        except Exception as e:
            print(f"Error processing line: {line}")
            print(f"Error details: {e}")
            continue
    
    return transactions

def parse_kvb_statement(input_file):
    """
    Parse KVB Bank statement CSV file and extract transaction data
    """
    # Read the entire file content
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # Find the line where transaction details start
    transaction_start = 0
    for i, line in enumerate(content):
        if 'Transaction Date,Value Date,Branch,Cheque No.,Description,Debit,Credit,Balance' in line:
            transaction_start = i
            break

    if transaction_start == 0:
        print("Error: Could not find transaction details header in the statement")
        return None

    # Create a list to store transaction data
    transactions = []

    # Process transaction lines
    for line in content[transaction_start+1:]:
        # Skip empty lines
        if not line.strip():
            continue

        # Parse the CSV line
        try:
            row = next(csv.reader([line]))

            # Check if this is a valid transaction row
            if len(row) >= 8:
                # Extract transaction data
                trans_date = row[0]
                value_date = row[1]
                description = "" #row[4]
                debit = row[5].replace(',', '') if row[5] else '0'
                credit = row[6].replace(',', '') if row[6] else '0'
                balance = row[7].replace(',', '')

                # Determine transaction type and amount
                if float(debit) > 0:
                    amount = float(debit)
                    trans_type = 'Expense'
                else:
                    amount = float(credit)
                    trans_type = 'Income'

                # Process and add to transactions list
                transactions.append({
                    'transaction_date': datetime.strptime(trans_date, '%d-%m-%Y %H:%M:%S').strftime('%d/%m/%Y'),
                    'description': description,
                    'ref_no': "", #row[3],
                    'amount': amount,
                    'type': trans_type,
                    'category': categorize_transaction(description),
                    'account': 'KVB'  # Default account name
                })
        except Exception as e:
            print(f"Error processing line: {line}")
            print(f"Error details: {e}")
            continue

    return transactions

def categorize_transaction(description):
    """
    Basic automatic categorization based on description keywords
    """
    description = description.lower()
    
    # Define category mapping based on keywords
    categories = {
        'Food': ['restaurant', 'food', 'swiggy', 'zomato', 'cafe', 'dine', 'food out','water', 'juice','hotel','milk','NEIGHBOURHOOD V'],
        'Transportation': ['uber', 'ola', 'cab', 'taxi', 'auto', 'petrol', 'fuel', 'railways', 'irctc', 'train', 'fuels', 'rail'],
        'Culture': ['movie', 'netflix', 'prime', 'hotstar', 'subscription'],
        'Household': ['bill', 'electricity', 'phone', 'mobile', 'recharge', 'dth', 'broadband', 'internet'],
        'Health': ['medical', 'hospital', 'doctor', 'pharmacy', 'medicine', 'health'],
        'Education': ['course', 'college', 'school', 'fees', 'tuition', 'education'],
        'Investment': ['investment', 'mutual fund', 'stocks', 'shares', 'sip'],
        'Apparel': ['clothes', 'clothing', 'fashion', 'dress', 'shirt', 'pants', 'shoes'],
        'Interests': ['premat'],
        "Gift": ['gift', 'present', 'gifts', 'birthday', 'anniversary']
    }
    
    # Try to match description with categories
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in description:
    
                return category
    
    # Default category if no match found
    return 'unknown'

def get_subcategory(category, description):
    """
    Returns a subcategory for a given category and description using keyword matching.
    """
    description = description.lower()
    subcategories = {
        'Household': [
            ('Maid', ['maid']),
            ('Furniture', ['furniture', 'sofa', 'table', 'chair', 'bed']),
            ('Kitchen', ['kitchen', 'utensil', 'cooker', 'mixer']),
            ('Phone Bill', ['phone', 'mobile', 'recharge']),
            ('Other Essentials', ['essential', 'grocery', 'daily', 'toiletries']),
            ('Appliances', ['appliance', 'fridge', 'ac', 'microwave', 'washing machine']),
            ('Internet', ['internet', 'broadband', 'wifi']),
            ('DTH', ['dth', 'set top']),
            ('Mom hyd', ['mom hyd']),
            ('Ironing', ['iron']),
            ('Maintenance', ['maintenance', 'repair']),
            ('Cook', ['cook']),
            ('Toiletries', ['toiletries', 'soap', 'shampoo', 'toothpaste']),
            ('Painting', ['paint', 'painting']),
            ('Electricity', ['electricity', 'power']),
            ('Packers and movers', ['packers', 'movers', 'moving']),
            ('Home Loan', ['home loan', 'loan'])
        ],
        'Food': [
            ('Vegis/Groceries', ['grocery', 'vegetable', 'vegi', 'groceries', 'fruit', 'milk', 'water']),
            ('Eating out', ['restaurant', 'swiggy', 'zomato', 'cafe', 'dine', 'hotel', 'food out', 'eating out']),
            ('Beverages', ['beverage', 'juice', 'coffee', 'tea', 'drink', 'beverages']),
            ('Snack', ['snack', 'chips', 'namkeen', 'biscuit']),
            ('Lunch', ['lunch']),
            ('Dinner', ['dinner'])
        ],
        'Transportation': [
            ('Taxi', ['uber', 'ola', 'taxi', 'cab']),
            ('Subway/Train', ['train', 'subway', 'metro', 'rail', 'irctc']),
            ('Bike', ['bike', 'cycle', 'bicycle']),
            ('Parcel/Courier', ['parcel', 'courier', 'delivery']),
            ('Car', ['car', 'drive']),
            ('Flight ✈️', ['flight', 'air', 'airport']),
            ('Bus', ['bus']),
            ('Fine', ['fine', 'penalty'])
        ],
        'Beauty': [
            ('Beauty', ['beauty', 'salon', 'spa']),
            ('Cosmetics', ['cosmetic', 'makeup', 'lipstick']),
            ('Haircut', ['haircut', 'hair']),
            ('Accessories', ['accessory', 'jewellery', 'earring', 'ring'])
        ],
        'Culture': [
            ('Music', ['music', 'spotify', 'itunes']),
            ('Sports', ['sport', 'cricket', 'football', 'badminton']),
            ('Apps', ['app', 'application', 'software']),
            ('Gaming', ['game', 'gaming']),
            ('OTT', ['netflix', 'prime', 'hotstar', 'ott', 'subscription']),
            ('Books', ['book', 'novel']),
            ('Movie', ['movie', 'cinema']),
            ('Dance/Club', ['dance', 'club']),
            ('Gym', ['gym', 'fitness']),
            ('Yoga', ['yoga']),
            ('Crafting', ['craft', 'crafting'])
        ],
        'Health': [
            ('Insurance', ['insurance']),
            ('Medicine', ['medicine', 'pharmacy', 'tablet', 'medic']),
            ('Health Tests', ['test', 'diagnostic', 'lab', 'scan']),
            ('Hospital', ['hospital', 'clinic']),
            ('Health', ['health', 'doctor', 'checkup']),
            ('Baby Food', ['baby food', 'infant']),
            ('Specs', ['specs', 'spectacles', 'glasses'])
        ],
        'Social Life': [
            ('Hangout', ['hangout', 'meet']),
            ('Party', ['party']),
            ('Fun', ['fun', 'outing']),
            ('Friend', ['friend'])
        ],
        'Trip': [
            ('Food', ['food', 'meal', 'lunch', 'dinner']),
            ('Misc', ['misc', 'other']),
            ('Transportation', ['taxi', 'train', 'flight', 'bus', 'car', 'transport']),
            ('Stay/Hotel', ['stay', 'hotel']),
            ('Tickets', ['ticket', 'tickets'])
        ],
        'Apparel': [
            ('Clothing', ['clothes', 'clothing', 'shirt', 'pant', 'dress', 'kurta', 'jeans', 'tshirt', 'saree']),
            ('Shoes', ['shoe', 'shoes', 'sandal']),
            ('Specs', ['specs', 'spectacles', 'glasses']),
            ('Fashion', ['fashion', 'style']),
            ('Laundry', ['laundry', 'wash']),
            ('Watch', ['watch'])
        ],
        'Tax': [
            ('PT', ['pt']),
            ('TDS', ['tds']),
            ('Tax', ['tax'])
        ],
        'Services': [
            ('House broker', ['broker', 'agent']),
            ('Taxation', ['taxation']),
            ('Passport', ['passport']),
            ('Cleaning', ['clean', 'cleaning'])
        ],
        'Event': [
            ('Stay', ['stay', 'hotel']),
            ('Food', ['food', 'meal']),
            ('Decorations', ['decor', 'decoration'])
        ],
        'Education': [
            ('Schooling', ['school', 'schooling'])
        ],
        'Marriage': [
            ('transport', ['transport', 'taxi', 'car', 'bus']),
            ('footwear', ['footwear', 'shoe', 'sandal']),
            ('clothes', ['clothes', 'clothing', 'dress']),
            ('gifts', ['gift', 'present']),
            ('photographer', ['photo', 'photographer']),
            ('food', ['food', 'meal']),
            ('stay', ['stay', 'hotel']),
            ('publicity', ['publicity']),
            ('beauty', ['beauty', 'salon']),
            ('invitation cards', ['invitation', 'card'])
        ]
    }

    if category in subcategories:
        #print(f"Finding subcategory for category: {category}")
        for subcat, keywords in subcategories[category]:
            #print(f"Checking subcategory: {subcat} with keywords: {keywords}")
            for keyword in keywords:
                #print(f"Checking keyword: {keyword} in description: {description}")
                if keyword in description:
                    #print(f"Matched subcategory: {subcat}")
                    return subcat
    return ''

def create_realbyte_import_file(transactions, output_file):
    """
    Create RealByte Money Manager import file in TSV format
    """
    # Ensure the output file is unique
    if os.path.exists(output_file):
        base, ext = os.path.splitext(output_file)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        output_file = f"{base}_{timestamp}{ext}"

    # Define header as per RealByte format
    headers = ['Date', 'Account', 'Category', 'Subcategory', 'Note', 'Amount', 'Income/Expense', 'Description']

    # Create DataFrame for easier handling
    df = pd.DataFrame(columns=headers)

    # Add transaction data
    for trans in transactions:
        df = df._append({
            'Date': trans['transaction_date'],
            'Account': trans['account'],  # Default account name
            'Category': trans['category'],
            'Subcategory': trans['subcategory'],  # Leave empty for now
            'Note': trans['ref_no'],
            'Amount': abs(trans['amount']),  # Absolute amount
            'Income/Expense': trans['type'],
            'Description': trans['description']
        }, ignore_index=True)

    # Write to TSV file
    df.to_csv(output_file, index=False, sep='\t')
    print(f"Successfully converted and saved to {output_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python kotak_to_realbyte.py <input_kotak_file> <output_realbyte_file>")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    bank = sys.argv[3]
    
    # Process the statement
    if bank == 'kotak':
        transactions = parse_kotak_statement(input_file)
    elif bank == 'kvb':
        transactions = parse_kvb_statement(input_file)
    
    if transactions:
        create_realbyte_import_file(transactions, output_file)
    else:
        print("No transactions found or error in processing the statement")

if __name__ == "__main__":
    main()
