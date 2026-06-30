import requests, os, time, json, subprocess
from colorama import Fore, Style, init

init(autoreset=True)

# --- CẤU HÌNH ---
CONFIG_FILE = "config_exTok.json"
BAD_JOBS_FILE = "bad_jobs.json"
BASE_URL = "https://api.extok.net/api"

def print_header(t): print(Fore.MAGENTA + Style.BRIGHT + f"\n=== {t} ===")

# Quản lý cấu hình
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"TOKEN": "", "ACCOUNTS": {}}

def save_config(data):
    with open(CONFIG_FILE, "w") as f: json.dump(data, f, indent=4)

# Quản lý Job lỗi
def load_bad_jobs():
    if os.path.exists(BAD_JOBS_FILE):
        try:
            with open(BAD_JOBS_FILE, "r") as f: return json.load(f)
        except: pass
    return []

def add_bad_job(job_id):
    bad_jobs = load_bad_jobs()
    if job_id not in bad_jobs:
        bad_jobs.append(job_id)
        with open(BAD_JOBS_FILE, "w") as f: json.dump(bad_jobs, f)

# --- LẤY DỮ LIỆU ---
def fetch_extok_accounts(headers):
    try:
        res = requests.get(f"{BASE_URL}/facebook-account?limit=100", headers=headers, timeout=10)
        return res.json().get("data", []) if res.status_code == 200 else []
    except: return []

# --- HÀM CHẠY JOB ---
def run_jobs(headers, uid, pkg, act):
    bad_jobs = load_bad_jobs()
    print_header(f"ĐANG CHẠY: {uid}")
    
    while True:
        try:
            res = requests.get(f"{BASE_URL}/facebook-jobs", params={"fb_id": uid, "limit": 1}, headers=headers, timeout=10).json()
            if res.get("status") == 200 and res.get("data"):
                job = res["data"][0]
                
                if job['id'] in bad_jobs: 
                    print(Fore.YELLOW + f"Bỏ qua Job {job['id']} (đã lưu trong danh sách lỗi).", end="\r")
                    continue
                
                print(Fore.GREEN + f"\n=> Job: {job['type']} | Link: {job['link']}")
                
                # Lệnh mở app/trình duyệt
                subprocess.run(['am', 'start', '-n', f'{pkg}/{act}', '-a', 'android.intent.action.VIEW', '-d', job["link"]], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                print(Fore.CYAN + "--------------------------------------------------")
                print(Fore.WHITE + "1. Thực hiện xong Job trong App/Trình duyệt")
                print(Fore.WHITE + "2. Quay lại đây nhấn lệnh:")
                act_user = input(Fore.YELLOW + "  [Enter]: Hoàn thành | [n]: Bỏ qua | [x]: Lưu lỗi: ").strip().lower()
                print(Fore.CYAN + "--------------------------------------------------")
                
                if act_user == 'x':
                    add_bad_job(job['id'])
                    bad_jobs.append(job['id'])
                    print(Fore.RED + f"Đã lưu Job {job['id']} vào file {BAD_JOBS_FILE}.")
                elif act_user == 'n':
                    requests.post(f"{BASE_URL}/facebook-jobs/skip", json={"job_id": job['id'], "fb_id": uid}, headers=headers)
                    print(Fore.YELLOW + "Đã bỏ qua Job này.")
                else:
                    resp = requests.post(f"{BASE_URL}/facebook-jobs/complete", json={"job_id": job['id'], "uid": uid, "success": True}, headers=headers).json()
                    if resp.get('status') == 200:
                        stats = resp.get("coin_statistics", {})
                        current_coin = stats.get("current_coin", "0")
                        pending_today = stats.get("coin_pending_today", "0")
                        
                        print(Fore.GREEN + f"✔ Xác nhận thành công!")
                        print(Fore.WHITE + f"   - Số dư hiện tại: {Fore.YELLOW}{current_coin} coin")
                        print(Fore.WHITE + f"   - Đang chờ duyệt hôm nay: {Fore.CYAN}{pending_today} coin")
                    else:
                        print(Fore.RED + "✘ Lỗi xác nhận với Server.")
            else:
                print(Fore.WHITE + "Đang đợi job mới...", end="\r")
                time.sleep(5)
        except Exception as e: print(Fore.RED + f"\nLỗi: {e}"); time.sleep(5)

# --- MENU CHÍNH ---
def main():
    data = load_config()
    if not data["TOKEN"]: data["TOKEN"] = input("Nhập JWT Token: ").strip(); save_config(data)
    headers = {"Authorization": f"Bearer {data['TOKEN']}", "Content-Type": "application/json"}
    
    print_header("MENU QUẢN LÝ")
    print("1. Chạy Job tự động")
    if input("Chọn: ") == '1':
        accounts = fetch_extok_accounts(headers)
        for i, acc in enumerate(accounts, 1):
            name = acc.get('facebook_name', 'Unknown')
            uid = acc.get('fb_id', 'N/A')
            print(f"{i}. {Fore.YELLOW}{Style.BRIGHT}{name}{Style.RESET_ALL} (ID: {Fore.CYAN}{uid}{Style.RESET_ALL})")
        
        idx = int(input("Chọn STT tài khoản: ")) - 1
        uid = accounts[idx].get('fb_id')
        
        if uid not in data["ACCOUNTS"] or not isinstance(data["ACCOUNTS"].get(uid), dict):
            print(Fore.YELLOW + "Cấu hình App/Trình duyệt:")
            pkg = input("Nhập Package (VD: com.facebook.litf hoặc mark.via.jd): ").strip() or "com.facebook.litf"
            
            if "facebook" in pkg: act = "com.facebook.lite.MainActivity"
            elif "via" in pkg: act = "mark.via.Shell"
            else: act = input("Nhập Activity (VD: mark.via.Shell): ").strip() or "com.facebook.lite.MainActivity"
            
            data["ACCOUNTS"][uid] = {"pkg": pkg, "act": act}
            save_config(data)
        
        cfg = data["ACCOUNTS"][uid]
        run_jobs(headers, uid, cfg["pkg"], cfg["act"])

if __name__ == "__main__":
    main()
