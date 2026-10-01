from flask import Flask, request, jsonify, render_template
import socket
from urllib.parse import urlparse

app = Flask(__name__)

@app.route('/')
def index():
    # عرض واجهة المستخدم
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    url_input = request.form.get('url', '').strip()
    
    if not url_input:
        return jsonify({'status': 'error', 'message': 'الرابط فارغ', 'details': ''})

    # استخراج الهوست والبورت من المدخلات
    host = url_input
    port = 3443 # المنفذ الافتراضي

    # تنظيف الرابط
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

    try:
        # محاولة الاتصال المباشر بالمنفذ
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10.0) # مهلة 10 ثواني
        s.connect((host, port))
        s.close()
        
        return jsonify({
            'status': 'success',
            'message': 'شغال',
            'details': f'Socket Connection Established (Port {port} is OPEN)'
        })
    except socket.timeout:
        return jsonify({
            'status': 'error',
            'message': 'التطبيق واقف',
            'details': 'Socket Error: Connection timed out'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'التطبيق واقف',
            'details': f'Socket Error: {str(e)}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
