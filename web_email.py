import smtplib
import os

PORT = 587
MY_EMAIL = "lukassofka@gmail.com" #os.environ.get("MY_EMAIL")
MY_PASSWORD = "crlcdwshzdebdqcw" #os.environ.get("MY_PASSWORD")

def send_email(name: str, email: str, phone_number:str, message: str):
    if not email:
        return False
    try:
        with smtplib.SMTP(host="smtp.gmail.com", port=PORT) as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=MY_EMAIL,
                msg=(f"Subject: Received message from {name}\n\nThe message:\n\n{message}\n\nContact info:\nEmail address: {email}\nPhone number: {phone_number}").encode("utf-8"))
        return True
    except(UnicodeEncodeError):
        return False