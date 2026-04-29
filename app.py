import streamlit as st
from supabase import create_client
from datetime import datetime, date
import time

# --- 1. إعدادات الاتصال الآمن ---
# نستخدم Supabase كقاعدة بيانات سحابية مركزية لربط كافة المراكز
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as connection_error:
    st.error(f"فشل الاتصال بالخادم المركزي: {connection_error}")

# --- 2. التنسيق الجمالي (CSS) - تم تبسيطه لمنع الخط الطولي ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    /* واجهة داكنة مريحة للعين */
    .stApp { background-color: #0e1117; color: white; }
    
    /* ضبط الاتجاه من اليمين لليسار لكافة العناصر */
    .main .block-container { direction: rtl; text-align: right; }
    
    /* تحسين شكل الحقول المدخلة */
    .stTextInput input, .stSelectbox div { background-color: #1e293b !important; color: white !important; border-radius: 8px !important; }
    
    /* تنسيق أزرار الإرسال لتكون واضحة وباللون الأزرق الطبي */
    .stButton>button { 
        width: 100%; border-radius: 8px; background-color: #2563eb; color: white;
        height: 3em; border: none; font-weight: bold;
    }
    
    /* إخفاء القوائم غير الضرورية لزيادة المساحة */
    #MainMenu, footer, header { visibility: hidden; }

    /* تنسيق حاوية الدردشة لمنع التداخل */
    .chat-area {
        border: 1px solid #334155; border-radius: 12px; padding: 15px;
        background-color: #111827; height: 550px; overflow-y: auto;
    }
</style>""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية لإدارة البيانات (Backend Logic) ---

def insert_new_patient(p_name, p_address, p_inf, p_dev, p_date, p_notes):
    """إضافة مراجع جديد لقاعدة البيانات المركزية مع التحقق من الهوية"""
    entry_data = {
        "full_name": p_name, "address": p_address, "test_date": str(p_date),
        "infection_type": p_inf, "test_device": p_dev, 
        "pcr_result": p_notes, "entry_center": st.session_state.center
    }
    try:
        supabase.table("patients").insert(entry_data).execute()
        return True
    except:
        return False

def broadcast_message(content):
    """إرسال رسالة فورية لكافة المختبرات المرتبطة"""
    if content.strip():
        try:
            supabase.table("chat_messages").insert({
                "username": st.session_state.center, 
                "message": content
            }).execute()
            return True
        except:
            return False
    return False

# --- 4. نظام إدارة الدخول والتحقق من الصلاحيات ---

if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #60a5fa;'>🏥 بوابة مختبرات قضاء حديثة الموحدة</h1>", unsafe_allow_html=True)
    
    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
    with auth_col2:
        st.info("الرجاء اختيار المركز وإدخال كود التحقق للمتابعة")
        center_list = [
            'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
            'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
            'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
            'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص'
        ]
        
        target_center = st.selectbox("المركز المستخدِم:", center_list)
        secret_key = st.text_input("كود الدخول السري:", type="password")
        
        if st.button("تسجيل الدخول الآمن"):
            # التحقق من قاعدة البيانات مباشرة
            auth_res = supabase.table("center_access").select("*").eq("center_name", target_center).eq("access_code", secret_key).execute()
            if auth_res.data:
                st.session_state.logged_in = True
                st.session_state.center = target_center
                st.session_state.is_doctor = "أطباء الاختصاص" in target_center
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ فشل التحقق: الكود السري غير صحيح لهذا المركز")

# --- 5. الواجهة التشغيلية بعد تسجيل الدخول ---

else:
    # القائمة الجانبية (Sidebar)
    with st.sidebar:
        st.markdown(f"### 🛡️ جلسة نشطة\n**المكان:** {st.session_state.center}")
        st.write("---")
        if st.button("🔒 تسجيل الخروج الآمن"):
            st.session_state.clear()
            st.rerun()
        st.caption("نظام إدارة الفحوصات الفيروسية v2.4")

    # إعداد التبويبات حسب الصلاحية
    if st.session_state.is_doctor:
        main_tabs = st.tabs(["🔍 محرك البحث المركزي", "💬 غرفه التواصل الفوري"])
    else:
        main_tabs = st.tabs(["📝 تسجيل مراجع جديد", "🔍 السجل العام والبحث", "💬 غرفه التواصل الفوري"])

    # --- تبويب الإدخال (للمختبرات فقط) ---
    if not st.session_state.is_doctor:
        with main_tabs[0]:
            st.subheader("📝 إستمارة تسجيل البيانات الفيروسية")
            with st.form("entry_form", clear_on_submit=True):
                row1_c1, row1_c2 = st.columns(2)
                with row1_c1:
                    name_input = st.text_input("الاسم الرباعي للمراجع:")
                    address_input = st.text_input("عنوان السكن بالتفصيل:")
                    infection_input = st.selectbox("نوع الإصابة المشخصة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with row1_c2:
                    device_input = st.selectbox("جهاز المختبر المعتمد:", ["Strips", "ELISA", "PCR", "VITEK"])
                    date_input = st.date_input("تاريخ إجراء الفحص:", value=date.today())
                    notes_input = st.text_input("ملاحظات تقنية إضافية:")
                
                if st.form_submit_button("حفظ البيانات في السجل المركزي"):
                    if name_input and address_input:
                        if insert_new_patient(name_input, address_input, infection_input, device_input, date_input, notes_input):
                            st.success(f"✅ تم بنجاح أرشفة بيانات: {name_input}")
                        else:
                            st.error("❌ خطأ فني: تعذر الاتصال بالسحابة")
                    else:
                        st.warning("⚠️ يرجى إكمال الحقول الإلزامية (الاسم والعنوان)")

    # --- تبويب البحث والاستعلام ---
    search_tab_idx = 0 if st.session_state.is_doctor else 1
    with main_tabs[search_tab_idx]:
        st.subheader("🔍 استعلام فوري عن مراجع")
        search_term = st.text_input("ادخل الاسم الرباعي للبحث في السجلات:")
        
        if search_term:
            query_res = supabase.table("patients").select("*").ilike("full_name", f"%{search_term}%").execute()
            if query_res.data:
                st.write(f"📊 تم العثور على {len(query_res.data)} سجلات:")
                for patient in query_res.data:
                    with st.container():
                        st.markdown(f"#### 👤 {patient['full_name']}")
                        col_a, col_b, col_c = st.columns(3)
                        col_a.write(f"**📍 السكن:** {patient['address']}")
                        col_b.write(f"**🔬 التشخيص:** {patient['infection_type']}")
                        col_c.write(f"**📅 التاريخ:** {patient['test_date']}")
                        st.markdown(f"*📝 ملاحظات:* {patient['pcr_result']} | *🏢 المركز الموثق:* {patient['entry_center']}")
                        st.divider()
            else:
                st.info("لا يوجد سجل مطابق لهذا الاسم في قاعدة البيانات الحالية.")

    # --- تبويب الدردشة (الحل النهائي لمشكلة المحادثة والخط الطولي) ---
    chat_tab_idx = 1 if st.session_state.is_doctor else 2
    with main_tabs[chat_tab_idx]:
        st.subheader("💬 منصة التواصل والتنسيق المباشر")
        
        # جلب الرسائل
        messages_query = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
        
        # حاوية الدردشة باستخدام عناصر Streamlit الأصلية لمنع الخط الطولي
        with st.container():
            st.write("---")
            # عرض الرسائل بترتيبها الزمني الصحيح
            for msg in reversed(messages_query.data):
                # نستخدم st.chat_message لأنها تظهر الرسالة في مربع أبيض/رمادي مرتب تلقائياً
                with st.chat_message("user"):
                    st.write(f"**{msg['username']}**")
                    st.write(msg['message'])
                    # عرض الوقت بتنسيق بسيط
                    msg_time = msg['created_at'][11:16]
                    st.caption(f"توقيت الإرسال: {msg_time}")
            st.write("---")

        # نظام إدخال الرسائل
        with st.form("chat_box", clear_on_submit=True):
            chat_col1, chat_col2 = st.columns([5, 1])
            with chat_col1:
                input_msg = st.text_input("اكتب رسالتك للمختبرات الأخرى...", label_visibility="collapsed")
            with chat_col2:
                if st.form_submit_button("إرسال"):
                    if broadcast_message(input_msg):
                        st.rerun()
