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
import threading
import json
import argparse
#web server's db
tweets = []
users = set()
parser = argparse.ArgumentParser(description='Start the web server with a specified coordinator port.')
parser.add_argument('port', type=int, help='Coordinator port number')
args = parser.parse_args()

HOST = '0.0.0.0'
PORT = 8888
COORDINATOR_HOST = '127.0.0.1'  # Assuming the coordinator runs on the same host
COORDINATOR_PORT = args.port 

#send to coordinator function
def send_to_coordinator(data, request_type):
    #request type and data sent to the coordinator
    data_with_type = {"type": request_type, "data": data}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((COORDINATOR_HOST, COORDINATOR_PORT))
        sock.sendall(json.dumps(data_with_type).encode('utf-8'))
        response = sock.recv(1024)
    return response.decode('utf-8')

#handle client function
def handle_client(client_sock):
    try:
        request = client_sock.recv(1024).decode('utf-8')
        
        if not request:  # check if request is empty
            client_sock.close()
            return

        header, body = request.split("\r\n\r\n") if '\r\n\r\n' in request else (request, "")

        # Check for any improper requests
        lines = header.split("\r\n")
        if not lines:
            client_sock.close()
            return

        #parsing request
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) < 3:
            client_sock.close()
            return

        method, path, _ = parts

        response = 'HTTP/1.1 '
        
        #checking for path
        if path == "/":
            response += '200 OK\r\nContent-Type: text/html\r\n\r\n'
            with open('file.html', 'r') as file:
                response += file.read()
        elif path.startswith("/api/"):
            if path == "/api/tweet" and method == "GET":
                response_data = send_to_coordinator({}, "GET")
                print(f"GET's Response from Coordinator: {response_data}")

                # Parse the response and update the tweets list
                coordinator_reply = json.loads(response_data)
                if coordinator_reply.get('status') and 'data' in coordinator_reply:
                    tweets = list(coordinator_reply['data'].values())  # Update tweets

                response += '200 OK\r\nContent-Type: application/json\r\n\r\n'
                response += json.dumps(tweets)  # Send updated tweets list
            elif path == "/api/tweet" and method == "POST":
                tweet_data = json.loads(body)
                response_data = send_to_coordinator(tweet_data, "POST")
                print(f"POST's Response from Coordinator: {response_data}")
                # Fetch the latest tweets from the coordinator
                latest_tweets_fetch = send_to_coordinator({}, "GET")
                latest_tweets = json.loads(latest_tweets_fetch)
                if latest_tweets.get('status') and 'data' in latest_tweets:
                    tweets = list(latest_tweets['data'].values())
                    response += '200 OK\r\nContent-Type: application/json\r\n\r\n'
                    response += json.dumps(tweets)
                else:
                    response += '400 BAD REQUEST\r\n\r\nFailed to post tweet'
            elif path.startswith("/api/tweet/") and method == "PUT":
                try:
                    tweet_id = int(path.split("/")[-1])
                    tweet_data = json.loads(body)
                    response_data = send_to_coordinator({"id": tweet_id, "data": tweet_data}, "PUT")
                    print(f"PUT's Response from Coordinator: {response_data}")
                    # Retrieving the latest tweets from the coordinator
                    latest_tweets_response = send_to_coordinator({}, "GET")
                    latest_tweets = json.loads(latest_tweets_response)
                    if latest_tweets.get('status') and 'data' in latest_tweets:
                        tweets = list(latest_tweets['data'].values())
                        response += '200 OK\r\nContent-Type: application/json\r\n\r\n'
                        response += json.dumps(tweets)
                    else:
                        response += '400 BAD REQUEST\r\n\r\nFailed to update tweet'
                except ValueError:
                    response += '400 BAD REQUEST\r\n\r\nInvalid Tweet ID'
            elif path == "/api/login" and method == "POST":  # Added this
                login_data = json.loads(body)
                username = login_data.get('username', '')
                print(username)
                if username:  # If username is provided
                    users.add(username)  # Store the username (optional)
                    response += '200 OK\r\n'
                    response += f'Set-Cookie: username={username}; Path=/;\r\n\r\n'  # Set a cookie
                else:
                    response += '400 BAD REQUEST\r\n\r\n'
            elif path.startswith("/api/tweet/") and method == "DELETE":
                try:
                    tweet_id = int(path.split("/")[-1])
                    response_data = send_to_coordinator({"id": tweet_id}, "DELETE")
                    print(f"DELETE's Response from Coordinator: {response_data}")
                    # After deleting, you might want to fetch the latest tweets
                    response += '200 OK\r\nContent-Type: application/json\r\n\r\n'
                    response += '{"message": "Tweet deleted successfully"}'
                except ValueError:
                    response += '400 BAD REQUEST\r\n\r\nInvalid Tweet ID'
            elif path == "/api/login" and method == "DELETE":  # For logging out
                response += '200 OK\r\n'
                response += 'Set-Cookie: username=; Path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly\r\n'  # Clear the cookie
                response += 'Content-Type: text/html\r\n\r\n'
                response += '<p>You are logged out already. <a href="/">Click here</a> to login again.</p>'
            else:
                response += '404 NOT FOUND\r\n\r\n'
        else:
            response += '404 NOT FOUND\r\n\r\n'

        client_sock.send(response.encode('utf-8'))
        client_sock.close()
    except Exception as e:
        print(f"Error handling client: {e}")
        client_sock.send("HTTP/1.1 500 INTERNAL SERVER ERROR\r\n\r\n".encode('utf-8'))
        client_sock.close()

#main function
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f">>>Server Listening on {HOST}:{PORT}")

    while True:
        client, addr = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

if __name__ == "__main__":
    main()
