
def normalize_phone(phone):
    """Convert Nigerian phone to international format for Paystack SMS."""
    if not phone:
        return "08000000000"
    
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    
    if phone.startswith("0"):
        return "234" + phone[1:]
    elif phone.startswith("234"):
        return phone
    else:
        return "234" + phone
