import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. الاتصال بقاعدة البيانات ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("فشل الاتصال")

# --- 2. تنسيق الواجهة (حل مشكلة الكتابة الطولية نهائياً) ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    /* منع النصوص من الالتفاف الطولي وتوسيع الحاويات */
    .main .block-container { max-width: 95% !important; padding: 1rem; direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { background: #1e293b; border-radius: 8px; margin-bottom: 10px; border: 1px solid #334155; }
    /* تنسيق النصوص لتكون واضحة وعريضة */
    .stMarkdown p, .stMarkdown h3 { white-space: nowrap; overflow: visible; }
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🔐 تسجيل دخول النظام</h2>", unsafe_allow_html=True)
    centers = ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية', 'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'أطباء الاختصاص']
    u_center = st.selectbox("اختر جهة العمل:", centers)
    u_code = st.text_input("رمز الدخول:", type="password")
    if st.button("دخول"):
        res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
        if res.data:
            st.session_state.logged_in = True
            st.session_state.center = u_center
            st.session_state.is_admin = (u_center == 'مختبر مستشفى حديثة للفحوصات الفيروسية')
            st.session_state.is_doctor = (u_center == 'أطباء الاختصاص')
            st.rerun()
        else: st.error("الرمز خطأ")

else:
    # القوائم العلوية (التبويبات) رجعت لمكانها الصحيح
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 سجل المرضى العام"])
    else:
        tabs = st.tabs(["🔍 السجل العام", "📝 إضافة إصابة", "💬 الدردشة"])

    # --- تبويب السجل ---
    with tabs[0]:
        st.subheader("📋 أرشيف الإصابات")
        s_term = st.text_input("ابحث عن اسم المراجع هنا:")
        
        if s_term:
            p_data = supabase.table("patients").select("*").ilike("full_name", f"%{s_term}%").order("created_at", desc=True).execute()
        else:
            p_data = supabase.table("patients").select("*").order("created_at", desc=True).execute()

        if p_data.data:
            for p in p_data.data:
                # صلاحية الحذف والتعديل (المدير أو صاحب السجل)
                can_edit = st.session_state.is_admin or (p['entry_center'] == st.session_state.center)
                
                with st.expander(f"👤 {p['full_name']} | {p['infection_type']} | {p['test_date']}"):
                    st.write(f"🏠 السكن: {p['address']} | 🔬 الجهاز: {p['test_device']}")
                    st.write(f"🏢 المركز: {p['entry_center']}")
                    st.info(f"📝 ملاحظات: {p['pcr_result']}")
                    
                    if not st.session_state.is_doctor:
                        c1, c2 = st.columns(2)
                        with c1:
                            if can_edit:
                                if st.button(f"🗑️ حذف السجل", key=f"d_{p['id']}"):
                                    supabase.table("patients").delete().eq("id", p['id']).execute()
                                    st.rerun()
                            else: st.warning("🔒 للقراءة فقط")
                        with c2:
                            if can_edit:
                                edit_note = st.text_input("تحديث الملاحظة:", value=p['pcr_result'], key=f"e_{p['id']}")
                                if st.button("تأكيد التعديل", key=f"b_{p['id']}"):
                                    supabase.table("patients").update({"pcr_result": edit_note}).eq("id", p['id']).execute()
                                    st.rerun()

    # --- تبويب الإضافة (مخفي عن الطبيب) ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            st.subheader("📝 إدخال بيانات جديدة")
            with st.form("add_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("العنوان:")
                    inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with col2:
                    dev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    dt = st.date_input("التاريخ:", value=date.today())
                    note = st.text_area("الملاحظات:")
                
                if st.form_submit_button("حفظ وإرسال"):
                    if name and addr:
                        supabase.table("patients").insert({
                            "full_name": name, "address": addr, "infection_type": inf,
                            "test_device": dev, "test_date": str(dt), "pcr_result": note,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("تم الحفظ بنجاح")
                        st.rerun()

        # --- تبويب الدردشة ---
        with tabs[2]:
            st.subheader("💬 التواصل بين المراكز")
            chat_res = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
            for m in reversed(chat_res.data):
                st.markdown(f"**{m['username']}**: {m['message']}")
            
            with st.form("chat_input", clear_on_submit=True):
                c_msg = st.text_input("رسالتك...")
                if st.form_submit_button("إرسال") and c_msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": c_msg}).execute()
                    st.rerun()

    if st.sidebar.button("🔴 خروج"):
        st.session_state.clear()
        st.rerun()
