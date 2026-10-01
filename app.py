from flask import Flask, request, jsonify, render_template
import socket
from urllib.parse import urlparse
import time
import threading
import requests
import os

app = Flask(__name__)

# سحب إعدادات تليجرام من المتغيرات في Railway
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# متغير لحفظ الحالة السابقة لضمان عدم إرسال رسائل متكررة
last_status = None

def check_socket(host, port, timeout=10.0):
    """دالة الفحص الأساسية"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return "شغال"
    except Exception:
        return "واقف"

def send_telegram_message(message):
    """دالة إرسال الرسالة لتليجرام مع طباعة السجلات لاكتشاف الأخطاء"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("تحذير: التوكن أو الآيدي غير موجود في المتغيرات (Variables)!")
        return 
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        # هذا السطر سيطبع رد تليجرام في سجلات Railway لمعرفة سبب الرفض
        print(f"محاولة إرسال لتليجرام | كود الحالة: {response.status_code} | الرد: {response.text}")
    except Exception as e:
        print("فشل الاتصال بسيرفر تليجرام:", e)

def monitor_host():
    """المراقب الذي يعمل في الخلفية كل 15 ثانية"""
    global last_status
    target_host = 'mobile4.bok-sd.com'
    target_port = 3443

    while True:
        current_status = check_socket(target_host, target_port)
        
        # إذا تغيرت الحالة عن الفحص السابق، أرسل رسالة
        if current_status != last_status:
            if current_status == "شغال":
                msg = "✅ <b>تطبيق بنكك الآن شغال</b>\nالخادم يستجيب للاتصال بشكل طبيعي."
            else:
                msg = "❌ <b>تطبيق بنكك الآن واقف</b>\nالخادم لا يستجيب."
            
            send_telegram_message(msg)
            last_status = current_status
        
        # انتظار 15 ثانية قبل الفحص التالي
        time.sleep(15)

# تشغيل المراقب في الخلفية فور تشغيل السيرفر
monitor_thread = threading.Thread(target=monitor_host, daemon=True)
monitor_thread.start()

@app.route('/')
def index():
    # عرض الواجهة
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    url_input = request.form.get('url', '').strip()
    if not url_input:
        return jsonify({'status': 'error', 'message': 'الرابط فارغ', 'details': ''})

    host = url_input
    port = 3443

    if '://' in host:
        parsed = urlparse(host)
        host = parsed.hostname
        port = parsed.port if parsed.port else 3443
    elif ':' in host:
        parts = host.split(':')
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            port = 3443

    host = host.replace('https://', '').replace('http://', '').split('/')[0]
    
    # استخدام نفس دالة الفحص للواجهة
    status = check_socket(host, port)
    
    if status == "شغال":
        return jsonify({'status': 'success', 'message': 'شغال', 'details': f'Socket Connection Established (Port {port} is OPEN)'})
    else:
        return jsonify({'status': 'error', 'message': 'التطبيق واقف', 'details': 'Socket Error: Connection Failed'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
