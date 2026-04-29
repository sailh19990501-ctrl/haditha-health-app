import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# --- 2. التنسيق الجمالي والألوان الأصلية ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    /* الإعدادات العامة للاتجاه من اليمين لليسار */
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    
    /* الألوان الزرقاء للأزرار والعناوين */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        background-color: #1e3a8a; 
        color: white !important; 
        font-weight: bold;
    }
    
    label, h2, h3 { font-weight: bold; color: #1e3a8a; text-align: right; }

    /* --- تنسيق الدردشة المباشرة (النمط الأول النظيف) --- */
    .chat-container {
        background: #f8fafc;
        padding: 15px;
        border-radius: 12px;
        height: 400px;
        overflow-y: auto;
        border: 1px solid #cbd5e1;
        direction: rtl;
    }
    .chat-bubble {
        background: #ffffff;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-right: 5px solid #1e3a8a;
        text-align: right;
        color: #000000 !important; /* لون الخط أسود واضح جداً */
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    #MainMenu, footer, header {visibility: hidden;} /* إخفاء قوائم ستريمليت الافتراضية */
    </style>""", unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🏥 نظام مختبرات قضاء حديثة المركزية</h2>", unsafe_allow_html=True)
    centers_list = [
        'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
        'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
        'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
        'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص'
    ]
    col_l, _ = st.columns([1.5, 1])
    with col_l:
        c_choice = st.selectbox("الجهة المستخدِمة:", centers_list)
        a_code = st.text_input("رمز الدخول السري:", type="password")
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", c_choice).eq("access_code", a_code).execute()
            if res.data:
                st.session_state.logged_in, st.session_state.center = True, c_choice
                st.session_state.is_admin = res.data[0]['is_admin']
                st.session_state.is_doctor = "أطباء الاختصاص" in c_choice
                st.rerun()
            else: st.error("❌ الكود غير صحيح")
else:
    # القائمة الجانبية (لوحة التحكم)
    st.sidebar.markdown(f"### 🛠️ لوحة التحكم")
    st.sidebar.info(f"المستخدم الحالي:\n{st.session_state.center}")
    if st.sidebar.button("🔴 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # التبويبات (الإضافات والبحث والدردشة)
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 استعلام عن حالة مراجع", "💬 الدردشة المباشرة"])
    else:
        tabs = st.tabs(["📝 تسجيل إصابة جديدة / أرشفة قديمة", "🔍 سجل المرضى والبحث", "💬 الدردشة المباشرة"])

    # --- تبويب الإدخال (الذي ظهر في صوره 1000134295) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.markdown("### 📝 إضافة سجل مراجع")
            with st.form("main_entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    fname = st.text_input("الاسم الرباعي للمراجع:")
                    addr = st.text_input("عنوان السكن:")
                    itype = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with c2:
                    tdev = st.selectbox("جهاز الفحص المستخدم:", ["Strips", "ELISA", "PCR", "VITEK"])
                    tdate = st.date_input("تاريخ إجراء الفحص (اختر اليوم بدقة):", value=date.today())
                    pcr_note = st.text_input("ملاحظات إضافية (اختياري):")
                
                if st.form_submit_button("إرسال البيانات للقاعدة المركزية"):
                    if fname and addr:
                        supabase.table("patients").insert({
                            "full_name": fname, "address": addr, "test_date": str(tdate),
                            "infection_type": itype, "test_device": tdev, "pcr_result": pcr_note,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الحفظ والمزامنة بنجاح")
                    else: st.warning("يرجى ملء الحقول الأساسية (الاسم والعنوان)")

    # --- تبويب البحث (الذي ظهر في صوره 1000134291) ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_idx]:
        st.markdown("### 🔍 استعلام عن حالة مراجع")
        q_name = st.text_input("ادخل الاسم الرباعي للبحث عنه في كافة المراكز:")
        if q_name:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{q_name}%").execute()
            if results.data:
                for row in results.data:
                    with st.expander(f"👤 {row['full_name']} - {row['infection_type']}"):
                        st.write(f"**📍 السكن:** {row['address']} | **📅 التاريخ:** {row['test_date']}")
                        st.write(f"**🏢 المركز:** {row['entry_center']} | **🔬 الجهاز:** {row['test_device']}")
                        st.write(f"**📝 ملاحظات:** {row['pcr_result']}")
                        if not st.session_state.is_doctor and (st.session_state.is_admin or st.session_state.center == row['entry_center']):
                            if st.button(f"حذف السجل", key=f"del_{row['id']}"):
                                supabase.table("patients").delete().eq("id", row['id']).execute()
                                st.rerun()
            else: st.info("🔍 لا توجد نتائج مطابقة لهذا الاسم.")

    # --- تبويب الدردشة (الذي ظهر في صوره 1000134300) ---
    chat_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_idx]:
        st.markdown("### 💬 دردشة التواصل الفوري")
        
        # جلب الرسائل من قاعدة البيانات
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(25).execute()
        
        chat_html = "<div class='chat-container'>"
        for m in reversed(msgs.data):
            msg_time = m['created_at'][11:16]
            chat_html += f"""
            <div class='chat-bubble'>
                <b style='color: #1e3a8a;'>{m['username']}</b> 
                <small style='color: #666;'>({msg_time})</small><br>
                <span>{m['message']}</span>
            </div>
            """
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # حقل الإرسال
        with st.container():
            c_input, c_send = st.columns([5, 1])
            with c_input:
                new_msg = st.text_input("اكتب رسالتك هنا...", key="chat_msg_input", label_visibility="collapsed")
            with c_send:
                if st.button("إرسال"):
                    if new_msg:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": new_msg}).execute()
                        st.rerun()

