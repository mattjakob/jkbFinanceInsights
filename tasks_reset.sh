#!/bin/bash
# Reset all tasks and clear the queue script

echo "🔄 Resetting all tasks and clearing the queue..."
echo "================================================"

# Check if Python script exists
if [ ! -f "tasks_reset.py" ]; then
    echo "❌ Error: tasks_reset.py not found"
    exit 1
fi

# Run the Python script
python3 tasks_reset.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Task clearing completed successfully"
else
    echo ""
    echo "❌ Task clearing failed"
    exit 1
fi
