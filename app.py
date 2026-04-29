import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. التنسيق (حل مشكلة الخط الطولي وترتيب المربعات البيضاء) ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    /* الواجهة السوداء */
    .stApp { background-color: #0e1117; color: white; }
    
    /* منع الخط الطولي تماماً وتعديل الاتجاه لليمين */
    .main .block-container { direction: rtl; text-align: right; }
    
    /* حاوية الدردشة مع خاصية السكرول (صعود ونزول) */
    .chat-container { 
        background-color: #1e293b; padding: 15px; border-radius: 12px; 
        height: 450px; overflow-y: auto; border: 1px solid #334155; 
        display: flex; flex-direction: column; gap: 10px;
    }
    
    /* المربع الأبيض للرسالة (نفس الصورة الأصلية) */
    .message-bubble { 
        background-color: #ffffff; color: #000000 !important; 
        padding: 12px; border-radius: 10px; border-right: 6px solid #1e3a8a;
        width: 95%; margin-bottom: 5px; box-shadow: 0px 2px 4px rgba(0,0,0,0.3);
    }
    .message-bubble b { color: #1e3a8a; font-size: 14px; }
    .message-bubble span { display: block; margin-top: 5px; font-size: 16px; font-weight: 500; }
    .message-bubble small { color: #666; font-size: 11px; }

    #MainMenu, footer, header {visibility: hidden;}
    </style>""", unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🏥 نظام مختبرات قضاء حديثة المركزية</h1>", unsafe_allow_html=True)
    centers = ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية', 'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر', 'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص']
    
    col1, _ = st.columns([1.5, 1])
    with col1:
        c_choice = st.selectbox("اختر الجهة المستخدِمة:", centers)
        a_code = st.text_input("كود الدخول السري:", type="password")
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", c_choice).eq("access_code", a_code).execute()
            if res.data:
                st.session_state.logged_in, st.session_state.center = True, c_choice
                st.session_state.is_doctor = "أطباء الاختصاص" in c_choice
                st.rerun()
            else: st.error("❌ الكود غير صحيح")
else:
    # السايد بار (بدون تداخل)
    with st.sidebar:
        st.markdown(f"### 🛠️ لوحة التحكم\n**المستخدم:**\n{st.session_state.center}")
        if st.button("🔴 تسجيل الخروج"):
            st.session_state.clear()
            st.rerun()

    # التبويبات
    tab_titles = ["🔍 استعلام عن مراجع", "💬 الدردشة المباشرة"] if st.session_state.is_doctor else ["📝 تسجيل إصابة جديدة", "🔍 سجل المرضى والبحث", "💬 الدردشة المباشرة"]
    tabs = st.tabs(tab_titles)

    # --- تبويب الإضافة (أفقي وسليم) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.markdown("### 📝 تسجيل مراجع جديد")
            with st.form("new_patient", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    fname = st.text_input("الاسم الرباعي للمراجع:")
                    addr = st.text_input("عنوان السكن:")
                    itype = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with c2:
                    tdev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    tdate = st.date_input("تاريخ الفحص:", value=date.today())
                    note = st.text_input("ملاحظات إضافية:")
                if st.form_submit_button("إرسال البيانات للقاعدة المركزية"):
                    if fname and addr:
                        supabase.table("patients").insert({"full_name": fname, "address": addr, "test_date": str(tdate), "infection_type": itype, "test_device": tdev, "pcr_result": note, "entry_center": st.session_state.center}).execute()
                        st.success(f"✅ تم حفظ {fname} بنجاح")

    # --- تبويب البحث (تم إصلاحه ليعمل بشكل مستقل) ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_idx]:
        st.markdown("### 🔍 خانة البحث في سجل المرضى")
        q = st.text_input("ادخل اسم المراجع للبحث عنه:")
        if q:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
            if results.data:
                for row in results.data:
                    with st.expander(f"👤 {row['full_name']} - {row['infection_type']}"):
                        st.write(f"📍 العنوان: {row['address']} | 📅 التاريخ: {row['test_date']}")
                        st.write(f"🏢 المركز: {row['entry_center']} | 🔬 الجهاز: {row['test_device']}")
            else: st.warning("لا توجد نتائج لهذا الاسم.")

    # --- تبويب الدردشة (حل مشكلة المربعات البيضاء والسكرول) ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.markdown("### 💬 دردشة التواصل الفوري")
        
        # جلب الرسائل
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(40).execute()
        
        # عرض الرسائل داخل "حاوية" بيضاء مرتبة
        chat_html = "<div class='chat-container'>"
        for m in reversed(msgs.data):
            t_str = m['created_at'][11:16]
            chat_html += f"""
            <div class='message-bubble'>
                <b>{m['username']}</b>
                <span>{m['message']}</span>
                <small>{t_str}</small>
            </div>
            """
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # نموذج الإرسال (تصفير تلقائي)
        with st.form("chat_input", clear_on_submit=True):
            ci, cb = st.columns([5, 1])
            with ci:
                u_msg = st.text_input("اكتب رسالتك هنا...", label_visibility="collapsed")
            with cb:
                if st.form_submit_button("إرسال") and u_msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": u_msg}).execute()
                    st.rerun()
