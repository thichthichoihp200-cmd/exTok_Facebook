import requests
import os
import time
import json
from colorama import Fore, init

init(autoreset=True)

CONFIG_FILE = "accounts.json"
BASE_URL = "https://api.extok.net/api/v3"

def load_data():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_data(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def main():
    data = load_data()
    
    print(Fore.CYAN + "\n--- QUẢN LÝ TÀI KHOẢN ---")
    keys = list(data.keys())
    print("1. Chọn Key đã lưu\n2. Nhập Key mới")
    menu_choice = input("Lựa chọn (1/2): ")
    
    if menu_choice == '2':
        API_KEY = input("Nhập API Key mới: ").strip()
        if API_KEY not in data: data[API_KEY] = []
    else:
        if not keys: print(Fore.RED + "Chưa có Key!"); return
        for i, k in enumerate(keys): print(f"{i+1}. Key: {k[:5]}****")
        idx = int(input("Chọn số thứ tự Key: ")) - 1
        API_KEY = keys[idx]

    accs = data[API_KEY]
    print(Fore.CYAN + f"\n--- TÀI KHOẢN CỦA KEY {API_KEY[:5]}**** ---")
    for i, acc in enumerate(accs): 
        print(f"{i+1}. [{acc['name']}] FB_ID: {acc['fb_id']} | App: {acc['package']}")
    print(f"{len(accs)+1}. Thêm tài khoản mới")
    
    choice_acc = int(input("Chọn tài khoản để chạy: ")) - 1
    
    if choice_acc == len(accs):
        new_name = input("Nhập tên hiển thị: ").strip()
        new_id = input("Nhập FB_ID: ").strip()
        new_pkg = input("Nhập Package Name (VD: mark.via.gq): ").strip()
        data[API_KEY].append({"name": new_name, "fb_id": new_id, "package": new_pkg})
        save_data(data)
        selected = data[API_KEY][-1]
    else:
        selected = accs[choice_acc]

    NAME = selected['name']
    FB_ID = selected['fb_id']
    PACKAGE = selected['package']

    while True:
        params = {"key": API_KEY, "fb_id": FB_ID, "type": "like", "limit": 1}
        try:
            job_data = requests.get(f"{BASE_URL}/facebook-jobs", params=params, timeout=10).json()
        except: job_data = None
        
        if job_data and job_data.get("status") == 200 and len(job_data.get("data", [])) > 0:
            os.system('clear')
            job = job_data["data"][0]
            print(Fore.CYAN + "--- ĐANG LÀM JOB ---")
            # Hiển thị Tên + ID + Loại Job + Xu
            print(Fore.GREEN + f"Tài khoản: {NAME} ({FB_ID})")
            print(Fore.YELLOW + f"[+] Loại: {job['type'].upper()} | Xu: {job.get('fix_coin_job', 0)}")
            
            time.sleep(1)
            os.system(f'am start -n {PACKAGE}/mark.via.Shell -a android.intent.action.VIEW -d "{job["link"]}" > /dev/null 2>&1')
            
            confirm = input(Fore.MAGENTA + "=> Enter (Hoàn thành) | n (Bỏ qua): ").strip().lower()
            
            if confirm != 'n':
                payload = {"key": API_KEY, "job_id": job['id'], "fb_id": FB_ID, "success": True}
                res = requests.post(f"{BASE_URL}/facebook-jobs/complete", data=payload).json()
                print(Fore.GREEN + f"[SUCCESS] {res.get('message')}")
            else:
                payload = {"key": API_KEY, "job_id": job['id'], "fb_id": FB_ID}
                res = requests.post(f"{BASE_URL}/facebook-jobs/skip", data=payload).json()
                print(Fore.YELLOW + f"[SKIP] {res.get('message')}")
            
            time.sleep(1.5)
        else:
            print(Fore.WHITE + "[-] Chưa có job, chờ 30 giây...          ", end="\r")
            time.sleep(30)

if __name__ == "__main__":
    main()
