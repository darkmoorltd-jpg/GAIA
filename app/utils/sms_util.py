import requests
import streamlit as st


def send_sms(phone, message):
    """Send SMS via Termii."""
    try:
        api_key = st.secrets["termii"]["api_key"]
    except BaseException:
        api_key = "tlv_X4pCCI6rCP7B8ovuHztPQhtVXo91Y0VQTF-pB8jF9xw"  # Fallback

    # Normalize phone
    if not phone:
        return False, "No phone number"
    phone = phone.replace("+", "").replace(" ", "").strip()
    if phone.startswith("0"):
        phone = "234" + phone[1:]
    elif not phone.startswith("234"):
        phone = "234" + phone

    url = "https://api.ng.termii.com/api/sms/send"
    payload = {
        "api_key": api_key,
        "to": phone,
        "from": "GAIA",
        "sms": message,
        "type": "plain",
        "channel": "generic",
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            return True, None
        return False, f"Termii: {resp.status_code}"
    except Exception as e:
        return False, str(e)


def send_payment_receipt_sms(phone, amount, reference, plan_name):
    """Send payment receipt SMS with amount and reference."""
    message = f"GAIA: Payment successful! {plan_name} activated. Amount: N{
        amount:,.2f}. Ref: {reference}. Thank you!"
    return send_sms(phone, message)
