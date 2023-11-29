#-----------------------------------------
# NAME: Akashkumar Ghelani 
# STUDENT NUMBER: 7870902
# COURSE: COMP 3010, SECTION: A01
# INSTRUCTOR: Robert Guderian
# ASSIGNMENT: Assignment 2
#          
#-----------------------------------------
#Necessary imports
import socket
import json
import sys
import time
#setting timout
LOCK_TIMEOUT=1
#worker object
class Worker:
    #init function
    def __init__(self, port):
        self.data = {}
        self.locks = {}
        self.port = port
    #start function
    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', self.port))
            s.listen()
            print(f"Worker listening on port {self.port}")

            while True:
                conn, addr = s.accept()
                print(f"Connection accepted from {addr}")
                self.handle_connection(conn)
    #handle connection function
    def handle_connection(self, conn):
        with conn:
            try:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break  # No more data, connection closed by client
                    request = json.loads(data.decode())
                    print(f"Received request from CO-ORDINATOR: {request}")
                    response = self.process_request(request)
                    if response is not None:
                        conn.sendall(response.encode())  # Make sure response is not None before encoding
            except Exception as e:
                print(f"Error in handling connection: {e}")

    #process request function
    def process_request(self, request):

        if request.get('type') == 'GET':
            # Return the whole db for GET requests
            return json.dumps({'status': True, 'data': self.data})
    
        action = request.get('action')
        key = request.get('key')

        if action == 'lock':
            return json.dumps({'status': self.lock_with_timeout(key)})
        elif action == 'commit':
            value = request.get('value')
            return json.dumps({'status': self.commit(key, value)})
        elif request.get('type') == 'DELETE':
            tweet_id = request.get('id')
            response = self.delete_tweet(tweet_id)
            return response 
        elif request.get('type') == 'POST':
            data = request.get('data')
            if data:
                # Generating a unique key
                key = str(len(self.data))  
                # Store in db
                self.data[key] = data
                print(f"Worker's DATABASE: {self.data}")  # Print the updated database
                return json.dumps({'status': True, 'message': 'Data stored successfully'})
        else:
            return json.dumps({'status': False, 'error': 'No data provided'})
        
    #lock with timeout function is for 1st phase
    def lock_with_timeout(self, key):
        if key in self.locks and (time.time() - self.locks[key]) < LOCK_TIMEOUT:
            print("Lock fail - key already locked and timeout not expired.")
            return False
        else:
            print("Lock success - locking key.")
            self.locks[key] = time.time()  # Lock the key with the current timestamp
            return True

    #delete tweet function
    def delete_tweet(self, tweet_id):
        # Converting tweet_id to strings because dictionary keys are strings
        tweet_id_str = str(tweet_id)

        # Attempt to lock the tweet ID
        if not self.lock_with_timeout(tweet_id_str):
            return json.dumps({'status': False, 'message': 'Tweet is currently locked or does not exist'})

        # Check if the tweet exists in the database
        if tweet_id_str in self.data:
            # Delete the tweet
            del self.data[tweet_id_str]
            # Unlock the tweet ID
            self.locks.pop(tweet_id_str, None)
            print(f"Deleted tweet with ID: {tweet_id_str}")
            return json.dumps({'status': True, 'message': 'Tweet deleted successfully'})
        else:
            # Unlock the tweet ID if it was previously locked
            self.locks.pop(tweet_id_str, None)
            print(f"Delete fail - no tweet with ID: {tweet_id_str}")
            return json.dumps({'status': False, 'message': 'Tweet not found'})
        
    #commit function for 2nd phase
    def commit(self, key, value):
        print(f"Attempting to commit key: {key} with value: {value}")
        if key not in self.locks:
            print("Key not locked. Cannot commit.")
            return False

        try:
            if self.locks[key]:
                new_data = json.loads(value)
                # Update the existing structure
                if key in self.data:
                    current_data = self.data[key]
                    current_data['content'] = new_data.get('content', current_data.get('content'))
                    current_data['user'] = new_data.get('editor', current_data.get('user'))  
                else:
                    # If the key is not in it then creating a new entry with the { user , content } structure
                    self.data[key] = {'user': new_data.get('editor'), 'content': new_data.get('content')}
                
                del self.locks[key]  
                print(f"Committed key: {key}. Updated data: {self.data[key]}")
                return True
            else:
                print("Key is not locked yet.")
                return False
        except Exception as e:
            print(f"Error while commit: {e}")
            return False
        


#main function
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 worker.py [port]")
        sys.exit(1)

    port = int(sys.argv[1])
    worker = Worker(port)
    worker.start()
