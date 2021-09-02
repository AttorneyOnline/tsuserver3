#!/bin/sh
while [ true ]
do
	echo "Starting up server..."
	python3.8 start_server.py
	echo "Server has shut down. Will restart in 2 seconds (use CTRL-C to cancel)"
	sleep 2
done

