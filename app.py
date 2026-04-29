import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. التنسيق (حل مشكلة الخط الطولي وترتيب النص) ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    /* الواجهة السوداء */
    .stApp { background-color: #0e1117; color: white; }
    
    /* منع الخط الطولي وتنسيق الصفحة لليمين */
    .main .block-container { direction: rtl; }
    
    /* مربع الدردشة - ثابت مع سكرول (صعود ونزول) */
    .chat-box { 
        background-color: #1e293b; 
        padding: 20px; 
        border-radius: 15px; 
        height: 500px; 
        overflow-y: scroll; /* يسمح بالصعود والنزول للرسائل القديمة */
        border: 1px solid #334155;
        display: flex;
        flex-direction: column;
    }
    
    /* الفقاعة البيضاء - النص بداخلها أسود ومرتب */
    .bubble {
        background-color: #ffffff;
        color: #000000 !important;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        width: fit-content;
        max-width: 80%;
        align-self: flex-start; /* تبدأ من اليمين بسبب الـ rtl */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    
    .bubble b { color: #1e3a8a; display: block; margin-bottom: 5px; }
    .bubble small { color: #666; }

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
    # السايد بار (لوحة التحكم)
    with st.sidebar:
        st.markdown(f"### 🛠️ لوحة التحكم\n**المستخدم:**\n{st.session_state.center}")
        if st.button("🔴 تسجيل الخروج"):
            st.session_state.clear()
            st.rerun()

    # التبويبات
    tab_titles = ["🔍 استعلام عن مراجع", "💬 الدردشة المباشرة"] if st.session_state.is_doctor else ["📝 تسجيل إصابة جديدة", "🔍 سجل المرضى", "💬 الدردشة المباشرة"]
    tabs = st.tabs(tab_titles)

    # --- تبويب الإضافة ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.markdown("### 📝 تسجيل مراجع جديد")
            with st.form("add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    f_name = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("العنوان:")
                    itype = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with c2:
                    tdev = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR", "VITEK"])
                    tdate = st.date_input("التاريخ:", value=date.today())
                    note = st.text_input("ملاحظات:")
                if st.form_submit_button("إرسال البيانات"):
                    if f_name:
                        supabase.table("patients").insert({"full_name": f_name, "address": addr, "test_date": str(tdate), "infection_type": itype, "test_device": tdev, "pcr_result": note, "entry_center": st.session_state.center}).execute()
                        st.success("✅ تم الحفظ")

    # --- تبويب الدردشة (المطلوب) ---
    chat_tab_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_tab_idx]:
        st.markdown("### 💬 دردشة التواصل الفوري")
        
        # جلب الرسائل من القاعدة
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(50).execute()
        
        # عرض الرسائل داخل الحاوية المخصصة (chat-box) التي تسمح بالسكرول
        chat_html = "<div class='chat-box'>"
        for m in reversed(msgs.data):
            time_val = m['created_at'][11:16]
            chat_html += f"""
            <div class='bubble'>
                <b>{m['username']}</b>
                <span>{m['message']}</span>
                <br><small>{time_val}</small>
            </div>
            """
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # نموذج الإرسال (تصفير تلقائي)
        with st.form("chat_form", clear_on_submit=True):
            ci, cb = st.columns([5, 1])
            with ci:
                u_msg = st.text_input("اكتب رسالتك...", label_visibility="collapsed")
            with cb:
                if st.form_submit_button("إرسال") and u_msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": u_msg}).execute()
                    st.rerun()
