# Project Tile
## Guest House Management System API
A Django REST API for managing guest house operations including room bookings, meal reservations, and debit card payments.

## Project Overview
This application provides a backend RESTful service for a guest house, allowing guests to reserve rooms and meals. Payment is handled via a simulated debit card transaction system where amounts are added or deducted from card accounts. Once a guest selects a service (room or meal), they are redirected to a payment process to complete the transaction using their debit card number.

# Features
- Features
- Manage room availability, pricing, and reservations
- Meal reservation and order system
- Guest profile and information management
- Simulated debit card payment processing (transactional balance updates)
- Transaction history tracking for debit card usage
- REST API with endpoints for all core operations
- Comprehensive API documentation (Postman)

## Technologies Used
- Python 3.13
- Django 5.2.4
- Django REST Framework 3.16.0
-  SQLite (default DB)

# Installation 
1. Create and activate a virtual environment (Windows):
    - python -m venv venv
    - venv\Scripts\activate

2. Install dependencies:
    - pip install -r requirements.txt

3. Configure database
    - python manage.py migrate
    
4. Run migrations to set up the database schema:
    - python manage.py makemigrations
    - python manage.py migrate

5. Create a superuser (for admin access):
    - python manage.py createsuperuser

6. Start the development server:
    - python manage.py runserver
