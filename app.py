import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الاتصال (مؤمنة) ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. التنسيق العام (الواجهة السوداء والترتيب الأفقي) ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    /* الواجهة السوداء */
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    
    /* إجبار المحاذاة لليمين بدون تداخل طولي */
    [data-testid="stVerticalBlock"] > div { direction: rtl !important; }
    
    /* أزرار زرقاء قوية */
    .stButton>button { 
        width: 100%; border-radius: 8px; font-weight: bold; 
        background-color: #1e3a8a; color: white !important; 
    }
    
    /* تنسيق الدردشة - فقاعة بيضاء بخط أسود فاحم */
    .chat-container { 
        background: #1e293b; padding: 15px; border-radius: 12px; 
        height: 400px; overflow-y: auto; border: 1px solid #334155; 
        margin-bottom: 15px;
    }
    .chat-bubble { 
        background: #ffffff; padding: 10px; border-radius: 8px; 
        margin-bottom: 10px; border-right: 5px solid #3b82f6; 
        color: #000000 !important; text-align: right; 
    }
    .chat-bubble b { color: #1e3a8a; } /* اسم المرسل أزرق */
    
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
    st.sidebar.markdown(f"### 🛠️ لوحة التحكم\n**المستخدم:** {st.session_state.center}")
    if st.sidebar.button("🔴 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 استعلام عن مراجع", "💬 الدردشة المباشرة"])
    else:
        tabs = st.tabs(["📝 تسجيل إصابة جديدة", "🔍 سجل المرضى والبحث", "💬 الدردشة المباشرة"])

    # --- تبويب الإضافة (أفقي ومرتب) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.markdown("### 📝 تسجيل مراجع جديد")
            # استخدام clear_on_submit يضمن تصفير الخانات فوراً بعد النجاح
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
                
                submitted = st.form_submit_button("إرسال البيانات للقاعدة المركزية")
                if submitted:
                    if fname and addr:
                        # عملية الإضافة للقاعدة
                        supabase.table("patients").insert({
                            "full_name": fname, "address": addr, "test_date": str(tdate),
                            "infection_type": itype, "test_device": tdev, "pcr_result": note,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success(f"✅ تم حفظ بيانات المراجع ({fname}) بنجاح")
                    else:
                        st.error("❌ يرجى كتابة الاسم والعنوان أولاً")

    # --- تبويب البحث ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_idx]:
        st.markdown("### 🔍 البحث في السجل المركزي")
        search_q = st.text_input("ادخل اسم المراجع للبحث:")
        if search_q:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{search_q}%").execute()
            if results.data:
                for row in results.data:
                    with st.expander(f"👤 {row['full_name']} | {row['infection_type']}"):
                        st.write(f"**📍 السكن:** {row['address']} | **📅 التاريخ:** {row['test_date']}")
                        st.write(f"**🏢 المركز:** {row['entry_center']} | **🔬 الجهاز:** {row['test_device']}")
                        st.write(f"**📝 ملاحظات:** {row['pcr_result']}")
            else: st.info("لا توجد سجلات بهذا الاسم.")

    # --- تبويب الدردشة (نظام تصفير الحقل بدون أخطاء) ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.markdown("### 💬 دردشة التواصل الفوري")
        
        # عرض الرسائل في حاوية
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(25).execute()
        
        # بناء شكل المحادثة
        chat_html = "<div class='chat-container'>"
        for m in reversed(msgs.data):
            time_val = m['created_at'][11:16]
            chat_html += f"<div class='chat-bubble'><b>{m['username']}</b> <small>({time_val})</small><br>{m['message']}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # نموذج الإرسال - يصفر تلقائياً بمجرد الضغط على إرسال
        with st.form("chat_input_form", clear_on_submit=True):
            col_msg, col_btn = st.columns([5, 1])
            with col_msg:
                msg_input = st.text_input("اكتب رسالتك هنا...", label_visibility="collapsed")
            with col_btn:
                send_btn = st.form_submit_button("إرسال")
            
            if send_btn and msg_input:
                supabase.table("chat_messages").insert({"username": st.session_state.center, "message": msg_input}).execute()
                st.rerun()
