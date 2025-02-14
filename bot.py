# -*- coding: utf-8 -*-
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import csv
import os
import threading
import json

# ? Configurar Logs para Railway
DEBUG = True

def log(msg):
    if DEBUG:
        print(msg)

# ? Credenciales de Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7974219914:AAHAK1tg7lLQ4OkRV2UBQUeuz-3XhsRt3VE"
GROUP_ESPANOL_ID = -1002341781692
GROUP_INGLES_ID = -1002286734461  
GROUP_AIRDROP_ID = -1002163471969

# ? Configurar conexi車n con Google Sheets
SHEET_CREDENTIALS = "bot-telegram-referidos.json"
SHEET_ID = "1XvtuOEH-TEvTovOPK_DhPg1hFytdo0YIhRr3HMKFRbI"

# ? Cargar credenciales desde variables de entorno (Railway)
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
if GOOGLE_CREDENTIALS:
    with open(SHEET_CREDENTIALS, "w") as json_file:
        json_file.write(GOOGLE_CREDENTIALS)
else:
    log("?? ERROR: No se encontraron credenciales de Google en Railway.")

# ? Configurar bot de Telegram
bot = telebot.TeleBot(BOT_TOKEN)

# ? Verificar conexi車n con Google Sheets
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(SHEET_CREDENTIALS, scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(SHEET_ID).sheet1
    log("? Conexi車n con Google Sheets exitosa.")
except Exception as e:
    log(f"? ERROR en conexi車n con Google Sheets: {e}")

# ? Archivos para guardar IDs
ID_FILE = "usuarios_ids.csv"
usuarios_ids = {}  
moved_users = set()

# ? Cargar IDs de usuarios
def cargar_usuarios_ids():
    if os.path.exists(ID_FILE):
        with open(ID_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  
            for row in reader:
                if len(row) >= 2:
                    usuario = row[0].strip().lower()
                    if not usuario.startswith("@"):
                        usuario = f"@{usuario}"
                    usuarios_ids[usuario] = row[1].strip()
    log(f"?? Lista de usuarios cargados: {usuarios_ids}")

# ? Guardar IDs en CSV
def guardar_usuarios_ids():
    with open(ID_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Usuario", "ID"])
        for usuario, user_id in usuarios_ids.items():
            writer.writerow([usuario, user_id])

# ? Registrar nuevos usuarios
@bot.message_handler(func=lambda message: message.text and message.text.lower() in ["participar", "participate"])
def enviar_informacion(message):
    username = message.from_user.username.lower() if message.from_user.username else f"user_{message.from_user.id}"
    if not username.startswith("@"):
        username = f"@{username}"

    usuarios_ids[username] = str(message.from_user.id)
    guardar_usuarios_ids()
    
    idioma = "en" if "participate" in message.text.lower() else "es"
    
    mensaje_es = """?? ?Bienvenido! Para participar en la promoci車n, sigue estos pasos:
1?? Completa el formulario aqu赤: https://docs.google.com/forms/d/e/1FAIpQLScljV2XiOm_1aacLMsXGPK2QifIVeBAx76Ix_rcHbst9O1x2Q/viewform
2?? Comparte tu usuario con amigos.
3?? ?Consigue 10 referidos y desbloquea el grupo del Airdrop! ??"""
    
    mensaje_en = """?? Welcome! To participate in the promotion, follow these steps:
1?? Fill out the form here: https://docs.google.com/forms/d/e/1FAIpQLScljV2XiOm_1aacLMsXGPK2QifIVeBAx76Ix_rcHbst9O1x2Q/viewform
2?? Share your username with friends.
3?? Get 10 referrals and unlock the Airdrop group! ??"""
    
    bot.send_message(message.chat.id, mensaje_es if idioma == "es" else mensaje_en)

# ? Contar referidos desde Google Sheets
def contar_referidos():
    conteo = {}
    try:
        datos = sheet.get_all_records()
        log(f"?? {len(datos)} registros obtenidos de Google Sheets.")
        for row in datos:
            referido = row.get("?Qui谷n te refiri車? @:", "").strip().lower()
            if referido:
                if not referido.startswith("@"):
                    referido = f"@{referido}"
                conteo[referido] = conteo.get(referido, 0) + 1
                log(f"?? {referido} tiene {conteo[referido]} referidos.")
    except Exception as e:
        log(f"? ERROR al obtener referidos: {e}")
    return conteo

# ? Verificar referidos cada 30 segundos
def verificar_referidos():
    while True:
        conteo = contar_referidos()
        for user, cantidad in conteo.items():
            if cantidad >= 10 and user not in moved_users:
                log(f"? {user} ha alcanzado 10 referidos. Movi谷ndolo al grupo Airdrop...")
                mover_usuario(user)
        time.sleep(30)

# ? Mover usuarios al grupo especial
def mover_usuario(user):
    try:
        user_key = user.lower().strip()
        if not user_key.startswith("@"):
            user_key = f"@{user_key}"

        user_id = usuarios_ids.get(user_key)
        if not user_id:
            log(f"?? ERROR: No se encontr車 el ID de {user}.")
            bot.send_message(GROUP_ESPANOL_ID, f"?? {user}, env赤a 'PARTICIPAR' en privado para registrarte.")
            return

        invite_link = bot.create_chat_invite_link(GROUP_AIRDROP_ID, member_limit=1).invite_link

        bot.send_message(user_id, f"""?? ?Felicidades {user}! Has alcanzado 10 referidos y puedes unirte al grupo Airdrop.
?? 迆nete aqu赤: {invite_link}""")

        bot.send_message(GROUP_AIRDROP_ID, f"?? ?Bienvenido {user} al Grupo del Airdrop!")

        moved_users.add(user)
    except Exception as e:
        log(f"? Error al mover usuario: {e}")

# ? Iniciar el bot
if __name__ == "__main__":
    cargar_usuarios_ids()
    bot.send_message(GROUP_ESPANOL_ID, "?? Bot de referidos activo! Envia 'PARTICIPAR' para registrarte.")
    
    thread = threading.Thread(target=verificar_referidos, daemon=True)
    thread.start()
    
    bot.polling(none_stop=True)
