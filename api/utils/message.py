import requests, base64, os, httpx
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv(".env")


base_url = os.getenv("TERMI_BASE_URL")
termi_api_key= os.getenv("TERMI_API_KEY")
from_client = os.getenv("TERMI_FROM_CLIENT")

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
        "from": f"{from_client}",
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
            f"https://{base_url}/api/sms/send", headers=headers, json=payload
        )

    return response.json()


def send_sms_termii(
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
        "from": f"{from_client}",
        "sms": sms_content,
        "type": "plain",
        "channel": "generic",
        "api_key": termi_api_key,
    }
    url = f"https://{base_url}/api/sms/send"

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, json=payload)

    return response.json()
