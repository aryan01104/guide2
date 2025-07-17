#!/bin/bash


# Start Python poller in background
python ./backend/poller.py &

# Start JS app in foreground
node ./backend/main.js # this starts all else apart from polling, that is sessionizing, and more.

echo "Script completed successfully"
