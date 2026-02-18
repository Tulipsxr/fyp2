import csv
from pymongo import MongoClient
import os

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['user_auth_db']  # Your main database

def migrate_users():
    users_collection = db['users']
    
    # Read users.csv and insert into MongoDB
    with open('users.csv', 'r') as file:
        csv_reader = csv.DictReader(file)
        users = list(csv_reader)
        
        if users:  # Only insert if there are users
            try:
                users_collection.insert_many(users)
                print(f"Successfully migrated {len(users)} users to MongoDB")
            except Exception as e:
                print(f"Error migrating users: {str(e)}")

def migrate_assessment_data():
    assessment_collection = db['assessments']
    
    # Read Dyt-desktop.csv and insert into MongoDB
    with open('Dyt-desktop.csv', 'r') as file:
        # The CSV appears to be semicolon-separated
        csv_reader = csv.reader(file, delimiter=';')
        
        # Get headers (first row)
        headers = next(csv_reader)
        
        # Convert data to list of dictionaries
        assessments = []
        for row in csv_reader:
            assessment = {}
            for i, value in enumerate(row):
                # Convert string numbers to float where possible
                try:
                    if '.' in value:
                        assessment[headers[i]] = float(value)
                    else:
                        assessment[headers[i]] = int(value)
                except ValueError:
                    assessment[headers[i]] = value
            assessments.append(assessment)
        
        if assessments:  # Only insert if there is data
            try:
                assessment_collection.insert_many(assessments)
                print(f"Successfully migrated {len(assessments)} assessment records to MongoDB")
            except Exception as e:
                print(f"Error migrating assessments: {str(e)}")

if __name__ == "__main__":
    # Drop existing collections to avoid duplicates
    db.users.drop()
    db.assessments.drop()
    
    print("Starting migration...")
    migrate_users()
    migrate_assessment_data()
    print("Migration completed!")
    
    # Print summary
    print("\nDatabase Summary:")
    print(f"Users collection count: {db.users.count_documents({})}")
    print(f"Assessments collection count: {db.assessments.count_documents({})}")
