#!/usr/bin/env python3
"""
🚀 Simple Setup Script - APC Gym Log System
Minimal setup script for quick deployment on a new computer.

Usage: python simple-setup.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {description} - Failed")
        return False

def main():
    """Main setup function"""
    print("🚀 APC Gym Log System - Simple Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Error: manage.py not found!")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    print("📋 Starting automated setup...\n")
    
    # Setup steps
    steps_passed = 0
    total_steps = 4
    
    # Step 1: Install Python dependencies
    if run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        steps_passed += 1
    
    # Step 2: Install Node.js dependencies
    if run_command("npm install", "Installing Node.js dependencies"):
        steps_passed += 1
    
    # Step 3: Run database migrations
    if run_command("python manage.py migrate", "Setting up database"):
        steps_passed += 1
    
    # Step 4: Verify Django setup
    if run_command("python manage.py check", "Verifying Django configuration"):
        steps_passed += 1
    
    # Results
    print("\n" + "=" * 50)
    print(f"📊 Setup Results: {steps_passed}/{total_steps} steps completed")
    
    if steps_passed == total_steps:
        print("🎉 Setup completed successfully!")
        print("\n🚀 Ready to start:")
        print("   python start-dev.py")
        print("\n📍 Then open: http://localhost:5173")
    else:
        print("⚠️  Setup completed with issues.")
        print("You may need to run the failed commands manually.")
        print("See SETUP.md for detailed instructions.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Setup interrupted.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Try manual setup using SETUP.md")
