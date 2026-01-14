import requests

response = requests.get("direct-api-url-of-dynamic-content")
data = response.json()
print(data)