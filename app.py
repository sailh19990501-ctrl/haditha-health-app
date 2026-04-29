import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الاتصال ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"فشل الاتصال: {e}")

# --- 2. تنسيق الواجهة (CSS) لمنع الكتابة الطولية ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { padding: 1rem; direction: rtl; text-align: right; }
    
    /* حل مشكلة النص الطولي بجعل الحاويات مرنة */
    .patient-card {
        background: #1e293b; 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 15px; 
        border-right: 6px solid #3b82f6;
        line-height: 1.6;
    }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. الدوال التشغيلية ---

def delete_record(record_id):
    try:
        supabase.table("patients").delete().eq("id", record_id).execute()
        st.success("✅ تم حذف السجل بنجاح")
        return True
    except:
        st.error("❌ فشل الحذف")
        return False

# --- 4. تسجيل الدخول ---

if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🏥 دخول نظام مختبرات حديثة</h2>", unsafe_allow_html=True)
    with st.container():
        centers = ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية', 'المركز التخصصي للاسنان', 'أطباء الاختصاص']
        u_center = st.selectbox("جهة العمل:", centers)
        u_code = st.text_input("الرمز السري:", type="password")
        if st.button("دخول"):
            res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                st.session_state.is_doctor = "أطباء الاختصاص" in u_center
                st.rerun()
            else:
                st.error("⚠️ الرمز غير صحيح")
else:
    # القائمة الجانبية للتنقل
    menu = ["🔍 السجل والبحث", "📝 إضافة إصابة", "💬 الدردشة"]
    if st.session_state.is_doctor: menu = ["🔍 السجل والبحث"]
    
    choice = st.sidebar.radio("القائمة:", menu)
    
    if st.sidebar.button("🔴 خروج"):
        st.session_state.clear()
        st.rerun()

    # --- أ: إضافة إصابة ---
    if choice == "📝 إضافة إصابة":
        st.subheader("📝 تسجيل بيانات مراجع")
        with st.form("add_form"):
            name = st.text_input("الاسم الرباعي:")
            addr = st.text_input("السكن:")
            inf = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
            dev = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR"])
            dt = st.date_input("التاريخ:", value=date.today())
            note = st.text_area("ملاحظات:")
            
            if st.form_submit_button("حفظ البيانات"):
                if name and addr:
                    supabase.table("patients").insert({
                        "full_name": name, "address": addr, "infection_type": inf,
                        "test_device": dev, "test_date": str(dt), "pcr_result": note,
                        "entry_center": st.session_state.center
                    }).execute()
                    st.success("✅ تم الحفظ")
                else:
                    st.warning("⚠️ املأ الحقول")

    # --- ب: السجل والبحث (مع التعديل والحذف) ---
    elif choice == "🔍 السجل والبحث":
        st.subheader("🔍 سجل المرضى المركزي")
        q = st.text_input("ابحث عن اسم المراجع:")
        
        # جلب البيانات
        if q:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute()
        else:
            results = supabase.table("patients").select("*").order("created_at", desc=True).limit(20).execute()
        
        if results.data:
            for p in results.data:
                with st.container():
                    st.markdown(f"""<div class='patient-card'>
                        <b>👤 الاسم:</b> {p['full_name']}<br>
                        <b>📍 السكن:</b> {p['address']} | <b>🔬 الإصابة:</b> {p['infection_type']}<br>
                        <b>📅 التاريخ:</b> {p['test_date']} | <b>🏢 الجهة:</b> {p['entry_center']}
                    </div>""", unsafe_allow_html=True)
                    
                    # أزرار التحكم (تظهر بوضوح تحت كل سجل)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🗑️ حذف السجل", key=f"del_{p['id']}"):
                            if delete_record(p['id']): st.rerun()
                    with col2:
                        # التعديل يفتح نافذة منبثقة أو خيارات (هنا بسطناها للتعديل السريع)
                        if st.expander(f"⚙️ تعديل بيانات {p['full_name'].split()[0]}"):
                            new_note = st.text_input("تعديل الملاحظات:", value=p['pcr_result'], key=f"edit_n_{p['id']}")
                            if st.button("تحديث السجل", key=f"upd_{p['id']}"):
                                supabase.table("patients").update({"pcr_result": new_note}).eq("id", p['id']).execute()
                                st.success("✅ تم التحديث")
                                st.rerun()

    # --- ج: الدردشة ---
    elif choice == "💬 الدردشة":
        st.subheader("💬 منصة التواصل الفوري")
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
        
        for m in reversed(msgs.data):
            st.markdown(f"**{m['username']}**: {m['message']}  \n<small>{m['created_at'][11:16]}</small>")
            st.write("---")
            
        with st.form("chat_form", clear_on_submit=True):
            txt = st.text_input("رسالتك:")
            if st.form_submit_button("إرسال") and txt:
                supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute()
                st.rerun()
