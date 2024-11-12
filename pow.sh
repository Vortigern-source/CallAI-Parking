#!/bin/bash

for utils in argon2 xxd bc; do
    if ! command -v $utils  &> /dev/null; then
        echo "$utils is not installed. Please install it and try again." 
        exit 1
    fi
done
 	
if [ $# -lt 1 ]; then
    read -p "Enter Challenge Code: " challenge
else
    challenge=$1
fi 

challenge=$(echo "$challenge" | xargs)

IFS=':' read -r _ memory_cost time_cost salt difficulty <<< "$challenge" 

memory_cost=$(echo "$memory_cost" | xargs)
time_cost=$(echo "$time_cost" | xargs)
difficulty=$(echo "$difficulty" | xargs)

pw_prefix="UNBLOCK-$(head /dev/urandom | tr -dc A-Z0-9 | head -c 8)-"
difficulty_raw=$(echo "scale=10; e(l(256) * (4 - l($difficulty) / l(256))) / 1" | bc -l | xargs printf %.0f)	

echo "Estimated iterations: $difficulty"
echo "Time Cost: $time_cost"
echo
 
n=1

start_time=$(date +%s)

elapsed_time() {
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    echo -ne "\rElapsed Time: $elapsed_time seconds."
}

while true; do
    pw="$pw_prefix$n"
    hash=$(echo -n "$pw" | argon2 "$salt" -t "$time_cost" -k "$memory_cost" -p 1  -id -v 13 -r)
    hash_bytes=${hash:0:8}
 
    if [ $((16#$hash_bytes)) -lt "$difficulty_raw" ]; then
        echo
        echo "SOLUTION FOUND"
        echo "Your unblock code is: $pw"
        echo "This is the code you enter into the site to pass the challenge."
        echo
        break
    else
        elapsed_time
        n=$((n + 1)) 
    fi
done

