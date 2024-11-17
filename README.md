## CallAI Parking Web Application

### Project Overview
A web application for managing parking bookings with admin and user management features.

### Database Action Tests

To verify database-related actions, run the test script:

```bash
python web-ui/backend/test_database_actions.py
```

#### Test Details

The script tests critical database operations:
1. Initial admin user creation
2. User authentication
3. Adding multiple users
4. Fetching all users

### Setup and Installation

#### Prerequisites
- Python 3.8+
- Node.js and npm
- SQLAlchemy
- passlib

#### Backend Setup
1. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

2. Install dependencies
```bash
pip install -r web-ui/backend/requirements.txt
```

3. Set Environment Variables
```bash
export INITIAL_ADMIN_USERNAME=youradmin
export INITIAL_ADMIN_EMAIL=admin@example.com
export INITIAL_ADMIN_PASSWORD=SecurePassword123!
```

#### Running the Application

1. Start Backend Server
```bash
cd web-ui/backend
uvicorn main:app --reload
```

2. Start Frontend
```bash
cd ../..
npm start
```

### Testing Database Actions

Run the comprehensive database test script:
```bash
python web-ui/backend/test_database_actions.py
```

This script will:
- Create a test admin user
- Authenticate the admin
- Add two test client users
- Fetch and display all users

### Troubleshooting
- Verify database connection settings in `database.py`
- Check environment variables
- Ensure all dependencies are installed

### Development Notes
- Uses SQLAlchemy for database management
- Implements role-based access control
- Supports user creation, authentication, and management
