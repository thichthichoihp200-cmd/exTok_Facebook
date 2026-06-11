import requests
import os
import time
import json
import subprocess
import re
from colorama import Fore, Style, init

# Khởi tạo màu sắc
init(autoreset=True)

# --- CÁC TÊN FILE ĐÃ ĐƯỢC ĐỔI ---
CONFIG_FILE = "config_exTok.json"
ERROR_FILE = "error_jobs_exTok.json"
BASE_URL = "https://api.extok.net/api"

# --- HÀM HỖ TRỢ MÀU SẮC ---
def print_header(text):
    print(Fore.MAGENTA + Style.BRIGHT + f"\n=== {text} ===")

def print_success(text):
    print(Fore.GREEN + Style.BRIGHT + f"[✅] {text}")

def print_error(text):
    print(Fore.RED + Style.BRIGHT + f"[!] {text}")

# --- QUẢN LÝ CẤU HÌNH ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: return json.load(f)
            except: return {"TOKEN": "", "ACCOUNTS": {}}
    return {"TOKEN": "", "ACCOUNTS": {}}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- QUẢN LÝ JOB LỖI ---
def load_error_jobs():
    if os.path.exists(ERROR_FILE):
        with open(ERROR_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []

def save_error_job(job_id):
    errors = load_error_jobs()
    if job_id not in errors:
        errors.append(job_id)
        with open(ERROR_FILE, "w") as f:
            json.dump(errors, f)

def extract_uid(url_or_uid):
    patterns = [r"id=(\d+)", r"facebook\.com/(\d+)"]
    for pattern in patterns:
        match = re.search(pattern, url_or_uid)
        if match:
            return match.group(1)
    return url_or_uid.strip()

# --- HÀM XỬ LÝ JOB ---
def run_jobs(headers, uid, package):
    print_header(f"ĐANG CHẠY JOB CHO UID: {uid}")
    print(Fore.YELLOW + f"Trình duyệt: {package}")
    
    while True:
        try:
            params = {"fb_id": uid, "limit": 1}
            res = requests.get(f"{BASE_URL}/facebook-jobs", params=params, headers=headers, timeout=10).json()
            
            if res.get("status") == 200 and res.get("data"):
                job = res["data"][0]
                job_id = job['id']
                
                # Kiểm tra job lỗi
                if job_id in load_error_jobs():
                    print(Fore.RED + f"[-] Job {job_id} đã nằm trong danh sách lỗi, đang bỏ qua...")
                    requests.post(f"{BASE_URL}/facebook-jobs/skip", json={"job_id": job_id, "fb_id": uid}, headers=headers)
                    time.sleep(2)
                    continue

                print(Fore.GREEN + f"\n=> Loại Job: {job['type']} | Link: {job['link']}")
                print(Fore.YELLOW + ">>> Đang chờ 2 giây để mở trình duyệt...", end="\r")
                time.sleep(2)
                
                subprocess.run(['am', 'start', '-n', f'{package}/mark.via.Shell', '-a', 'android.intent.action.VIEW', '-d', job["link"]],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                choice = input(Fore.MAGENTA + "\n[Enter] Hoàn thành | [n] Bỏ qua | [x] Lỗi & Bỏ qua | [q] Thoát: ").lower()
                
                if choice == 'q': break
                
                if choice == 'x':
                    save_error_job(job_id)
                    requests.post(f"{BASE_URL}/facebook-jobs/complete", json={"job_id": job_id, "uid": uid, "success": False}, headers=headers)
                    print_error("Đã lưu job lỗi vào danh sách đen.")
                elif choice == 'n':
                    requests.post(f"{BASE_URL}/facebook-jobs/skip", json={"job_id": job_id, "fb_id": uid}, headers=headers)
                else:
                    resp = requests.post(f"{BASE_URL}/facebook-jobs/complete", json={"job_id": job_id, "uid": uid, "success": True}, headers=headers).json()
                    
                    if resp.get('status') == 200:
                        msg = resp.get('message', 'Thành công')
                        coin = resp.get('data', {}).get('coin', '0')
                        total = resp.get('coin_statistics', {}).get('current_coin', '0')
                        count = resp.get('count_jobs_today', '0')
                        
                        print_success(f"{msg}")
                        print(Fore.YELLOW + "--- THỐNG KÊ ---")
                        print(Fore.CYAN + f"Xu cộng: {coin} | Tổng xu: {total} | Job hôm nay: {count}")
                    else:
                        print_error(f"Lỗi từ server: {resp.get('message')}")
            else:
                print(Fore.WHITE + "Chưa có job, đợi 30s...", end="\r")
                time.sleep(30)
        except Exception as e:
            print_error(f"Lỗi hệ thống: {e}")
            time.sleep(10)

# --- HÀM MAIN ---
def main():
    data = load_config()
    if not data["TOKEN"]:
        data["TOKEN"] = input(Fore.YELLOW + "Nhập JWT Token: ").strip()
        save_config(data)
    
    while True:
        print_header("QUẢN LÝ TÀI KHOẢN")
        print(f"{Fore.CYAN}1.{Style.RESET_ALL} Thêm tài khoản | {Fore.CYAN}2.{Style.RESET_ALL} Chọn làm Job | {Fore.CYAN}3.{Style.RESET_ALL} Thoát")
        c = input("Chọn: ")
        
        if c == '1':
            input_val = input("Nhập Link hoặc UID: ").strip()
            uid = extract_uid(input_val)
            pkg = input("Nhập Package Name (ví dụ: mark.via.gp): ").strip()
            data["ACCOUNTS"][uid] = pkg
            save_config(data)
            print_success(f"Đã thêm: {uid}")
        elif c == '2':
            keys = list(data["ACCOUNTS"].keys())
            for i, uid in enumerate(keys, 1): 
                print(f"{Fore.YELLOW}{i}.{Style.RESET_ALL} {uid} -> {Fore.GREEN}{data['ACCOUNTS'][uid]}")
            
            c_in = input("Chọn STT hoặc dán Link Facebook: ").strip()
            # Xử lý chọn
            if c_in.isdigit() and int(c_in) <= len(keys):
                uid = keys[int(c_in)-1]
            else:
                uid = extract_uid(c_in)
            
            if uid in data["ACCOUNTS"]:
                run_jobs({"Authorization": f"Bearer {data['TOKEN']}", "Content-Type": "application/json"}, uid, data["ACCOUNTS"][uid])
            else:
                print_error("Không tìm thấy tài khoản!")
        elif c == '3': break

if __name__ == "__main__":
    main()
