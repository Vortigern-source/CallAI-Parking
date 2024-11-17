from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from database import get_db, User
from auth import get_current_active_user, check_admin_role
import os
import json
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive dashboard statistics
    """
    # User statistics
    total_users = db.query(User).count()
    admin_users = db.query(User).filter(User.role == "admin").count()
    active_users = db.query(User).filter(User.is_active == True).count()

    # Initialize booking variables
    total_bookings = 0
    active_bookings = []
    terminal_counts = {}
    recent_bookings = 0

    # Fetch Airtable bookings
    try:
        import aiohttp

        # Load Airtable configuration
        airtable_api_key = os.getenv("AIRTABLE_API_KEY")
        airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
        airtable_bookings_table = os.getenv("AIRTABLE_BOOKINGS_TABLE")

        if not all([airtable_api_key, airtable_base_id, airtable_bookings_table]):
            raise ValueError("Airtable configuration is incomplete")

        url = (
            f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_bookings_table}?"
            "cellFormat=string&timeZone=Europe/London&userLocale=en-gb"
        )

        headers = {"Authorization": f"Bearer {airtable_api_key}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    bookings = data.get("records", [])

                    # Booking statistics
                    total_bookings = len(bookings)

                    # Calculate active bookings (not collected)
                    active_bookings = [
                        booking
                        for booking in bookings
                        if (
                            booking["fields"].get("Drop_Off_Status", "").lower() != "collected"
                            and booking["fields"].get("Collection_Status", "").lower()
                            != "collected"
                        )
                    ]

                    # Calculate bookings by terminal
                    terminal_counts = {}
                    for booking in active_bookings:
                        terminal = booking["fields"].get("Terminal", "Unknown")
                        terminal_counts[terminal] = terminal_counts.get(terminal, 0) + 1

                    # Recent bookings (last 7 days)
                    now = datetime.now()
                    recent_bookings = sum(
                        1
                        for b in bookings
                        if datetime.strptime(
                            b["fields"].get("Entry_Date_Time", "01/01/2000 00:00"), "%d/%m/%Y %H:%M"
                        )
                        > now - timedelta(days=7)
                    )

    except Exception as e:
        # Log the error but continue with default values
        pass

    # System information
    try:
        import psutil

        # CPU and Memory usage
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
    except ImportError:
        cpu_usage = memory_usage = 0

    return {
        "users": {"total": total_users, "admin": admin_users, "active": active_users},
        "bookings": {
            "total": len(active_bookings),  # Only count active bookings
            "by_terminal": terminal_counts,
            "recent": recent_bookings,
        },
        "system": {"cpu_usage": cpu_usage, "memory_usage": memory_usage},
    }
