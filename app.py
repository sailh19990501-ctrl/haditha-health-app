import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الاتصال ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. التنسيق (تم حذف مسببات الخط الطولي) ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    /* الواجهة السوداء */
    .stApp { background-color: #0e1117; color: white; }
    
    /* ضبط الاتجاه العام لليمين بشكل آمن */
    .main .block-container { direction: rtl; text-align: right; }
    
    /* تنسيق الدردشة - فقاعة بيضاء نص أسود */
    .chat-container { 
        background: #1e293b; padding: 15px; border-radius: 12px; 
        height: 400px; overflow-y: auto; border: 1px solid #334155; 
        margin-bottom: 10px;
    }
    .chat-bubble { 
        background: #ffffff; padding: 10px; border-radius: 8px; 
        margin-bottom: 10px; border-right: 5px solid #3b82f6; 
        color: #000000 !important; text-align: right;
    }
    .chat-bubble b { color: #1e3a8a; }

    /* إخفاء القوائم غير الضرورية */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* منع تداخل السايد بار مع المحتوى */
    section[data-testid="stSidebar"] { direction: rtl; }
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
    # القائمة الجانبية (Sidebar) - عادت لمكانها الطبيعي
    with st.sidebar:
        st.markdown(f"### 🛠️ لوحة التحكم\n**المستخدم:**\n{st.session_state.center}")
        if st.button("🔴 تسجيل الخروج"):
            st.session_state.clear()
            st.rerun()

    # التبويبات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 استعلام عن مراجع", "💬 الدردشة المباشرة"])
    else:
        tabs = st.tabs(["📝 تسجيل إصابة جديدة", "🔍 سجل المرضى والبحث", "💬 الدردشة المباشرة"])

    # --- تبويب الإضافة (أفقي وسليم) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.markdown("### 📝 تسجيل مراجع جديد")
            with st.form("add_patient_form", clear_on_submit=True):
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
                        supabase.table("patients").insert({
                            "full_name": fname, "address": addr, "test_date": str(tdate),
                            "infection_type": itype, "test_device": tdev, "pcr_result": note,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success(f"✅ تم الحفظ بنجاح: {fname}")

    # --- تبويب البحث ---
    s_idx = 0 if st.session_state.is_doctor else 1
    with tabs[s_idx]:
        st.markdown("### 🔍 البحث في السجل")
        q = st.text_input("ادخل الاسم للبحث:")
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
            for row in res.data:
                with st.expander(f"👤 {row['full_name']} | {row['infection_type']}"):
                    st.write(f"📍 السكن: {row['address']} | 🏢 المركز: {row['entry_center']}")

    # --- تبويب الدردشة (تصفير تلقائي بدون Error) ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.markdown("### 💬 دردشة التواصل الفوري")
        
        # جلب الرسائل
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
        
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for m in reversed(msgs.data):
            t_str = m['created_at'][11:16]
            st.markdown(f"<div class='chat-bubble'><b>{m['username']}</b> <small>({t_str})</small><br>{m['message']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # نموذج الإرسال (تصفير تلقائي)
        with st.form("chat_form", clear_on_submit=True):
            col_in, col_btn = st.columns([5, 1])
            with col_in:
                u_msg = st.text_input("اكتب رسالتك...", label_visibility="collapsed")
            with col_btn:
                if st.form_submit_button("إرسال") and u_msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": u_msg}).execute()
                    st.rerun()
