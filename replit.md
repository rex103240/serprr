# IronLifter Gym Management Software

## Overview
A comprehensive gym management desktop application built with Flask and SQLAlchemy, featuring modern UI with Bootstrap 5.

## Project Structure
```
/src
  /models/__init__.py     - SQLAlchemy models (Member, Plan, Staff, Equipment, etc.)
  /routes/                - Flask blueprints for all modules
  /templates/             - Jinja2 templates with Bootstrap 5 UI
  /utils/                 - Helpers, PDF generator, backup utilities
  /static/                - CSS, JS, uploaded files
  /config.py              - Application configuration
  /app.py                 - Flask app factory
/main.py                  - Application entry point
/backups/                 - Database backups
```

## Features
- **Member Management**: Registration, renewal, profile photos, emergency contacts, body measurements tracking
- **Plan Management**: Flexible membership plans with duration options
- **Staff Management**: Trainers, roles, salary tracking
- **Equipment Tracker**: Inventory, maintenance logs, warranty tracking
- **Financial Dashboard**: Income/expense tracking, profit analysis
- **Attendance System**: Kiosk mode for check-ins, peak hours analytics
- **PDF Generation**: Invoices and member cards with QR codes
- **Backup & Restore**: Database backup functionality
- **Role-based Access**: Admin and staff roles

## Tech Stack
- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **PDF Generation**: ReportLab, QRCode
- **Authentication**: Werkzeug password hashing

## Running the Application
```bash
python main.py
```
The app runs on port 5000.

## Default Credentials
- Username: admin
- Password: password123

## Environment Variables
- DATABASE_URL: PostgreSQL connection string
- SESSION_SECRET: Flask secret key
- KIOSK_SECRET: API token for kiosk mode
- TG_TOKEN, TG_CHAT_ID: Telegram notifications (optional)

## Recent Changes
- Modernized from SQLite to PostgreSQL with SQLAlchemy ORM
- Refactored to MVC architecture
- Added Bootstrap 5 UI
- Added staff management, equipment tracking
- Added PDF invoice and member card generation
- Added body measurements tracking
- Added database backup functionality
