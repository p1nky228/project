#!/bin/sh
set -e

# Start the bot in polling mode in the background
python -m app.bot.runner --polling &
BOT_PID=$!

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8080 &
UVCORN_PID=$!

# Wait for either process to exit
wait -n

# If we get here, one of the processes has exited
echo "One of the processes has exited, shutting down..."
kill $BOT_PID $UVCORN_PID 2>/dev/null || true
wait $BOT_PID $UVCORN_PID 2>/dev/null || true
exit 0
