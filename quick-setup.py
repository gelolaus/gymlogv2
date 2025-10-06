#!/usr/bin/env python3
"""
🚀 Quick Setup Script - APC Gym Log System
This script automatically sets up the project on a new computer after downloading from Google Drive.

Usage: python quick-setup.py
"""

import subprocess
import sys
import os
import time
import platform
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(message, color=Colors.END):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.END}")

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print_colored(f"🚀 {title}", Colors.BOLD + Colors.BLUE)
    print("="*60)

def print_step(step_num, description):
    """Print formatted step"""
    print_colored(f"\n📋 Step {step_num}: {description}", Colors.BOLD + Colors.GREEN)

def print_success(message):
    """Print success message"""
    print_colored(f"✅ {message}", Colors.GREEN)

def print_error(message):
    """Print error message"""
    print_colored(f"❌ {message}", Colors.RED)

def print_warning(message):
    """Print warning message"""
    print_colored(f"⚠️  {message}", Colors.YELLOW)

def run_command(command, description="", check_output=False, timeout=300):
    """Run a command and return success status"""
    try:
        if description:
            print(f"   Running: {description}")
        
        if check_output:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=timeout
            )
            return True, result.stdout.strip()
        else:
            subprocess.run(command, shell=True, check=True, timeout=timeout)
            return True, ""
    
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out after {timeout} seconds: {command}")
        return False, ""
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        if hasattr(e, 'stderr') and e.stderr:
            print_error(f"Error output: {e.stderr}")
        return False, ""
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False, ""

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python version")
    
    version = sys.version_info
    print(f"   Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("Python 3.8 or higher is required!")
        print("   Please download from: https://python.org")
        return False
    
    print_success("Python version is compatible")
    return True

def check_node_version():
    """Check if Node.js is installed and compatible"""
    print_step(2, "Checking Node.js version")
    
    success, output = run_command("node --version", "Checking Node.js version", check_output=True)
    if not success:
        print_error("Node.js is not installed!")
        print("   Please download from: https://nodejs.org")
        return False
    
    try:
        # Extract version number (remove 'v' prefix)
        version_str = output.replace('v', '')
        major_version = int(version_str.split('.')[0])
        
        print(f"   Node.js version: {output}")
        
        if major_version < 16:
            print_error("Node.js 16 or higher is required!")
            print("   Please update from: https://nodejs.org")
            return False
        
        print_success("Node.js version is compatible")
        return True
        
    except (ValueError, IndexError):
        print_error("Could not determine Node.js version")
        return False

def check_npm():
    """Check if npm is available"""
    success, output = run_command("npm --version", "Checking npm version", check_output=True)
    if success:
        print(f"   npm version: {output}")
        print_success("npm is available")
        return True
    else:
        print_error("npm is not available")
        return False

def check_project_files():
    """Check if essential project files exist"""
    print_step(3, "Checking project files")
    
    required_files = [
        "requirements.txt",
        "package.json", 
        "manage.py",
        "gymlog_backend/settings.py",
        "src/main.jsx"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"   ✓ {file_path}")
    
    if missing_files:
        print_error("Missing essential files:")
        for file_path in missing_files:
            print(f"     - {file_path}")
        print("\n   Make sure you downloaded the complete project from Google Drive.")
        return False
    
    print_success("All essential project files found")
    return True

def check_database():
    """Check database file"""
    db_path = Path("db.sqlite3")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"   Database file found (Size: {size_mb:.2f} MB)")
        print_success("Database file is present")
        return True
    else:
        print_warning("Database file not found - will be created during migration")
        return True

def install_python_dependencies():
    """Install Python dependencies"""
    print_step(4, "Installing Python dependencies")
    
    # Check if virtual environment should be created
    if not Path("venv").exists() and not os.environ.get('VIRTUAL_ENV'):
        print("   No virtual environment detected.")
        create_venv = input("   Create virtual environment? (recommended) [Y/n]: ").strip().lower()
        
        if create_venv != 'n':
            print("   Creating virtual environment...")
            success, _ = run_command("python -m venv venv", "Creating virtual environment")
            if not success:
                print_error("Failed to create virtual environment")
                return False
            
            # Provide activation instructions
            system = platform.system().lower()
            if system == "windows":
                activate_cmd = "venv\\Scripts\\activate"
            else:
                activate_cmd = "source venv/bin/activate"
            
            print_warning(f"Please activate the virtual environment and re-run this script:")
            print_warning(f"   {activate_cmd}")
            print_warning(f"   python quick-setup.py")
            return False
    
    print("   Installing packages from requirements.txt...")
    success, _ = run_command(
        "pip install -r requirements.txt", 
        "Installing Python packages",
        timeout=600  # 10 minutes timeout for pip install
    )
    
    if success:
        print_success("Python dependencies installed successfully")
        return True
    else:
        print_error("Failed to install Python dependencies")
        print("   Try running manually: pip install -r requirements.txt")
        return False

def install_node_dependencies():
    """Install Node.js dependencies"""
    print_step(5, "Installing Node.js dependencies")
    
    # Clean install for better reliability
    if Path("node_modules").exists():
        print("   Removing existing node_modules...")
        try:
            import shutil
            shutil.rmtree("node_modules")
        except Exception as e:
            print_warning(f"Could not remove node_modules: {e}")
    
    print("   Installing packages from package.json...")
    success, _ = run_command(
        "npm install", 
        "Installing Node.js packages",
        timeout=600  # 10 minutes timeout for npm install
    )
    
    if success:
        print_success("Node.js dependencies installed successfully")
        return True
    else:
        print_error("Failed to install Node.js dependencies")
        print("   Try running manually: npm install")
        return False

def setup_database():
    """Set up Django database"""
    print_step(6, "Setting up database")
    
    print("   Running Django migrations...")
    success, _ = run_command("python manage.py migrate", "Running database migrations")
    
    if success:
        print_success("Database setup completed")
        return True
    else:
        print_error("Database migration failed")
        print("   Try running manually: python manage.py migrate")
        return False

def verify_installation():
    """Verify that the installation was successful"""
    print_step(7, "Verifying installation")
    
    # Check if we can import Django
    try:
        print("   Testing Django import...")
        import django
        print(f"   Django version: {django.get_version()}")
        print_success("Django is working")
    except ImportError:
        print_error("Django import failed")
        return False
    
    # Check if manage.py commands work
    print("   Testing Django configuration...")
    success, _ = run_command(
        "python manage.py check", 
        "Running Django system check",
        timeout=30
    )
    
    if success:
        print_success("Django configuration is valid")
    else:
        print_error("Django configuration check failed")
        return False
    
    # Check if frontend build works
    print("   Testing frontend build...")
    success, _ = run_command(
        "npm run build", 
        "Testing frontend build",
        timeout=120
    )
    
    if success:
        print_success("Frontend build successful")
        return True
    else:
        print_warning("Frontend build test failed (but project may still work)")
        return True

def provide_next_steps():
    """Provide instructions for next steps"""
    print_header("Setup Complete! 🎉")
    
    print_colored("\n🚀 Your APC Gym Log System is ready to use!", Colors.BOLD + Colors.GREEN)
    
    print("\n📋 Next Steps:")
    print("   1. Start the development servers:")
    print_colored("      python start-dev.py", Colors.BLUE)
    
    print("\n   2. Open your browser and visit:")
    print_colored("      Frontend: http://localhost:5173", Colors.BLUE)
    print_colored("      Backend API: http://localhost:8000/api", Colors.BLUE)
    print_colored("      Admin Panel: http://localhost:8000/admin", Colors.BLUE)
    
    print("\n   3. Optional - Create admin account:")
    print_colored("      python create_admin.py", Colors.BLUE)
    
    print("\n   4. Optional - Add sample data:")
    print_colored("      python scripts/dev-setup.py", Colors.BLUE)
    
    print("\n💡 Tips:")
    print("   • Use 'Ctrl+C' to stop the servers")
    print("   • Check the browser console for any error messages")
    print("   • See SETUP.md for detailed documentation")
    
    print_colored("\n🎯 Happy coding! Your gym log system is ready to go!", Colors.BOLD + Colors.GREEN)

def main():
    """Main setup function"""
    print_header("APC Gym Log System - Quick Setup")
    print("This script will automatically set up your project on this computer.")
    print("Make sure you have downloaded the complete project from Google Drive.\n")
    
    # Confirmation
    proceed = input("Do you want to proceed with the setup? [Y/n]: ").strip().lower()
    if proceed == 'n':
        print("Setup cancelled.")
        return
    
    # Track setup success
    setup_steps = [
        ("Check Python version", check_python_version),
        ("Check Node.js version", check_node_version),
        ("Check npm availability", check_npm),
        ("Verify project files", check_project_files),
        ("Check database", check_database),
        ("Install Python dependencies", install_python_dependencies),
        ("Install Node.js dependencies", install_node_dependencies),
        ("Setup database", setup_database),
        ("Verify installation", verify_installation),
    ]
    
    failed_steps = []
    
    # Execute setup steps
    for step_name, step_function in setup_steps:
        if not step_function():
            failed_steps.append(step_name)
            
            # Ask if user wants to continue
            if step_name in ["Install Python dependencies", "Install Node.js dependencies"]:
                continue_setup = input(f"\n❓ {step_name} failed. Continue anyway? [y/N]: ").strip().lower()
                if continue_setup != 'y':
                    print("\nSetup aborted.")
                    return
    
    # Final results
    print_header("Setup Results")
    
    if not failed_steps:
        print_success("All setup steps completed successfully!")
        provide_next_steps()
    else:
        print_warning("Setup completed with some issues:")
        for step in failed_steps:
            print(f"   ❌ {step}")
        
        print("\n💡 You may still be able to run the project manually.")
        print("   Check the error messages above and try running the failed commands manually.")
        
        # Still provide next steps
        provide_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n🛑 Setup interrupted by user", Colors.YELLOW)
        print("You can run this script again anytime: python quick-setup.py")
    except Exception as e:
        print_colored(f"\n❌ Unexpected error during setup: {str(e)}", Colors.RED)
        print("Please report this error and try manual setup using SETUP.md")
