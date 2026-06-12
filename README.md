# RestaurantPro - Enterprise Restaurant Management System

A full-stack, production-ready restaurant management web application built with Flask, MySQL, and Flask-SocketIO.

## Features

- **8 User Roles**: Super Admin, Admin, Manager, Chef, Waiter, Cashier, Delivery Boy, Customer
- **Customer Portal**: Menu browsing, cart, orders, table booking, payments, loyalty program, reviews
- **Admin Panel**: Food/menu management, orders, bookings, tables, staff, inventory, analytics
- **Staff Panels**: Chef KDS, Waiter service, Cashier billing, Delivery tracking
- **Real-time**: Order tracking, kitchen display, waiter notifications via SocketIO
- **Payments**: Razorpay integration with GST invoices and PDF bills
- **Security**: JWT auth, CSRF protection, password hashing, rate limiting, RBAC
- **PWA**: Installable progressive web app with offline support
- **REST API**: Full API with Swagger documentation at `/api/v1/docs`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python Flask |
| Database | MySQL 8+ |
| Realtime | Flask-SocketIO + Redis |
| Payments | Razorpay |
| Images | Cloudinary |
| PDF | ReportLab |
| Deploy | Docker, Nginx, Gunicorn |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Start MySQL and Redis, then:
python seed_data.py
python run.py
```

Visit `http://localhost:5000`

## Project Structure

```
restaurant-management/
├── app/
│   ├── models/          # SQLAlchemy database models
│   ├── routes/          # Web and API route blueprints
│   ├── services/        # Business logic layer
│   ├── utils/           # Helpers, decorators, PDF/QR generators
│   ├── sockets/         # SocketIO event handlers
│   ├── config.py        # Application configuration
│   └── extensions.py    # Flask extensions
├── templates/           # Jinja2 HTML templates
├── static/              # CSS, JS, images, PWA manifest
├── database/            # SQL schema file
├── nginx/               # Nginx configuration
├── docker-compose.yml   # Docker orchestration
├── seed_data.py         # Sample data seeder
└── DEPLOYMENT.md        # Production deployment guide
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register customer |
| POST | `/api/v1/auth/login` | Login (returns JWT) |
| GET | `/api/v1/restaurants` | List restaurants |
| GET | `/api/v1/restaurants/{id}/menu` | Get menu |
| POST | `/api/v1/cart/add` | Add to cart |
| POST | `/api/v1/orders` | Place order |
| GET | `/api/v1/bookings/availability` | Check table availability |
| POST | `/api/v1/payments/create` | Create payment |

Full API docs: `/api/v1/docs`

## License

Proprietary - All rights reserved.
