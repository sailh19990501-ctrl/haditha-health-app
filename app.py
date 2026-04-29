import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. ربط قاعدة البيانات ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"فشل الاتصال: {e}")

# --- 2. إعدادات الواجهة (CSS) لمنع النص الطولي نهائياً ---
st.set_page_config(page_title="نظام مختبرات حديثة الموحد", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { padding: 1.5rem; direction: rtl; text-align: right; }
    
    /* تصميم البطاقة العريضة لمنع النص الطولي */
    .patient-box {
        background: #1e293b; 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 20px; 
        border-right: 8px solid #3b82f6;
        width: 100%;
        display: block;
    }
    .patient-box h3 { color: #60a5fa; margin-bottom: 10px; }
    .patient-box p { font-size: 1.1em; line-height: 1.6; color: #cbd5e1; }
    
    /* تنسيق الأزرار */
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
    
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. نظام تسجيل الدخول المركزي ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🏥 نظام إدارة مختبرات قضاء حديثة</h1>", unsafe_allow_html=True)
    
    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
    with auth_col2:
        centers_list = [
            'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
            'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
            'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
            'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص'
        ]
        u_center = st.selectbox("اختر جهة العمل:", centers_list)
        u_code = st.text_input("رمز الدخول السري:", type="password")
        
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                # المختبر الرئيسي (مدير النظام)
                st.session_state.is_admin = (u_center == 'مختبر مستشفى حديثة للفحوصات الفيروسية')
                # طبيب الاختصاص (للقراءة فقط)
                st.session_state.is_doctor = (u_center == 'أطباء الاختصاص')
                st.rerun()
            else:
                st.error("⚠️ الرمز السري غير صحيح!")

# --- 4. واجهة النظام بعد الدخول ---
else:
    # القائمة الجانبية (Sidebar)
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state.center}")
        st.write("---")
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.clear()
            st.rerun()

    # تحديد التبويبات بناءً على الصلاحية
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 السجل العام والبحث"])
    else:
        tabs = st.tabs(["🔍 السجل العام والبحث", "📝 إضافة إصابة جديدة", "💬 التواصل المباشر"])

    # --- أ: تبويب السجل والبحث (القلب النابض للنظام) ---
    search_tab_idx = 0 
    with tabs[search_tab_idx]:
        st.subheader("🔍 قاعدة بيانات المصابين المركزية")
        q_term = st.text_input("ابحث عن اسم المراجع (اتركه فارغاً لعرض الكل):")
        
        # جلب البيانات
        if q_term:
            p_res = supabase.table("patients").select("*").ilike("full_name", f"%{q_term}%").order("created_at", desc=True).execute()
        else:
            p_res = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if p_res.data:
            st.info(f"📊 عدد السجلات المعروضة: {len(p_res.data)}")
            for p in p_res.data:
                # قانون الصلاحيات: المسؤول يعدل الكل، المركز يعدل مرضاه فقط
                can_manage = st.session_state.is_admin or (p['entry_center'] == st.session_state.center)
                
                # عرض البطاقة (Card)
                st.markdown(f"""
                <div class="patient-box">
                    <h3>👤 {p['full_name']}</h3>
                    <p>
                        📍 <b>السكن:</b> {p['address']} | 🔬 <b>نوع الإصابة:</b> {p['infection_type']}<br>
                        🏢 <b>المركز المسجل:</b> {p['entry_center']} | 📅 <b>التاريخ:</b> {p['test_date']}
                    </p>
                    <p style="color: #94a3b8; font-size: 0.9em;">📝 ملاحظات: {p['pcr_result']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # أزرار التحكم (تختفي تماماً عند الطبيب)
                if not st.session_state.is_doctor:
                    c1, c2 = st.columns(2)
                    with c1:
                        if can_manage:
                            if st.button(f"🗑️ حذف السجل", key=f"del_{p['id']}"):
                                supabase.table("patients").delete().eq("id", p['id']).execute()
                                st.rerun()
                        else:
                            st.write("🔒 للقراءة فقط")
                    with c2:
                        if can_manage:
                            if st.expander("⚙️ تعديل البيانات"):
                                new_note = st.text_input("تحديث الملاحظات:", value=p['pcr_result'], key=f"ed_{p['id']}")
                                if st.button("تحديث السجل", key=f"up_{p['id']}"):
                                    supabase.table("patients").update({"pcr_result": new_note}).eq("id", p['id']).execute()
                                    st.rerun()
                st.divider()
        else:
            st.warning("🔎 لا توجد سجلات مطابقة.")

    # --- ب: تبويب الإضافة (مخفي عن الطبيب) ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            st.subheader("📝 استمارة تسجيل إصابة")
            with st.form("new_patient_form", clear_on_submit=True):
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    f_name = st.text_input("الاسم الرباعي:")
                    f_addr = st.text_input("محل السكن:")
                    f_inf = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with col_i2:
                    f_dev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    f_date = st.date_input("تاريخ الفحص:", value=date.today())
                    f_note = st.text_area("ملاحظات إضافية:")
                
                if st.form_submit_button("إرسال للسجل المركزي"):
                    if f_name and f_addr:
                        supabase.table("patients").insert({
                            "full_name": f_name, "address": f_addr, "infection_type": f_inf,
                            "test_device": f_dev, "test_date": str(f_date), "pcr_result": f_note,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الحفظ بنجاح")
                    else:
                        st.error("⚠️ يرجى إدخال الاسم والعنوان")

        # --- ج: تبويب الدردشة (مخفي عن الطبيب) ---
        with tabs[2]:
            st.subheader("💬 منصة التواصل بين المختبرات")
            
            # عداد المتصلين النشطين
            recent_m = supabase.table("chat_messages").select("username").order("created_at", desc=True).limit(20).execute()
            online = list(set([m['username'] for m in recent_m.data]))
            st.markdown(f"🟢 **المراكز النشطة:** {', '.join(online)}")
            
            # عرض الرسائل
            chats = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(25).execute()
            for m in reversed(chats.data):
                with st.chat_message("user", avatar="🏢"):
                    st.write(f"**{m['username']}**")
                    st.write(m['message'])
                    st.caption(f"🕒 {m['created_at'][11:16]}")
            
            with st.form("chat_box", clear_on_submit=True):
                ci, cb = st.columns([5, 1])
                msg = ci.text_input("اكتب رسالتك...", label_visibility="collapsed")
                if cb.form_submit_button("إرسال") and msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": msg}).execute()
                    st.rerun()
