# Manchester Airport Parking Call Bot

A voice-enabled call bot for handling Manchester Airport parking reservations, built with Pipecat AI and Twilio.

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Airtable (for booking management)
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
AIRTABLE_TABLE_NAME=your_airtable_table_name

# WhatsApp (for driver notifications)
WHATSAPP_NUMBER=your_whatsapp_number
```

## Usage

1. Start the server:
```bash
python server.py
```

2. The bot will be available to handle incoming calls at your configured Twilio phone number.

## Features

- Handles both car drop-offs and collections
- Manages booking lookups via registration number or booking reference
- Updates booking details (vehicle, terminal, phone number)
- Sends WhatsApp notifications to drivers
- Manages expired bookings and date discrepancies
