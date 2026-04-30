#!/bin/bash

# Script to create a desktop launcher for MutualCircle

set -e

# Get the project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DESKTOP_DIR="$HOME/Desktop"

echo "Creating desktop launcher for MutualCircle..."

# Create the AppleScript application
cat > "/tmp/MutualCircle.applescript" << 'APPLESCRIPT'
on run
    set projectPath to "/Volumes/External Drive/02_DEVELOPMENT/Active Projects/Vibecoding/MutualAidApp"
    
    tell application "Terminal"
        activate
        do script "cd '" & projectPath & "' && ./launch.sh"
    end tell
end run
APPLESCRIPT

# Compile the AppleScript into an application
osacompile -o "$DESKTOP_DIR/MutualCircle.app" "/tmp/MutualCircle.applescript"

# Set the icon (if we can find a suitable one)
if [ -f "$PROJECT_DIR/frontend/public/manifest.json" ]; then
    echo "Application created successfully!"
fi

echo ""
echo "✅ Desktop launcher created!"
echo "📱 Look for 'MutualCircle.app' on your Desktop"
echo ""
echo "You can now double-click it to launch the application!"

