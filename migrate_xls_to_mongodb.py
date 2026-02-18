import pandas as pd
from pymongo import MongoClient
import csv
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['user_auth_db']

def read_assessment_data():
    # Read the file as CSV with semicolon separator
    try:
        with open('dyslexia/Dyt-desktop.xls', 'r') as file:
            # Read the first line to get headers
            headers = next(csv.reader([file.readline()], delimiter=';'))
            
            # Read the rest of the file
            reader = csv.DictReader(file, fieldnames=headers, delimiter=';')
            records = []
            
            for row in reader:
                # Convert string numbers to float or int where possible
                cleaned_row = {}
                for key, value in row.items():
                    try:
                        if '.' in value:
                            cleaned_row[key] = float(value)
                        else:
                            cleaned_row[key] = int(value)
                    except (ValueError, TypeError):
                        cleaned_row[key] = value
                records.append(cleaned_row)
            
            return records
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None

def migrate_xls():
    # Create or get the collection
    xls_collection = db['assessment_data']
    
    # Drop existing collection to avoid duplicates
    xls_collection.drop()

    try:
        # Get the records from the CSV
        records = read_assessment_data()
        
        if records:
            # Insert the records
            result = xls_collection.insert_many(records)
            print(f"Successfully migrated {len(result.inserted_ids)} records to MongoDB")
        else:
            print("No records found to migrate")
    except Exception as e:
        print(f"Error inserting records: {str(e)}")

if __name__ == "__main__":
    print("Starting XLS migration...")
    migrate_xls()
    
    # Print summary
    print("\nDatabase Summary:")
    print(f"XLS data collection count: {db.xls_data.count_documents({})}")
