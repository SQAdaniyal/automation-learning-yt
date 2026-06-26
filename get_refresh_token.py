"""
EK BAAR chalayein NeuralEdge ke YouTube refresh token ke liye.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

print("\n" + "=" * 60)
print("YEH GITHUB SECRET MEIN DALEIN:")
print("=" * 60)
print(f"YT_CLIENT_ID     = {creds.client_id}")
print(f"YT_CLIENT_SECRET = {creds.client_secret}")
print(f"YT_REFRESH_TOKEN = {creds.refresh_token}")
print("=" * 60)
