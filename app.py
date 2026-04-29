import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. إعدادات الصفحة والتصميم الأبيض الاحترافي ---
st.set_page_config(page_title="نظام مختبرات حديثة المركزي", layout="wide")

st.markdown("""
    <style>
    /* محاذاة الصفحة بالكامل وخلفية بيضاء */
    .main, .stApp {
        direction: rtl;
        text-align: right;
        background-color: #ffffff; /* خلفية بيضاء */
        color: #000000; /* خط أسود */
    }
    
    /* جعل كافة النصوص باللون الأسود */
    h1, h2, h3, h4, label, p, span, div {
        color: #000000 !important;
    }

    /* تنسيق الحقول والقوائم */
    div[data-testid="stSelectbox"], div[data-testid="stTextInput"], 
    div[data-testid="stTextArea"], div[data-testid="stDateInput"] {
        direction: rtl;
        text-align: right;
        background-color: #fcfcfc;
    }

    /* تصميم الدردشة */
    .chat-container {
        background: #fdfdfd;
        padding: 15px;
        border-radius: 12px;
        height: 400px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        direction: rtl;
    }
    .msg-box {
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 8px;
        background: #f5f5f5;
        border-right: 5px solid #424242; /* خط أسود/رمادي غامق */
        text-align: right;
        color: #000000;
    }

    /* إخفاء خيارات المطورين */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* تنسيق الأزرار (رمادي غامق/أسود لتناسب الواجهة البيضاء) */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #212121;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #000000;
        color: white;
    }

    /* لوغو متحرك في الخلفية أو الأعلى */
    .logo-container {
        display: flex;
        justify-content: center;
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- إضافة لوغو مختبرات متحرك في أعلى الصفحة (عبر رابط Lottie) ---
st.markdown("""
    <div class="logo-container">
        <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
        <lottie-player src="https://assets10.lottiefiles.com/packages/lf20_7wwmup6o.json"  
            background="transparent"  speed="1"  style="width: 150px; height: 150px;"  loop  autoplay>
        </lottie-player>
    </div>
""", unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🏥 نظام مختبرات قضاء حديثة</h1>", unsafe_allow_html=True)
    
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
            else:
                st.error("❌ الكود غير صحيح")
else:
    # القائمة الجانبية
    st.sidebar.markdown(f"### 👤 الملف الشخصي")
    st.sidebar.info(f"المستخدم: {st.session_state.center}")
    st.sidebar.success("🟢 أجهزة متصلة: 11 جهاز")
    
    if st.sidebar.button("🔴 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 البحث في السجل", "💬 الدردشة الفورية"])
    else:
        tabs = st.tabs(["📝 تسجيل مراجع", "🔍 السجل والإدارة", "💬 الدردشة الفورية"])

    # --- 1. واجهة الإدخال ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.subheader("📋 إدخال بيانات مراجع")
            with st.form("entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    fname = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("العنوان:")
                with c2:
                    tdate = st.date_input("تاريخ الفحص:", value=date.today())
                    itype = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                
                c3, c4 = st.columns(2)
                with c3:
                    tdev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                with c4:
                    pcr_n = st.text_input("ملاحظات إضافية:")
                
                if st.form_submit_button("حفظ وإرسال"):
                    if fname and addr:
                        supabase.table("patients").insert({
                            "full_name": fname, "address": addr, "test_date": str(tdate),
                            "infection_type": itype, "test_device": tdev, "pcr_result": pcr_n,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success(f"✅ تم الحفظ: {fname}")
                    else:
                        st.warning("⚠️ أكمل الاسم والعنوان")

    # --- 2. واجهة البحث ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_idx]:
        st.subheader("🔍 استعلام عن حالة")
        q_name = st.text_input("ابحث بالاسم:")
        if q_name:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{q_name}%").execute()
            if results.data:
                for row in results.data:
                    with st.expander(f"📄 {row['full_name']} | {row.get('infection_type','-')}"):
                        ca, cb = st.columns(2)
                        with ca:
                            st.write(f"**📍 العنوان:** {row.get('address','-')}")
                            st.write(f"**📅 التاريخ:** {row.get('test_date','-')}")
                        with cb:
                            st.write(f"**🏢 المركز:** {row.get('entry_center','-')}")
                            st.write(f"**🔬 الجهاز:** {row.get('test_device','-')}")
                        
                        if not st.session_state.is_doctor:
                            if st.session_state.is_admin or st.session_state.center == row.get('entry_center'):
                                if st.button(f"🗑️ حذف", key=f"del_{row['id']}"):
                                    supabase.table("patients").delete().eq("id", row['id']).execute()
                                    st.rerun()

    # --- 3. الدردشة ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.subheader("💬 دردشة التواصل")
        messages = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
        
        chat_html = "<div class='chat-container'>"
        for m in reversed(messages.data):
            chat_html += f"<div class='msg-box'><b>{m['username']}:</b> {m['message']}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        c_msg, c_btn = st.columns([4, 1])
        with c_msg:
            user_msg = st.text_input("اكتب هنا...", key="chat_input", label_visibility="collapsed")
        with c_btn:
            if st.button("إرسال"):
                if user_msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": user_msg}).execute()
                    st.rerun()
