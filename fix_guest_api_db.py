import os
import subprocess
import sys

def run_command(command):
    """Helper function to run shell commands."""
    print(f"\nExecuting: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("STDOUT:\n", result.stdout)
        if result.stderr:
            print("STDERR:\n", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Command '{command.split()[0]}' not found. Make sure Python and Django are in your PATH.")
        return False

def main():
    print("--- Django Database Migration Fix ---")
    print("This script will help resolve 'no such column' errors by ensuring your database schema is up-to-date.")

    # Step 1: Verify your Guest model
    print("\nStep 1: Please ensure your 'guest_house/models.py' file contains the 'first_name' field in your Guest model, like this:")
    print("""
# guest_house/models.py (Example)
from django.db import models

class Guest(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # ... other fields
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
""")
    input("Press Enter to continue after verifying your model...")

    # Step 2: Create new migrations
    print("\nStep 2: Creating new migrations for the 'guest_house' app...")
    if not run_command("python manage.py makemigrations guest_house"):
        print("Failed to create migrations. Please check your models and Django project setup.")
        sys.exit(1)
    print("Migrations created successfully (if there were changes).")

    # Step 3: Apply migrations
    print("\nStep 3: Applying pending migrations to the database...")
    if not run_command("python manage.py migrate"):
        print("Failed to apply migrations. This might be due to existing data conflicts or other issues.")
        print("Consider the advanced step below if you are in a development environment and can lose data.")
        sys.exit(1)
    print("Migrations applied successfully.")

    # Step 4: Optional - Database Reset (for development)
    print("\n--- Advanced Step (Use ONLY in Development if previous steps failed and you can lose data) ---")
    print("If the issue persists, your database file might be corrupted or severely out of sync.")
    print("You can delete the 'db.sqlite3' file and re-run migrations to start fresh.")
    confirm = input("Do you want to delete 'db.sqlite3' and re-run migrations? (yes/no): ").lower()
    if confirm == 'yes':
        db_path = "db.sqlite3"
        if os.path.exists(db_path):
            print(f"Deleting {db_path}...")
            os.remove(db_path)
            print(f"{db_path} deleted.")
        else:
            print(f"{db_path} not found. Skipping deletion.")

        print("\nRe-running makemigrations and migrate after database deletion...")
        if not run_command("python manage.py makemigrations guest_house"):
            print("Failed to create migrations after database reset.")
            sys.exit(1)
        if not run_command("python manage.py migrate"):
            print("Failed to apply migrations after database reset.")
            sys.exit(1)
        print("Database reset and migrations re-applied successfully.")
    else:
        print("Skipping database reset.")

    print("\n--- Fix Attempt Complete ---")
    print("Please try accessing your API endpoint again: http://127.0.0.1:8000/api/guests/")
    print("If the issue persists, review your Django models, serializers, and views for any inconsistencies.")

if __name__ == "__main__":
    main()
