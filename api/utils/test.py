import requests, os
from dotenv import load_dotenv
load_dotenv(".env")

base_url = os.getenv("TERMI_BASE_URL")
api_key = os.getenv("TERMI_API_KEY")

url = f"https://{base_url}/api/sms/send"
payload = {
    "to": "+2349132907873",
    "from": "Gcft",
    "sms": "Hi there, testing Termii ",
    "type": "plain",
    "channel": "generic",
    "api_key": f"{api_key}",
}
headers = {
    "Content-Type": "application/json",
}
response = requests.request("POST", url, headers=headers, json=payload)
print(response.text)
