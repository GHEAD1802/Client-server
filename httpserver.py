import socket
import threading
import json

# In-memory data storage
tweets = []
users = set()

HOST = '127.0.0.1'
PORT = 65432
COORDINATOR_HOST = '127.0.0.1'  # Assuming the coordinator runs on the same host
COORDINATOR_PORT = 9000  # Replace with the actual port of your coordinator

def send_to_coordinator(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((COORDINATOR_HOST, COORDINATOR_PORT))
        sock.sendall(json.dumps(data).encode('utf-8'))
        response = sock.recv(1024)
    return response.decode('utf-8')

def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode('utf-8')
        
        if not request:  # check if request is empty
            client_socket.close()
            return

        header, body = request.split("\r\n\r\n") if '\r\n\r\n' in request else (request, "")

        # Check for improperly formatted requests
        lines = header.split("\r\n")
        if not lines:
            client_socket.close()
            return

        first_line = lines[0]
        parts = first_line.split()
        if len(parts) < 3:
            client_socket.close()
            return

        method, path, _ = parts

        response = 'HTTP/1.1 '

        if path == "/":
            response += '200 OK\r\nContent-Type: text/html\r\n\r\n'
            with open('file.html', 'r') as file:
                response += file.read()
        elif path.startswith("/api/"):
            if path == "/api/tweet" and method == "GET":
                response += '200 OK\r\nContent-Type: application/json\r\n\r\n'
                response += json.dumps(tweets)
            elif path == "/api/tweet" and method == "POST":
                
                tweet_data = json.loads(body)
                
                tweets.append({"id": len(tweets), "content": tweet_data['content'], "user": tweet_data['user']})
                response_data = send_to_coordinator(json.loads(body))
                response += '200 CREATED\r\n\r\n'
            elif path.startswith("/api/tweet/") and method == "PUT":
                try:
                    tweet_id = int(path.split("/")[-1])
                    response_data = send_to_coordinator({"id": tweet_id, "data": json.loads(body)})
                    tweet_data = json.loads(body)
                    found = False
                    for tweet in tweets:
                        if tweet['id'] == tweet_id:
                            tweet['content'] = tweet_data['content']
                            found = True
                            break
                    if found:
                        response += '200 OK\r\n\r\n'
                    else:
                        response += '404 NOT FOUND\r\n\r\nTweet not found'
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
            else:
                response += '404 NOT FOUND\r\n\r\n'
        else:
            response += '404 NOT FOUND\r\n\r\n'

        client_socket.send(response.encode('utf-8'))
        client_socket.close()
    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.send("HTTP/1.1 500 INTERNAL SERVER ERROR\r\n\r\n".encode('utf-8'))
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Listening on {HOST}:{PORT}")

    while True:
        client, addr = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

if __name__ == "__main__":
    main()
