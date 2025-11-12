-- MutualCircle Launch Script for macOS
-- This creates a double-clickable application launcher

on run
    set scriptPath to POSIX path of (path to me as string)
    set projectPath to text 1 thru -19 of scriptPath -- Remove "launch.applescript"
    
    tell application "Terminal"
        activate
        do script "cd '" & projectPath & "' && ./launch.sh"
    end tell
end run

