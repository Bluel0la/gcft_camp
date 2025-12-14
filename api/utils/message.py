import requests, base64, os
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

def send_sms_termii(phone_number: str, name: str, arrival_date: str, hall: str, floor: str, bed_no: str, country: str):
    # Clean the phone number depending on the Country by replacing the first number with the country code
    if country.lower() == "nigeria":
        if phone_number.startswith("0"):
            phone_number = "+234" + phone_number[1:]
    elif country.lower() == "ghana":
        if phone_number.startswith("0"):
            phone_number = "+233" + phone_number[1:]
    elif country.lower() == "kenya":
        if phone_number.startswith("0"):
            phone_number = "+254" + phone_number[1:]
    else:
        pass
    print(phone_number)
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
           "from": "CampMeet",
           "sms": sms_content,
           "type": "plain",
           "channel": "dnd",
           "api_key": termi_api_key,
       }
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.request("POST", base_url + "/api/sms/send", headers=headers, json=payload)
    print(response.text)