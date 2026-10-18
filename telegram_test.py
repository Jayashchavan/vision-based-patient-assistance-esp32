import requests

BOT_TOKEN = "8511867001:AAE0rSVL_rlku9tZAhuVEkAofmt6DyX4vOk"
CHAT_ID = "8127873527"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

try:
    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": "🚨 Winston: Patient needs assistance! Test alert."
        },
        timeout=10
    )

    print(response.status_code)
    print(response.text)
    response.raise_for_status()

except requests.RequestException as error:
    print("Error:", error)