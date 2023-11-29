#!/bin/bash

# Change this!
PORT=9000

for item in `seq 1 40`
do
    (echo '{"type": "POST", "data": {"user": "user", "content": "content '$item'"}}' | nc -w4 localhost $PORT) &
done
wait
echo "Done setting. Most of these should fail."

# get them all (any order)

echo '{"type": "GET", "data": {}}' | nc -w1 localhost $PORT

wait
echo "Done"