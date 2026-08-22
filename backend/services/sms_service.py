import requests
from typing import Tuple

class SMSService:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        phone = phone.replace("+", "").replace(" ", "").strip()
        if phone.startswith("0"):
            phone = "234" + phone[1:]
        elif not phone.startswith("234"):
            phone = "234" + phone
        url = "https://api.ng.termii.com/api/sms/send"
        payload = {
            "api_key": self.api_key,
            "to": phone,
            "from": "GAIA",
            "sms": message,
            "type": "plain",
            "channel": "generic"
        }
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                return True, ""
            return False, f"Termii: {r.status_code}"
        except Exception as e:
            return False, str(e)
