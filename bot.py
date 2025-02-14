# -*- coding: utf-8 -*-
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import csv
import os
import threading
import requests
from langdetect import detect

# Credenciales de Telegram
BOT_TOKEN = "7974219914:AAHAK1tg7lLQ4OkRV2UBQUeuz-3XhsRt3VE"
GROUP_ESPANOL_ID = -1002341781692
GROUP_INGLES_ID = -1002286734461  # Reemplaza con el ID correcto
GROUP_AIRDROP_ID = -1002163471969

# Configurar conexión con Google Sheets
SHEET_CREDENTIALS = "bot-telegram-referidos-ab44d5b3c572.json"
SHEET_ID = "1XvtuOEH-TEvTovOPK_DhPg1hFytdo0YIhRr3HMKFRbI"

# Configurar bot de Telegram
bot = telebot.TeleBot(BOT_TOKEN)

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(SHEET_CREDENTIALS, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).sheet1

# Archivo CSV para almacenar referidos
CSV_FILE = "referidos.csv"
ID_FILE = "usuarios_ids.csv"
usuarios_ids = {}  # Diccionario para almacenar IDs de usuarios
moved_users = set()

# Crear los archivos CSV si no existen
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Usuario", "ID", "Referido Por"])

if not os.path.exists(ID_FILE):
    with open(ID_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Usuario", "ID"])

# Función para leer IDs guardados en CSV
def cargar_usuarios_ids():
    if os.path.exists(ID_FILE):
        with open(ID_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Saltar encabezado
            for row in reader:
                usuarios_ids[row[0].lower()] = row[1]  # Guardar en minúsculas para evitar errores
    print("📂 Lista de usuarios cargados en memoria:", usuarios_ids)

# Función para guardar IDs en CSV
def guardar_usuarios_ids():
    with open(ID_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Usuario", "ID"])
        for usuario, user_id in usuarios_ids.items():
            writer.writerow([usuario, user_id])

# Función para manejar nuevos usuarios y detectar idioma
@bot.message_handler(func=lambda message: message.text and message.text.lower() in ["participar", "participate"])
def enviar_informacion(message):
    username = message.from_user.username.lower() if message.from_user.username else f"user_{message.from_user.id}"
    usuarios_ids[f"@{username}"] = str(message.from_user.id)
    guardar_usuarios_ids()
    
    if "participate" in message.text.lower():
        idioma = "en"
    else:
        idioma = "es"
    
    if idioma == "es":
        bot.send_message(message.chat.id, """👋 ¡Bienvenido! Para participar en la promoción, sigue estos pasos:

1️⃣ Completa el formulario aquí: https://docs.google.com/forms/d/e/1FAIpQLScljV2XiOm_1aacLMsXGPK2QifIVeBAx76Ix_rcHbst9O1x2Q/viewform

Si no tienes un referido, coloca tu nombre.

2️⃣ Comparte tu usuario con amigos.

3️⃣ ¡Consigue 10 referidos y desbloquea el grupo del Airdrop! 🚀""")
    else:
        bot.send_message(message.chat.id, """👋 Welcome! To participate in the promotion, follow these steps:

1️⃣ Fill out the form here: https://docs.google.com/forms/d/e/1FAIpQLScljV2XiOm_1aacLMsXGPK2QifIVeBAx76Ix_rcHbst9O1x2Q/viewform

If you don't have a referrer, put your name!

2️⃣ Share your username with friends.

3️⃣ Get 10 referrals and unlock the Airdrop group! 🚀""")

# Función para contar referidos
def contar_referidos():
    conteo = {}
    datos = sheet.get_all_records()
    for row in datos:
        referido = "@" + row.get("¿Quién te refirió? @:", "").lstrip('@').strip().lower()
        if referido in conteo:
            conteo[referido] += 1
        else:
            conteo[referido] = 1
    print(f"📊 Conteo de referidos actualizado: {conteo}")
    return conteo

# Función para verificar referidos
def verificar_referidos():
    conteo = contar_referidos()
    for user, cantidad in conteo.items():
        if cantidad >= 10 and user not in moved_users:
            print(f"✅ {user} ha alcanzado 10 referidos. Moviéndolo al grupo Airdrop...")
            mover_usuario(user)

# Función para mover usuarios al grupo especial
def mover_usuario(user):
    try:
        user_key = f"@{user.lstrip('@').strip().lower()}"  # Convertir en minúsculas para buscar
        print(f"🔍 Buscando ID de {user_key} en usuarios_ids: {usuarios_ids}")
        user_id = usuarios_ids.get(user_key)
        
        if not user_id:
            return

        # Generar un link de invitación para el grupo especial
        invite_link = bot.create_chat_invite_link(GROUP_AIRDROP_ID, member_limit=1).invite_link

        # Enviar mensaje por privado
        bot.send_message(user_id, f"""🎉 Congratulations {user}! You have reached 10 referrals and unlocked access to the Airdrop group.

🔗 Join here: {invite_link}""")
        bot.send_message(GROUP_AIRDROP_ID, f"🚀 Welcome {user} to the Airdrop Group! / ¡Bienvenido {user} al Grupo del Airdrop!")
        moved_users.add(user)
    except Exception as e:
        print(f"Error al mover usuario: {e}")

# Iniciar el bot
if __name__ == "__main__":
    cargar_usuarios_ids()
    bot.send_message(GROUP_ESPANOL_ID, "🤖 Bot de referidos activo! Envía 'PARTICIPAR' a @referidnewtokenbot para registrarte y recibir el formulario.")
    bot.send_message(GROUP_INGLES_ID, "🤖 Referral bot is active! Send 'PARTICIPATE' to @referidnewtokenbot register and receive the form.")
    thread = threading.Thread(target=verificar_referidos, daemon=True)
    thread.start()
    bot.polling(none_stop=True)