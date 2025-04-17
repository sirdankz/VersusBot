# VersusBot
SoftEther VPN Discord Bot – PCB Slot and Virtual Hub Tracker

A Python bot that watches your Softether vpn logs over ssh and keeps your Discord server updated with who's connected and which PCB slots are in use. super handy for setups where you’ve got limited "slots" (like PCBs for arcade games) and need to track who’s using what — in real time.
---

## 🔧 What It Does

1. **Watches the logs**  
   Connects to your VPN server over SSH and tails the SoftEther log file to detect when users connect or disconnect.

2. **Assigns slots automatically**  
   As users connect, it gives them the next free PCB slot (1–4). When they disconnect, the slot gets freed up.

3. **Posts updates to Discord**  
   It sends a clean, single embedded message that shows:
   - Who’s using which slot
   - Which slots are still open

Example of the bot

╔═════════════ VPN Status - DEFAULT ═════════════╗

╠════════════════════════════════════════════════╣

║ PCB 1: [Empty]                    AVAILABLE ║

║ PCB 2: [Empty]                    AVAILABLE ║

║ PCB 3: [Empty]                    AVAILABLE ║

║ PCB 4: [Empty]                    AVAILABLE ║

╚════════════════════════════════════════════════╝

╔══════════════ VPN Status - TEST ═══════════════╗

╠════════════════════════════════════════════════╣

║ PCB 1: [Empty]                    AVAILABLE ║

║ PCB 2: [Empty]                    AVAILABLE ║

║ PCB 3: [Empty]                    AVAILABLE ║

║ PCB 4: [Empty]                    AVAILABLE ║

╚════════════════════════════════════════════════╝ 


4. **Keeps tracking even if things drop**  
   Handles network hiccups, reconnects, and automatically switches to the next log file each day.

---
====================================================================================
## 🚀 Setup Instructions

### Step 1: Install Requirements

Make sure Python and `pip` are installed.  
Then install the required packages:


pip install discord.py paramiko
py -m pip install discord.py paramiko

REMOTE_SERVER = "your-server-ip"

REMOTE_USER = "your-user"

REMOTE_PASSWORD = "your-password"

REMOTE_LOG_PATH = "/usr/local/softether/server_log"

VIRTUAL_HUB_NAME = "your-hub-name"

DISCORD_TOKEN = "your-token"

DISCORD_CHANNEL_ID = your-channel-id
=================================================

Here’s what each one does:

REMOTE_SERVER: The IP or hostname of your VPN server

REMOTE_USER: Your SSH login username

REMOTE_PASSWORD: The SSH password (or set up key auth if you want better security)

REMOTE_LOG_PATH: Path to your SoftEther logs (usually /usr/local/softether/server_log)

VIRTUAL_HUB_NAME: The exact name of your SoftEther virtual hub (case-sensitive)

DISCORD_TOKEN: Your bot token from the Discord Developer Portal

DISCORD_CHANNEL_ID: The numeric ID of the channel where the bot should post updates
