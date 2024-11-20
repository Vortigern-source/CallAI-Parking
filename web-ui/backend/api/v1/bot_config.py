from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import json
import os
from typing import Dict, Any

from database import get_db, User
from auth import get_current_active_user, check_admin_role

router = APIRouter(prefix="/bot/config", tags=["bot_config"])


class BotConfigModel(BaseModel):
    prompts: Dict[str, Any]
    discussion: Dict[str, str]
    environment_variables: Dict[str, str]


def read_params():
    """
    Read parameters from a JSON file.
    """
    params_file = os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        ),
        "params.json",
    )

    try:
        with open(params_file, "r") as f:
            params = json.load(f)
        return params
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing configuration file")


def write_params(params):
    """
    Write parameters to the JSON file.
    """
    params_file = os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        ),
        "params.json",
    )

    try:
        with open(params_file, "w") as f:
            json.dump(params, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing configuration file: {str(e)}")


@router.get("")
async def get_bot_config(
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve bot configuration
    """
    params = read_params()

    # Collect ALL environment variables used in the bot
    env_vars = {
        # AI Service Keys
        "OPENAI_API_KEY": "sk-" + os.getenv("OPENAI_API_KEY", "")[-10:]
        if os.getenv("OPENAI_API_KEY")
        else "",
        "DEEPGRAM_API_KEY": "dk-" + os.getenv("DEEPGRAM_API_KEY", "")[-10:]
        if os.getenv("DEEPGRAM_API_KEY")
        else "",
        "CARTESIA_API_KEY": "ca-" + os.getenv("CARTESIA_API_KEY", "")[-10:]
        if os.getenv("CARTESIA_API_KEY")
        else "",
        "GLADIA_API_KEY": os.getenv("GLADIA_API_KEY", ""),
        # Twilio Credentials
        "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "TWILIO_AUTH_TOKEN": "tk-" + os.getenv("TWILIO_AUTH_TOKEN", "")[-10:]
        if os.getenv("TWILIO_AUTH_TOKEN")
        else "",
        "FROM_NUMBER": os.getenv("FROM_NUMBER", ""),
        "APP_NUMBER": os.getenv("APP_NUMBER", ""),
        "YOUR_NUMBER": os.getenv("YOUR_NUMBER", ""),
        "TWILIO_WHATSAPP_NUMBER": os.getenv("TWILIO_WHATSAPP_NUMBER", ""),
        "MANAGER_WHATSAPP_GROUP": os.getenv("MANAGER_WHATSAPP_GROUP", ""),
        # Notion Integration
        "NOTION_API_KEY": "ntn-" + os.getenv("NOTION_API_KEY", "")[-10:]
        if os.getenv("NOTION_API_KEY")
        else "",
        "NOTION_PAGE_ID": os.getenv("NOTION_PAGE_ID", ""),
        # Voice and TTS Services
        "XI_API_KEY": "xi-" + os.getenv("XI_API_KEY", "")[-10:] if os.getenv("XI_API_KEY") else "",
        "XI_MODEL_ID": os.getenv("XI_MODEL_ID", ""),
        "XI_VOICE_ID": os.getenv("XI_VOICE_ID", ""),
        "PLAYHT_USER_ID": os.getenv("PLAYHT_USER_ID", ""),
        "PLAYHT_API_KEY": "ph-" + os.getenv("PLAYHT_API_KEY", "")[-10:]
        if os.getenv("PLAYHT_API_KEY")
        else "",
        # Azure Speech
        "AZURE_SPEECH_KEY": "az-" + os.getenv("AZURE_SPEECH_KEY", "")[-10:]
        if os.getenv("AZURE_SPEECH_KEY")
        else "",
        "AZURE_SPEECH_REGION": os.getenv("AZURE_SPEECH_REGION", ""),
        # Airtable Configuration
        "AIRTABLE_API_KEY": "pat-" + os.getenv("AIRTABLE_API_KEY", "")[-10:]
        if os.getenv("AIRTABLE_API_KEY")
        else "",
        "AIRTABLE_BASE_ID": os.getenv("AIRTABLE_BASE_ID", ""),
        "AIRTABLE_BOOKINGS_TABLE": os.getenv("AIRTABLE_BOOKINGS_TABLE", ""),
        "AIRTABLE_DEPARTURES_TABLE": os.getenv("AIRTABLE_DEPARTURES_TABLE", ""),
        "AIRTABLE_ARRIVALS_TABLE": os.getenv("AIRTABLE_ARRIVALS_TABLE", ""),
        # Server and Deployment
        "SERVER": os.getenv("SERVER", ""),
        "TZ": os.getenv("TZ", ""),
        # Voice Model
        "VOICE_MODEL": os.getenv("VOICE_MODEL", ""),
        # Recording
        "RECORDING_ENABLED": os.getenv("RECORDING_ENABLED", ""),
    }

    return {
        "prompts": params.get("prompts", {}),
        "discussion": params.get("discussion", {}),
        "environment_variables": env_vars,
    }


@router.put("")
async def update_bot_config(
    config: BotConfigModel,
    current_user: User = Depends(check_admin_role),
):
    """
    Update bot configuration
    """
    try:
        # Read existing params
        params = read_params()

        # Update prompts and discussion
        if config.prompts:
            params["prompts"].update(config.prompts)
        if config.discussion:
            params["discussion"].update(config.discussion)

        # Update environment variables
        if config.environment_variables:
            for key, value in config.environment_variables.items():
                if value:
                    os.environ[key] = value

        # Write updated params back to file
        write_params(params)

        return {"message": "Bot configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")
