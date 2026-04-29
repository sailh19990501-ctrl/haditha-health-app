import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. التنسيق لضبط المحاذاة (الوسط واليمين) ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    /* إجبار الصفحة بالكامل على الاتجاه من اليمين لليسار */
    .stApp { background-color: #0e1117; color: white; direction: rtl !important; }
    
    /* إجبار كافة النصوص والحقول على المحاذاة لليمين */
    div[data-testid="stBlock"], .stTabs, .stForm, label, p, span { 
        direction: rtl !important; 
        text-align: right !important; 
    }

    /* توسيط العناوين الرئيسية */
    .centered-title {
        text-align: center !important;
        width: 100%;
        color: #3b82f6;
        font-weight: bold;
    }

    /* تعديل مدخلات النصوص لتكون يمين تماماً */
    input, select, textarea {
        text-align: right !important;
        direction: rtl !important;
    }

    /* تنسيق الأزرار */
    .stButton>button { 
        width: 100%; border-radius: 8px; font-weight: bold; 
        background-color: #1e3a8a; color: white !important; 
    }

    /* تنسيق الدردشة - الخط أسود والفقاعة يمين */
    .chat-container { background: #1e293b; padding: 15px; border-radius: 12px; height: 400px; overflow-y: auto; border: 1px solid #334155; }
    .chat-bubble { background: #ffffff; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-right: 5px solid #1e3a8a; color: #000000 !important; text-align: right; }
    
    #MainMenu, footer, header {visibility: hidden;}
    </style>""", unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='centered-title'>🏥 نظام مختبرات قضاء حديثة المركزية</h1>", unsafe_allow_html=True)
    centers = ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية', 'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر', 'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص']
    
    # توسيط نموذج الدخول
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
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
    # القائمة الجانبية يمين
    st.sidebar.markdown(f"<div style='text-align:right;'><h3>🛠️ لوحة التحكم</h3><b>المستخدم:</b><br>{st.session_state.center}</div>", unsafe_allow_html=True)
    if st.sidebar.button("🔴 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 استعلام عن مراجع", "💬 الدردشة المباشرة"])
    else:
        tabs = st.tabs(["📝 تسجيل إصابة جديدة", "🔍 سجل المرضى والبحث", "💬 الدردشة المباشرة"])

    # --- تبويب الإضافة ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.markdown("<h3 style='text-align:right;'>📝 تسجيل مراجع جديد</h3>", unsafe_allow_html=True)
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
        st.markdown("<h3 style='text-align:right;'>🔍 البحث في السجل</h3>", unsafe_allow_html=True)
        q = st.text_input("ادخل الاسم للبحث:")
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
            for row in res.data:
                with st.expander(f"👤 {row['full_name']} | {row['infection_type']}"):
                    st.write(f"📍 السكن: {row['address']} | 📅 التاريخ: {row['test_date']}")
                    st.write(f"🏢 المركز: {row['entry_center']} | 🔬 الجهاز: {row['test_device']}")

    # --- تبويب الدردشة (تصفير الحقل ثابت) ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.markdown("<h3 style='text-align:right;'>💬 دردشة التواصل الفوري</h3>", unsafe_allow_html=True)
        
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
        
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for m in reversed(msgs.data):
            time_str = m['created_at'][11:16]
            st.markdown(f"""
                <div class='chat-bubble'>
                    <b style='color: #1e3a8a;'>{m['username']}</b> <small style='color: #666;'>({time_str})</small><br>
                    <span style='color: #000000;'>{m['message']}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.container():
            c_in, c_bt = st.columns([5, 1])
            with c_in:
                st.text_input("اكتب رسالتك...", key="chat_input_key", label_visibility="collapsed")
            with c_bt:
                if st.button("إرسال"):
                    msg_text = st.session_state.get("chat_input_key", "")
                    if msg_text:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": msg_text}).execute()
                        st.session_state["chat_input_key"] = ""
                        st.rerun()
