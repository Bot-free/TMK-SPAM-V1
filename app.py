from flask import Flask, jsonify, request
import requests
import mymessage_pb2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import random
import binascii
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# إعدادات التشفير
AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'
keys = set()  # مجموعة لتخزين المفاتيح الصالحة

# دالة إنشاء مفتاح UID عشوائي (لو احتجتها مستقبلاً)
def generate_random_uid_64():
    return random.randint(1, 9_223_372_036_854_775_807)

# دالة تشفير الرسالة
def encrypt_message(key, iv, plaintext):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(plaintext, AES.block_size)
    encrypted_message = cipher.encrypt(padded_message)
    return encrypted_message

# دالة جلب التوكينات - تصحيح: دالة عادية
def fetch_tokens():
    token_url = 'https://tmk-token-spam-33.vercel.app/api/token'
    response = requests.get(token_url)
    if response.status_code == 200:
        tokens = response.json()
        if isinstance(tokens, list):
            # استخراج قائمة التوكنات
            token_list = [item['token'] for item in tokens if 'token' in item]
            return token_list[:100]  # أخذ أول 100 توكن
        else:
            return []
    else:
        return []

# دالة إرسال طلبات الرسائل
def send_request(token, hex_encrypted_data):
    url = "https://clientbp.ggblueshark.com/RequestAddingFriend"
    payload = bytes.fromhex(hex_encrypted_data)
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/octet-stream",
        'Expect': "100-continue",
        'Authorization': f"Bearer {token}",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': "OB48"
    }

    response = requests.post(url, data=payload, headers=headers)
    return response.status_code == 200

# إضافة مفتاح جديد

# إرسال طلبات الرسائل باستخدام مفتاح
@app.route('/request', methods=['GET'])
def send_spam():
    user_id = request.args.get('uid')

    message = mymessage_pb2.MyMessage()
    message.field1 = 9797549324  # ثابت
    message.field2 = int(user_id)  # UID المرسل
    message.field3 = 22  # ثابت

    # تسلسل وتشفير الرسالة
    serialized_message = message.SerializeToString()
    encrypted_data = encrypt_message(AES_KEY, AES_IV, serialized_message)
    hex_encrypted_data = binascii.hexlify(encrypted_data).decode('utf-8')

    # جلب التوكنات
    tokens = fetch_tokens()
    if not tokens:
        return jsonify({"error": "No tokens available"}), 500

    # إرسال طلبات الصداقة
    success_count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda token: send_request(token, hex_encrypted_data), tokens)

    success_count = sum(1 for result in results if result)

    return jsonify({"message": f"SUCCESSFULLY SENT {success_count} FRIEND REQUESTS"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50066)
