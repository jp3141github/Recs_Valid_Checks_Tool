"""
Synthetic Data Generator for Reconciliation and Validation Tool

This script generates comprehensive synthetic datasets to test the reconciliation
and validation tool. It creates realistic financial transaction data with
intentional discrepancies to demonstrate the tool's capabilities.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_RECORDS = 500
DISCREPANCY_RATE = 0.08  # 8% of records will have discrepancies
MISSING_RATE = 0.03  # 3% of records will be missing in one source

def generate_transaction_id(prefix, num):
    """Generate a unique transaction ID."""
    return f"{prefix}-{str(num).zfill(8)}"

def generate_random_date(start_date, end_date):
    """Generate a random date between start and end dates."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def generate_customer_name():
    """Generate a random customer name."""
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", 
                   "Michael", "Linda", "William", "Elizabeth", "David", "Barbara",
                   "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
                   "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
                  "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
                  "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_account_number():
    """Generate a random account number."""
    return ''.join(random.choices(string.digits, k=10))

def generate_source1_data(num_records):
    """
    Generate primary source data (e.g., internal transaction system).
    """
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)
    
    categories = ["Sales", "Refund", "Transfer", "Fee", "Interest", "Adjustment"]
    statuses = ["Completed", "Pending", "Cancelled", "Processing"]
    regions = ["North", "South", "East", "West", "Central"]
    currencies = ["USD", "EUR", "GBP", "JPY", "CAD"]
    
    data = []
    for i in range(1, num_records + 1):
        trans_id = generate_transaction_id("TXN", i)
        trans_date = generate_random_date(start_date, end_date)
        amount = round(random.uniform(10, 50000), 2)
        category = random.choice(categories)
        status = random.choices(statuses, weights=[0.7, 0.15, 0.1, 0.05])[0]
        customer = generate_customer_name()
        account = generate_account_number()
        region = random.choice(regions)
        currency = random.choices(currencies, weights=[0.5, 0.2, 0.15, 0.1, 0.05])[0]
        quantity = random.randint(1, 100) if category == "Sales" else 1
        unit_price = round(amount / quantity, 2)
        
        data.append({
            "transaction_id": trans_id,
            "transaction_date": trans_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "category": category,
            "status": status,
            "customer_name": customer,
            "account_number": account,
            "region": region,
            "currency": currency,
            "quantity": quantity,
            "unit_price": unit_price,
            "created_at": trans_date.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (trans_date + timedelta(hours=random.randint(0, 48))).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return pd.DataFrame(data)

def generate_source2_data(source1_df, discrepancy_rate, missing_rate):
    """
    Generate secondary source data (e.g., external bank records) with intentional
    discrepancies for testing reconciliation.
    """
    # Start with a copy of source1 data
    source2_data = []
    
    num_records = len(source1_df)
    num_discrepancies = int(num_records * discrepancy_rate)
    num_missing = int(num_records * missing_rate)
    
    # Randomly select indices for discrepancies and missing records
    all_indices = list(range(num_records))
    discrepancy_indices = set(random.sample(all_indices, num_discrepancies))
    remaining_indices = [i for i in all_indices if i not in discrepancy_indices]
    missing_indices = set(random.sample(remaining_indices, num_missing))
    
    discrepancy_types = []
    
    for idx, row in source1_df.iterrows():
        if idx in missing_indices:
            # Skip this record to simulate missing data
            discrepancy_types.append({
                "transaction_id": row["transaction_id"],
                "discrepancy_type": "missing_in_source2",
                "source1_value": "Record exists",
                "source2_value": "Record missing"
            })
            continue
        
        record = {
            "ref_id": row["transaction_id"],  # Different column name
            "posting_date": row["transaction_date"],
            "transaction_amount": row["amount"],
            "trans_type": row["category"],
            "trans_status": row["status"],
            "client_name": row["customer_name"],
            "client_account": row["account_number"],
            "branch_region": row["region"],
            "currency_code": row["currency"],
            "units": row["quantity"],
            "price_per_unit": row["unit_price"]
        }
        
        if idx in discrepancy_indices:
            # Introduce a discrepancy
            discrepancy_type = random.choice([
                "amount_mismatch",
                "date_mismatch", 
                "status_mismatch",
                "name_typo",
                "quantity_mismatch"
            ])
            
            if discrepancy_type == "amount_mismatch":
                original = record["transaction_amount"]
                # Small percentage difference
                record["transaction_amount"] = round(original * random.uniform(0.95, 1.05), 2)
                discrepancy_types.append({
                    "transaction_id": row["transaction_id"],
                    "discrepancy_type": "amount_mismatch",
                    "source1_value": original,
                    "source2_value": record["transaction_amount"]
                })
            
            elif discrepancy_type == "date_mismatch":
                original = record["posting_date"]
                # Off by 1-3 days
                new_date = datetime.strptime(original, "%Y-%m-%d") + timedelta(days=random.choice([-3, -2, -1, 1, 2, 3]))
                record["posting_date"] = new_date.strftime("%Y-%m-%d")
                discrepancy_types.append({
                    "transaction_id": row["transaction_id"],
                    "discrepancy_type": "date_mismatch",
                    "source1_value": original,
                    "source2_value": record["posting_date"]
                })
            
            elif discrepancy_type == "status_mismatch":
                original = record["trans_status"]
                statuses = ["Completed", "Pending", "Cancelled", "Processing"]
                statuses.remove(original)
                record["trans_status"] = random.choice(statuses)
                discrepancy_types.append({
                    "transaction_id": row["transaction_id"],
                    "discrepancy_type": "status_mismatch",
                    "source1_value": original,
                    "source2_value": record["trans_status"]
                })
            
            elif discrepancy_type == "name_typo":
                original = record["client_name"]
                # Introduce a typo
                name_list = list(original)
                if len(name_list) > 3:
                    pos = random.randint(1, len(name_list) - 2)
                    name_list[pos] = random.choice(string.ascii_lowercase)
                record["client_name"] = ''.join(name_list)
                discrepancy_types.append({
                    "transaction_id": row["transaction_id"],
                    "discrepancy_type": "name_typo",
                    "source1_value": original,
                    "source2_value": record["client_name"]
                })
            
            elif discrepancy_type == "quantity_mismatch":
                original = record["units"]
                record["units"] = original + random.choice([-2, -1, 1, 2])
                if record["units"] < 1:
                    record["units"] = 1
                discrepancy_types.append({
                    "transaction_id": row["transaction_id"],
                    "discrepancy_type": "quantity_mismatch",
                    "source1_value": original,
                    "source2_value": record["units"]
                })
        
        source2_data.append(record)
    
    # Add some records that exist only in source2 (orphan records)
    num_orphans = int(num_records * 0.02)  # 2% orphan records
    for i in range(num_orphans):
        orphan_id = generate_transaction_id("EXT", 9000 + i)
        trans_date = generate_random_date(datetime(2025, 1, 1), datetime(2025, 12, 31))
        source2_data.append({
            "ref_id": orphan_id,
            "posting_date": trans_date.strftime("%Y-%m-%d"),
            "transaction_amount": round(random.uniform(100, 10000), 2),
            "trans_type": random.choice(["Sales", "Refund", "Transfer"]),
            "trans_status": "Completed",
            "client_name": generate_customer_name(),
            "client_account": generate_account_number(),
            "branch_region": random.choice(["North", "South", "East", "West"]),
            "currency_code": "USD",
            "units": random.randint(1, 10),
            "price_per_unit": round(random.uniform(10, 1000), 2)
        })
        discrepancy_types.append({
            "transaction_id": orphan_id,
            "discrepancy_type": "missing_in_source1",
            "source1_value": "Record missing",
            "source2_value": "Record exists"
        })
    
    return pd.DataFrame(source2_data), pd.DataFrame(discrepancy_types)

def generate_reference_data():
    """
    Generate reference/lookup data for validation checks.
    """
    # Valid categories
    categories = pd.DataFrame({
        "category_code": ["Sales", "Refund", "Transfer", "Fee", "Interest", "Adjustment"],
        "category_description": [
            "Product or service sales",
            "Customer refunds",
            "Internal transfers",
            "Service fees",
            "Interest payments",
            "Manual adjustments"
        ],
        "is_active": [True, True, True, True, True, True]
    })
    
    # Valid regions
    regions = pd.DataFrame({
        "region_code": ["North", "South", "East", "West", "Central"],
        "region_name": ["Northern Region", "Southern Region", "Eastern Region", "Western Region", "Central Region"],
        "manager": ["Alice Brown", "Bob Wilson", "Carol Davis", "Dan Miller", "Eve Johnson"]
    })
    
    # Currency exchange rates
    currencies = pd.DataFrame({
        "currency_code": ["USD", "EUR", "GBP", "JPY", "CAD"],
        "currency_name": ["US Dollar", "Euro", "British Pound", "Japanese Yen", "Canadian Dollar"],
        "exchange_rate_to_usd": [1.0, 1.08, 1.27, 0.0067, 0.74]
    })
    
    # Account master data
    accounts = []
    for i in range(100):
        accounts.append({
            "account_number": generate_account_number(),
            "account_holder": generate_customer_name(),
            "account_type": random.choice(["Checking", "Savings", "Business", "Investment"]),
            "credit_limit": random.choice([5000, 10000, 25000, 50000, 100000]),
            "is_active": random.choices([True, False], weights=[0.95, 0.05])[0]
        })
    accounts_df = pd.DataFrame(accounts)
    
    return categories, regions, currencies, accounts_df

def generate_validation_test_data():
    """
    Generate data specifically designed to test various validation rules.
    """
    data = []
    
    # Valid records
    for i in range(50):
        data.append({
            "record_id": f"VAL-{str(i+1).zfill(5)}",
            "amount": round(random.uniform(100, 10000), 2),
            "percentage": round(random.uniform(0, 100), 2),
            "email": f"user{i+1}@example.com",
            "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "date_field": generate_random_date(datetime(2025, 1, 1), datetime(2025, 12, 31)).strftime("%Y-%m-%d"),
            "category": random.choice(["Sales", "Refund", "Transfer"]),
            "status": "Active",
            "score": random.randint(0, 100)
        })
    
    # Records with validation issues
    validation_issues = [
        {"record_id": "VAL-ERR01", "amount": -500, "percentage": 50, "email": "valid@test.com", 
         "phone": "+1-555-123-4567", "date_field": "2025-06-15", "category": "Sales", "status": "Active", "score": 75},
        {"record_id": "VAL-ERR02", "amount": 1000, "percentage": 150, "email": "valid@test.com",
         "phone": "+1-555-123-4567", "date_field": "2025-06-15", "category": "Sales", "status": "Active", "score": 75},
        {"record_id": "VAL-ERR03", "amount": 1000, "percentage": 50, "email": "invalid-email",
         "phone": "+1-555-123-4567", "date_field": "2025-06-15", "category": "Sales", "status": "Active", "score": 75},
        {"record_id": "VAL-ERR04", "amount": 1000, "percentage": 50, "email": "valid@test.com",
         "phone": "invalid-phone", "date_field": "2025-06-15", "category": "Sales", "status": "Active", "score": 75},
        {"record_id": "VAL-ERR05", "amount": 1000, "percentage": 50, "email": "valid@test.com",
         "phone": "+1-555-123-4567", "date_field": "invalid-date", "category": "Sales", "status": "Active", "score": 75},
        {"record_id": "VAL-ERR06", "amount": 1000, "percentage": 50, "email": "valid@test.com",
         "phone": "+1-555-123-4567", "date_field": "2025-06-15", "category": "InvalidCategory", "status": "Active", "score": 75},
        {"record_id": "VAL-ERR07", "amount": None, "percentage": 50, "email": "valid@test.com",
         "phone": "+1-555-123-4567", "date_field": "2025-06-15", "category": "Sales", "status": "Active", "score": 75},
        {"record_id": "VAL-ERR08", "amount": 1000, "percentage": 50, "email": "",
         "phone": "+1-555-123-4567", "date_field": "2025-06-15", "category": "Sales", "status": "Active", "score": 75},
        {"record_id": "VAL-ERR09", "amount": 1000, "percentage": 50, "email": "valid@test.com",
         "phone": "+1-555-123-4567", "date_field": "2025-06-15", "category": "Sales", "status": "InvalidStatus", "score": 75},
        {"record_id": "VAL-ERR10", "amount": 1000, "percentage": 50, "email": "valid@test.com",
         "phone": "+1-555-123-4567", "date_field": "2025-06-15", "category": "Sales", "status": "Active", "score": 150},
    ]
    
    data.extend(validation_issues)
    
    return pd.DataFrame(data)

def main():
    """Main function to generate all synthetic data."""
    print("Generating synthetic data for reconciliation and validation tool...")
    
    # Generate primary source data
    print("  Creating Source 1 (Internal System) data...")
    source1_df = generate_source1_data(NUM_RECORDS)
    source1_df.to_csv("/home/ubuntu/recon_tool/data/source1_transactions.csv", index=False)
    print(f"    Generated {len(source1_df)} records")
    
    # Generate secondary source data with discrepancies
    print("  Creating Source 2 (External Bank) data with discrepancies...")
    source2_df, discrepancies_df = generate_source2_data(source1_df, DISCREPANCY_RATE, MISSING_RATE)
    source2_df.to_csv("/home/ubuntu/recon_tool/data/source2_bank_records.csv", index=False)
    discrepancies_df.to_csv("/home/ubuntu/recon_tool/data/expected_discrepancies.csv", index=False)
    print(f"    Generated {len(source2_df)} records with {len(discrepancies_df)} expected discrepancies")
    
    # Generate reference data
    print("  Creating reference/lookup data...")
    categories, regions, currencies, accounts = generate_reference_data()
    categories.to_csv("/home/ubuntu/recon_tool/data/ref_categories.csv", index=False)
    regions.to_csv("/home/ubuntu/recon_tool/data/ref_regions.csv", index=False)
    currencies.to_csv("/home/ubuntu/recon_tool/data/ref_currencies.csv", index=False)
    accounts.to_csv("/home/ubuntu/recon_tool/data/ref_accounts.csv", index=False)
    print("    Generated reference tables: categories, regions, currencies, accounts")
    
    # Generate validation test data
    print("  Creating validation test data...")
    validation_df = generate_validation_test_data()
    validation_df.to_csv("/home/ubuntu/recon_tool/data/validation_test_data.csv", index=False)
    print(f"    Generated {len(validation_df)} records for validation testing")
    
    # Summary
    print("\n" + "="*60)
    print("SYNTHETIC DATA GENERATION COMPLETE")
    print("="*60)
    print(f"\nFiles created in /home/ubuntu/recon_tool/data/:")
    print(f"  - source1_transactions.csv     ({len(source1_df)} records)")
    print(f"  - source2_bank_records.csv     ({len(source2_df)} records)")
    print(f"  - expected_discrepancies.csv   ({len(discrepancies_df)} discrepancies)")
    print(f"  - ref_categories.csv           ({len(categories)} categories)")
    print(f"  - ref_regions.csv              ({len(regions)} regions)")
    print(f"  - ref_currencies.csv           ({len(currencies)} currencies)")
    print(f"  - ref_accounts.csv             ({len(accounts)} accounts)")
    print(f"  - validation_test_data.csv     ({len(validation_df)} records)")
    
    print("\nDiscrepancy Summary:")
    print(discrepancies_df['discrepancy_type'].value_counts().to_string())

if __name__ == "__main__":
    main()
