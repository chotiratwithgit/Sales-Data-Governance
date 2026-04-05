import os           # นำเข้าโมดูล `os` เพื่อใช้เข้าถึงค่าตัวแปรสภาพแวดล้อมของระบบปฏิบัติการ
from datetime import datetime       # นำเข้า `datetime` เพื่อใช้สร้างเวลาปัจจุบันสำหรับแสดงสถานะการรีเฟรชข้อมูล
import hashlib      # นำเข้า `hashlib` เพื่อใช้สร้างค่า hash สำหรับ mask ชื่อลูกค้าแบบย้อนกลับไม่ได้ง่าย
import pandas as pd             # นำเข้า `pandas` และตั้งชื่อย่อเป็น `pd` สำหรับจัดการข้อมูลตาราง
import streamlit as st          # นำเข้า `streamlit` และตั้งชื่อย่อเป็น `st` เพื่อสร้างหน้าเว็บแอป
from dotenv import load_dotenv          # นำเข้า `load_dotenv` เพื่ออ่านค่าคอนฟิกจากไฟล์ `.env`
from sqlalchemy import create_engine        # นำเข้า `create_engine` เพื่อสร้างตัวเชื่อมต่อฐานข้อมูลผ่าน SQLAlchemy
from streamlit.errors import StreamlitSecretNotFoundError       # นำเข้า exception นี้เพื่อรองรับกรณีที่แอปไม่มีการตั้งค่า `st.secrets`



# ตั้งค่าพื้นฐานของหน้า Streamlit ก่อนเริ่มสร้างองค์ประกอบอื่นบนหน้าเว็บ
st.set_page_config(
    # ชื่อที่จะแสดงบนแท็บของเบราว์เซอร์
    page_title="Sales Data Portal",
    # ไอคอนของหน้าเว็บ
    page_icon="🏢",
    # กำหนด layout ให้เป็นแบบกว้างเพื่อเหมาะกับ dashboard
    layout="wide",
)


# โหลดค่าจากไฟล์ `.env` เข้ามาเป็น environment variables
load_dotenv()


# ฟังก์ชันนี้ใช้ดึงค่าคอนฟิกหรือ secret จากหลายแหล่งตามลำดับ
# โดยจะลองอ่านจาก `st.secrets` ก่อน แล้วค่อย fallback ไปที่ environment variables
def get_secret(name: str) -> str | None:
    # ใช้ `try` เพื่อกันกรณีที่ Streamlit ยังไม่มี secrets ให้ใช้งาน
    try:
        # ถ้าชื่อคีย์ที่ต้องการมีอยู่ใน `st.secrets`
        if name in st.secrets:
            # คืนค่าจาก `st.secrets` ทันที
            return st.secrets[name]
    # ถ้าเข้าถึง `st.secrets` ไม่ได้ ให้ข้ามไปใช้ environment variables แทน
    except StreamlitSecretNotFoundError:
        # `pass` หมายถึงไม่ทำอะไรใน except นี้ แล้วปล่อยให้ฟังก์ชันไปทำบรรทัดถัดไป
        pass
    # ถ้าไม่มีค่าใน `st.secrets` หรือเกิด exception ให้ลองอ่านจาก environment variables
    return os.getenv(name)


# ใช้ cache ของ Streamlit เพื่อไม่ต้อง query ฐานข้อมูลใหม่ทุกครั้งที่หน้าเว็บ re-run
@st.cache_data
# ฟังก์ชันนี้ใช้โหลดข้อมูลยอดขายจากฐานข้อมูล Supabase
def get_sales_data() -> pd.DataFrame:
    # อ่าน URL สำหรับเชื่อมต่อฐานข้อมูลจาก secret ชื่อ `SUPABASE_DB_URL`
    db_url = get_secret("SUPABASE_DB_URL")

    # ถ้าไม่พบ URL ของฐานข้อมูล แปลว่ายังตั้งค่าการเชื่อมต่อไม่ครบ
    if not db_url:
        # แจ้งข้อผิดพลาดให้ผู้ใช้ทราบว่าไม่พบคอนฟิกที่จำเป็น
        st.error("ไม่พบ SUPABASE_DB_URL")
        # แสดงคำแนะนำเพิ่มเติมสำหรับกรณี deploy บน Streamlit Cloud
        st.info(
            # บอกตำแหน่งที่ต้องเพิ่มค่า secret
            "บน Streamlit Cloud ให้เพิ่มค่าใน App Settings > Secrets โดยใส่บรรทัด "
            # แสดงรูปแบบตัวอย่างของ secret ที่ถูกต้อง
            '`SUPABASE_DB_URL = "postgresql://..."`'
        )
        # คืนค่า DataFrame ว่าง เพื่อให้โค้ดส่วนล่างตรวจจับและหยุดการทำงานได้อย่างปลอดภัย
        return pd.DataFrame()

    # สร้าง engine สำหรับเชื่อมต่อฐานข้อมูลจาก URL ที่ได้มา
    engine = create_engine(db_url)
    # อ่านข้อมูลทั้งหมดจากตาราง `public.mock_pii_data` แล้วคืนค่าเป็น DataFrame
    return pd.read_sql(
        # คำสั่ง SQL ที่ใช้ดึงข้อมูล
        "SELECT * FROM public.mock_pii_data",
        # ใช้ engine ที่สร้างไว้เป็นตัวเชื่อมต่อกับฐานข้อมูล
        engine,
    )

# ฟังก์ชันนี้ใช้ mask ชื่อลูกค้าโดยแปลงเป็น hash แบบย่อ
def mask_name(customer_name):
    # ถ้าค่าเป็นค่าว่าง (`NaN`) ให้คืนค่าเดิมกลับไป
    if pd.isna(customer_name):
        return customer_name
    # แปลงชื่อเป็น string เข้ารหัส UTF-8 แล้วสร้าง SHA-256 จากนั้นตัดมาแค่ 10 ตัวอักษรแรก
    return hashlib.sha256(str(customer_name).encode("utf-8")).hexdigest()[:10]


# Data Masking Process
# ฟังก์ชันนี้ทำหน้าที่เซนเซอร์ข้อมูลส่วนบุคคล เพื่อให้การแสดงผลสอดคล้องกับแนวคิด PDPA
def apply_data_masking(df: pd.DataFrame) -> pd.DataFrame:
    # docstring อธิบายหน้าที่ของฟังก์ชันแบบสั้น ๆ
    """เซนเซอร์ข้อมูลส่วนบุคคล (PDPA)"""
    # ถ้า DataFrame ว่างอยู่แล้ว ก็คืนค่าเดิมกลับไปทันที
    if df.empty:
        return df

    # ทำสำเนาข้อมูลเพื่อป้องกันไม่ให้แก้ไข DataFrame ต้นฉบับโดยตรง
    df_cleaned = df.copy()

    # ถ้ามีคอลัมน์ `phone` อยู่ในข้อมูล
    if "phone" in df_cleaned.columns:
        # แปลงค่าในคอลัมน์ `phone` ทีละแถวด้วย `apply`
        df_cleaned["phone"] = df_cleaned["phone"].apply(
            # ถ้ามีค่า ให้โชว์เพียง 3 ตัวแรก แล้วปิดบังส่วนที่เหลือ ถ้าไม่มีค่าก็คงค่าเดิมไว้
            lambda x: f"{str(x)[:3]}-XXX-XXXX" if pd.notna(x) else x
        )

    # นิยามฟังก์ชันย่อยสำหรับ mask email
    def mask_email(email):
        # ถ้า email เป็นค่าว่าง ให้คืนค่าเดิมกลับไป
        if pd.isna(email):
            return email
        # แยก email ออกเป็นส่วนหน้ากับ domain ด้วยเครื่องหมาย @
        parts = str(email).split("@")
        # ถ้าแยกได้ถูกต้องเป็น 2 ส่วน
        if len(parts) == 2:
            # แสดงเฉพาะ 2 ตัวแรกของชื่อหน้า @ แล้วปิดบังส่วนที่เหลือ
            return f"{parts[0][:2]}***@{parts[1]}"
        # ถ้ารูปแบบ email ผิดปกติ ให้คืนค่าเดิมกลับไป
        return email

    # ถ้ามีคอลัมน์ `email` อยู่ในข้อมูล
    if "email" in df_cleaned.columns:
        # นำฟังก์ชัน `mask_email` ไปใช้กับทุกค่าในคอลัมน์ email
        df_cleaned["email"] = df_cleaned["email"].apply(mask_email)

    # ถ้ามีคอลัมน์ `customer_name` อยู่ในข้อมูล
    if "customer_name" in df_cleaned.columns:
        # นำฟังก์ชัน `mask_name` ไปใช้กับทุกค่าในคอลัมน์ชื่อลูกค้า
        df_cleaned["customer_name"] = df_cleaned["customer_name"].apply(mask_name)

    # คืนค่า DataFrame ที่ถูก mask แล้วกลับออกไป
    return df_cleaned




# แสดงหัวข้อหลักของหน้า dashboard
st.title("🏢 Sales Data Portal")
# แสดงคำอธิบายสั้น ๆ ของระบบใต้หัวข้อหลัก
st.markdown("ระบบศูนย์กลางข้อมูลสำหรับการวิเคราะห์และปฏิบัติการด้านยอดขาย")

# โหลดข้อมูลยอดขายทั้งหมดจากฐานข้อมูล
df_sales_data = get_sales_data()

# ถ้าข้อมูลว่าง ให้หยุดการทำงานทันทีเพื่อป้องกัน error ในส่วนถัดไป
if df_sales_data.empty:
    st.stop()

# ระบุรายชื่อคอลัมน์สำคัญที่ระบบต้องใช้ในการทำงาน
required_columns = ["order_id", "customer_name", "phone", "email", "sales"]
# ตรวจสอบว่ามีคอลัมน์ใดที่จำเป็นแต่หายไปจากข้อมูลหรือไม่
missing_columns = [col for col in required_columns if col not in df_sales_data.columns]

# ถ้ามีคอลัมน์จำเป็นหายไป
if missing_columns:
    # แสดง error พร้อมรายชื่อคอลัมน์ที่หาย
    st.error(f"ไม่พบคอลัมน์ที่จำเป็น: {', '.join(missing_columns)}")
    # แสดงรายการคอลัมน์ที่มีอยู่จริงเพื่อช่วย debug โครงสร้างข้อมูล
    st.write("Available columns:", df_sales_data.columns.tolist())
    # หยุดการทำงาน เพราะหน้าอื่นต้องพึ่งคอลัมน์เหล่านี้
    st.stop()

# ทำสำเนาข้อมูลก่อนแก้ไขชนิดข้อมูล
# เพื่อให้แน่ใจว่าเราไม่ได้แก้ DataFrame ที่อาจอ้างอิงจาก cache โดยตรง
df_sales_data = df_sales_data.copy()
# แปลงคอลัมน์ `sales` ให้เป็นตัวเลข ถ้าแปลงไม่ได้ให้เป็น `NaN`
df_sales_data["sales"] = pd.to_numeric(df_sales_data["sales"], errors="coerce")
# สร้างเวอร์ชันข้อมูลที่ถูก mask แล้ว สำหรับใช้แสดงผลในบางส่วนของ UI
masked_sales_data = apply_data_masking(df_sales_data)

# เตรียมรายการลูกค้าทั้งหมดแบบไม่ซ้ำและไม่เป็นค่าว่าง เพื่อใช้เป็นค่าเริ่มต้นของตัวกรอง
selected_customers = sorted(df_sales_data["customer_name"].dropna().unique())
# หาค่ายอดขายต่ำสุด โดยแทนค่า `NaN` ด้วย 0 ก่อน แล้วแปลงเป็น int
min_sales = int(df_sales_data["sales"].fillna(0).min())
# หาค่ายอดขายสูงสุด โดยแทนค่า `NaN` ด้วย 0 ก่อน แล้วแปลงเป็น int
max_sales = int(df_sales_data["sales"].fillna(0).max())
# กำหนดช่วงยอดขายเริ่มต้นให้ครอบคลุมตั้งแต่ต่ำสุดถึงสูงสุด
selected_sales_range = (min_sales, max_sales)
# กำหนดค่าเริ่มต้นของช่องค้นหาเป็นสตริงว่าง
search_text = ""
# เริ่มต้น DataFrame ที่กรองแล้วให้เท่ากับข้อมูลทั้งหมดก่อน
filtered_df = df_sales_data.copy()
# สร้าง DataFrame ว่างไว้ก่อนสำหรับเก็บข้อมูลที่มีปัญหาในแท็บ Quarantine
quarantine_df = pd.DataFrame()


# สร้างแท็บหลัก 6 แท็บ และเก็บออบเจ็กต์แท็บไว้ใช้งานต่อ
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    # แท็บภาพรวมสำหรับผู้บริหาร
    "📊 Executive Overview",
    # แท็บสำรวจข้อมูลยอดขาย
    "🔍 Sales Explorer",
    # แท็บดาวน์โหลดข้อมูล
    "📥 Data Download",
    # แท็บรายงานยอดขายมาตรฐาน
    "📑 Sales Reports",
    # แท็บกักข้อมูลที่มีปัญหา
    "🚨 Quarantine",
    # แท็บแสดงสถานะ pipeline และระบบหลังบ้าน
    "⚙️ Pipeline Health",
])


# เริ่มเนื้อหาภายในแท็บที่ 1: Executive Overview
with tab1:
    # แสดงหัวข้อย่อยของแท็บภาพรวมข้อมูลยอดขาย
    st.subheader("ภาพรวมข้อมูลยอดขาย")

    # นับจำนวนออเดอร์ทั้งหมดจากจำนวนแถวในข้อมูล
    total_orders = len(df_sales_data)
    # นับจำนวนลูกค้าแบบไม่ซ้ำกัน
    total_customers = df_sales_data["customer_name"].nunique()
    # รวมยอดขายทั้งหมด แล้วแปลงเป็น float เพื่อให้ใช้งานต่อได้สม่ำเสมอ
    total_sales_amount = float(df_sales_data["sales"].sum())
    # คำนวณค่าเฉลี่ยยอดขายต่อออเดอร์ แล้วแปลงเป็น float
    average_order_value = float(df_sales_data["sales"].mean())

    # แบ่งพื้นที่เป็น 4 คอลัมน์สำหรับแสดง KPI cards
    col1, col2, col3, col4 = st.columns(4)
    # แสดงจำนวนออเดอร์ทั้งหมด
    col1.metric("Orders ทั้งหมด", total_orders)
    # แสดงจำนวนลูกค้าทั้งหมด
    col2.metric("ลูกค้าทั้งหมด", total_customers)
    # แสดงยอดขายรวม โดยจัดรูปแบบตัวเลขไม่มีจุดทศนิยม
    col3.metric("ยอดขายรวม", f"{total_sales_amount:,.0f}")
    # แสดงยอดขายเฉลี่ยต่อออเดอร์ โดยจัดรูปแบบตัวเลขไม่มีจุดทศนิยม
    col4.metric("ยอดขายเฉลี่ยต่อออเดอร์", f"{average_order_value:,.0f}")

    # แทรกเส้นคั่นก่อนเข้าส่วนกราฟ
    st.divider()
    # แบ่งพื้นที่เป็น 2 คอลัมน์สำหรับแสดงกราฟสองชุด
    left, right = st.columns(2)

    # เริ่มเนื้อหาของคอลัมน์ซ้าย
    with left:
        # แสดงหัวข้อของกราฟฝั่งซ้าย ซึ่งกราฟนี้ตั้งใจโชว์เฉพาะออเดอร์ที่ยอดขายสูงที่สุด
        # โดยใช้ order_id แทนข้อมูลลูกค้าเพื่อหลีกเลี่ยงการเปิดเผยข้อมูลส่วนบุคคล
        st.write("📦 ออเดอร์ที่มียอดขายสูงสุด")

        # เรียงข้อมูลจากยอดขายมากไปน้อย
        # แล้วเลือกมาแค่ 10 แถวแรกเพื่อให้กราฟอ่านง่ายและไม่แน่นจนเกินไป
        top_orders = (
            # เรียงข้อมูลตามคอลัมน์ `sales` แบบมากไปน้อย
            df_sales_data.sort_values("sales", ascending=False)
            # เลือกมาเฉพาะ 10 รายการแรก
            .head(10)
            # ตั้ง `order_id` เป็น index เพื่อใช้เป็น label ของกราฟ
            .set_index("order_id")["sales"]
        )

        # วาดกราฟแท่งจาก Series ที่มี index เป็น order_id และ value เป็นยอดขาย
        st.bar_chart(top_orders)

    # เริ่มเนื้อหาของคอลัมน์ขวา
    with right:
        # แสดงหัวข้อของกราฟฝั่งขวา
        # กราฟนี้ไม่มีชื่อบุคคล จึงเหมาะกับการนำเสนอภาพรวมแบบสอดคล้องกับ PDPA มากกว่า
        st.write("📊 การกระจายช่วงยอดขาย")

        # แบ่งข้อมูลยอดขายทั้งหมดออกเป็นช่วง (bucket)
        # เพื่อดูว่าออเดอร์ส่วนใหญ่อยู่ในช่วงยอดขายระดับใด
        sales_ranges = pd.cut(
            # ใช้คอลัมน์ยอดขายเป็นข้อมูลตั้งต้นในการแบ่งช่วง
            df_sales_data["sales"],
            # กำหนดขอบเขตของแต่ละช่วงยอดขาย
            bins=[0, 1000, 5000, 10000, 20000, float("inf")],
            # กำหนดชื่อ label สำหรับแต่ละช่วงยอดขาย
            labels=[
                "0-1,000",
                "1,001-5,000",
                "5,001-10,000",
                "10,001-20,000",
                "20,000+",
            ],
            # ให้รวมค่าขอบล่างสุดเข้าไปด้วย
            include_lowest=True,
        )

        # นับจำนวนออเดอร์ในแต่ละช่วงยอดขาย
        # ใช้ sort=False เพื่อให้ลำดับของช่วงยอดขายเรียงตาม bins ที่กำหนดไว้ ไม่สลับตามจำนวนมากน้อย
        sales_range_summary = sales_ranges.value_counts(sort=False).reset_index()

        # ตั้งชื่อคอลัมน์ใหม่ให้อ่านเข้าใจง่าย
        # sales_range คือชื่อช่วงยอดขาย และ order_count คือจำนวนออเดอร์ในช่วงนั้น
        sales_range_summary.columns = ["sales_range", "order_count"]

        # วาดกราฟแท่งโดยใช้ช่วงยอดขายเป็นแกน X และจำนวนออเดอร์เป็นแกน Y
        # การ set_index ช่วยให้ Streamlit ใช้ชื่อช่วงยอดขายเป็น label ของแต่ละแท่งได้ตรง ๆ
        st.bar_chart(sales_range_summary.set_index("sales_range")["order_count"])

    # แทรกเส้นคั่นก่อนแสดงตารางออเดอร์ยอดขายสูงสุด
    st.divider()
    # แสดงหัวข้อของตาราง
    st.write("📋 รายการออเดอร์ยอดขายสูงสุด")
    # แสดง 10 รายการที่มียอดขายสูงสุดจากข้อมูลที่ถูก mask แล้ว
    st.dataframe(
        # เรียงข้อมูลที่ถูก mask ตามยอดขายจากมากไปน้อย และเลือกมา 10 แถวแรก
        masked_sales_data.sort_values("sales", ascending=False).head(10),
        # ให้ตารางใช้ความกว้างเต็ม container
        use_container_width=True,
        # ซ่อนคอลัมน์ index ในตาราง
        hide_index=True,
    )

# เริ่มเนื้อหาภายในแท็บที่ 2: Sales Explorer
with tab2:
    # แสดงหัวข้อย่อยของแท็บสำรวจข้อมูลยอดขาย
    st.subheader("Sales Explorer")
    # แสดงข้อความแนะนำการใช้งานของหน้า explorer
    st.info("💡 ค้นหา กรอง และตรวจข้อมูลยอดขายจากหน้านี้")

    # แบ่งพื้นที่เป็น 2 คอลัมน์สำหรับตัวกรอง
    col_filter1, col_filter2 = st.columns(2)
    # เริ่มส่วนของตัวกรองฝั่งซ้าย
    with col_filter1:
        # สร้าง multiselect สำหรับเลือกลูกค้าได้หลายราย
        selected_customers = st.multiselect(
            # ข้อความกำกับกล่องเลือกลูกค้า
            "เลือกลูกค้า",
            # ตัวเลือกทั้งหมดคือรายชื่อลูกค้าแบบไม่ซ้ำ
            options=sorted(df_sales_data["customer_name"].dropna().unique()),
            # ค่าเริ่มต้นคือเลือกทั้งหมด
            default=selected_customers,
        )
    # เริ่มส่วนของตัวกรองฝั่งขวา
    with col_filter2:
        # สร้าง slider สำหรับกรองช่วงยอดขาย
        selected_sales_range = st.slider(
            # ข้อความกำกับ slider
            "ช่วงยอดขาย",
            # ค่าต่ำสุดของ slider
            min_value=min_sales,
            # ค่าสูงสุดของ slider
            max_value=max_sales,
            # ค่าเริ่มต้นคือครอบคลุมทั้งช่วง
            value=(min_sales, max_sales),
        )

    # สร้างช่องค้นหาข้อความสำหรับค้นหา Order ID, ชื่อลูกค้า หรือ Email
    search_text = st.text_input("ค้นหาจาก Order ID, ชื่อลูกค้า หรือ Email")

    # กรองข้อมูลตามลูกค้าที่เลือกและช่วงยอดขายที่เลือก
    filtered_df = df_sales_data[
        # เงื่อนไขแรก: ลูกค้าต้องอยู่ในรายการที่ผู้ใช้เลือก
        df_sales_data["customer_name"].isin(selected_customers)
        # เงื่อนไขที่สอง: ยอดขายต้องอยู่ภายในช่วงที่ผู้ใช้เลือก
        & df_sales_data["sales"].between(selected_sales_range[0], selected_sales_range[1])
        # ทำสำเนาผลลัพธ์เพื่อใช้งานต่ออย่างปลอดภัย
    ].copy()

    # ถ้าผู้ใช้พิมพ์ข้อความค้นหาเข้ามา
    if search_text:
        # กรองต่อเฉพาะแถวที่ข้อความค้นหาตรงกับ order_id หรือ customer_name หรือ email
        filtered_df = filtered_df[
            # ค้นหาใน order_id หลังแปลงเป็น string
            filtered_df["order_id"].astype(str).str.contains(search_text, case=False, na=False)
            # หรือค้นหาใน customer_name หลังแปลงเป็น string
            | filtered_df["customer_name"].astype(str).str.contains(search_text, case=False, na=False)
            # หรือค้นหาใน email หลังแปลงเป็น string
            | filtered_df["email"].astype(str).str.contains(search_text, case=False, na=False)
        ]

    # เรียงข้อมูลที่กรองแล้วตามยอดขายจากมากไปน้อย
    filtered_df = filtered_df.sort_values("sales", ascending=False)
    # สร้างเวอร์ชันข้อมูลที่กรองแล้วและถูก mask สำหรับนำไปแสดงผล
    mask_filtered_df = apply_data_masking(filtered_df)

    # แสดงจำนวนข้อมูลที่พบหลังกรองเสร็จ
    st.caption(f"พบข้อมูล {len(filtered_df):,} รายการ")
    # แสดงตารางข้อมูลที่กรองแล้วในรูปแบบ masked data
    st.dataframe(mask_filtered_df, use_container_width=True, hide_index=True)


# เริ่มเนื้อหาภายในแท็บที่ 3: Data Download
with tab3:
    # แสดงหัวข้อย่อยของแท็บดาวน์โหลดข้อมูล
    st.subheader("Data Download")
    # อธิบายว่าข้อมูลที่ดาวน์โหลดจะอิงจากผลลัพธ์ในหน้า Sales Explorer
    st.markdown("ดาวน์โหลดข้อมูลที่กรองจากหน้า Sales Explorer ได้โดยตรง")

    # ให้ผู้ใช้เลือกคอลัมน์ที่ต้องการดาวน์โหลด
    export_columns = st.multiselect(
        # ป้ายกำกับของกล่องเลือกคอลัมน์
        "เลือกคอลัมน์สำหรับดาวน์โหลด",
        # ใช้รายชื่อคอลัมน์จากข้อมูลที่กรองแล้วเป็นตัวเลือก
        options=filtered_df.columns.tolist(),
        # ค่าเริ่มต้นคือเลือกทุกคอลัมน์
        default=filtered_df.columns.tolist(),
    )


    # ถ้ามีการเลือกคอลัมน์ ให้ส่งออกเฉพาะคอลัมน์นั้น ไม่เช่นนั้นใช้ข้อมูลที่ถูก mask ทั้งหมด
    export_df = mask_filtered_df[export_columns] if export_columns else mask_filtered_df.copy()
    # แปลงข้อมูลที่ส่งออกเป็น CSV แบบ UTF-8 แล้วเก็บไว้ในตัวแปร `csv_data`
    csv_data = export_df.to_csv(index=False).encode('utf-8')
    # แสดงจำนวนแถวที่พร้อมดาวน์โหลด
    st.caption(f"พร้อมดาวน์โหลด {len(export_df):,} รายการ")
    # แสดง preview ของข้อมูลที่จะดาวน์โหลด
    st.dataframe(export_df, use_container_width=True, hide_index=True)
    # สร้างปุ่มดาวน์โหลดไฟล์ CSV
    st.download_button(
        # ข้อความบนปุ่มดาวน์โหลด
        "📥 Download Filtered Data (CSV)",
        # แปลงข้อมูลเป็น CSV แบบ UTF-8 สำหรับส่งให้ผู้ใช้ดาวน์โหลด
        data=export_df.to_csv(index=False).encode("utf-8"),
        # ตั้งชื่อไฟล์สำหรับการดาวน์โหลด
        file_name="secure_sales_data.csv",
        # ระบุ MIME type ของไฟล์
        mime="text/csv",
    )

# เริ่มเนื้อหาภายในแท็บที่ 4: Sales Reports
with tab4:
    # แสดงหัวข้อย่อยของแท็บรายงานยอดขายมาตรฐาน
    st.subheader("Standard Sales Reports (รายงานมาตรฐาน)")
    # สร้าง selectbox ให้ผู้ใช้เลือกรูปแบบรายงาน
    report_type = st.selectbox(
        # ป้ายกำกับของ selectbox
        "รายงาน",
        # รายการประเภทรายงานที่รองรับ
        [
            "ยอดขายรวมตามลูกค้า",
            "ออเดอร์ยอดขายสูงสุด",
            "การกระจายช่วงยอดขาย",
        ],
    )

    # ถ้าผู้ใช้เลือกดูรายงานยอดขายรวมตามลูกค้า
    if report_type == "ยอดขายรวมตามลูกค้า":
        # จัดกลุ่มตามชื่อลูกค้า รวมยอดขาย และเรียงจากมากไปน้อย
        report_df = (
            # groupby ตาม customer_name โดยไม่ใช้เป็น index
            filtered_df.groupby("customer_name", as_index=False)["sales"]
            # รวมยอดขายของแต่ละลูกค้า
            .sum()
            # เรียงข้อมูลตามยอดขายรวมจากมากไปน้อย
            .sort_values("sales", ascending=False)
        )
        # เปลี่ยนชื่อคอลัมน์ให้ชัดเจนมากขึ้น
        report_df.columns = ["customer_name", "total_sales"]

        # ถ้ายังมีคอลัมน์ชื่อลูกค้าอยู่ในรายงาน
        if "customer_name" in report_df.columns:
            # mask ชื่อลูกค้าก่อนแสดงผลหรือดาวน์โหลด
            report_df["customer_name"] = report_df["customer_name"].apply(mask_name)

    # ถ้าผู้ใช้เลือกดูรายงานออเดอร์ยอดขายสูงสุด
    elif report_type == "ออเดอร์ยอดขายสูงสุด":
        # เรียงข้อมูลตามยอดขายจากมากไปน้อย เลือกเฉพาะคอลัมน์สำคัญ และดึงมา 20 แถวแรก
        report_df = filtered_df.sort_values("sales", ascending=False)[
            ["order_id", "customer_name", "sales"]
        ].head(20)
    # ถ้าไม่ใช่สองกรณีด้านบน ให้ถือว่าเป็นรายงานการกระจายช่วงยอดขาย
    else:
        # แบ่งยอดขายออกเป็น bucket ตามช่วงที่กำหนด
        sales_buckets = pd.cut(
            # ใช้ข้อมูลคอลัมน์ยอดขายที่กรองแล้ว
            filtered_df["sales"],
            # กำหนดขอบเขตของแต่ละช่วงยอดขาย
            bins=[0, 1000, 5000, 10000, 20000, float("inf")],
            # กำหนดชื่อ label ของแต่ละ bucket
            labels=[
                "0-1,000",
                "1,001-5,000",
                "5,001-10,000",
                "10,001-20,000",
                "20,000+",
            ],
            # ให้รวมค่าขอบล่างสุดด้วย
            include_lowest=True,
        )
        # นับจำนวนข้อมูลในแต่ละ bucket แล้วแปลงเป็น DataFrame
        report_df = sales_buckets.value_counts(sort=False).reset_index()
        # เปลี่ยนชื่อคอลัมน์ให้สื่อความหมายชัดเจน
        report_df.columns = ["sales_range", "order_count"]

    # แสดงตารางรายงานที่คำนวณเสร็จแล้ว
    st.dataframe(report_df, use_container_width=True, hide_index=True)
    # สร้างปุ่มสำหรับดาวน์โหลดรายงานเป็นไฟล์ CSV
    st.download_button(
        # ข้อความบนปุ่มดาวน์โหลด
        "📥 Download Report (CSV)",
        # แปลงรายงานเป็น CSV แบบ UTF-8
        data=report_df.to_csv(index=False).encode("utf-8"),
        # ตั้งชื่อไฟล์ตามประเภทรายงานที่เลือก โดยแทนช่องว่างด้วย `_`
        file_name=f"{report_type.replace(' ', '_')}.csv",
        # ระบุ MIME type ของไฟล์ CSV
        mime="text/csv",
    )


# เริ่มเนื้อหาภายในแท็บที่ 5: Quarantine
with tab5:
    # แสดงหัวข้อย่อยของแท็บคุณภาพข้อมูล
    st.subheader("Data Quality (คุณภาพข้อมูล)")
    # อธิบายว่าข้อมูลส่วนนี้คือรายการที่ควรตรวจสอบก่อนนำไปใช้งานจริง
    st.markdown("รายการที่ควรตรวจสอบก่อนนำข้อมูลไปใช้วิเคราะห์หรือรายงาน")

    # ทำสำเนาข้อมูลต้นฉบับมาใช้ตรวจคุณภาพ
    df_qc = df_sales_data.copy()
    # สร้าง list ว่างสำหรับสะสมรายการปัญหาที่พบ
    issues = []

    # วนตรวจข้อมูลทีละแถว
    for _, row in df_qc.iterrows():
        # เตรียมค่า phone แบบตัดช่องว่าง ถ้าไม่มีค่าให้เป็นสตริงว่าง
        phone_value = str(row["phone"]).strip() if pd.notna(row["phone"]) else ""
        # เตรียมค่า email แบบตัดช่องว่าง ถ้าไม่มีค่าให้เป็นสตริงว่าง
        email_value = str(row["email"]).strip() if pd.notna(row["email"]) else ""
        # เก็บค่ายอดขายไว้ในตัวแปรเพื่ออ่านง่ายขึ้น
        sales_value = row["sales"]

        # ถ้าไม่มี order_id หรือเป็นค่าว่าง
        if pd.isna(row["order_id"]) or str(row["order_id"]).strip() == "":
            # เพิ่มรายการปัญหาว่าไม่มี Order ID
            issues.append({**row.to_dict(), "issue": "Missing Order ID"})
        # ถ้าไม่มีชื่อลูกค้าหรือเป็นค่าว่าง
        elif pd.isna(row["customer_name"]) or str(row["customer_name"]).strip() == "":
            # เพิ่มรายการปัญหาว่าไม่มีชื่อลูกค้า
            issues.append({**row.to_dict(), "issue": "Missing Customer Name"})
        # ถ้าไม่มีเบอร์โทรศัพท์
        elif not phone_value:
            # เพิ่มรายการปัญหาว่าไม่มีเบอร์โทร
            issues.append({**row.to_dict(), "issue": "Missing Phone"})
        # ถ้าเบอร์โทรไม่ใช่ตัวเลขล้วน หรือความยาวไม่เท่ากับ 10 หลัก
        elif not phone_value.isdigit() or len(phone_value) != 10:
            # เพิ่มรายการปัญหาว่าเบอร์โทรไม่ถูกต้อง
            issues.append({**row.to_dict(), "issue": "Invalid Phone"})
        # ถ้าไม่มี email
        elif not email_value:
            # เพิ่มรายการปัญหาว่าไม่มีอีเมล
            issues.append({**row.to_dict(), "issue": "Missing Email"})
        # ถ้า email ไม่มีเครื่องหมาย @
        elif "@" not in email_value:
            # เพิ่มรายการปัญหาว่าอีเมลไม่ถูกต้อง
            issues.append({**row.to_dict(), "issue": "Invalid Email"})
        # ถ้ายอดขายเป็นค่าว่าง
        elif pd.isna(sales_value):
            # เพิ่มรายการปัญหาว่าไม่มียอดขาย
            issues.append({**row.to_dict(), "issue": "Missing Sales"})
        # ถ้ายอดขายน้อยกว่าหรือเท่ากับ 0
        elif sales_value <= 0:
            # เพิ่มรายการปัญหาว่ายอดขายไม่ถูกต้อง
            issues.append({**row.to_dict(), "issue": "Invalid Sales Amount"})

    # หาแถวที่มี order_id ซ้ำกัน โดยเก็บทุกรายการที่ซ้ำไว้
    dup_order_id = df_qc[df_qc["order_id"].duplicated(keep=False)]
    # วนเพิ่มข้อมูลที่มี order_id ซ้ำเข้าไปในรายการปัญหา
    for _, row in dup_order_id.iterrows():
        # เพิ่มรายการปัญหาว่า Order ID ซ้ำ
        issues.append({**row.to_dict(), "issue": "Duplicate Order ID"})

    # แปลง list ปัญหาเป็น DataFrame และลบแถวซ้ำที่อาจถูกเพิ่มซ้ำ
    quarantine_df = pd.DataFrame(issues).drop_duplicates()

    # แสดงจำนวน records ที่มีปัญหาคุณภาพข้อมูล
    st.metric("Records with Issues", len(quarantine_df))

    # ถ้าไม่พบข้อมูลผิดปกติเลย
    if quarantine_df.empty:
        # แสดงข้อความ success ว่าคุณภาพข้อมูลผ่านเกณฑ์
        st.success("✅ ไม่พบข้อมูลผิดปกติ (No data quality issues found)")
    # ถ้ามีข้อมูลผิดปกติอย่างน้อย 1 รายการ
    else:
        # แสดงตารางรายการข้อมูลที่มีปัญหา
        st.dataframe(quarantine_df, use_container_width=True, hide_index=True)
        # สร้างปุ่มดาวน์โหลดรายการปัญหาเป็นไฟล์ CSV
        st.download_button(
            # ข้อความบนปุ่มดาวน์โหลด
            "📥 Download Data Quality Issues (CSV)",
            # แปลงรายการปัญหาเป็น CSV แบบ UTF-8
            data=quarantine_df.to_csv(index=False).encode("utf-8"),
            # ตั้งชื่อไฟล์สำหรับการดาวน์โหลด
            file_name="sales_data_quality_issues.csv",
            # ระบุ MIME type ของไฟล์
            mime="text/csv",
        )


# เริ่มเนื้อหาภายในแท็บที่ 6: Pipeline Health
with tab6:
    # แสดงหัวข้อย่อยของแท็บสถานะระบบหลังบ้าน
    st.subheader("Pipeline Health (สถานะระบบหลังบ้าน)")
    # อธิบายว่าหน้านี้ใช้ดูสถานะการทำงานของระบบและ ETL
    st.markdown("ตรวจสอบสถานะการทำงานของระบบและประสิทธิภาพของกระบวนการ ETL")

    # นับจำนวนข้อมูลที่อยู่ใน quarantine
    quarantine_count = len(quarantine_df)
    # นับจำนวนข้อมูลทั้งหมดในชุดข้อมูลยอดขาย
    total_records = len(df_sales_data)
    # คำนวณจำนวนข้อมูลที่ถือว่า valid
    valid_records = total_records - quarantine_count
    # เก็บเวลาปัจจุบันเพื่อแสดงว่ารีเฟรชข้อมูลล่าสุดเมื่อไร
    last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # แบ่งพื้นที่เป็น 4 คอลัมน์สำหรับแสดง metric ของระบบ
    col1, col2, col3, col4 = st.columns(4)
    # แสดงจำนวนข้อมูลทั้งหมด
    col1.metric("Total Records", total_records)
    # แสดงจำนวนข้อมูลที่ valid
    col2.metric("Valid Records", valid_records)
    # แสดงจำนวนข้อมูลใน quarantine
    col3.metric("Quarantine Records", quarantine_count)
    # แสดงเวลา refresh ล่าสุด
    col4.metric("Last Refresh", last_refresh)

    # แทรกเส้นคั่นก่อนส่วนแสดงสถานะ pipeline
    st.divider()

    # ถ้าไม่มีข้อมูลเสียเลยให้ถือว่าระบบ healthy ไม่เช่นนั้นให้เป็น warning
    pipeline_status = "healthy" if quarantine_count == 0 else "warning"
    # แสดงหัวข้อส่วนสถานะของ pipeline
    st.write("Pipeline Status:")
    # ถ้าสถานะระบบเป็น healthy
    if pipeline_status == "healthy":
        # แสดงข้อความว่าระบบทำงานปกติ
        st.success("✅ ระบบทำงานปกติ (All systems operational)")
    # ถ้าสถานะระบบไม่ healthy
    else:
        # แสดงข้อความเตือนว่าระบบยังมีปัญหา
        st.warning("⚠️ ระบบมีปัญหา (System has issues)")

    # แสดงหัวข้อส่วนรายละเอียดของ pipeline
    st.write("รายละเอียด:")
    # แสดงรายละเอียดเชิงเทคนิคของแหล่งข้อมูลและสภาพแวดล้อมแบบ code block
    st.code(
        # ข้อความหลายบรรทัดสรุปข้อมูลของ pipeline
        """Source: Supabase PostgreSQL
Data Domain: Sales Mock PII Data
Load Method: SQL query
Environment: Local, Streamlit"""
    )

    # แสดงหัวข้อส่วน system logs
    st.write("System Logs:")
    # แสดงกล่องข้อความสำหรับแสดง log สรุปของระบบ
    st.text_area(
        # ป้ายกำกับของกล่อง log
        "Logs",
        # ประกอบข้อความ log จากค่าที่คำนวณได้ในรอบล่าสุด
        value=(
            # log จำนวน sales records ที่โหลดมาได้
            f"INFO: Loaded {total_records} sales records from Supabase\n"
            # log จำนวน records ที่ valid
            f"INFO: Valid records: {valid_records}\n"
            # log จำนวน records ที่ถูกกักไว้ใน quarantine
            f"INFO: Quarantine records: {quarantine_count}\n"
            # log เวลา refresh ล่าสุด
            f"INFO: Last refresh at {last_refresh}\n"
        ),
        # กำหนดความสูงของ text area
        height=180,
    )
