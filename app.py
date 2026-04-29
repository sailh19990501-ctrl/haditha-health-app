import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. استعادة الألوان السابقة وتنسيق RTL ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    /* الألوان السابقة (خلفية هادئة ونصوص واضحة) */
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    
    /* تصميم البلوكات (العودة للنمط السابق المريح) */
    div[data-testid="stExpander"] { 
        background-color: #ffffff; 
        border-radius: 12px; 
        border: 1px solid #e2e8f0; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    
    /* الألوان الزرقاء والداكنة السابقة للأزرار */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        background-color: #1e3a8a; 
        color: white; 
    }
    
    label { font-weight: bold; font-size: 1.1rem; color: #1e3a8a; }

    /* نظام الدردشة المباشرة - تصميم مريح */
    .chat-container {
        background: #f1f5f9;
        padding: 15px;
        border-radius: 10px;
        height: 350px;
        overflow-y: auto;
        border: 1px solid #cbd5e1;
        direction: rtl;
        margin-bottom: 10px;
    }
    .chat-msg {
        background: white;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-right: 4px solid #1e3a8a;
        text-align: right;
    }
    
    #MainMenu, footer, header {visibility: hidden;} /* تنظيف الواجهة */
    </style>""", unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.title("🏥 نظام مختبرات قضاء حديثة")
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
    # القائمة الجانبية (Sidebar)
    st.sidebar.info(f"المستخدم: {st.session_state.center}")
    st.sidebar.success("🟢 المتصلون الآن: 11 جهاز")
    if st.sidebar.button("🔴 خروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات (حسب الصلاحية)
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 البحث والاستعلام", "💬 الدردشة المباشرة"])
    else:
        tabs = st.tabs(["📝 تسجيل مراجع", "🔍 السجلات والإدارة", "💬 الدردشة المباشرة"])

    # --- 1. تسجيل السجلات (للمخوّلين) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.subheader("📝 إدخال بيانات مراجع جديد")
            with st.form("main_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    fname = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("العنوان:")
                    tdate = st.date_input("تاريخ الفحص:", value=date.today())
                with c2:
                    itype = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    tdev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    pcr = st.text_input("ملاحظات إضافية:")
                if st.form_submit_button("حفظ وإرسال"):
                    if fname and addr:
                        supabase.table("patients").insert({"full_name": fname, "address": addr, "test_date": str(tdate), "infection_type": itype, "test_device": tdev, "pcr_result": pcr, "entry_center": st.session_state.center}).execute()
                        st.success("✅ تم الحفظ بنجاح")
                    else: st.warning("اكمل الحقول")

    # --- 2. البحث (متاح للجميع) ---
    s_idx = 0 if st.session_state.is_doctor else 1
    with tabs[s_idx]:
        st.subheader("🔍 البحث في السجل المركزي")
        q = st.text_input("ابحث بالاسم الرباعي:")
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
            for row in res.data:
                with st.expander(f"👤 {row['full_name']} | {row['infection_type']}"):
                    st.write(f"📍 السكن: {row.get('address','-')} | 📅 التاريخ: {row.get('test_date','-')}")
                    st.write(f"🏢 المركز: {row.get('entry_center','-')} | 🔬 الجهاز: {row.get('test_device','-')}")
                    if not st.session_state.is_doctor and (st.session_state.is_admin or st.session_state.center == row.get('entry_center')):
                        if st.button("🗑️ حذف السجل", key=f"del_{row['id']}"):
                            supabase.table("patients").delete().eq("id", row['id']).execute()
                            st.rerun()

    # --- 3. الدردشة المباشرة (Live Chat) ---
    c_idx = 1 if st.session_state.is_doctor else 2
    with tabs[c_idx]:
        st.subheader("💬 دردشة التواصل الفوري")
        
        # جلب الرسائل
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
        
        chat_html = "<div class='chat-container'>"
        for m in reversed(msgs.data):
            t = m['created_at'][11:16]
            chat_html += f"<div class='chat-msg'><b>{m['username']}</b> <small>({t})</small>:<br>{m['message']}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # صندوق الإرسال
        with st.container():
            c_in, c_bt = st.columns([4, 1])
            with c_in:
                u_msg = st.text_input("اكتب رسالتك...", key="chat_input", label_visibility="collapsed")
            with c_bt:
                if st.button("إرسال"):
                    if u_msg:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": u_msg}).execute()
                        st.rerun()
