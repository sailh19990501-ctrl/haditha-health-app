import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الاتصال والقاعدة ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    # محاولة الاتصال بقاعدة البيانات
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"حدث خطأ في الاتصال بالسيرفر: {e}")

# --- 2. التنسيق البصري الشامل (CSS) ---
# هذا القسم هو المسؤول عن منع النص الطولي وترتيب الدردشة
st.set_page_config(page_title="نظام مختبرات حديثة الموحد", layout="wide")

st.markdown("""<style>
    /* إعدادات الصفحة العامة */
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; padding-top: 2rem; }
    
    /* تنسيق بطاقة المراجع العريضة لمنع النص الطولي */
    .patient-card {
        background: #1e293b; 
        padding: 25px; 
        border-radius: 15px; 
        margin-bottom: 20px; 
        border-right: 10px solid #3b82f6;
        width: 100%;
        display: block;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .patient-card h3 { color: #60a5fa; margin-bottom: 15px; font-size: 1.5em; }
    .info-row { font-size: 1.1em; line-height: 1.8; margin-bottom: 8px; }
    
    /* تنسيق مربعات الدردشة (Bubbles) */
    .chat-container { margin-bottom: 15px; display: flex; flex-direction: column; }
    .chat-bubble {
        background-color: #262730; 
        padding: 15px; 
        border-radius: 18px; 
        border: 1px solid #3b82f6; 
        width: fit-content; 
        max-width: 85%;
        margin-bottom: 5px;
    }
    .chat-sender { color: #60a5fa; font-weight: bold; font-size: 0.9em; margin-bottom: 5px; border-bottom: 1px solid #334155; padding-bottom: 3px; }
    .chat-text { font-size: 1.05em; color: #e2e8f0; }

    /* تنسيق الأزرار */
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; height: 45px; transition: 0.3s; }
    
    /* إخفاء القوائم الافتراضية */
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. بوابة تسجيل الدخول المخصصة ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🏥 نظام إدارة مختبرات قضاء حديثة</h1>", unsafe_allow_html=True)
    
    with st.container():
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            centers_list = [
                'مركز مستشفى حديثة للتبرع بالدم', 
                'مختبر مستشفى حديثة للفحوصات الفيروسية', 
                'المركز التخصصي للاسنان', 
                'مركز صحي بروانه', 
                'أطباء الاختصاص'
            ]
            selected_center = st.selectbox("يرجى اختيار جهة العمل:", centers_list)
            access_code = st.text_input("أدخل الرمز السري الخاص بالمركز:", type="password")
            
            if st.button("تسجيل الدخول"):
                # التحقق من الرمز في قاعدة البيانات
                auth_query = supabase.table("center_access").select("*").eq("center_name", selected_center).eq("access_code", access_code).execute()
                
                if auth_query.data:
                    st.session_state.logged_in = True
                    st.session_state.center = selected_center
                    # تحديد نوع الحساب بدقة
                    st.session_state.is_admin = (selected_center == 'مختبر مستشفى حديثة للفحوصات الفيروسية')
                    st.session_state.is_doctor = (selected_center == 'أطباء الاختصاص')
                    st.rerun()
                else:
                    st.error("⚠️ الرمز السري الذي أدخلته غير صحيح، حاول مرة أخرى.")

# --- 4. واجهة النظام الرئيسية ---
else:
    # شريط التنقل الجانبي
    with st.sidebar:
        st.write(f"### 👤 {st.session_state.center}")
        st.write("---")
        if st.button("🔴 خروج من النظام"):
            st.session_state.clear()
            st.rerun()

    # توزيع التبويبات بناءً على الصلاحيات
    if st.session_state.is_doctor:
        app_tabs = st.tabs(["🔍 استعراض السجل العام"])
    else:
        app_tabs = st.tabs(["🔍 السجل والبحث", "📝 إضافة مراجع جديد", "💬 منصة الدردشة"])

    # --- أ: تبويب السجل العام ---
    with app_tabs[0]:
        st.subheader("🔍 البحث في أرشيف المصابين الموحد")
        search_term = st.text_input("ابحث عن اسم المراجع للوصول السريع:")
        
        # جلب البيانات مع الفلترة
        if search_term:
            query_res = supabase.table("patients").select("*").ilike("full_name", f"%{search_term}%").order("created_at", desc=True).execute()
        else:
            query_res = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if query_res.data:
            for patient in query_res.data:
                # قانون الصلاحيات الصارم:
                # 1. الأدمن (مختبر الفيروسية) يملك كل الصلاحيات.
                # 2. المركز يملك صلاحية التعديل والحذف فقط لمراجعيه.
                # 3. الطبيب لا يملك أي صلاحية تعديل.
                can_modify = st.session_state.is_admin or (patient['entry_center'] == st.session_state.center)
                
                st.markdown(f"""
                <div class="patient-card">
                    <h3>👤 الاسم: {patient['full_name']}</h3>
                    <div class="info-row">📍 <b>السكن:</b> {patient['address']}</div>
                    <div class="info-row">🔬 <b>نوع الإصابة:</b> {patient['infection_type']} | 📅 <b>التاريخ:</b> {patient['test_date']}</div>
                    <div class="info-row">🏢 <b>جهة الإدخال:</b> {patient['entry_center']}</div>
                    <div class="info-row" style="color: #94a3b8;">📝 <b>ملاحظات:</b> {patient['pcr_result']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # أزرار الإجراءات للمخولين فقط
                if not st.session_state.is_doctor:
                    btn_col1, btn_col2 = st.columns([1, 1])
                    with btn_col1:
                        if can_modify:
                            if st.button(f"🗑️ حذف هذا السجل", key=f"del_btn_{patient['id']}"):
                                supabase.table("patients").delete().eq("id", patient['id']).execute()
                                st.success("تم الحذف بنجax!")
                                st.rerun()
                        else:
                            st.caption("🔒 لا تملك صلاحية حذف هذا السجل")
                            
                    with btn_col2:
                        if can_modify:
                            with st.expander("⚙️ تعديل الملاحظات أو النتيجة"):
                                updated_note = st.text_area("أدخل الملاحظة الجديدة هنا:", value=patient['pcr_result'], key=f"note_input_{patient['id']}")
                                if st.button("حفظ التعديلات الآن", key=f"save_edit_{patient['id']}"):
                                    supabase.table("patients").update({"pcr_result": updated_note}).eq("id", patient['id']).execute()
                                    st.success("تم التحديث")
                                    st.rerun()
                        else:
                            st.caption("🔒 لا تملك صلاحية تعديل هذا السجل")
                st.divider()
        else:
            st.warning("لم يتم العثور على أي نتائج مطابقة.")

    # --- ب: تبويب إضافة البيانات (مخفي عن الأطباء) ---
    if not st.session_state.is_doctor:
        with app_tabs[1]:
            st.subheader("📝 استمارة تسجيل مراجع جديد")
            with st.form("new_entry_form", clear_on_submit=True):
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    p_name = st.text_input("الاسم الرباعي للمراجع:")
                    p_address = st.text_input("محل السكن الحالي:")
                    p_inf_type = st.selectbox("نوع الإصابة المشخصة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with f_col2:
                    p_device = st.selectbox("جهاز الفحص المستخدم:", ["Strips", "ELISA", "PCR", "VITEK"])
                    p_test_date = st.date_input("تاريخ إجراء الفحص:", value=date.today())
                    p_notes = st.text_area("ملاحظات إضافية أو نتيجة الـ PCR:")
                
                submit_btn = st.form_submit_button("إرسال البيانات إلى السجل المركزي")
                if submit_btn:
                    if p_name and p_address:
                        supabase.table("patients").insert({
                            "full_name": p_name, 
                            "address": p_address, 
                            "infection_type": p_inf_type,
                            "test_device": p_device, 
                            "test_date": str(p_test_date), 
                            "pcr_result": p_notes,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم حفظ البيانات وإضافتها للسجل العام بنجاح.")
                    else:
                        st.error("⚠️ يرجى ملء الحقول الأساسية (الاسم والسكن) قبل الإرسال.")

        # --- ج: تبويب الدردشة (مربعات واضحة) ---
        with app_tabs[2]:
            st.subheader("💬 منصة التنسيق بين المختبرات والمراكز")
            
            # جلب آخر 25 رسالة
            chat_logs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(25).execute()
            
            # عرض الرسائل بنظام المربعات
            for msg in reversed(chat_logs.data):
                st.markdown(f"""
                <div class="chat-container">
                    <div class="chat-bubble">
                        <div class="chat-sender">🏢 {msg['username']}</div>
                        <div class="chat-text">{msg['message']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # حقل إرسال الرسالة
            with st.form("send_chat_form", clear_on_submit=True):
                input_col, send_col = st.columns([5, 1])
                user_msg = input_col.text_input("اكتب رسالتك للمراكز الأخرى هنا...", label_visibility="collapsed")
                if send_col.form_submit_button("إرسال"):
                    if user_msg:
                        supabase.table("chat_messages").insert({
                            "username": st.session_state.center, 
                            "message": user_msg
                        }).execute()
                        st.rerun()
