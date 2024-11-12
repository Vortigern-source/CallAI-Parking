# CallAI Parking Management UI

A comprehensive web interface for managing the CallAI Parking bot system.

## Features

- Real-time dashboard with call statistics
- Call logs management
- Bookings management
- System settings configuration
- Integration with existing bot functionality

## Project Structure

```
web-ui/
├── backend/              # FastAPI backend
│   ├── main.py          # Main API endpoints
│   └── requirements.txt # Python dependencies
├── public/              # Static assets
└── src/                 # React frontend
    ├── components/      # Reusable UI components
    ├── pages/          # Main application pages
    └── App.js          # Root component
```

## Getting Started

### Frontend Setup

1. Install dependencies:
```bash
cd web-ui
npm install
```

2. Start the development server:
```bash
npm start
```

The frontend will be available at http://localhost:3000

### Backend Setup

1. Install Python dependencies:
```bash
cd web-ui/backend
pip install -r requirements.txt
```

2. Start the FastAPI server:
```bash
python main.py
```

The API will be available at http://localhost:8000

## Available Pages

- **Dashboard**: Overview of system statistics and call volume
- **Call Logs**: View and manage call history
- **Bookings**: Manage parking bookings
- **Settings**: Configure system settings and API keys
