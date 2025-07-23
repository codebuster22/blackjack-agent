#!/usr/bin/env python3
"""
Test environment setup and management script.
"""
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_helpers import (
    start_test_database,
    stop_test_database,
    wait_for_database,
    get_test_database_connection,
    setup_test_environment,
    cleanup_test_environment
)


def setup_database():
    """Start the test database."""
    try:
        print("Starting test database...")
        start_test_database()
        print("✅ Test database started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start test database: {e}")
        return False


def teardown_database():
    """Stop the test database."""
    try:
        print("Stopping test database...")
        stop_test_database()
        print("✅ Test database stopped successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to stop test database: {e}")
        return False


def check_database():
    """Check if the test database is running and accessible."""
    try:
        print("Checking test database...")
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test_value")
                result = cursor.fetchone()
                if result[0] == 1:
                    print("✅ Test database is running and accessible")
                    return True
                else:
                    print("❌ Test database check failed")
                    return False
    except Exception as e:
        print(f"❌ Test database check failed: {e}")
        return False


def setup_environment():
    """Set up test environment variables."""
    try:
        print("Setting up test environment...")
        setup_test_environment()
        print("✅ Test environment set up successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to set up test environment: {e}")
        return False


def cleanup_environment():
    """Clean up test environment variables."""
    try:
        print("Cleaning up test environment...")
        cleanup_test_environment()
        print("✅ Test environment cleaned up successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to clean up test environment: {e}")
        return False


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Test environment management")
    parser.add_argument(
        "action",
        choices=["start", "stop", "check", "setup", "cleanup", "restart"],
        help="Action to perform"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Performing action: {args.action}")
    
    success = True
    
    if args.action == "start":
        success = setup_database()
    elif args.action == "stop":
        success = teardown_database()
    elif args.action == "check":
        success = check_database()
    elif args.action == "setup":
        success = setup_environment()
    elif args.action == "cleanup":
        success = cleanup_environment()
    elif args.action == "restart":
        print("Restarting test database...")
        success = teardown_database() and setup_database()
    
    if success:
        print("🎉 Operation completed successfully")
        sys.exit(0)
    else:
        print("💥 Operation failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 