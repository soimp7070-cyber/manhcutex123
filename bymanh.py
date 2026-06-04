import time
import os
import sys
import requests
from pystyle import Colors, Colorate, Write, System, Center
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn
import datetime

# Khởi tạo console rich
console = Console()

# Màu sắc (chỉ dùng cho text không qua rich, hoặc dùng style riêng)
end = "\033[0m"
trang = "\033[97m"
vang_sang = "\033[93m"
tim = "\033[95m"

# Style của rich cho các màu aura (dùng chính thức)
aura_styles = [
    "cyan", "magenta", "bright_magenta", "yellow", "green", 
    "bright_yellow", "bright_cyan", "bright_red", "red", 
    "bright_green", "blue"
]

os.system("cls" if os.name == "nt" else "clear")

# Hiệu ứng loading
with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
    progress.add_task(description="[cyan]HMK-TOOL Đang Khởi Động...", total=None)
    time.sleep(1.2)

System.Clear()

# Banner gradient (pystyle)
banner_ascii = r"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║    ██╗  ██╗███╗   ███╗██╗  ██╗      ████████╗ ██████╗  ██████╗ ██╗         ║
║    ██║  ██║████╗ ████║██║ ██╔╝      ╚══██╔══╝██╔═══██╗██╔═══██╗██║         ║
║    ███████║██╔████╔██║█████╔╝          ██║   ██║   ██║██║   ██║██║         ║
║    ██╔══██║██║╚██╔╝██║██╔═██╗          ██║   ██║   ██║██║   ██║██║         ║
║    ██║  ██║██║ ╚═╝ ██║██║  ██╗         ██║   ╚██████╔╝╚██████╔╝███████╗    ║
║    ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝         ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝    ║
║                                                                            ║
║                  ✨ HMK TOOL v10.0 - PREMIUM EDITION ✨                    ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
banner_gradient = Colorate.Vertical(Colors.rainbow, banner_ascii)
print(banner_gradient)
print()

# Thông tin thời gian
now = datetime.datetime.now()
date_str = now.strftime("%A, %d %B %Y")
time_str = now.strftime("%H:%M:%S")
info_text = Text()
info_text.append(f"📅 {date_str}", style="bold cyan")
info_text.append("   ⏰ ", style="bold white")
info_text.append(f"{time_str}", style="bold yellow")
rprint(Panel(info_text, border_style="bright_magenta", title="[bold green]⏳ SYSTEM STATUS[/bold green]", title_align="center"))

# Hàm tạo menu siêu đẹp không lỗi markup
def create_magic_menu(title, items, icon="✨"):
    table = Table(show_header=False, box=None, padding=(0, 2), border_style="bright_blue")
    table.add_column("ID", style="bold yellow", justify="center")
    table.add_column("TOOL", no_wrap=True)
    
    for idx, (code, desc) in enumerate(items):
        code_text = Text(f"{code}", style="bold yellow")
        style_name = aura_styles[idx % len(aura_styles)]
        desc_text = Text(desc, style=style_name)
        table.add_row(code_text, desc_text)
    
    title_text = Text(title, style="bold magenta")
    rprint(Panel(table, title=title_text, border_style="bright_cyan", title_align="center", padding=(0, 2)))
    print()

# Dữ liệu menu (đã xóa group4 và group8)
group1 = [
    ("1.1", "TDS TikTok V1 🔄"), ("1.2", "TDS Facebook V2"), ("1.3", "TDS Instagram ADB"),
    ("1.4", "TDS Instagram 🔄 "), ("1.5", "Tool TDS Facebook V3")
]
group2 = [("2.1", "Spam SMS Pro V1 📱"), ("2.2", "Spam SMS V2 📱")]
group3 = [
    ("3.1", "Tương tác chéo Facebook V1"), ("3.2", "Tương tác chéo FB Pro"),
    ("3.3", "Tool TTC Facebook Đa Luồng V2"), ("3.4", "Tool VTH Xworld Logic "), ("3.5", "Tương tác chéo PRO5 PC")
]
# group4 đã bị xóa
group5 = [
    ("5.1", "Buff Share FB"), ("5.2", "Reg Page Facebook"),
    ("5.3", "Nhập Code Xworld đa luồng🔄"), ("5.4", "Tool Bumx Facebook Vip V2"),
    ("5.5", "Tool TTC Pro5 Đa Luồng "), ("5.6", "Get Token Facebook (Khánh Huy) "),
    ("5.7", "Tool Rải Link Zalo")
]
group6 = [("6.1", "Auto TikTok ADB"), ("6.2", "Auto Pinterest Golike"), ("6.3", "Gộp Golike")]
group7 = [
    ("7.1", "Up Avatar đa luồng"), ("7.2", "Scan Via"), ("7.3", "Scan Facebook"),
    ("7.4", "Nuôi FB V1"), ("7.5", "Canh Code Xworld V1"),
    ("7.6", "Spam War Mess"), ("7.7", "Scan Acc Liên Quân")
]
# group8 đã bị xóa
group9 = [("7.8", "Scan Proxy"), ("00", "THOÁT TOOL")]

# In menu (bỏ qua group4 và group8)
create_magic_menu("📡 TRAO ĐỔI SUB", group1, "🔄")
create_magic_menu("📱 SPAM SMS", group2, "💣")
create_magic_menu("🔄 TƯƠNG TÁC CHÉO", group3, "💞")
create_magic_menu("🛠 BUFF SHARE & ENCODE", group5, "🎨")
create_magic_menu("❤️ AUTO GOLIKE", group6, "🔥")
create_magic_menu("🔧 CÔNG CỤ ĐA LOẠI", group7, "🛠️")
create_magic_menu("🔍 SCAN PROXY", group9, "🔎")

# Dòng nhập lệnh
print("╔" + "═" * 58 + "╗")
print(f"║{Center.XCenter('✨ NHẬP MÃ SỐ TOOL ✨', 58)}║")
print("╚" + "═" * 58 + "╝")
choice = input(f"\n{tim}[{trang}▶{tim}]{trang} Lựa chọn của bạn {vang_sang}➤ {end}")

# Xử lý lệnh (đã xóa các nhánh 4.x và 8.x)
if choice == '00':
    exec(requests.get('https://raw.githubusercontent.com/Khanh23047/thoattool/main/.github/workflows/main.yml').text)
elif choice == '1.1':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/bymanh.py').text)
elif choice == '1.2':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/TDSFB%20(1).py').text)
elif choice == '1.3':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/tdsig_adb.py').text)
elif choice == '1.4':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/ig1.py').text)
elif choice == '1.5':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteXbum/main/tdspold%20(2).py').text)
elif choice == '2.1':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/sms.py').text)
elif choice == '2.2':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/SMSHUY_1.py').text)
elif choice == '3.1':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/ttcfb%20(2).py').text)
elif choice == '3.2':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/ttcfbgoc.py').text)
elif choice == '3.3':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteXbum/main/ttcfb%20(2).py').text)
elif choice == '3.4':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcutex123/main/botvth.py').text)
elif choice == '3.5':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/TTCPRO5.py').text)
# Đã xóa các lệnh 4.x (4.1 -> 4.8)
elif choice == '5.1':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/buffshare.py').text)
elif choice == '5.2':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/manhdeptrairepg.py').text)
elif choice == '5.3':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/mc.py').text)
elif choice == '5.4':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteXbum/main/tool%20g%E1%BB%99p%20by%20m%E1%BA%A1nh%20cute.py').text)
elif choice == '5.5':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcutex123/main/ttc%20%C4%91a%20lu%E1%BB%93ng.py').text)
elif choice == '5.6':
    exec(requests.get('https://raw.githubusercontent.com/Khanh23047/Encode-Emoji-/main/p.py').text)
elif choice == '5.7':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteXbum/main/r%E1%BA%A3i%20link%20nh%C3%B3m%20zalo.py').text)
elif choice == '6.1':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/Dec_TikTokSTDI.py').text)
elif choice == '6.2':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/pint.py').text)
elif choice == '6.3':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/golike_gop_v8_1_fixed.py').text)
elif choice == '7.1':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/upavt_1_fixed_corrected.py').text)
elif choice == '7.2':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/scanv2.py').text)
elif choice == '7.3':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcutex123/main/get%20token%20fb.py').text)
elif choice == '7.4':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/nuoifb.py').text)
elif choice == '7.5':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/canhcode.py').text)
elif choice == '7.6':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/l.py').text)
elif choice == '7.7':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/lq.py').text)
# Đã xóa các lệnh 8.x (8.1 -> 8.6)
elif choice == '7.8':
    exec(requests.get('https://raw.githubusercontent.com/soimp7070-cyber/manhcuteX/main/ScanProxyVip.py').text)
else:
    Write.Print("\n[!] Lựa chọn không hợp lệ! Thoát...", Colors.red_to_yellow, interval=0.05)
    time.sleep(1)
    exit()
