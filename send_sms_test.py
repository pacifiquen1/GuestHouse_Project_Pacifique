from decouple import config
import africastalking

# Load credentials from .env
username = config("AT_USERNAME")       # sandbox for testing
api_key = config("AT_API_KEY")         # your long Africa's Talking key
recipient = config("AT_PHONE_NUMBER")  # your verified phone number

# Initialize SDK
africastalking.initialize(username, api_key)
sms = africastalking.SMS

# Send SMS
response = sms.send(
    "Hello! 🚀 This is a test SMS from your Guest House app.",
    [recipient]  # recipient must be inside a list
)

print("Message response:", response)
