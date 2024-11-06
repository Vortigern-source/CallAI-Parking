# CallAI-Parking

A sophisticated AI-powered call handling system specifically designed for parking services. This project integrates natural language processing capabilities with telephony services to automate parking-related customer interactions.

## Features

- Automated call handling for parking services
- Integration with Twilio for telephony services
- Custom AI processing pipeline for natural language understanding
- Booking management functionality
- Real-time ETA updates
- Vehicle registration handling
- WhatsApp message integration
- Terminal and vehicle details management

## Project Structure

```
├── custom_pipecat/           # Custom pipeline components
│   ├── custom_frames/       # Frame definitions
│   ├── custom_processors/   # Custom processing logic
│   ├── custom_services/     # Service integrations
│   ├── templates/          # Template definitions
│   └── twilio_utils/       # Twilio integration utilities
├── functions/               # Core business logic
│   ├── booking management
│   ├── call transfers
│   ├── vehicle management
│   └── messaging
├── utils/                   # Utility functions
├── logs/                    # Application logs
└── transcripts/            # Call transcripts
```

## Prerequisites

- Python 3.8+
- Poetry for dependency management
- Twilio account for telephony services
- Access to required AI services

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Configure environment:
- Copy `params.json.example` to `params.json` (if applicable)
- Set up required environment variables

## Configuration

The system can be configured through `params.json` which should include:
- API credentials
- Service endpoints
- Processing parameters
- Logging configurations

## Usage

1. Start the server:
```bash
python server.py
```

2. For development/testing:
```bash
python test-functions.py
```

## Docker Support

The project includes Docker support for containerized deployment:

```bash
docker build -t callai-parking .
docker run -p 8000:8000 callai-parking
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is proprietary and confidential. All rights reserved.

## Support

For support and queries, please contact the development team.
