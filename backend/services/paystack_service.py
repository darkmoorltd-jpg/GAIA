import requests
from backend.config import settings
from typing import Dict, Optional, Tuple

class PaystackService:
    def __init__(self):
        self.secret = settings.PAYSTACK_SECRET
        self.base_url = "https://api.paystack.co"

    def initialize_payment(self, email: str, amount: int, plan: str, phone: str = "") -> Tuple[Optional[Dict], Optional[str]]:
        url = f"{self.base_url}/transaction/initialize"
        headers = {"Authorization": f"Bearer {self.secret}"}
        payload = {
            "email": email,
            "amount": amount,
            "currency": "NGN",
            "metadata": {"plan": plan}
        }
        if phone:
            payload["phone"] = phone
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                data = r.json()
                return data.get("data", {}), None
            return None, f"Paystack error: {r.status_code}"
        except Exception as e:
            return None, str(e)

    def verify_payment(self, reference: str) -> Optional[Dict]:
        url = f"{self.base_url}/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {self.secret}"}
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("data", {}).get("status") == "success":
                    return data["data"]
        except:
            pass
        return None

    def get_scans_for_plan(self, plan: str) -> int:
        plans = {
            "starter": 150,
            "pro": 300,
            "business": 1000,
            "enterprise": 5000,
            "10": 10,
            "25": 25,
            "60": 60,
            "250": 250,
            "unlimited": 9999,
        }
        return plans.get(plan, 0)
