import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import traceback
from pymongo import MongoClient

# Configure error logging
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

# MongoDB setup
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['user_auth_db']
    users_collection = db['users']
    # Create a unique index on email
    users_collection.create_index('email', unique=True)
    logging.info('Connected to MongoDB successfully')
except Exception as e:
    logging.error(f'Error connecting to MongoDB: {str(e)}')
    raise

class AuthHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            logging.info(f'Received {self.path} request with data: {data}')
            
            response_data = {}
            if self.path == '/signup':
                # handle_signup returns True/False directly
                signup_success = self.handle_signup(data)
                response_data = {'success': signup_success}
            elif self.path == '/login':
                # handle_login returns a dictionary {'success': True/False, 'name': 'userName' (optional)}
                response_data = self.handle_login(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Ensure response_data is a dictionary before dumping to JSON
            if not isinstance(response_data, dict):
                # Fallback if response_data is not as expected (e.g. boolean from signup)
                # This case should ideally be handled by ensuring handle_signup also returns a dict
                # For now, we'll assume it's a boolean and wrap it.
                # However, handle_signup returns a boolean, so we need to structure it properly.
                if self.path == '/signup': # Re-check path to structure signup response
                    response_data = {'success': response_data} 
                else: # Default error for unexpected type
                    response_data = {'success': False, 'error': 'Invalid server response_data structure'}

            json_response = json.dumps(response_data)
            self.wfile.write(json_response.encode())
            logging.info(f'Sent response: {json_response}')
            
        except Exception as e:
            logging.error(f'Error in do_POST: {str(e)}\n{traceback.format_exc()}')
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_signup(self, data):
        try:
            # Validate required fields
            if not all(key in data for key in ['name', 'email', 'password']):
                logging.error('Missing required fields in signup data')
                return False

            # Try to insert new user
            try:
                users_collection.insert_one({
                    'name': data['name'],
                    'email': data['email'],
                    'password': data['password']  # In production, you should hash this
                })
                logging.info(f'Added new user: {data["email"]}')
                return True
            except Exception as e:
                if 'duplicate key error' in str(e):
                    logging.info(f'Email already exists: {data["email"]}')
                    return False
                raise

        except Exception as e:
            logging.error(f'Error in handle_signup: {str(e)}\n{traceback.format_exc()}')
            raise

    def handle_login(self, data):
        try:
            user = users_collection.find_one({
                'email': data['email'],
                'password': data['password']  # In production, you should compare hashed passwords
            })
            
            if user:
                logging.info(f'Successful login for: {data["email"]}')
                return {'success': True, 'name': user.get('name')}
            
            logging.info(f'Failed login attempt for: {data["email"]}')
            return {'success': False}

        except Exception as e:
            logging.error(f'Error in handle_login: {str(e)}\n{traceback.format_exc()}')
            # To ensure a consistent return type in case of an unexpected error during DB interaction
            return {'success': False, 'error': 'Database error during login'}
            # Not raising here to allow the server to send a 500 error if needed, 
            # but the calling function (do_POST) will handle the error response.

class CORSHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.info('Server initialized')

if __name__ == '__main__':
    try:
        server = CORSHTTPServer(('localhost', 8000), AuthHandler)
        logging.info('Server starting on port 8000...')
        server.serve_forever()
    except Exception as e:
        logging.error(f'Server failed to start: {str(e)}\n{traceback.format_exc()}')
        raise
