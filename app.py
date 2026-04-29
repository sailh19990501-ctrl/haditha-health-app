import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات قاعدة البيانات ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("فشل الاتصال بالسيرفر")

# --- 2. تصميم الواجهة والدردشة (CSS) ---
st.set_page_config(page_title="أرشيف المصابين", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; }
    
    /* منع النص الطولي وجعل البطاقات عريضة */
    .patient-card {
        background: #1e293b; padding: 20px; border-radius: 12px;
        margin-bottom: 15px; border-right: 8px solid #3b82f6; width: 100%;
    }

    /* نظام الدردشة (مثل الواتساب) */
    .chat-window {
        height: 400px; overflow-y: auto; 
        background: #0b141a; padding: 15px; border-radius: 10px;
        display: flex; flex-direction: column; gap: 10px;
        border: 1px solid #202c33;
    }
    .message-box {
        background: #202c33; color: white; padding: 10px 15px;
        border-radius: 10px; width: fit-content; max-width: 80%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .msg-sender { color: #00a884; font-weight: bold; font-size: 0.8em; margin-bottom: 3px; }
    .msg-text { font-size: 1em; line-height: 1.4; }

    /* تحسين شكل المدخلات */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. نظام الجلسة والدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🏥 أرشيف المصابين بالأمراض الانتقالية</h1>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            centers = [
                'مركز مصرف الدم الرئيسي', 
                'مختبر مستشفى حديثة للفحوصات الفيروسية', 
                'المركز التخصصي للاسنان', 
                'مركز صحي بروانه', 
                'مركز صحي حقلانية'
            ]
            u_center = st.selectbox("يرجى اختيار جهة العمل:", centers)
            u_code = st.text_input("الرمز السري:", type="password")
            
            if st.button("دخول النظام"):
                res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.center = u_center
                    # مصرف الدم والفيروسية هم الأدمن (الكل بالكل)
                    st.session_state.is_admin = u_center in ['مركز مصرف الدم الرئيسي', 'مختبر مستشفى حديثة للفحوصات الفيروسية']
                    st.rerun()
                else: st.error("❌ الرمز غير صحيح")

else:
    # --- القائمة الجانبية ---
    with st.sidebar:
        st.write(f"### 🏢 {st.session_state.center}")
        st.write("---")
        if st.button("🔴 خروج"):
            st.session_state.clear()
            st.rerun()

    # --- التبويبات الرئيسية ---
    tabs = st.tabs(["🔍 سجل المصابين والبحث", "📝 تسجيل إصابة جديدة", "💬 منصة الدردشة"])

    # --- 1. تبويب السجل والبحث ---
    with tabs[0]:
        st.subheader("🔍 البحث والمتابعة في السجل")
        search_name = st.text_input("ابحث عن الاسم الرباعي للمريض:")
        
        # جلب البيانات
        if search_name:
            data = supabase.table("patients").select("*").ilike("full_name", f"%{search_name}%").order("created_at", desc=True).execute()
        else:
            data = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if data.data:
            for p in data.data:
                # قانون الصلاحية: الأدمن يتحكم بالكل، المركز يتحكم بمالاته فقط
                can_action = st.session_state.is_admin or (p['entry_center'] == st.session_state.center)
                
                with st.container():
                    st.markdown(f"""<div class="patient-card">
                        <h3>👤 {p['full_name']}</h3>
                        <p>🔹 <b>الإصابة:</b> {p['infection_type']} | <b>التقنية:</b> {p['test_device']}</p>
                        <p>📅 <b>التاريخ:</b> {p['test_date']} | 🏢 <b>مكان الفحص:</b> {p['entry_center']}</p>
                        <p>📝 <b>ملاحظات:</b> {p['pcr_result']}</p>
                    </div>""", unsafe_allow_html=True)
                    
                    if can_action:
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button(f"🗑️ مسح المصاب نهائياً", key=f"del_{p['id']}"):
                                supabase.table("patients").delete().eq("id", p['id']).execute()
                                st.success("تم المسح بنجاح")
                                st.rerun()
                        with c2:
                            with st.expander("⚙️ تعديل بيانات المصاب"):
                                with st.form(f"edit_form_{p['id']}"):
                                    en = st.text_input("تعديل الاسم الرباعي:", value=p['full_name'])
                                    ei = st.selectbox("تعديل الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"], index=["HCV", "HBsAg", "HIV", "Syphilis"].index(p['infection_type']))
                                    ed = st.selectbox("تعديل التقنية:", ["Strips", "ELISA", "PCR"], index=["Strips", "ELISA", "PCR"].index(p['test_device']) if p['test_device'] in ["Strips", "ELISA", "PCR"] else 0)
                                    et = st.date_input("تعديل التاريخ:", value=datetime.strptime(p['test_date'], '%Y-%m-%d').date())
                                    enot = st.text_area("تعديل الملاحظات:", value=p['pcr_result'])
                                    
                                    if st.form_submit_button("حفظ التعديلات"):
                                        supabase.table("patients").update({
                                            "full_name": en, "infection_type": ei, "test_device": ed,
                                            "test_date": str(et), "pcr_result": enot
                                        }).eq("id", p['id']).execute()
                                        st.success("تم التعديل")
                                        st.rerun()
                    else:
                        st.caption("🔒 للقراءة فقط (لا تملك صلاحية التعديل/المسح لهذا المركز)")
                st.write("---")
        else: st.warning("لا توجد بيانات متاحة.")

    # --- 2. تبويب إضافة مراجع جديد ---
    with tabs[1]:
        st.subheader("📝 استمارة تسجيل إصابة")
        with st.form("add_new_patient", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                new_name = st.text_input("الاسم الرباعي للمريض:")
                new_inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                new_tech = st.selectbox("التقنية المستخدمة:", ["Strips", "ELISA", "PCR"])
            with col_b:
                new_date = st.date_input("تاريخ الفحص (تقويم مصغر):", value=date.today())
                new_notes = st.text_area("ملاحظات إضافية:")
            
            if st.form_submit_button("حفظ وإرسال إلى السجل"):
                if new_name:
                    supabase.table("patients").insert({
                        "full_name": new_name, "infection_type": new_inf,
                        "test_device": new_tech, "test_date": str(new_date),
                        "pcr_result": new_notes, "entry_center": st.session_state.center
                    }).execute()
                    st.success("✅ تم تسجيل المصاب بنجاح في سجل أرشيفك.")
                else: st.error("⚠️ يرجى كتابة الاسم الرباعي.")

    # --- 3. تبويب الدردشة (نظام واتساب) ---
    with tabs[2]:
        st.subheader("💬 منصة التواصل الفوري")
        
        # حاوية الرسائل (Scrolling)
        st.markdown('<div class="chat-window">', unsafe_allow_html=True)
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
        for m in reversed(msgs.data):
            st.markdown(f"""
            <div class="chat-bubble">
                <div class="msg-sender">{m['username']}</div>
                <div class="msg-text">{m['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # خانة الكتابة مع المسح التلقائي
        with st.form("chat_form", clear_on_submit=True):
            c_msg = st.text_input("اكتب رسالتك هنا...")
            if st.form_submit_button("إرسال"):
                if c_msg:
                    supabase.table("chat_messages").insert({
                        "username": st.session_state.center, 
                        "message": c_msg
                    }).execute()
                    st.rerun()
