import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. تنسيق الواجهة (العودة للنمط الأسود والخط الواضح) ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    /* التنسيق العام للواجهة السوداء */
    .main { background-color: #0e1117; color: white; direction: rtl; text-align: right; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    
    /* تنسيق الأزرار باللون الأزرق المعتاد */
    .stButton>button { 
        width: 100%; border-radius: 8px; font-weight: bold; 
        background-color: #1e3a8a; color: white !important; 
    }

    /* --- تنسيق فقاعة الدردشة (الخط الأسود الواضح) --- */
    .chat-container {
        background: #1e293b; padding: 15px; border-radius: 12px;
        height: 400px; overflow-y: auto; border: 1px solid #334155;
    }
    .chat-bubble {
        background: #ffffff; padding: 10px; border-radius: 8px;
        margin-bottom: 10px; border-right: 5px solid #1e3a8a;
        color: #000000 !important; /* اللون الأسود الصافي */
        text-align: right;
    }
    
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
    # القائمة الجانبية
    st.sidebar.markdown(f"### 🛠️ لوحة التحكم\n**المستخدم:**\n{st.session_state.center}")
    if st.sidebar.button("🔴 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات (استرجاع كل شيء كما كان)
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 استعلام عن مراجع", "💬 الدردشة المباشرة"])
    else:
        tabs = st.tabs(["📝 تسجيل إصابة جديدة / أرشفة قديمة", "🔍 سجل المرضى والبحث", "💬 الدردشة المباشرة"])

    # --- تبويب الإضافة (المفقود سابقاً) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.markdown("### 📝 تسجيل مراجع جديد")
            with st.form("add_form", clear_on_submit=True):
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
                        st.success("✅ تمت الإضافة والمزامنة بنجاح")

    # --- تبويب البحث ---
    s_idx = 0 if st.session_state.is_doctor else 1
    with tabs[s_idx]:
        st.markdown("### 🔍 البحث في السجل")
        q = st.text_input("ادخل الاسم للبحث:")
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
            for row in res.data:
                with st.expander(f"👤 {row['full_name']} | {row['infection_type']}"):
                    st.write(f"📍 السكن: {row['address']} | 📅 التاريخ: {row['test_date']}")
                    st.write(f"🏢 المركز: {row['entry_center']} | 🔬 الجهاز: {row['test_device']}")

    # --- تبويب الدردشة المباشرة (حل مشكلة الأكواد) ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.markdown("### 💬 دردشة التواصل الفوري")
        
        # جلب الرسائل
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
        
        # بناء المحادثة (استخدام st.markdown مع unsafe_allow_html في كل لفة)
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for m in reversed(msgs.data):
            time_str = m['created_at'][11:16]
            # هنا الحل: عرض كل رسالة كـ Markdown منفصل مع HTML
            st.markdown(f"""
                <div class='chat-bubble'>
                    <b style='color: #1e3a8a;'>{m['username']}</b> 
                    <small style='color: #666;'>({time_str})</small><br>
                    <span style='color: #000000;'>{m['message']}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # صندوق الإرسال
        with st.container():
            c_in, c_bt = st.columns([5, 1])
            with c_in:
                user_msg = st.text_input("اكتب رسالتك...", key="msg_input", label_visibility="collapsed")
            with c_bt:
                if st.button("إرسال"):
                    if user_msg:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": user_msg}).execute()
                        st.rerun()
