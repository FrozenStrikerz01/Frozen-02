import asyncio
import os
import time
import re
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ----------------- RENDER WEB SERVER PING -----------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"FROZEN 02 Bot is Alive and Running!")
    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Web server running on port {port}")
    server.serve_forever()

# Start web server in a background thread
threading.Thread(target=run_web_server, daemon=True).start()
# ----------------------------------------------------------

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

API_ID = 36932307
API_HASH = "f4bf98ccb466d9d6755c6dc1aae59d87"
BOT_TOKEN = "8790409386:AAEaoqELUtkVBUWrcdISYR04Piq_prq8GUc"

ADMIN_ID = 8969195021
VIP_GROUP_ID = -1003771099604

app = Client(
    "watermark_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    workers=16,
    max_concurrent_transmissions=4
)

global_session_start = 0

def get_video_duration(file_path):
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

async def send_synced_tracked_message(client, chat_id, body_text, keyboard=None, incoming_msg=None):
    global global_session_start
    try:
        current_time = time.time()
        if global_session_start == 0 or (current_time - global_session_start) > 300:
            global_session_start = current_time
            
        start_time = global_session_start
        total_duration = 300
        
        elapsed = current_time - start_time
        remaining = max(0, total_duration - elapsed)
        
        percent = int((elapsed / total_duration) * 100)
        percent = max(0, min(100, percent))
        
        if percent >= 100:
            mins_left = 0
        else:
            mins_left = int(remaining / 60) + (1 if (remaining % 60) > 0 else 0)
            mins_left = max(0, min(5, mins_left))
        
        bar_length = 10
        filled_length = int(bar_length * percent // 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        header = f"⚡ **AUTO-DELETE TIMER:** `[ ⏳ 0{mins_left} Min Remaining ]` `[{bar}] {percent}%`"
        full_text = f"{header}\n━━━━━━━━━━━━━━━━━━━━\n{body_text}"
        
        sent_msg = await client.send_message(chat_id, full_text, reply_markup=keyboard, protect_content=True)
        
        ids_to_track = [sent_msg.id]
        if incoming_msg:
            ids_to_track.append(incoming_msg.id)

        async def live_progress_and_delete():
            while True:
                await asyncio.sleep(5)
                cur_elapsed = time.time() - start_time
                cur_remaining = max(0, total_duration - cur_elapsed)
                
                cur_percent = int((cur_elapsed / total_duration) * 100)
                cur_percent = max(0, min(100, cur_percent))
                
                if cur_percent >= 100:
                    cur_mins = 0
                else:
                    cur_mins = int(cur_remaining / 60) + (1 if (cur_remaining % 60) > 0 else 0)
                    cur_mins = max(0, min(5, cur_mins))
                
                f_length = int(bar_length * cur_percent // 100)
                c_bar = '█' * f_length + '░' * (bar_length - f_length)
                
                new_header = f"⚡ **AUTO-DELETE TIMER:** `[ ⏳ 0{cur_mins} Min Remaining ]` `[{c_bar}] {cur_percent}%`"
                updated_text = f"{new_header}\n━━━━━━━━━━━━━━━━━━━━\n{body_text}"
                
                try:
                    await client.edit_message_text(chat_id, sent_msg.id, updated_text, reply_markup=keyboard)
                except Exception:
                    pass
                
                if cur_remaining <= 0 or cur_percent >= 100:
                    break
            
            for m_id in ids_to_track:
                try:
                    await client.delete_messages(chat_id, m_id)
                except Exception:
                    pass

        asyncio.create_task(live_progress_and_delete())
        return sent_msg
    except Exception:
        return None

async def send_admin_alert_and_delete(client, admin_text):
    try:
        admin_msg = await client.send_message(ADMIN_ID, admin_text)
        await asyncio.sleep(300)
        await admin_msg.delete()
    except Exception:
        pass

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    username = f"@{user.username}" if user.username else "No Username"
    user_id = user.id

    if user.id != ADMIN_ID:
        try:
            admin_alert = (
                f"🔔 **NEW BOT USER ACTIVITY (/start)**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Name: {name}\n"
                f"🌐 Username: {username}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"⏳ *This alert will auto-delete in 5 minutes.*"
            )
            asyncio.create_task(send_admin_alert_and_delete(client, admin_alert))
        except Exception:
            pass

        body = (
            f"🌟 **WELCOME TO VIP MEMBER PORTAL** 🌟\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👋 Hello **{name}**, Welcome to our exclusive community!\n\n"
            f"🤖 I am **FROZEN 02**, your dedicated assistant here. This space is designed to give you secure access to top-tier Westland game mods and LiP tools safely.\n\n"
            f"🔒 **Security Note:** All media shared here is heavily protected. Direct downloads, forwarding, or saving to gallery are restricted for maximum privacy.\n\n"
            f"📌 Please make sure to check the group rules and guidelines to ensure a safe and smooth experience! 🚀"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 View VIP Rules", callback_data="show_rules")],
            [InlineKeyboardButton("🛠️ Help & Support", callback_data="show_help")]
        ])
        await send_synced_tracked_message(client, message.chat.id, body, keyboard, message)
        return
        
    await message.reply_text("👋 Welcome back, Boss! Send me any video, and I will watermark and upload it to the VIP group securely. 🚀")

@app.on_message(filters.command("rules"))
async def rules_command(client, message):
    user = message.from_user
    name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    username = f"@{user.username}" if user.username else "No Username"
    user_id = user.id

    if user.id != ADMIN_ID:
        try:
            admin_alert = (
                f"🔔 **NEW BOT USER ACTIVITY (/rules)**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Name: {name}\n"
                f"🌐 Username: {username}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"⏳ *This alert will auto-delete in 5 minutes.*"
            )
            asyncio.create_task(send_admin_alert_and_delete(client, admin_alert))
        except Exception:
            pass

    body = (
        f"⚠️ **VIP GROUP RULES & REGULATIONS:**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ **Never test codes on your main account!** Always use a brand new secondary account for safety.\n\n"
        f"2️⃣ **Complete Chapters 1 to 3 in Westland.** You must finish these chapters first; otherwise, significant game changes and errors may occur.\n\n"
        f"3️⃣ **Anti-Ban Setup:** Complete levels 1 through 30 before enabling any anti-ban features.\n\n"
        f"4️⃣ **Use Code Safely:** Always enable the Anti-Ban protection *before* applying any game codes.\n\n"
        f"5️⃣ **Avoid Overuse:** No matter how strong the anti-ban is, abusing or overusing codes will result in a permanent account ban. Please be extremely careful!\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Read everything carefully and follow the steps to stay safe!"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠️ Help & Support", callback_data="show_help")]
    ])
    await send_synced_tracked_message(client, message.chat.id, body, keyboard, message)

@app.on_message(filters.command("help"))
async def help_command(client, message):
    user = message.from_user
    name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    username = f"@{user.username}" if user.username else "No Username"
    user_id = user.id

    if user.id != ADMIN_ID:
        try:
            admin_alert = (
                f"🔔 **NEW BOT USER ACTIVITY (/help)**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Name: {name}\n"
                f"🌐 Username: {username}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"⏳ *This alert will auto-delete in 5 minutes.*"
            )
            asyncio.create_task(send_admin_alert_and_delete(client, admin_alert))
        except Exception:
            pass

    body = (
        f"🛠️ **FROZEN 02 - HELP & SUPPORT** 🛠️\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 **Important Note on Privacy:** Due to the high-security protection of this VIP group, **no one (including the group owner/admin)** can download, forward, share, or save the videos to their gallery.\n\n"
        f"⚠️ If you face any issues or errors while following the steps, please check the group rules carefully. 🚀"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu / Start", callback_data="show_start")]
    ])
    await send_synced_tracked_message(client, message.chat.id, body, keyboard, message)

@app.on_chat_member_updated()
def welcome_new_member(client, chat_member: ChatMemberUpdated):
    if chat_member.chat.id == VIP_GROUP_ID:
        if chat_member.new_chat_member and not chat_member.old_chat_member:
            user = chat_member.new_chat_member.user
            
            if user.is_self:
                return
                
            name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
            username = f"@{user.username}" if user.username else "No Username"
            user_id = user.id
            
            body = (
                f"✨ **WELCOME TO VIP MEMBER GROUP!** ✨\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👋 Hi {name}, Welcome aboard to our exclusive VIP family!\n\n"
                f"💛 **Name:** {name}\n"
                f"💛 **Username:** {username}\n"
                f"💛 **ID:** {user_id}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 I am Frozen 02, your dedicated assistant in this VIP Member Group. I am here to guide you through using the LiP Tool for Westland game mods safely.\n\n"
                f"🔒 *Note: Due to high security, videos in this group cannot be downloaded, forwarded, or saved to gallery (even by the owner).* \n\n"
                f"📌 Please check the group rules and guidelines using the buttons below before proceeding! 🚀"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📜 View Rules", callback_data="show_rules")],
                [InlineKeyboardButton("🛠️ Help & Support", callback_data="show_help")]
            ])
            asyncio.create_task(send_synced_tracked_message(client, chat_member.chat.id, body, keyboard))

@app.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    if callback_query.data == "show_rules":
        body = (
            f"⚠️ **VIP GROUP RULES & REGULATIONS:**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ **Never test codes on your main account!** Always use a brand new secondary account for safety.\n\n"
            f"2️⃣ **Complete Chapters 1 to 3 in Westland.** You must finish these chapters first; otherwise, significant game changes and errors may occur.\n\n"
            f"3️⃣ **Anti-Ban Setup:** Complete levels 1 through 30 before enabling any anti-ban features.\n\n"
            f"4️⃣ **Use Code Safely:** Always enable the Anti-Ban protection *before* applying any game codes.\n\n"
            f"5️⃣ **Avoid Overuse:** No matter how strong the anti-ban is, abusing or overusing codes will result in a permanent account ban. Please be extremely careful!\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Read everything carefully and follow the steps to stay safe!"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠️ Help & Support", callback_data="show_help")]
        ])
        await callback_query.answer(text="Opening Rules...", show_alert=False)
        await send_synced_tracked_message(client, callback_query.message.chat.id, body, keyboard, incoming_msg=callback_query.message)

    elif callback_query.data == "show_help":
        body = (
            f"🛠️ **FROZEN 02 - HELP & SUPPORT** 🛠️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 **Important Note on Privacy:** Due to the high-security protection of this VIP group, **no one (including the group owner/admin)** can download, forward, share, or save the videos to their gallery.\n\n"
            f"⚠️ If you face any issues or errors while following the steps, please check the group rules carefully. 🚀"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Main Menu / Start", callback_data="show_start")]
        ])
        await callback_query.answer(text="Opening Help...", show_alert=False)
        await send_synced_tracked_message(client, callback_query.message.chat.id, body, keyboard, incoming_msg=callback_query.message)

    elif callback_query.data == "show_start":
        user = callback_query.from_user
        name = user.first_name
        body = (
            f"🌟 **WELCOME TO VIP MEMBER PORTAL** 🌟\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👋 Hello **{name}**, Welcome to our exclusive community!\n\n"
            f"🤖 I am **FROZEN 02**, your dedicated assistant here. This space is designed to give you secure access to top-tier Westland game mods and LiP tools safely.\n\n"
            f"🔒 **Security Note:** All media shared here is heavily protected. Direct downloads, forwarding, or saving to gallery are restricted for maximum privacy.\n\n"
            f"📌 Please make sure to check the group rules and guidelines to ensure a safe and smooth experience! 🚀"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 View VIP Rules", callback_data="show_rules")],
            [InlineKeyboardButton("🛠️ Help & Support", callback_data="show_help")]
        ])
        await callback_query.answer(text="Opening Start Menu...", show_alert=False)
        await send_synced_tracked_message(client, callback_query.message.chat.id, body, keyboard, incoming_msg=callback_query.message)

last_group_percent = -1

async def group_progress_callback(current, total, group_msg, video_title):
    global last_group_percent
    percent = int((current / total) * 100)
    
    if percent >= last_group_percent + 5 or current == total:
        last_group_percent = percent
        try:
            bar_length = 10
            filled_length = int(bar_length * percent // 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            await group_msg.edit_text(
                f"⚡ **UPLOADING SOON:** `[ {bar} ] {percent}%`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📹 **Title:** {video_title}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Please wait, the protected video is being uploaded to VIP.*"
            )
        except Exception:
            pass

@app.on_message(filters.video | filters.document)
async def add_watermark(client, message):
    if message.from_user.id != ADMIN_ID:
        await message.reply_text("⛔ You are not authorized to use this bot!")
        return

    global last_group_percent
    last_group_percent = -1

    msg = await message.reply_text("⚡ **UPLOADING SOON:** `[ [░░░░░░░░░░] 0% ]`")
    file_path = None
    output_path = None
    
    video_title = message.caption if message.caption else "Exclusive VIP Mod Video"
    
    group_msg = None
    try:
        group_msg = await client.send_message(
            VIP_GROUP_ID,
            f"⚡ **UPLOADING SOON:** `[ [░░░░░░░░░░] 0% ]`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📹 **Title:** {video_title}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Please wait, the protected video is being uploaded to VIP.*"
        )
    except Exception:
        pass

    try:
        last_dl_percent = -1
        def download_progress(current, total):
            nonlocal last_dl_percent
            percent = int((current / total) * 100)
            if percent >= last_dl_percent + 5 or current == total:
                last_dl_percent = percent
                bar_length = 10
                filled_length = int(bar_length * percent // 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            msg.edit_text(f"⚡ **UPLOADING SOON:** `[ [{bar}] {percent}% ]`"),
                            loop
                        )
                except Exception:
                    pass

        file_path = await message.download(progress=download_progress)
        await msg.edit_text("⚡ **UPLOADING SOON:** `[ [██████████] 100% ]`")
        
        file_ext = os.path.splitext(file_path)[1]
        output_path = f"watermarked_{message.id}{file_ext}"
        watermark_text = "FROZEN STRIKER" 
        total_duration = get_video_duration(file_path)
        
        command = [
            "ffmpeg", "-y", "-i", file_path,
            "-threads", "0",
            "-vf", f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,drawtext=text='{watermark_text}':fontcolor=white:fontsize=28:box=1:boxcolor=black@0.5:boxborderw=6:x=15:y=15,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy", output_path
        ]
        
        process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)
        
        last_ffmpeg_update = 0
        last_ff_percent = -1
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if "out_time_ms=" in line or "time=" in line:
                if total_duration > 0:
                    try:
                        time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
                        if time_match:
                            hours, minutes, seconds = map(float, time_match.groups())
                            current_time = hours * 3600 + minutes * 60 + seconds
                            percent = int(min(100.0, (current_time / total_duration) * 100))
                            
                            now = time.time()
                            if (percent >= last_ff_percent + 5 or percent == 100) and (now - last_ffmpeg_update > 2):
                                last_ffmpeg_update = now
                                last_ff_percent = percent
                                bar_length = 10
                                filled_length = int(bar_length * percent // 100)
                                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                                await msg.edit_text(f"⚡ **UPLOADING SOON:** `[ [{bar}] {percent}% ]`")
                    except Exception:
                        pass
                        
        process.wait()
        if process.returncode != 0:
            raise Exception("FFmpeg processing failed.")
        
        await msg.edit_text("⚡ **UPLOADING SOON:** `[ [██████████] 100% ]`")
        
        original_caption = message.caption if message.caption else ""
        my_branding = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💛 Name: FROZEN STRIKER\n"
            "💛 Username: @BLACKSUNGOD05"
        )
        
        if original_caption:
            caption_text = original_caption + "\n" + my_branding
        else:
            caption_text = my_branding.strip()
        
        await client.send_video(
            VIP_GROUP_ID, 
            output_path, 
            caption=caption_text,
            protect_content=True,
            progress=group_progress_callback,
            progress_args=(group_msg, video_title)
        )
        
        try:
            if group_msg:
                await group_msg.delete()
        except Exception:
            pass
        
        try:
            await msg.delete()
        except Exception:
            pass
            
        try:
            await message.delete()
        except Exception:
            pass
        
    except Exception as z:
        try:
            await msg.edit_text(f"❌ An error occurred: {z}")
            if group_msg:
                await group_msg.edit_text(f"❌ Video upload failed due to an error.")
        except Exception:
            pass
            
    finally:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        try:
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
        except Exception:
            pass

print("FROZEN 02 Bot with Render Web Server Support Running! 🚀")
app.run()
