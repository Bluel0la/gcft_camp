import requests, base64, os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv(".env")

username = os.getenv("SMS_USERNAME")
password= os.getenv("SMS_PASSWORD")
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_TOKEN")
client = Client(account_sid, auth_token)

# def send_sms_registered_campers(phone_number: str, name: str, arrival_date: str, hall: str, floor: str, bed_no: str, country: str):
#    url = "https://api.bulksms.com/v1/messages"
#
#   my_username = username
#    my_password = password
#
# Clean the phone number depending on the Country by replacing the first number with the country code
#    if country.lower() == "nigeria":
#        if phone_number.startswith("0"):
#            phone_number = "234" + phone_number[1:]
#    elif country.lower() == "ghana":
#        if phone_number.startswith("0"):
#            phone_number = "233" + phone_number[1:]
#    elif country.lower() == "kenya":
#        if phone_number.startswith("0"):
#            phone_number = "254" + phone_number[1:]
#    else:
#        pass
#    print(phone_number)


#    body = (
#        f"Good day {name}! You have been successfully registered for the camp meeting.\n"
#        f"Arrival Date: {arrival_date}\n"
#        f"Hall: {hall}\n"
#        f"Floor: Floor {floor}\n"
#        f"Bed No: {bed_no}\n\n"
#        f"Please ensure to arrive on the specified date. Thank you and God bless you."
#    )

# The details of the message sent to the Campers
#    my_data = {
#        "to": [phone_number],
#        "from": "GCFT",
#        "body": body,
#        "longMessageMaxParts": "30"
#    }

# Encode credentials to Base64
#    credentials = f"{my_username}:{my_password}"
#    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

# Headers
#    headers = {
#        "Content-Type": "application/json",
#        "Authorization": f"Basic {encoded_credentials}",
#    }

# Make the request
#    try:
#        response = requests.post(url, json=my_data, headers=headers)

# Check if the request was successful
#        response.raise_for_status()

# Print the response from the API for debugging
#        print(response.text)
#    except requests.exceptions.RequestException as ex:
# Show the general message
#        print("An error occurred: {}".format(ex))
#        if ex.response is not None:
#            print("Error Details: {}".format(ex.response.text))



def send_sms(phone_number: str, name: str, arrival_date: str, hall: str, floor: str, bed_no: str, country: str):
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
    body = (
        f"Good day {name}! You have been successfully registered for the camp meeting.\n"
        f"Arrival Date: {arrival_date}\n"
        f"Hall: {hall}\n"
        f"Floor: Floor {floor}\n"
        f"Bed No: {bed_no}\n\n"
        f"Please ensure to arrive on the specified date. Thank you and God bless you."
    )
    
    message = client.messages.create(
        from_="+16802069727",
        body=body,
        to=phone_number
    )
    print(message.sid)
