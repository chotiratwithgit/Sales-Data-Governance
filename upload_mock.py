import os
import requests
import json
import random
from dotenv import load_dotenv
from faker import Faker

# 1. โหลดกุญแจเข้าบ้าน
load_dotenv()
url = os.environ.get("SUPABASE_DB_URL")
key = os.environ.get("SUPABASE_KEY")

api_url = f"{url}/rest/v1/mock_pii_data"
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# 2. เตรียมเครื่องมือ Faker
# ตั้งค่าให้สร้างชื่อเป็นภาษาไทย และอีเมลเป็นภาษาอังกฤษ
fake_th = Faker('th_TH')
fake_en = Faker('en_US')

mock_data = []
print("กำลังใช้เวทมนตร์สร้างข้อมูลผู้ใช้งาน 200 คน...")

# 3. สั่งวนลูป 200 รอบ เพื่อสร้างข้อมูล 200 คน
for i in range(1, 201):
    # สุ่มเบอร์โทรศัพท์แบบไทยให้สมจริง
    prefix = random.choice(["08", "09", "06"])
    phone_number = prefix + str(random.randint(10000000, 99999999))
    
    # ประกอบร่างข้อมูลทีละคน
    row = {
        "order_id": f"ORD-{i:03d}",          # จะได้ ORD-001 ไล่ไปจนถึง ORD-200
        "customer_name": fake_th.name(),     # สุ่มชื่อ-นามสกุลไทย
        "phone": phone_number,               # เบอร์โทรที่สุ่มไว้
        "email": fake_en.email(),            # สุ่มอีเมลภาษาอังกฤษ
        "sales": random.randint(500, 25000)  # สุ่มยอดขายตั้งแต่ 500 ถึง 25,000
    }
    mock_data.append(row)

print("เตรียมข้อมูลเสร็จแล้ว! กำลังยิงขึ้น Supabase...")

# 4. สั่งยิงข้อมูล 200 แถว รวดเดียวขึ้น Cloud
response = requests.post(api_url, headers=headers, data=json.dumps(mock_data))

# 5. เช็คผลลัพธ์
if response.status_code == 201:
    print("✅ สำเร็จ! ยิงข้อมูล 200 แถวเข้า Database เรียบร้อยครับ")
    print("เข้าไปดูความอลังการของตารางคุณในเว็บ Supabase ได้เลย!")
else:
    print(f"❌ มีบางอย่างผิดพลาด: รหัส {response.status_code}")
    print(response.text)