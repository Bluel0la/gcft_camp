import requests, base64, os, httpx
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv(".env")

username = os.getenv("SMS_USERNAME")
password= os.getenv("SMS_PASSWORD")
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_TOKEN")
client = Client(account_sid, auth_token)

base_url = os.getenv("TERMI_BASE_URL")
termi_api_key= os.getenv("TERMI_API_KEY")


async def send_sms_termii_whatsapp(phone_number: str, name: str, arrival_date: str, hall: str, floor: str, bed_no: str, country: str,
):
    """
    Asynchronously sends an SMS via the Termii API.
    """

    # Normalize phone number based on country
    country = country.lower()
    if phone_number.startswith("0"):
        if country == "nigeria":
            phone_number = "234" + phone_number[1:]
        elif country == "ghana":
            phone_number = "233" + phone_number[1:]
        elif country == "kenya":
            phone_number = "254" + phone_number[1:]

    sms_content = (
        f"Good day {name}! You have been successfully registered for the camp meeting.\n"
        f"Arrival Date: {arrival_date}\n"
        f"Hall: {hall}\n"
        f"Floor: Floor {floor}\n"
        f"Bed No: {bed_no}\n\n"
        f"Please ensure to arrive on the specified date. Thank you and God bless you."
    )

    payload = {
        "to": phone_number,
        "from": "GCFT",
        "sms": sms_content,
        "type": "plain",
        "channel": "whatsapp",
        "api_key": termi_api_key,
    }

    headers = {
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{base_url}/api/sms/send", headers=headers, json=payload
        )

    return response.json()


async def send_sms_termii(
    phone_number: str,
    name: str,
    arrival_date: str,
    hall: str,
    floor: str,
    bed_no: str,
    country: str,
):
    """
    Asynchronously sends an SMS via the Termii API.
    """

    # Normalize phone number based on country
    country = country.lower()
    if phone_number.startswith("0"):
        if country == "nigeria":
            phone_number = "234" + phone_number[1:]
        elif country == "ghana":
            phone_number = "233" + phone_number[1:]
        elif country == "kenya":
            phone_number = "254" + phone_number[1:]

    sms_content = (
        f"Good day {name}! You have been successfully registered for the camp meeting.\n"
        f"Arrival Date: {arrival_date}\n"
        f"Hall: {hall}\n"
        f"Floor: Floor {floor}\n"
        f"Bed No: {bed_no}\n\n"
        f"Please ensure to arrive on the specified date. Thank you and God bless you."
    )

    payload = {
        "to": phone_number,
        "from": "GCFT",
        "sms": sms_content,
        "type": "plain",
        "channel": "dnd",
        "api_key": termi_api_key,
    }

    headers = {
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{base_url}/api/sms/send", headers=headers, json=payload
        )

    return response.json()
