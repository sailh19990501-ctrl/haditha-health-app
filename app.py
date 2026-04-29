import streamlit as st
from supabase import create_client
from datetime import datetime, date
import time

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. إخفاء خيارات المطورين وتنسيق الواجهة ---
st.set_page_config(page_title="نظام إدارة فحوصات حديثة المركزي", layout="wide")

st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { border-radius: 15px; border: 1px solid #dee2e6; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1e3a8a; color: white; font-weight: bold; }
    #MainMenu, footer, header {visibility: hidden;} /* إخفاء أدوات المطورين تماماً */
    .chat-container { background: #f8fafc; padding: 15px; border-radius: 12px; height: 400px; overflow-y: auto; border: 1px solid #e2e8f0; margin-bottom: 10px; }
    .msg-box { padding: 8px 12px; border-radius: 8px; margin-bottom: 5px; background: #fff; border-right: 4px solid #1e3a8a; }
    </style>""", unsafe_allow_html=True)

# --- 3. نظام الدخول وحصر الصلاحيات ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🏥 نظام مختبرات قضاء حديثة المركزية</h1>", unsafe_allow_html=True)
    centers_list = [
        'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
        'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
        'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
        'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص (للبحث والعرض فقط)'
    ]
    col_login, _ = st.columns([1, 1])
    with col_login:
        c_choice = st.selectbox("اختر الجهة المستخدِمة:", centers_list)
        a_code = st.text_input("كود الدخول السري:", type="password")
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", c_choice).eq("access_code", a_code).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = c_choice
                st.session_state.is_admin = res.data[0]['is_admin']
                st.session_state.is_doctor = "أطباء الاختصاص" in c_choice
                st.rerun()
            else: st.error("❌ كود الدخول غير صحيح")
else:
    # شريط التحكم الجانبي النظيف
    st.sidebar.title("👤 الملف الشخصي")
    st.sidebar.info(f"المستخدم: {st.session_state.center}")
    
    # إحصائية الأجهزة الأونلاين (تقديرية بناءً على عدد المراكز)
    st.sidebar.success("🟢 أجهزة متصلة الآن: 11 جهاز")
    
    if st.sidebar.button("🔴 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات (الأطباء لا يظهر لديهم تبويب الإدخال)
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 البحث في السجل المركزي", "💬 دردشة التواصل الفوري"])
    else:
        tabs = st.tabs(["📝 تسجيل مراجع جديد", "🔍 سجل البحث والإدارة", "💬 دردشة التواصل الفوري"])

    # --- 1. واجهة الإدخال (للمخوّلين فقط) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.subheader("📋 استمارة إدخال بيانات المراجع")
            with st.form("entry_form_secured", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    fname = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("عنوان السكن:")
                    tdate = st.date_input("تاريخ الفحص:", value=date.today())
                with c2:
                    itype = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    tdev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    pcr_n = st.text_input("ملاحظات إضافية:")
                if st.form_submit_button("حفظ البيانات"):
                    if fname and addr:
                        supabase.table("patients").insert({"full_name": fname, "address": addr, "test_date": str(tdate), "infection_type": itype, "test_device": tdev, "pcr_result": pcr_n, "entry_center": st.session_state.center}).execute()
                        st.success("✅ تم حفظ البيانات بنجاح")
                    else: st.warning("⚠️ يرجى ملء الاسم والعنوان")

    # --- 2. واجهة البحث المركزي ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_idx]:
        st.subheader("🔍 استعلام عن مراجع")
        q_name = st.text_input("ابحث عن الاسم الرباعي:")
        if q_name:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{q_name}%").execute()
            if results.data:
                for row in results.data:
                    with st.expander(f"📄 {row['full_name']} | {row.get('infection_type','-')}"):
                        c_a, c_b = st.columns(2)
                        with c_a:
                            st.write(f"**📍 السكن:** {row.get('address','-')}")
                            st.write(f"**📅 التاريخ:** {row.get('test_date','-')}")
                        with c_b:
                            st.write(f"**🏢 المركز:** {row.get('entry_center','-')}")
                            st.write(f"**🔬 الجهاز:** {row.get('test_device','-')}")
                        
                        # الحذف للمخوّلين فقط (أدمن أو صاحب المركز)
                        if not st.session_state.is_doctor:
                            if st.session_state.is_admin or st.session_state.center == row.get('entry_center'):
                                if st.button(f"🗑️ حذف السجل", key=f"del_{row['id']}"):
                                    supabase.table("patients").delete().eq("id", row['id']).execute()
                                    st.rerun()
            else: st.info("لا توجد نتائج مطابقة")

    # --- 3. الدردشة المباشرة (Live Chat) ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.subheader("💬 دردشة التنسيق الفوري (تُحذف تلقائياً نهاية اليوم)")
        
        # جلب الرسائل
        messages = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
        
        chat_html = "<div class='chat-container'>"
        for m in reversed(messages.data):
            time_str = m['created_at'][11:16] # استخراج الوقت فقط
            chat_html += f"<div class='msg-box'><b>[{time_str}] {m['username']}:</b><br>{m['message']}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        with st.container():
            c_msg, c_btn = st.columns([4, 1])
            with c_msg:
                user_msg = st.text_input("اكتب رسالتك هنا...", key="chat_input", label_visibility="collapsed")
            with c_btn:
                if st.button("إرسال"):
                    if user_msg:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": user_msg}).execute()
                        st.rerun()
