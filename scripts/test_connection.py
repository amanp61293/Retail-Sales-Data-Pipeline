
import requests

url = "https://idh-be.iowa.gov/api/v1/datasets/1263/rows.csv"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/csv",
}

try:
    response = requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=30
    )

    print("Status code:", response.status_code)
    print("Content type:", response.headers.get("Content-Type"))

    response.raise_for_status()
    print("Connection successful!")

    response.close()

except requests.RequestException as error:
    print("Connection failed:", error)
