import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. استعادة الألوان السابقة وتنسيق الدردشة (الخط الأسود) ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    /* الإعدادات العامة والاتجاه */
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    
    /* الألوان الزرقاء الأصلية للأزرار والعناوين */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        background-color: #1e3a8a; 
        color: white !important; 
    }
    
    label, h2, h3 { font-weight: bold; color: #1e3a8a; text-align: right; }

    /* --- تنسيق الدردشة المباشرة (تعديل لون الخط للأسود) --- */
    .chat-container {
        background: #f8fafc;
        padding: 15px;
        border-radius: 12px;
        height: 400px;
        overflow-y: auto;
        border: 1px solid #cbd5e1;
        direction: rtl;
        margin-bottom: 15px;
    }
    .chat-msg {
        background: #ffffff;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-right: 5px solid #1e3a8a;
        text-align: right;
        /* هنا التعديل المهم: لون الخط أسود وواضح */
        color: #000000 !important; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .chat-msg b {
        color: #1e3a8a; /* اسم المرسل بالأزرق للتمييز */
    }
    .chat-msg span {
        color: #000000; /* محتوى الرسالة أسود تماماً */
        font-size: 1.05rem;
    }
    
    /* تنظيف الواجهة */
    #MainMenu, footer, header {visibility: hidden;}
    </style>""", unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🏥 نظام مختبرات قضاء حديثة</h2>", unsafe_allow_html=True)
    centers_list = [
        'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
        'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
        'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
        'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص (للبحث والعرض فقط)'
    ]
    col_l, _ = st.columns([1.5, 1])
    with col_l:
        c_choice = st.selectbox("الجهة المستخدِمة:", centers_list)
        a_code = st.text_input("رمز الدخول:", type="password")
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", c_choice).eq("access_code", a_code).execute()
            if res.data:
                st.session_state.logged_in, st.session_state.center = True, c_choice
                st.session_state.is_admin = res.data[0]['is_admin']
                st.session_state.is_doctor = "أطباء الاختصاص" in c_choice
                st.rerun()
            else: st.error("❌ الكود غير صحيح")
else:
    # القائمة الجانبية
    st.sidebar.info(f"المستخدم: {st.session_state.center}")
    if st.sidebar.button("🔴 تسجيل خروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 البحث والاستعلام", "💬 الدردشة المباشرة"])
    else:
        tabs = st.tabs(["📝 تسجيل مراجع", "🔍 السجلات والإدارة", "💬 الدردشة المباشرة"])

    # --- تبويب البحث (سواء للطبيب أو المختبر) ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_idx]:
        st.subheader("🔍 البحث في السجل المركزي")
        q = st.text_input("ابحث بالاسم الرباعي:")
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
            if res.data:
                for row in res.data:
                    with st.expander(f"👤 {row['full_name']} | {row['infection_type']}"):
                        st.write(f"📍 السكن: {row.get('address','-')} | 📅 التاريخ: {row.get('test_date','-')}")
                        st.write(f"🏢 المركز: {row.get('entry_center','-')} | 🔬 الجهاز: {row.get('test_device','-')}")
            else: st.info("لا توجد نتائج")

    # --- تبويب الإدخال (لغير الأطباء) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.subheader("📝 إدخال بيانات مراجع جديد")
            with st.form("entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    fname = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("العنوان:")
                    tdate = st.date_input("تاريخ الفحص:", value=date.today())
                with c2:
                    itype = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    tdev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    pcr = st.text_input("ملاحظات:")
                if st.form_submit_button("حفظ وإرسال للبيانات"):
                    if fname and addr:
                        supabase.table("patients").insert({"full_name": fname, "address": addr, "test_date": str(tdate), "infection_type": itype, "test_device": tdev, "pcr_result": pcr, "entry_center": st.session_state.center}).execute()
                        st.success("✅ تم حفظ السجل بنجاح")

    # --- 💬 تبويب الدردشة المباشرة (اللون الأسود) ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.subheader("💬 دردشة التواصل الفوري")
        
        # جلب آخر 30 رسالة
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
        
        chat_html = "<div class='chat-container'>"
        for m in reversed(msgs.data):
            time_str = m['created_at'][11:16]
            # تنسيق الرسالة لضمان اللون الأسود للخط
            chat_html += f"""
            <div class='chat-msg'>
                <b>{m['username']}</b> <small style='color: #666;'>({time_str})</small><br>
                <span>{m['message']}</span>
            </div>
            """
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # حقل الإرسال
        with st.container():
            c_input, c_btn = st.columns([5, 1])
            with c_input:
                user_msg = st.text_input("اكتب رسالتك هنا...", key="chat_input", label_visibility="collapsed")
            with c_btn:
                if st.button("إرسال"):
                    if user_msg:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": user_msg}).execute()
                        st.rerun()
