import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- الجزء 1: الربط والأمان ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- الجزء 2: إعدادات الواجهة الاحترافية ---
st.set_page_config(page_title="نظام إدارة فحوصات حديثة المركزي", layout="wide")

st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 15px; border: 1px solid #dee2e6; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1e3a8a; color: white; font-weight: bold; height: 3em; }
    label { font-size: 1.1rem !important; font-weight: bold !important; color: #1e3a8a !important; }
    h1, h2, h3 { color: #1e3a8a; text-align: center; }
    </style>""", unsafe_allow_html=True)

# --- الجزء 3: إدارة الصلاحيات والدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1>🏥 نظام مختبرات قضاء حديثة</h1>", unsafe_allow_html=True)
    st.subheader("🔑 تسجيل الدخول للمخولين فقط")
    
    centers_list = [
        'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
        'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
        'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
        'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص (للبحث والعرض فقط)'
    ]
    
    with st.container():
        col_login, _ = st.columns([1, 1])
        with col_login:
            c_choice = st.selectbox("اختر الجهة المستخدِمة:", centers_list)
            a_code = st.text_input("أدخل رمز الدخول السري:", type="password")
            
            if st.button("دخول آمن للنظام"):
                res = supabase.table("center_access").select("*").eq("center_name", c_choice).eq("access_code", a_code).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.center = c_choice
                    st.session_state.is_admin = res.data[0]['is_admin']
                    st.session_state.is_doctor = "أطباء الاختصاص" in c_choice
                    st.rerun()
                else:
                    st.error("❌ الرمز السري غير صحيح أو الصلاحية منتهية.")

else:
    # شريط التحكم الجانبي
    st.sidebar.title("🛠️ لوحة التحكم")
    st.sidebar.markdown(f"**المستخدم الحالي:**\n\n{st.session_state.center}")
    if st.sidebar.button("🔴 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # توزيع التبويبات بناءً على نوع الحساب
    if st.session_state.is_doctor:
        main_tabs = st.tabs(["🔍 البحث والاستعلام المركزي"])
    else:
        main_tabs = st.tabs(["📝 إدخال بيانات المصابين", "🔍 البحث وإدارة السجلات"])

    # --- الجزء 4: واجهة الإدخال (للمراكز والمختبرات فقط) ---
    if not st.session_state.is_doctor:
        with main_tabs[0]:
            st.markdown("<h3>📝 تسجيل إصابة جديدة / أرشفة قديمة</h3>", unsafe_allow_html=True)
            with st.form("comprehensive_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    f_name = st.text_input("الاسم الرباعي للمراجع:")
                    f_addr = st.text_input("عنوان السكن:")
                    f_date = st.date_input("تاريخ إجراء الفحص (اختر اليوم بدقة):", value=date.today(), min_value=date(1990,1,1))
                with col2:
                    f_inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    f_dev = st.selectbox("جهاز الفحص المستخدم:", ["Strips", "ELISA", "PCR", "VITEK"])
                    f_pcr = st.text_input("ملاحظات إضافية (اختياري):")
                
                if st.form_submit_button("إرسال البيانات للقاعدة المركزية"):
                    if f_name and f_addr:
                        supabase.table("patients").insert({
                            "full_name": f_name, "address": f_addr, "test_date": str(f_date),
                            "infection_type": f_inf, "test_device": f_dev, "pcr_result": f_pcr,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success(f"✅ تم حفظ السجل للمراجع: {f_name}")
                        st.rerun()
                    else:
                        st.error("⚠️ يجب ملء الاسم والعنوان على الأقل.")

    # --- الجزء 5: واجهة البحث المتطورة (تعرض البيانات القديمة والجديدة) ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with main_tabs[search_idx]:
        st.markdown("<h3>🔍 البحث في سجلات قضاء حديثة</h3>", unsafe_allow_html=True)
        q_name = st.text_input("ابحث عن اسم المريض للتأكد من حالته:")
        
        if q_name:
            search_res = supabase.table("patients").select("*").ilike("full_name", f"%{q_name}%").execute()
            
            if search_res.data:
                for row in search_res.data:
                    # ميكانيكية "مانع الخطأ" للبيانات القديمة
                    disp_name = row.get('full_name', 'اسم غير معروف')
                    disp_date = row.get('test_date') if row.get('test_date') else "سجل قديم"
                    disp_addr = row.get('address') if row.get('address') else "غير متوفر"
                    disp_cent = row.get('entry_center') if row.get('entry_center') else "مركز سابق"
                    
                    with st.expander(f"📄 مراجع: {disp_name} | التاريخ: {disp_date}"):
                        c_a, c_b = st.columns(2)
                        with c_a:
                            st.write(f"**📍 السكن:** {disp_addr}")
                            st.write(f"**📅 تاريخ الفحص:** {disp_date}")
                            st.write(f"**🧬 نوع الإصابة:** {row.get('infection_type','-')}")
                        with c_b:
                            st.write(f"**🏢 المركز المسؤول:** {disp_cent}")
                            st.write(f"**🔬 الجهاز:** {row.get('test_device','-')}")
                            st.write(f"**📝 ملاحظات:** {row.get('pcr_result','-')}")
                        
                        # قيود الحذف
                        if not st.session_state.is_doctor:
                            if st.session_state.is_admin or st.session_state.center == disp_cent:
                                if st.button(f"🗑️ حذف السجل نهائياً", key=f"del_{row['id']}"):
                                    supabase.table("patients").delete().eq("id", row['id']).execute()
                                    st.rerun()
            else:
                st.warning("❌ لم يتم العثور على أي سجل بهذا الاسم.")
