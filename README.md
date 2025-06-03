# Cartlogs - Digital Accounts Marketplace

## Overview

Cartlogs is a Django-based web application that serves as a marketplace for digital accounts such as social media accounts, streaming services, VPNs, and more. The platform allows users to browse, purchase, and manage digital accounts with a secure wallet system and multiple payment options.

## Features

### User Authentication

- User registration and login
- Password reset functionality
- Profile management

### Marketplace

- Browse digital accounts by category
- View detailed account information
- Add accounts to cart
- Checkout process
- Order history and tracking

### Wallet System

- Add funds to wallet
- View transaction history
- Use wallet balance for purchases

### Payment Integration

- Korapay payment gateway integration
- Manual bank transfer option
- Secure payment processing

### Admin Features

- Manage social media accounts
- Track orders and payments
- User management
- Category management with position ordering

## Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript (Alpine.js)
- **Database**: SQLite (development), PostgreSQL (production)
- **Storage**: AWS S3 (optional)
- **Payment Processing**: Korapay

## Project Structure

- **core**: Contains user authentication, wallet system, and payment processing
- **marketplace**: Contains the marketplace functionality, including models for accounts, orders, and categories
- **server**: Contains project settings and URL configurations
- **templates**: Contains base templates and shared components
- **static**: Contains static files like CSS, JavaScript, and images

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Installation

1. Clone the repository

   ```
   git clone https://github.com/divuzki/cartlogs.git
   cd cartlogs
   ```

2. Create and activate a virtual environment

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables
   Create a `.env` file in the root directory with the following variables:

   ```
   DEBUG=True
   SECRET_KEY=your_secret_key
   KORAPAY_SECRET_KEY=your_korapay_secret_key
   KORAPAY_PUBLIC_KEY=your_korapay_public_key
   EMAIL_HOST_PASSWORD=your_email_password
   ADMIN_EMAIL=admin@example.com
   ```

5. Run migrations

   ```
   python manage.py migrate
   ```

6. Create a superuser

   ```
   python manage.py createsuperuser
   ```

7. Run the development server

   ```
   python manage.py runserver
   ```

8. Access the application at `http://127.0.0.1:8000`

## User Workflow

1. User creates an account or logs in
2. User adds digital accounts to cart and proceeds to checkout (order is created in the database)
3. User pays for the order using Korapay or manual bank transfer
4. User receives the purchased accounts via email (these accounts are also stored in the database)

## Deployment

The application is configured to work with various deployment options:

- **Static Files**: Can be served locally or via AWS S3
- **Database**: Works with SQLite locally and can be configured for PostgreSQL in production using `dj_database_url`
- **Security**: Includes settings for HTTPS, HSTS, and other security measures when `DEBUG=False`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.
