from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['user_auth_db']
users_collection = db['users']

# Create a test user
test_user = {
    'name': 'Test User',
    'email': 'test@example.com',
    'password': 'testpassword123'
}

# Insert the test user
try:
    result = users_collection.insert_one(test_user)
    print(f"Test user created with id: {result.inserted_id}")
except Exception as e:
    print(f"Error: {str(e)}")

# Show all users
print("\nAll users in database:")
for user in users_collection.find():
    print(user)
