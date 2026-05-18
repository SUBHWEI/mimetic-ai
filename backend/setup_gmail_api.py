"""
Script de configuracion unica para obtener el refresh token de Gmail API.
Ejecutar UNA SOLA vez en local:

    python setup_gmail_api.py

Sigue las instrucciones en pantalla.
"""
import json
import urllib.request
import urllib.parse

CLIENT_ID = input("Pega el GMAIL_API_CLIENT_ID: ").strip()
CLIENT_SECRET = input("Pega el GMAIL_API_CLIENT_SECRET: ").strip()

SCOPE = "https://www.googleapis.com/auth/gmail.send"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

auth_url = (
    "https://accounts.google.com/o/oauth2/v2/auth?"
    + urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    })
)

print("\n" + "=" * 60)
print("1. Abre esta URL en el navegador:")
print("=" * 60)
print(auth_url)
print("\n2. Inicia sesion con mimeticvalidated@gmail.com")
print("3. Da clic en 'Continuar' (puede salir 'App not verified', ignoralo)")
print("4. Copia el codigo que aparece y pegalo aqui abajo")
print("=" * 60)

auth_code = input("\nPega el codigo de autorizacion: ").strip()

data = urllib.parse.urlencode({
    "code": auth_code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
}).encode()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

with urllib.request.urlopen(req) as resp:
    token_data = json.loads(resp.read())

refresh_token = token_data.get("refresh_token")
if not refresh_token:
    print("\nERROR: No se obtuvo refresh token.")
    print("Asegurate de usar la cuenta mimeticvalidated@gmail.com")
    print("y que la pantalla de consentimiento muestre 'Google' no una cuenta especifica.")
    exit(1)

print("\n" + "=" * 60)
print("REFRESH TOKEN (copia esto a Render):")
print("=" * 60)
print(refresh_token)
print("=" * 60)
print("\nAgrega estas 3 variables a Render > Environment:")
print(f"  GMAIL_API_CLIENT_ID = {CLIENT_ID}")
print(f"  GMAIL_API_CLIENT_SECRET = {CLIENT_SECRET}")
print(f"  GMAIL_API_REFRESH_TOKEN = {refresh_token}")
