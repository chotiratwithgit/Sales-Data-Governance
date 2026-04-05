# Data Governance Sales Portal

แดชบอร์ดตัวอย่างสำหรับงาน Data Governance และการปกปิดข้อมูลส่วนบุคคล (PDPA) บนข้อมูลยอดขาย โดยใช้ `Streamlit` เป็นหน้าบ้าน และ `Supabase PostgreSQL` เป็นแหล่งข้อมูลหลัก

## Live App

Streamlit Cloud: https://sales-data-governance-7awi3zwxnnbnvpjfwwgc5p.streamlit.app/

โปรเจ็กต์นี้มี 2 ส่วนหลัก:

- `mask_app.py` สำหรับแสดงผล dashboard, filtering, reporting, data quality และ pipeline health
- `upload_mock.py` สำหรับสร้าง mock data แล้วส่งขึ้นตาราง `mock_pii_data`

## Features

- แสดงภาพรวมข้อมูลยอดขายในรูปแบบ dashboard
- ค้นหาและกรองข้อมูลตามลูกค้า, คำค้นหา และช่วงยอดขาย
- ปกปิดข้อมูลส่วนบุคคล เช่น `customer_name`, `phone`, `email`
- ดาวน์โหลดข้อมูลที่ผ่านการ mask แล้วเป็น CSV
- สร้างรายงานมาตรฐาน เช่นยอดขายรวมตามลูกค้าและการกระจายช่วงยอดขาย
- ตรวจคุณภาพข้อมูล เช่นข้อมูลหาย, รูปแบบเบอร์โทรผิด, email ผิด, order ซ้ำ
- แสดงสถานะ pipeline แบบสรุปในหน้าเดียว

## Project Structure

```text
Data-Governance/
├─ mask_app.py        # Streamlit dashboard หลัก
├─ upload_mock.py     # สคริปต์สร้างและอัปโหลด mock sales data
├─ requirements.txt   # รายการ Python packages ที่โปรเจ็กต์ใช้
├─ .env               # เก็บค่าคอนฟิกในเครื่อง (ไม่ควร push)
└─ .gitignore         # ไฟล์ที่ไม่ต้องการให้เข้า git
```

## Tech Stack

- Python
- Streamlit
- Pandas
- SQLAlchemy
- Supabase PostgreSQL
- Faker
- Requests

## Data Schema

โปรเจ็กต์นี้คาดหวังตาราง `public.mock_pii_data` ที่มีคอลัมน์หลักดังนี้

```text
order_id
customer_name
phone
email
sales
```

## Installation

สร้าง virtual environment และติดตั้ง dependencies:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

สร้างไฟล์ `.env` แล้วกำหนดค่าอย่างน้อยตามนี้:

```env
SUPABASE_DB_URL=postgresql://username:password@host:5432/postgres
SUPABASE_KEY=your-supabase-service-role-or-api-key
```

หมายเหตุ:

- `mask_app.py` ใช้ `SUPABASE_DB_URL` สำหรับเชื่อมต่อฐานข้อมูล PostgreSQL
- `upload_mock.py` ใช้ `SUPABASE_KEY` สำหรับยิง REST API ไปยัง Supabase

ถ้าจะใช้งาน `upload_mock.py` ตามโค้ดปัจจุบัน ควรตรวจสอบเพิ่มเติมว่าค่า URL ที่นำไปประกอบ `api_url` ตรงกับ endpoint ที่ต้องการใช้งานจริง

## Running The Dashboard

รันแอปหลักด้วยคำสั่ง:

```powershell
streamlit run mask_app.py
```

เมื่อแอปเริ่มทำงาน จะมีแท็บหลักดังนี้:

- `Executive Overview` สรุป KPI และกราฟภาพรวมยอดขาย
- `Sales Explorer` ค้นหาและกรองข้อมูล
- `Data Download` ดาวน์โหลดข้อมูลที่ผ่านการ mask แล้ว
- `Sales Reports` ดูรายงานมาตรฐาน
- `Quarantine` ตรวจข้อมูลที่มีปัญหาคุณภาพ
- `Pipeline Health` ดูสถานะระบบและสรุปการโหลดข้อมูล

## Generating Mock Data

ถ้าต้องการสร้างข้อมูลทดสอบและอัปโหลดขึ้น Supabase:

```powershell
python upload_mock.py
```

สคริปต์นี้จะ:

- สร้างข้อมูลลูกค้าจำลอง 200 รายการ
- สุ่มชื่อภาษาไทย, อีเมล, เบอร์โทร และยอดขาย
- ส่งข้อมูลไปยังตาราง `mock_pii_data`

## Privacy And Masking

ใน dashboard มีการทำ data masking ก่อนแสดงผลในหลายจุด เช่น:

- `customer_name` ถูกแปลงเป็น hash แบบสั้น
- `phone` แสดงเพียง 3 ตัวแรก
- `email` แสดงเพียง 2 ตัวแรกก่อน `@`

แนวทางนี้ช่วยให้ใช้งานข้อมูลเพื่อวิเคราะห์ต่อได้ โดยลดความเสี่ยงในการเปิดเผยข้อมูลส่วนบุคคลโดยตรง

## Data Quality Rules

ระบบตรวจสอบคุณภาพข้อมูลในแท็บ `Quarantine` โดยดูเงื่อนไขหลัก เช่น:

- ไม่มี `order_id`
- ไม่มี `customer_name`
- ไม่มี `phone`
- เบอร์โทรไม่ใช่ตัวเลข 10 หลัก
- ไม่มี `email`
- email ไม่มี `@`
- ไม่มี `sales`
- `sales` น้อยกว่าหรือเท่ากับ 0
- `order_id` ซ้ำ

## Notes

- ไฟล์ `.env` ถูก ignore แล้ว ไม่ควรนำ secret ขึ้น repository
- โฟลว์ของ `upload_mock.py` เป็นแบบ script ตรง ๆ เมื่อรันแล้วจะยิงข้อมูลทันที
- ถ้าจะ deploy จริง ควรแยกค่า config สำหรับ Database URL และ REST API URL ให้ชัดเจน

## Next Improvements

- แยก environment variable ของ database และ REST API ออกจากกัน
- เพิ่ม pinned versions ใน `requirements.txt`
- เพิ่ม test สำหรับ data masking และ data quality rules
- เพิ่ม `README` ส่วน deployment สำหรับ Streamlit Cloud

## License

ใช้งานภายในทีม หรือปรับแก้ต่อได้ตามบริบทของโปรเจ็กต์
