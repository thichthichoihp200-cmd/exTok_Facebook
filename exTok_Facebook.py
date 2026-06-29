import requests, os, time, json, subprocess
from colorama import Fore, Style, init

init(autoreset=True)

# --- CẤU HÌNH ---
CONFIG_FILE = "config_exTok.json"
BASE_URL = "https://api.extok.net/api"

def print_header(t): print(Fore.MAGENTA + Style.BRIGHT + f"\n=== {t} ===")
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"TOKEN": "", "ACCOUNTS": {}}

def save_config(data):
    with open(CONFIG_FILE, "w") as f: json.dump(data, f, indent=4)

# --- LẤY DỮ LIỆU ---
def fetch_extok_accounts(headers):
    try:
        res = requests.get(f"{BASE_URL}/facebook-account?limit=100", headers=headers, timeout=10)
        return res.json().get("data", []) if res.status_code == 200 else []
    except: return []

# --- HÀM CHẠY JOB ---
def run_jobs(headers, uid, pkg, act):
    bad_jobs = []
    print_header(f"ĐANG CHẠY: {uid}")
    
    while True:
        try:
            res = requests.get(f"{BASE_URL}/facebook-jobs", params={"fb_id": uid, "limit": 1}, headers=headers, timeout=10).json()
            if res.get("status") == 200 and res.get("data"):
                job = res["data"][0]
                if job['id'] in bad_jobs: continue
                
                print(Fore.GREEN + f"\n=> Job: {job['type']} | Link: {job['link']}")
                # Lệnh mở app/trình duyệt
                subprocess.run(['am', 'start', '-n', f'{pkg}/{act}', '-a', 'android.intent.action.VIEW', '-d', job["link"]], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Hướng dẫn thao tác
                print(Fore.CYAN + "--------------------------------------------------")
                print(Fore.WHITE + "1. Thực hiện xong Job trong App/Trình duyệt")
                print(Fore.WHITE + "2. Quay lại đây nhấn lệnh:")
                act_user = input(Fore.YELLOW + "  [Enter]: Hoàn thành | [n]: Bỏ qua | [x]: Lưu lỗi: ").strip().lower()
                print(Fore.CYAN + "--------------------------------------------------")
                
                if act_user == 'x':
                    bad_jobs.append(job['id'])
                    print(Fore.RED + f"Đã lưu Job {job['id']} vào danh sách bỏ qua.")
                elif act_user == 'n':
                    requests.post(f"{BASE_URL}/facebook-jobs/skip", json={"job_id": job['id'], "fb_id": uid}, headers=headers)
                    print(Fore.YELLOW + "Đã bỏ qua Job này.")
                else:
                    # Gửi xác nhận hoàn thành
                    resp = requests.post(f"{BASE_URL}/facebook-jobs/complete", json={"job_id": job['id'], "uid": uid, "success": True}, headers=headers).json()
                    if resp.get('status') == 200:
                        print(Fore.GREEN + "✔ Xác nhận thành công!")
                    else:
                        print(Fore.RED + "✘ Lỗi xác nhận với Server.")
            else:
                print(Fore.WHITE + "Đang đợi job mới...", end="\r")
                time.sleep(5)
        except Exception as e: print(Fore.RED + f"Lỗi: {e}"); time.sleep(5)

# --- MENU CHÍNH ---
def main():
    data = load_config()
    if not data["TOKEN"]: data["TOKEN"] = input("Nhập JWT Token: ").strip(); save_config(data)
    headers = {"Authorization": f"Bearer {data['TOKEN']}", "Content-Type": "application/json"}
    
    print_header("MENU QUẢN LÝ")
    print("1. Chạy Job tự động")
    if input("Chọn: ") == '1':
        accounts = fetch_extok_accounts(headers)
        for i, acc in enumerate(accounts, 1): print(f"{i}. {acc.get('facebook_name')} (ID: {acc.get('fb_id')})")
        
        idx = int(input("Chọn STT tài khoản: ")) - 1
        uid = accounts[idx].get('fb_id')
        
        # Xử lý cấu hình thông minh
        if uid not in data["ACCOUNTS"] or not isinstance(data["ACCOUNTS"].get(uid), dict):
            print(Fore.YELLOW + "Cấu hình App/Trình duyệt:")
            pkg = input("Nhập Package (VD: com.facebook.litf hoặc mark.via.jd): ").strip() or "com.facebook.litf"
            
            # Tự động gợi ý Activity
            if "facebook" in pkg: act = "com.facebook.lite.MainActivity"
            elif "via" in pkg: act = "mark.via.Shell"
            else: act = input("Nhập Activity (VD: mark.via.Shell): ").strip() or "com.facebook.lite.MainActivity"
            
            data["ACCOUNTS"][uid] = {"pkg": pkg, "act": act}
            save_config(data)
        
        cfg = data["ACCOUNTS"][uid]
        run_jobs(headers, uid, cfg["pkg"], cfg["act"])

if __name__ == "__main__":
    main()
