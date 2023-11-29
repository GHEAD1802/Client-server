#!/bin/bash

# Change this to your coordinator's port
PORT=$1

# Simulate POST requests
for item in `seq 1 30`
do
    (echo '{"type": "POST", "data": {"user": "user'${item}'", "content": "content '${item}'"}}' | nc -w4 localhost $PORT) &
done
wait
echo "Done with POST requests. Should have taken less than four seconds."

# Simulate PUT requests to update
for item in `seq 1 30`
do
    (echo '{"type": "PUT", "data": {"id": '${item}', "data": {"content": "updated content '${item}'"}}}' | nc -w4 localhost $PORT) &
done
wait
echo "Done with PUT requests. Should have taken less than four seconds."

# Simulate a GET request to fetch all data
echo '{"type": "GET", "data": {}}' | nc -w4 localhost $PORT

wait
echo "Done with GET request."
