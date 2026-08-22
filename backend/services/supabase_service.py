from supabase import create_client, Client
from backend.config import settings
from typing import Tuple, List, Dict, Any, Optional

class SupabaseService:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.service_key = settings.SERVICE_KEY
        self.client = create_client(self.url, self.key)
        self.service_client = create_client(self.url, self.service_key)

    def sign_up(self, email: str, password: str, first_name: str = "", last_name: str = "", phone: str = "") -> Tuple[Optional[Dict], Optional[str]]:
        try:
            res = self.client.auth.sign_up({"email": email, "password": password})
            if res.user:
                self.service_client.table("user_scans").insert({
                    "user_id": res.user.id,
                    "scans_remaining": 30,
                    "plan": "free"
                }).execute()
                if first_name or last_name or phone:
                    self.service_client.table("user_profiles").insert({
                        "user_id": res.user.id,
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": phone,
                        "verification_status": "pending"
                    }).execute()
            return {"id": res.user.id, "email": res.user.email}, None
        except Exception as e:
            return None, str(e)

    def sign_in(self, email: str, password: str) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            res = self.client.auth.sign_in_with_password({"email": email, "password": password})
            return {"id": res.user.id, "email": res.user.email}, None
        except Exception as e:
            return None, str(e)

    def sign_in_with_google(self, redirect_to: str = "") -> Tuple[Optional[str], Optional[str]]:
        try:
            options = {}
            if redirect_to:
                options["redirect_to"] = redirect_to
            res = self.client.auth.sign_in_with_oauth({"provider": "google", "options": options})
            return res.url, None
        except Exception as e:
            return None, str(e)

    def sign_out(self):
        self.client.auth.sign_out()

    def reset_password(self, email: str) -> Optional[str]:
        try:
            self.client.auth.reset_password_for_email(email)
            return None
        except Exception as e:
            return str(e)

    def get_scan_balance(self, user_id: str) -> int:
        res = self.service_client.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0].get("scans_remaining", 0)
        return 0

    def deduct_scans(self, user_id: str, amount: int, feature: str) -> Tuple[bool, int]:
        balance = self.get_scan_balance(user_id)
        if balance < amount:
            return False, balance
        new_balance = balance - amount
        self.service_client.table("user_scans").update({"scans_remaining": new_balance}).eq("user_id", user_id).execute()
        return True, new_balance

    def credit_scans_by_email(self, email: str, amount: int, plan: str):
        auth_user = self.service_client.auth.admin.get_user_by_email(email)
        if auth_user:
            balance = self.get_scan_balance(auth_user.id)
            new_balance = balance + amount
            self.service_client.table("user_scans").update({
                "scans_remaining": new_balance,
                "plan": plan
            }).eq("user_id", auth_user.id).execute()
            self.service_client.table("payment_history").insert({
                "user_id": auth_user.id,
                "amount": 0,
                "scans_added": amount,
                "plan": plan
            }).execute()

    def get_all_users(self) -> List[Dict]:
        users = []
        try:
            resp = self.service_client.auth.admin.list_users()
            if hasattr(resp, 'users'):
                users = resp.users
            elif isinstance(resp, list):
                users = resp
        except:
            pass
        return [{"id": u.id, "email": u.email} for u in users if hasattr(u, 'id')]

    def create_user(self, email: str, password: str, first_name: str, last_name: str, phone: str) -> Tuple[bool, Optional[str]]:
        try:
            res = self.service_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True
            })
            if res.user:
                self.service_client.table("user_profiles").insert({
                    "user_id": res.user.id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "verification_status": "pending"
                }).execute()
                self.service_client.table("user_scans").insert({
                    "user_id": res.user.id,
                    "scans_remaining": 30,
                    "plan": "free"
                }).execute()
                return True, None
            return False, "Failed to create user"
        except Exception as e:
            return False, str(e)

    def add_scans(self, user_id: str, amount: int) -> Tuple[bool, Optional[str]]:
        try:
            balance = self.get_scan_balance(user_id)
            new_balance = balance + amount
            self.service_client.table("user_scans").update({"scans_remaining": new_balance}).eq("user_id", user_id).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def approve_kyc(self, user_id: str):
        self.service_client.table("farmer_verifications").update({"status": "approved"}).eq("user_id", user_id).execute()

    def reject_kyc(self, user_id: str):
        self.service_client.table("farmer_verifications").update({"status": "rejected"}).eq("user_id", user_id).execute()
