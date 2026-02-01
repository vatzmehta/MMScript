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
    print(f"Reading KVB statement from {input_file}")
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

                category = categorize_transaction(description)
                subcategory = get_subcategory(category, description)

                # Process and add to transactions list
                transactions.append({
                    'transaction_date': datetime.strptime(trans_date, '%d-%m-%Y %H:%M:%S').strftime('%d/%m/%Y'),
                    'description': description,
                    'ref_no': "", #row[3],
                    'amount': amount,
                    'type': trans_type,
                    'category': category,
                    'subcategory': subcategory,
                    'account': 'KVB'  # Default account name
                })
        except Exception as e:
            print(f"Error processing line: {line}")
            print(f"Error details: {e}")
            continue

    return transactions

def parse_equitas_statement(input_file):
    """
    Parse Equitas Small Finance Bank statement CSV file and extract transaction data
    """
    # Read entire file content
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find the line where transaction details start (look for "Narration" to identify header)
    transaction_start = -1
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Narration' in line and 'Date' in line:
            transaction_start = i
            break
    
    if transaction_start == -1:
        print("Error: Could not find transaction details header in the statement")
        return None
    
    # Create a list to store transaction data
    transactions = []
    
    # Use pandas to read from the header line onwards to handle complex CSV properly
    from io import StringIO
    csv_content = '\n'.join(lines[transaction_start:])
    
    try:
        df = pd.read_csv(StringIO(csv_content), skipinitialspace=True)
        
        # Clean up column names (remove extra whitespace and newlines)
        df.columns = df.columns.str.replace('\n', ' ').str.strip()
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Skip rows with NaN dates or empty dates
                if pd.isna(row.get('Date')) or row.get('Date') == '*** End of the Statement ***':
                    continue
                
                trans_date_str = str(row.get('Date', '')).strip()
                if not trans_date_str or trans_date_str.startswith('***'):
                    continue
                
                # Parse the date
                trans_date = datetime.strptime(trans_date_str, '%d-%b-%Y').strftime('%d/%m/%Y')
                
                # Extract fields
                narration = str(row.get('Narration', '')).strip()
                ref_no = str(row.get('Reference No. / Cheque No.', '')).strip()
                
                # Handle withdrawal and deposit columns (which may have newlines in header)
                withdrawal_val = str(row.get('Withdrawal\nINR', row.get('Withdrawal INR', ''))).strip()
                deposit_val = str(row.get('Deposit\nINR', row.get('Deposit INR', ''))).strip()
                
                # Clean currency values
                withdrawal = float(withdrawal_val.replace(',', '')) if withdrawal_val and withdrawal_val != 'nan' else 0.0
                deposit = float(deposit_val.replace(',', '')) if deposit_val and deposit_val != 'nan' else 0.0
                
                # Determine transaction type and amount
                if withdrawal > 0:
                    amount = withdrawal
                    trans_type = 'Expense'
                elif deposit > 0:
                    amount = deposit
                    trans_type = 'Income'
                else:
                    continue
                
                category = categorize_transaction(narration)
                subcategory = get_subcategory(category, narration)
                
                transactions.append({
                    'transaction_date': trans_date,
                    'description': narration,
                    'ref_no': ref_no,
                    'amount': amount,
                    'type': trans_type,
                    'category': category,
                    'subcategory': subcategory,
                    'account': 'Equitas'
                })
            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                continue
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None
    
    return transactions

def parse_axis_statement(input_file):
    """
    Parse Axis Bank statement text file and extract transaction data
    """
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    transactions = []
    # Regex to capture date, description, and amounts with Dr/Cr identifiers
    # It handles cases with one or two amounts on the same line.
    pattern = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(.*?)\s+([\d,]+\.\d{2})\s+(Dr|Cr)(?:\s+([\d,]+\.\d{2})\s+(Dr|Cr))?")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = pattern.search(line)
        if match:
            date_str, description, amount1_str, type1, amount2_str, type2 = match.groups()
            
            # Clean up description
            description = description.strip()

            # First amount
            amount1 = float(amount1_str.replace(',', ''))
            if amount1 > 0:
                category1 = categorize_transaction(description)
                subcategory1 = get_subcategory(category1, description)
                transactions.append({
                    'transaction_date': datetime.strptime(date_str, '%d/%m/%Y').strftime('%d/%m/%Y'),
                    'description': description,
                    'ref_no': '',
                    'amount': amount1,
                    'type': 'Expense' if type1 == 'Dr' else 'Income',
                    'category': category1,
                    'subcategory': subcategory1,
                    'account': 'Axis Credit Card'
                })

            # Second amount, if it exists
            if amount2_str:
                amount2 = float(amount2_str.replace(',', ''))
                if amount2 > 0:
                    # For cashback, the description is often related to the primary transaction
                    desc2 = "Cashback for " + description if type2 == 'Cr' else description
                    category2 = categorize_transaction(desc2)
                    subcategory2 = get_subcategory(category2, desc2)
                    transactions.append({
                        'transaction_date': datetime.strptime(date_str, '%d/%m/%Y').strftime('%d/%m/%Y'),
                        'description': desc2,
                        'ref_no': '',
                        'amount': amount2,
                        'type': 'Expense' if type2 == 'Dr' else 'Income',
                        'category': category2,
                        'subcategory': subcategory2,
                        'account': 'Axis Credit Card'
                    })
        else:
            print(f"Warning: Could not parse line: {line}")

    return transactions

def categorize_transaction(description):
    """
    Basic automatic categorization based on description keywords
    """
    description = description.lower()
    
    # Define category mapping based on keywords
    categories = {
        'Food': ['restaurant', 'food', 'swiggy', 'zomato', 'cafe', 'dine', 'food out', 'water', 'juice', 'hotel', 'milk', 'NEIGHBOURHOOD V', 'grocery', 'snack', 'breakfast', 'lunch', 'dinner', 'tea', 'coffee', 'ice cream', 'bakery', 'dhaba', 'thindi', 'tiffin', 'coconut', 'veggie','Groceries'],
        'Transportation': ['uber', 'ola', 'cab', 'taxi', 'auto', 'petrol', 'fuel', 'railways', 'irctc', 'train', 'fuels', 'rail', 'emission test', 'number plate', 'parking', 'metro', 'bus', 'bmtc', 'zoomcar', 'car rental'],
        'Culture': ['movie', 'netflix', 'prime', 'hotstar', 'subscription', 'entertainment', 'theatre', 'concert', 'show', 'cinema', 'shetty cinemas', 'badminton', 'sports', 'gaming'],
        'Household': ['bill', 'electricity', 'phone', 'mobile', 'recharge', 'dth', 'broadband', 'internet', 'wifi', 'maintenance', 'repair', 'rent', 'cleaning', 'appliance', 'furniture'],
        'Health': ['medical', 'hospital', 'doctor', 'pharmacy', 'medicine', 'health', 'clinic', 'consultation', 'test', 'optical', 'lenskart', 'specs', 'apollo'],
        'Education': ['course', 'college', 'school', 'fees', 'tuition', 'education', 'books', 'stationery', 'class', 'study'],
        'Investment': ['investment', 'mutual fund', 'stocks', 'shares', 'sip', 'trading', 'deposit', 'zerodha'],
        'Apparel': ['clothes', 'clothing', 'fashion', 'dress', 'shirt', 'pants', 'shoes', 'wardrobe', 'accessories'],
        'Beauty': ['salon', 'haircut', 'spa', 'cosmetics', 'grooming', 'beauty'],
        'Services': ['broker', 'agent', 'service', 'consultation', 'professional', 'fees'],
        'Rent': ['rent', 'house rent', 'room rent', 'deposit'],
        'Social Life': ['party', 'hangout', 'friends', 'club', 'social', 'gathering', 'treat', 'meet', 'couple meet', 'date'],
        'Shopping': ['amazon', 'flipkart', 'online shopping', 'retail', 'mart', 'store', 'bazaar'],
        'Digital': ['aws', 'cloud', 'subscription', 'digital', 'online service', 'jio', 'airtel', 'phone bill'],
        'Donation': ['donation', 'charity', 'trust', 'temple', 'religious'],
        'Interests': ['premat'],
        'Gift': ['gift', 'present', 'gifts', 'birthday', 'anniversary', 'celebration', 'rakhi', 'festival'],
        'Interests': ['int.pd', 'interest', 'int paid', 'int. paid', 'int credited', 'interest credited']
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
            ('Maid', ['maid', 'house help', 'cleaning']),
            ('Furniture', ['furniture', 'sofa', 'table', 'chair', 'bed', 'shelf', 'cabinet']),
            ('Kitchen', ['kitchen', 'utensil', 'cooker', 'mixer', 'plates', 'cups']),
            ('Phone Bill', ['phone', 'mobile', 'recharge', 'postpaid', 'prepaid']),
            ('Other Essentials', ['essential', 'grocery', 'daily', 'toiletries']),
            ('Appliances', ['appliance', 'fridge', 'ac', 'microwave', 'washing machine', 'fan', 'cooler']),
            ('Internet', ['internet', 'broadband', 'wifi', 'data', 'connection']),
            ('DTH', ['dth', 'set top', 'cable', 'television']),
            ('Mom hyd', ['mom hyd']),
            ('Ironing', ['iron', 'press', 'laundry']),
            ('Maintenance', ['maintenance', 'repair', 'fix', 'service']),
            ('Cook', ['cook', 'chef', 'cooking']),
            ('Toiletries', ['toiletries', 'soap', 'shampoo', 'toothpaste', 'personal care']),
            ('Painting', ['paint', 'painting', 'wall', 'decor']),
            ('Electricity', ['electricity', 'power', 'electric', 'current']),
            ('Packers and movers', ['packers', 'movers', 'moving', 'relocation', 'shifting']),
            ('Home Loan', ['home loan', 'loan', 'emi', 'mortgage']),
            ('Rent', ['rent', 'deposit', 'advance', 'lease'])
        ],
        'Food': [
            ('Vegis/Groceries', ['grocery', 'Groceries','vegetable', 'vegi', 'groceries', 'fruit', 'milk', 'water', 'provisions', 'mart', 'store']),
            ('Eating out', ['restaurant', 'swiggy', 'zomato', 'cafe', 'dine', 'hotel', 'food out', 'eating out', 'takeaway']),
            ('Beverages', ['beverage', 'juice', 'coffee', 'tea', 'drink', 'beverages', 'soda', 'soft drink']),
            ('Snack', ['snack', 'chips', 'namkeen', 'biscuit', 'cookie', 'bakery']),
            ('Lunch', ['lunch', 'afternoon meal', 'tiffin']),
            ('Dinner', ['dinner', 'night meal', 'supper']),
            ('Breakfast', ['breakfast', 'morning meal', 'toast']),
            ('Food Delivery', ['delivery', 'online order', 'swiggy', 'zomato']),
            ('Street Food', ['street food', 'chaat', 'roadside', 'vendor'])
        ],
        'Transportation': [
            ('Taxi', ['uber', 'ola', 'taxi', 'cab', 'ride', 'hire']),
            ('Subway/Train', ['train', 'subway', 'metro', 'rail', 'irctc', 'railway']),
            ('Bike', ['bike', 'cycle', 'bicycle', 'fuel', 'petrol', 'diesel']),
            ('Parcel/Courier', ['parcel', 'courier', 'delivery', 'shipping', 'post']),
            ('Car', ['car', 'drive', 'parking', 'toll', 'fastag']),
            ('Flight', ['flight', 'air', 'airport', 'airline', 'plane']),
            ('Bus', ['bus', 'transport', 'ST', 'roadways']),
            ('Vehicle Service', ['service', 'repair', 'maintenance', 'emission test', 'number plate']),
            ('Fine', ['fine', 'penalty', 'challan', 'ticket'])
        ],
        'Beauty': [
            ('Salon', ['salon', 'haircut', 'spa', 'massage', 'parlor', 'unisex']),
            ('Cosmetics', ['cosmetics', 'makeup', 'beauty products', 'skincare']),
            ('Personal Care', ['personal care', 'grooming', 'hygiene']),
            ('Beauty Services', ['facial', 'waxing', 'threading', 'manicure', 'pedicure']),
            ('Optical', ['lenskart', 'specs', 'glasses', 'contact lens', 'eye care'])
        ],
        'Services': [
            ('Professional', ['professional', 'consultant', 'advisor', 'expert']),
            ('Broker', ['broker', 'agent', 'dealer', 'intermediary']),
            ('Legal', ['legal', 'lawyer', 'advocate', 'notary']),
            ('Documentation', ['document', 'certificate', 'attestation']),
            ('Home Services', ['repair', 'plumber', 'electrician', 'carpenter'])
        ],
        'Investment': [
            ('Trading', ['zerodha', 'trading', 'stocks', 'shares']),
            ('Mutual Funds', ['mutual fund', 'sip', 'investment']),
            ('Fixed Deposits', ['fd', 'fixed deposit', 'deposit']),
            ('Other Investments', ['gold', 'bonds', 'crypto'])
        ],
        'Digital': [
            ('Cloud Services', ['aws', 'cloud', 'server', 'hosting']),
            ('Subscriptions', ['subscription', 'netflix', 'prime', 'hotstar']),
            ('Mobile Services', ['jio', 'airtel', 'vodafone', 'phone bill']),
            ('Apps', ['app purchase', 'playstore', 'appstore'])
        ],
        'Rent': [
            ('House Rent', ['house rent', 'home rent', 'flat rent']),
            ('Deposit', ['deposit', 'advance', 'security']),
            ('Maintenance', ['maintenance', 'society', 'association']),
            ('Utilities', ['utility', 'electricity', 'water', 'gas'])
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
    if len(sys.argv) < 4:
        print("Usage: python csv_to_realbyte.py <input_file> <output_file> <bank>")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    bank = sys.argv[3]

    print(f"Processing {input_file} for bank: {bank}")
    
    transactions = None
    # Process the statement
    if bank == 'kotak':
        transactions = parse_kotak_statement(input_file)
    elif bank == 'kvb':
        transactions = parse_kvb_statement(input_file)
    elif bank == 'axis':
        transactions = parse_axis_statement(input_file)
    elif bank == 'equitas':
        transactions = parse_equitas_statement(input_file)
    
    if transactions:
        create_realbyte_import_file(transactions, output_file)
    else:
        print("No transactions found or error in processing the statement")

if __name__ == "__main__":
    main()
