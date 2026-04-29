import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. التصميم الطبي الأبيض النقي (RTL) ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""
    <style>
    /* بياض كامل للخلفية */
    .stApp {
        background-color: #FFFFFF !important;
        direction: rtl;
    }
    
    /* نصوص سوداء واضحة */
    h1, h2, h3, h4, label, p, span, div, .stMarkdown {
        color: #000000 !important;
        text-align: right !important;
    }

    /* صناديق إدخال بيضاء بحدود خفيفة (تجنب البلوكات السوداء) */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stDateInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
    }

    /* تنسيق التبويبات العلوي */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E5E7EB;
    }
    .stTabs [data-baseweb="tab"] {
        color: #000000 !important;
        font-weight: bold;
    }

    /* نظام الدردشة المدمج بتصميم طبي */
    .chat-window {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        height: 450px;
        overflow-y: auto;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        direction: rtl;
    }
    .chat-bubble {
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        background: #F3F4F6;
        border-right: 4px solid #111827; /* علامة سوداء رسمية */
        color: #000000;
    }

    /* إخفاء شعارات المطورين */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* أزرار سوداء/رمادية رسمية */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #000000;
        color: #FFFFFF !important;
        font-weight: bold;
        border: none;
        height: 45px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. اللوغو الطبي المتحرك في المقدمة ---
st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; flex-direction: column; padding-bottom: 20px;">
        <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
        <lottie-player src="https://assets10.lottiefiles.com/packages/lf20_7wwmup6o.json"  
            background="transparent"  speed="0.8"  style="width: 140px; height: 140px;"  loop  autoplay>
        </lottie-player>
        <h2 style="margin-top: 10px; font-weight: bold;">نظام الإدارة المخبرية - قضاء حديثة</h2>
    </div>
""", unsafe_allow_html=True)

# --- 4. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    centers_list = [
        'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
        'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
        'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
        'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص (للبحث والعرض فقط)'
    ]
    
    col_login, _ = st.columns([1.5, 1])
    with col_login:
        c_choice = st.selectbox("جهة الدخول:", centers_list)
        a_code = st.text_input("رمز الأمان الخاص بالجهة:", type="password")
        if st.button("دخول آمن"):
            res = supabase.table("center_access").select("*").eq("center_name", c_choice).eq("access_code", a_code).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = c_choice
                st.session_state.is_admin = res.data[0]['is_admin']
                st.session_state.is_doctor = "أطباء الاختصاص" in c_choice
                st.rerun()
            else:
                st.error("❌ الرمز غير صحيح")
else:
    # القائمة الجانبية
    st.sidebar.markdown(f"### 👤 {st.session_state.center}")
    st.sidebar.success("🟢 النظام متصل (Online)")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات بناءً على الصلاحيات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 استعلام مركزي", "💬 المحادثة المباشرة"])
    else:
        tabs = st.tabs(["📝 إضافة سجل", "🔍 السجلات العامة", "💬 المحادثة المباشرة"])

    # --- تبويب الإدخال ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            with st.form("entry_form"):
                st.markdown("#### 📄 بيانات المراجع")
                c1, c2 = st.columns(2)
                with c1:
                    fname = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("عنوان السكن:")
                with c2:
                    tdate = st.date_input("تاريخ الفحص:", value=date.today())
                    itype = st.selectbox("نوع الحالة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                
                c3, c4 = st.columns(2)
                with c3:
                    tdev = st.selectbox("الجهاز المستخدم:", ["Strips", "ELISA", "PCR", "VITEK"])
                with c4:
                    pcr_txt = st.text_input("نتائج إضافية / ملاحظات:")
                
                if st.form_submit_button("حفظ في القاعدة المركزية"):
                    if fname and addr:
                        supabase.table("patients").insert({
                            "full_name": fname, "address": addr, "test_date": str(tdate),
                            "infection_type": itype, "test_device": tdev, "pcr_result": pcr_txt,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الحفظ بنجاح")
                    else: st.warning("أكمل الحقول المطلوبة")

    # --- تبويب البحث ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_idx]:
        st.markdown("#### 🔍 البحث عن حالة")
        q = st.text_input("ادخل اسم المراجع:")
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
            if res.data:
                for row in res.data:
                    with st.expander(f"👤 {row['full_name']} - {row['infection_type']}"):
                        st.write(f"**📍 العنوان:** {row.get('address','-')} | **📅 التاريخ:** {row.get('test_date','-')}")
                        st.write(f"**🏢 الجهة:** {row.get('entry_center','-')} | **🔬 الجهاز:** {row.get('test_device','-')}")
                        if not st.session_state.is_doctor and (st.session_state.is_admin or st.session_state.center == row['entry_center']):
                            if st.button(f"حذف السجل نهائياً", key=f"d_{row['id']}"):
                                supabase.table("patients").delete().eq("id", row['id']).execute()
                                st.rerun()

    # --- تبويب المحادثة المباشرة المدمج ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.markdown("#### 💬 التواصل الفوري بين المراكز والمختبرات")
        
        # عرض الرسائل بتصميم فقاعات
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(25).execute()
        
        chat_html = "<div class='chat-window'>"
        for m in reversed(msgs.data):
            time_only = m['created_at'][11:16]
            chat_html += f"<div class='chat-bubble'><b>{m['username']}</b> <small style='color:#666;'>({time_only})</small><br>{m['message']}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # حقل الإرسال
        with st.container():
            c_input, c_send = st.columns([5, 1])
            with c_input:
                new_msg = st.text_input("اكتب رسالتك هنا...", key="msg_input", label_visibility="collapsed")
            with c_send:
                if st.button("إرسال"):
                    if new_msg:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": new_msg}).execute()
                        st.rerun()
