import asyncio
import re
import paramiko
import discord
from datetime import datetime

# --- CONFIG ---
REMOTE_SERVER = "Server-IP"
REMOTE_USER = "Your-User"
REMOTE_PASSWORD = "Password"
REMOTE_LOG_PATH = "/usr/local/softether/server_log"

# ✅ List of virtual hubs to monitor
VIRTUAL_HUB_NAMES = [
    "TEST-1",
    "TEST-2",
    # "TEST-3",
    # "TEST-4",
    # "TEST-5",
    # "TEST-6",
]

DISCORD_TOKEN = "token"
DISCORD_CHANNEL_ID = ID

CHECK_INTERVAL = 1
RECONNECT_INTERVAL = 10
LOG_ROTATION_CHECK_INTERVAL = 30

# --- DISCORD SETUP ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- HELPERS ---
def get_latest_log_filename(sftp):
    files = sftp.listdir(REMOTE_LOG_PATH)
    log_files = [f for f in files if re.match(r"vpn_\d{8}\.log", f)]
    latest = sorted(log_files)[-1] if log_files else None
    return f"{REMOTE_LOG_PATH}/{latest}" if latest else None

def connect_to_server():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(REMOTE_SERVER, username=REMOTE_USER, password=REMOTE_PASSWORD)
        print("✅  SSH connection established.")
        return ssh
    except Exception as e:
        print(f"❌  SSH connection failed: {e}")
        return None

def format_user_message(active_users_per_hub):
    TOP_LEFT = "╔"
    TOP_RIGHT = "╗"
    BOTTOM_LEFT = "╚"
    BOTTOM_RIGHT = "╝"
    HORIZONTAL = "═"
    VERTICAL = "║"
    T_RIGHT = "╠"
    T_LEFT = "╣"

    width = 50
    lines = []

    for hub_name in VIRTUAL_HUB_NAMES:
        title = f" VPN Status - {hub_name} "
        padding = (width - len(title)) // 2
        top_border = TOP_LEFT + HORIZONTAL * (padding - 1) + title + HORIZONTAL * (width - padding - len(title) - 1) + TOP_RIGHT
        lines.append(top_border)
        lines.append(T_RIGHT + HORIZONTAL * (width - 2) + T_LEFT)

        hub_users = active_users_per_hub.get(hub_name, {})
        for pcb_id in range(1, 5):
            user = next((u for u, pid in hub_users.items() if pid == pcb_id), None)
            if user:
                status = "🟢 CONNECTED"
                user_line = f"{VERTICAL} PCB {pcb_id}: {user[:20]:<20} {status:>16} {VERTICAL}"
            else:
                status = "⚪ AVAILABLE"
                user_line = f"{VERTICAL} PCB {pcb_id}: {'[Empty]':<20} {status:>16} {VERTICAL}"
            lines.append(user_line)

        lines.append(BOTTOM_LEFT + HORIZONTAL * (width - 2) + BOTTOM_RIGHT)
        lines.append("")  # spacing between hubs

    return "\n".join(lines)

# --- MAIN TRACKING FUNCTION ---
async def monitor_log(channel):
    active_users_per_hub = {hub: {} for hub in VIRTUAL_HUB_NAMES}
    message = await channel.send("🌐 Initializing VPN tracker...")

    while True:
        ssh = connect_to_server()
        if not ssh:
            await asyncio.sleep(RECONNECT_INTERVAL)
            continue

        try:
            sftp = ssh.open_sftp()
            current_log = get_latest_log_filename(sftp)
            if not current_log:
                print("❌  No log files found.")
                sftp.close()
                ssh.close()
                await asyncio.sleep(RECONNECT_INTERVAL)
                continue

            log_file = sftp.open(current_log, 'r')
            log_file.seek(0, 2)
            print(f"📄  Watching log: {current_log}")

            last_rotation_check = datetime.now()

            while True:
                now = datetime.now()
                if (now - last_rotation_check).total_seconds() >= LOG_ROTATION_CHECK_INTERVAL:
                    new_log = get_latest_log_filename(sftp)
                    if new_log and new_log != current_log:
                        print(f"🔁  Switching to new log file: {new_log}")
                        log_file.close()
                        current_log = new_log
                        log_file = sftp.open(current_log, 'r')
                        log_file.seek(0, 2)
                        print(f"📄  Now watching: {current_log}")
                    last_rotation_check = now

                line = log_file.readline()
                if not line:
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                # Login match
                login_match = re.search(r'\[HUB "([^"]+)"\].*?authenticated as user "([^"]+)"', line)
                if login_match:
                    hub, username = login_match.groups()
                    if hub in VIRTUAL_HUB_NAMES and username not in active_users_per_hub[hub]:
                        used_ids = set(active_users_per_hub[hub].values())
                        for pcb_id in range(1, 5):
                            if pcb_id not in used_ids:
                                active_users_per_hub[hub][username] = pcb_id
                                print(f"✅  Connected: {username} -> PCB ID {pcb_id} @ {hub}")
                                await message.edit(content=format_user_message(active_users_per_hub))
                                break

                # Logout match
                logout_match = re.search(r'\[HUB "([^"]+)"\] Session "SID-([^-"]+)-\d+": The session has been terminated', line)
                if logout_match:
                    hub, sid_user = logout_match.groups()
                    disconnect = None
                    if hub in VIRTUAL_HUB_NAMES:
                        for user in list(active_users_per_hub[hub]):
                            if sid_user.lower() in user.lower():
                                disconnect = user
                                break
                        if disconnect:
                            print(f"👋  Disconnected: {disconnect} @ {hub}")
                            del active_users_per_hub[hub][disconnect]
                            await message.edit(content=format_user_message(active_users_per_hub))

        except Exception as e:
            print(f"⚠️ Error while monitoring log file: {e}")
        finally:
            try:
                log_file.close()
                sftp.close()
                ssh.close()
            except:
                pass
            print(f"🔁  Reconnecting in {RECONNECT_INTERVAL} seconds...")
            await asyncio.sleep(RECONNECT_INTERVAL)

# --- DISCORD EVENT ---
@client.event
async def on_ready():
    print(f"🤖  Logged in as {client.user}")
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await monitor_log(channel)
    else:
        print("❌  Channel not found.")

# --- RUN BOT ---
if __name__ == "__main__":
    print("🚀  Starting VPN tracker bot...")
    client.run(DISCORD_TOKEN)
