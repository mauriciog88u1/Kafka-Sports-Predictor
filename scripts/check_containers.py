#!/usr/bin/env python3
"""Check if required containers are running."""
import subprocess
import sys
import time

def check_containers():
    """Check if required containers are running."""
    try:
        # Check if Docker is running
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        
        # Check if our app container is running
        result = subprocess.run(
            ["docker-compose", "ps", "app"],
            capture_output=True,
            text=True
        )
        
        if "Up" not in result.stdout:
            print("App container is not running. Starting containers...")
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            # Wait for containers to be ready
            time.sleep(5)
            
        print("All containers are running and ready!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error checking containers: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    if not check_containers():
        sys.exit(1) 