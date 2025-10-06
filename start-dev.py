#!/usr/bin/env python
"""
Quick development server start script for APC Gym Log System
This script starts both Django backend and React frontend servers.
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

def run_command(command, cwd=None, name="Process"):
    """Run a command in a separate thread"""
    try:
        print(f"🚀 Starting {name}...")
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                print(f"[{name}] {line.strip()}")
        
        process.stdout.close()
        return_code = process.wait()
        
        if return_code != 0:
            print(f"❌ {name} exited with code {return_code}")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping {name}...")
        process.terminate()
    except Exception as e:
        print(f"❌ Error running {name}: {str(e)}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies
    try:
        import django
        print("✅ Django is installed")
    except ImportError:
        print("❌ Django not found. Run: pip install -r requirements.txt")
        return False
    
    # Check if node_modules exists
    if not Path("node_modules").exists():
        print("❌ Node modules not found. Run: npm install")
        return False
    else:
        print("✅ Node modules are installed")
    
    return True

def run_migrations():
    """Run Django migrations"""
    print("🔄 Running Django migrations...")
    try:
        result = subprocess.run(
            ["python", "manage.py", "migrate"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e.stderr}")
        return False

def main():
    """Main function to start development servers"""
    print("🏃‍♂️ APC Gym Log System - Development Server Starter")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("\n❌ Database migration failed. Please check your setup.")
        sys.exit(1)
    
    print("\n🚀 Starting development servers...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📍 Frontend will be available at: http://localhost:5173")
    print("📍 Press Ctrl+C to stop both servers")
    print("-" * 60)
    
    try:
        # Start Django backend in a thread
        backend_thread = threading.Thread(
            target=run_command,
            args=("python manage.py runserver", None, "Django Backend"),
            daemon=True
        )
        backend_thread.start()
        
        # Give backend time to start
        time.sleep(3)
        
        # Start React frontend in a thread
        frontend_thread = threading.Thread(
            target=run_command,
            args=("npm run dev", None, "React Frontend"),
            daemon=True
        )
        frontend_thread.start()
        
        # Keep main thread alive
        print("\n✅ Both servers are starting...")
        print("💡 Tip: Open http://localhost:5173 in your browser")
        print("💡 Admin panel: http://localhost:8000/admin")
        print("\n🔄 Server logs will appear below:")
        print("-" * 60)
        
        # Wait for threads to complete (they won't unless there's an error)
        backend_thread.join()
        frontend_thread.join()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
        print("👋 Thanks for using APC Gym Log System!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
