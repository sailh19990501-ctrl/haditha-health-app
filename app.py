import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. التنسيق والألوان الأصلية ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    
    /* الألوان الزرقاء الأصلية */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        background-color: #1e3a8a; 
        color: white !important; 
    }
    
    /* تنسيق حاوية الدردشة - النمط الأول */
    .chat-container {
        background: #f1f5f9;
        padding: 15px;
        border-radius: 10px;
        height: 400px;
        overflow-y: auto;
        border: 1px solid #cbd5e1;
    }
    
    /* تنسيق فقاعة الرسالة - لون أسود واضح */
    .chat-bubble {
        background: white;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-right: 5px solid #1e3a8a;
        color: #000000 !important; /* خط أسود غامق */
        text-align: right;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        font-family: sans-serif;
    }
    </style>""", unsafe_allow_html=True)

# --- 3. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏥 نظام مختبرات قضاء حديثة</h2>", unsafe_allow_html=True)
    centers_list = ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية', 'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر', 'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص']
    
    col_l, _ = st.columns([1.5, 1])
    with col_l:
        c_choice = st.selectbox("الجهة المستخدِمة:", centers_list)
        a_code = st.text_input("رمز الدخول:", type="password")
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", c_choice).eq("access_code", a_code).execute()
            if res.data:
                st.session_state.logged_in, st.session_state.center = True, c_choice
                st.session_state.is_doctor = "أطباء الاختصاص" in c_choice
                st.rerun()
            else: st.error("❌ الرمز خاطئ")
else:
    # القائمة الجانبية
    st.sidebar.info(f"المستخدم الحالي: {st.session_state.center}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات
    tabs = st.tabs(["📝 السجلات", "💬 الدردشة المباشرة"])

    # --- تبويب السجلات ---
    with tabs[0]:
        st.subheader("🔍 البحث والإدارة")
        # (هنا تضع كود البحث والإدخال كما في النسخ السابقة)
        st.info("قسم السجلات والبحث نشط وفق الألوان الأصلية.")

    # --- تبويب الدردشة المباشرة (حل مشكلة ظهور الأكواد) ---
    with tabs[1]:
        st.subheader("💬 دردشة التواصل الفوري")
        
        # جلب الرسائل
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
        
        # بناء شكل الدردشة يدوياً لمنع ظهور الأكواد كنص
        chat_content = "<div class='chat-container'>"
        for m in reversed(msgs.data):
            time_val = m['created_at'][11:16]
            chat_content += f"""
            <div class='chat-bubble'>
                <b style='color: #1e3a8a;'>{m['username']}</b> 
                <small style='color: #666;'>({time_val})</small><br>
                <span style='color: #000000; font-size: 1.1rem;'>{m['message']}</span>
            </div>
            """
        chat_content += "</div>"
        
        # العرض باستخدام دالة التنسيق الصحيحة
        st.markdown(chat_content, unsafe_allow_html=True)
        
        # الإرسال
        with st.container():
            c_in, c_bt = st.columns([5, 1])
            with c_in:
                new_msg = st.text_input("اكتب رسالتك...", key="chat_input", label_visibility="collapsed")
            with c_bt:
                if st.button("إرسال"):
                    if new_msg:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": new_msg}).execute()
                        st.rerun()
