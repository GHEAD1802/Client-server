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
import threading
import select
import random
#Cordinator object
class Coordinator:
    #init function
    def __init__(self, port, worker_address_strings):
       
        self.host = 'localhost'
        self.port = port
        self.worker_addresses = [self.parse_addr(addr_str) for addr_str in worker_address_strings]
    #parse address function
    def parse_addr(self, address_string):
        host, port = address_string.split(':')
        return host, int(port)

    #start function
    def start(self):
        # Try to connect to all workers before starting
        all_connected = True
        for worker_addr in self.worker_addresses:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(worker_addr)
                print(f"Successfully connected to worker at {worker_addr}")
            except Exception as e:
                print(f"Error connecting to worker at {worker_addr}: {e}")
                all_connected = False
                break  # Stop trying to connect to other workers if one fails

        # Only proceed if all workers are connected
        if not all_connected:
            print("Failed to connect to all workers. Coordinator is shutting down.")
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Coordinator listening on {self.host}:{self.port}")

            while True:
                conn, _ = s.accept()
                threading.Thread(target=self.handle_connection, args=(conn,)).start()
    
    #handle connection function
    def handle_connection(self, conn):
        try:
            while True:
                data = b''
                while True:
                    part = conn.recv(1024)
                    data += part
                    if len(part) < 1024:
                        # No more data or end of data pattern found.
                        break
                if not data:
                    break

                raw_req = data.decode('utf-8')
                print("Request received from WEB-SERVER:", raw_req)
                request = json.loads(raw_req)
                response = self.process_request(request)
                conn.sendall(json.dumps(response).encode('utf-8'))

        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()

    #Process request function 
    def process_request(self, request):
        if request.get('type') == 'GET':
            # Handling GET requests which randomely select worker and balance load 
            return self.handle_get_request()
        elif request.get('type') == 'POST':
            # Directly add data to all workers without using 2PC
            return self.post_to_workers(request)
        elif request.get('type') == 'PUT':
            # 2PC to updating data to both worker's db
            return self.two_phase_commit(request)
        elif request.get('type') == 'DELETE' and 'id' in request.get('data', {}):
            tweet_id = request['data']['id']
            #delete data to both worker's db
            return self.delete_tweet(tweet_id)
        else:
            return {'status': 'error', 'message': 'Unsupported request type'}
        
    #Send request to worker function
    def send_request_to_worker(self, worker_address, request):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as worker_socket:
            try:
                worker_socket.connect(worker_address)
                worker_socket.sendall(json.dumps(request).encode('utf-8') + b'\n')  # Notice the newline character here
                response_data = b""
                while True:
                    part = worker_socket.recv(1024)
                    response_data += part
                    if len(part) < 1024:
                        break
                return json.loads(response_data.decode()) if response_data else {'status': False, 'message': 'No response'}
            except Exception as e:
                print(f"Error sending request to worker: {e}")
                return {'status': False, 'message': str(e)}
        
    #handle get request function
    def handle_get_request(self):
        # Randomly select a worker address
        worker_address = random.choice(self.worker_addresses)
        return self.send_request_to_worker(worker_address, {'type': 'GET'})
    
    #delete tweet function
    def delete_tweet(self, tweet_id):
        responses = []
        for worker_address in self.worker_addresses:
            response = self.send_request_to_worker(worker_address, {'type': 'DELETE', 'id': tweet_id})
            responses.append(response)

        # Check if all worker's response is successfully done or not
        if all(response.get('status') for response in responses):
            return {'status': 'ok', 'message': 'Tweet deleted successfully'}
        else:
            return {'status': 'error', 'message': 'Failed to delete tweet on one or more workers'}
    
    #post worker function
    def post_to_workers(self, request):
        # Send the request to all workers
        responses = []
        for worker_address in self.worker_addresses:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as worker_socket:
                try:
                    worker_socket.connect(worker_address)
                    worker_socket.sendall(json.dumps(request).encode('utf-8'))
                    response = worker_socket.recv(1024).decode('utf-8')
                    responses.append(json.loads(response))
                except Exception as e:
                    print(f"Error sending request to worker at {worker_address}: {e}")
                    responses.append({'status': False, 'message': str(e)})

        # Check if all workers responded with success
        all_success = all(res.get('status') for res in responses)
        if all_success:
            return {'status': 'ok', 'message': 'Data stored successfully on all workers'}
        else:
            return {'status': 'error', 'message': 'Data storage failed on one or more workers'}


    #two phase commit function
    def two_phase_commit(self, request):
        transaction_value = request.get('data', {})
        key = str(transaction_value.get('id'))
        value = json.dumps(transaction_value.get('data'))

        if not self.lock_phase(key):
            return {'status': 'error', 'message': 'Prepare phase failed, transaction cannot proceed'}
        if not self.update_phase(key, value):
            return {'status': 'error', 'message': 'Commit phase failed'}
        
        return {'status': 'ok', 'message': 'Transaction committed'}

    #lock phase function
    def lock_phase(self, key):
        lock_message = json.dumps({'action': 'lock', 'key': key})
        all_prepared = True
        for worker_address in self.worker_addresses:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(worker_address)
                    sock.sendall(lock_message.encode('utf-8'))
                    worker_reply = json.loads(sock.recv(1024).decode('utf-8'))
                    if not worker_reply.get('status'):
                        all_prepared = False
                        break
            except Exception as e:
                print(f"Error during lock request to worker: {e}")
                all_prepared = False
                break

        return all_prepared
    
    #update phase function
    def update_phase(self, key, value):
        commit_message = json.dumps({'action': 'commit', 'key': key, 'value': value})
        check_all_updated = True
        for worker_address in self.worker_addresses:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(worker_address)
                    sock.sendall(commit_message.encode('utf-8'))
                    worker_reply = json.loads(sock.recv(1024).decode('utf-8'))
                    if not worker_reply.get('status'):
                        check_all_updated = False
                        break
            except Exception as e:
                print(f"Error during commit request to worker: {e}")
                check_all_updated = False
                break

        return check_all_updated

        

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 coordinator.py [myport] [WorkerHost1:WorkerPort1] [WorkerHost2:WorkerPort2] ...")
        sys.exit(1)

    my_port = int(sys.argv[1])
    worker_addresses = sys.argv[2:]
    coordinator = Coordinator(my_port, worker_addresses)
    coordinator.start()
