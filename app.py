import streamlit as st
from supabase import create_client
from datetime import datetime, date
import time

# --- 1. إعدادات الاتصال والبيانات المركزية ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

# محاولة الاتصال بقاعدة البيانات مع معالجة الأخطاء
try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")

# --- 2. التصميم الهندسي للواجهة (CSS الاحترافي) ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    /* تنسيق الواجهة والخلفية */
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { padding-top: 2rem; direction: rtl; text-align: right; }
    
    /* منع ظهور الخطوط الطولية المزعجة */
    div[data-testid="stVerticalBlock"] > div { direction: rtl !important; }

    /* تنسيق أزرار الإرسال */
    .stButton>button { 
        width: 100%; border-radius: 10px; font-weight: bold; 
        background-color: #1e3a8a; color: white !important;
        transition: 0.3s; height: 3em; border: none;
    }
    .stButton>button:hover { background-color: #3b82f6; border: 1px solid white; }

    /* تصميم حاوية الدردشة الاحترافية */
    .chat-window { 
        background-color: #1e293b; padding: 20px; border-radius: 15px; 
        height: 500px; overflow-y: auto; border: 1px solid #334155; 
        display: flex; flex-direction: column; gap: 12px;
    }

    /* تصميم فقاعة الرسالة (المربع الأبيض) */
    .msg-bubble { 
        background-color: #ffffff; color: #000000 !important; 
        padding: 15px; border-radius: 12px; border-right: 8px solid #1e3a8a;
        width: 92%; margin: 5px auto 10px auto; 
        box-shadow: 0px 4px 6px rgba(0,0,0,0.4);
        position: relative;
    }
    .msg-bubble b { color: #1e3a8a; font-size: 15px; display: block; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .msg-bubble p { margin-top: 8px; font-size: 17px; line-height: 1.4; color: #000; font-weight: 500; }
    .msg-bubble .time { color: #888; font-size: 10px; text-align: left; display: block; margin-top: 5px; }

    /* إخفاء عناصر ستريمليت الزائدة */
    #MainMenu, footer, header {visibility: hidden;}
    </style>""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية (Logic Functions) ---

def save_patient(name, address, infection, device, test_date, notes):
    """دالة لحفظ بيانات المريض في السحاب"""
    try:
        data = {
            "full_name": name, "address": address, "test_date": str(test_date),
            "infection_type": infection, "test_device": device, 
            "pcr_result": notes, "entry_center": st.session_state.center
        }
        supabase.table("patients").insert(data).execute()
        return True
    except:
        return False

def send_chat_msg(msg):
    """دالة لإرسال رسالة دردشة وتصفير الحقل"""
    if msg.strip():
        supabase.table("chat_messages").insert({
            "username": st.session_state.center, 
            "message": msg
        }).execute()
        return True
    return False

# --- 4. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🏥 نظام إدارة مختبرات حديثة المركزية</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>يرجى تسجيل الدخول للوصول إلى قاعدة البيانات الموحدة</p>", unsafe_allow_html=True)
    
    centers_list = [
        'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
        'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
        'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
        'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص'
    ]
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container():
            selected_center = st.selectbox("المركز المختبري:", centers_list)
            access_code = st.text_input("رمز التفويض السري:", type="password")
            
            if st.button("تفعيل الدخول للنظام"):
                # التحقق من الكود من قاعدة البيانات
                res = supabase.table("center_access").select("*").eq("center_name", selected_center).eq("access_code", access_code).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.center = selected_center
                    st.session_state.is_doctor = "أطباء الاختصاص" in selected_center
                    st.success("تم التحقق بنجاح.. جاري التحميل")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ الرمز غير صحيح أو غير مفوض لهذا المركز")

# --- 5. واجهة النظام الرئيسية بعد الدخول ---
else:
    # القائمة الجانبية للمعلومات
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2750/2750657.png", width=100)
        st.markdown(f"### 👤 الحساب الحالي\n**{st.session_state.center}**")
        st.divider()
        if st.button("🚪 خروج من النظام"):
            st.session_state.clear()
            st.rerun()

    # إنشاء التبويبات بناءً على الصلاحيات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 البحث والاستعلام", "💬 التواصل المباشر"])
    else:
        tabs = st.tabs(["📝 إدخال سجل جديد", "🔍 السجل العام والبحث", "💬 التواصل المباشر"])

    # --- تبويب الإدخال ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.subheader("📝 استمارة تسجيل مراجع جديد")
            with st.form("patient_form", clear_on_submit=True):
                r1_c1, r1_c2 = st.columns(2)
                with r1_c1:
                    f_name = st.text_input("الاسم الرباعي للمراجع:")
                    f_address = st.text_input("محل السكن الحالي:")
                    f_infection = st.selectbox("التشخيص المبدئي:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with r1_c2:
                    f_device = st.selectbox("جهاز المختبر المستخدم:", ["Strips", "ELISA", "PCR", "VITEK"])
                    f_date = st.date_input("تاريخ إجراء الفحص:", value=date.today())
                    f_note = st.text_input("ملاحظات فنية إضافية:")
                
                if st.form_submit_button("إرسال البيانات إلى السحابة المركزية"):
                    if f_name.strip() and f_address.strip():
                        if save_patient(f_name, f_address, f_infection, f_device, f_date, f_note):
                            st.success(f"✅ تم أرشفة بيانات المراجع {f_name} بنجاح")
                        else:
                            st.error("❌ حدث خطأ أثناء الاتصال بالقاعدة")
                    else:
                        st.warning("⚠️ يرجى ملء الحقول الأساسية (الاسم والعنوان)")

    # --- تبويب البحث ---
    search_tab_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_tab_idx]:
        st.subheader("🔍 محرك البحث في قاعدة البيانات المركزية")
        search_query = st.text_input("ادخل اسم المراجع (أو جزء منه) للبحث في كافة السجلات:")
        
        if search_query:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{search_query}%").execute()
            if results.data:
                st.write(f"تم العثور على ({len(results.data)}) سجلات مطابقة:")
                for row in results.data:
                    with st.expander(f"👤 {row['full_name']} | التشخيص: {row['infection_type']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**📍 العنوان:** {row['address']}")
                            st.write(f"**🔬 الجهاز:** {row['test_device']}")
                        with col2:
                            st.write(f"**📅 التاريخ:** {row['test_date']}")
                            st.write(f"**🏢 المركز المدخل:** {row['entry_center']}")
                        st.info(f"**📝 ملاحظات إضافية:** {row['pcr_result']}")
            else:
                st.warning("🔎 لا يوجد مراجع مسجل بهذا الاسم في قاعدة البيانات.")

    # --- تبويب الدردشة (نظام الفقاعات البيضاء المطور) ---
    chat_tab_idx = 1 if st.session_state.is_doctor else 2
    with tabs[chat_tab_idx]:
        st.subheader("💬 منصة التواصل الفوري بين المختبرات")
        
        # جلب آخر 50 رسالة
        msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(50).execute()
        
        # بناء منطقة الرسائل
        chat_html = "<div class='chat-window'>"
        for m in reversed(msgs.data):
            # تنسيق الوقت
            created_at = datetime.fromisoformat(m['created_at'].replace('Z', '+00:00'))
            time_display = created_at.strftime("%I:%M %p")
            
            chat_html += f"""
            <div class='msg-bubble'>
                <b>🏢 {m['username']}</b>
                <p>{m['message']}</p>
                <span class='time'>{time_display}</span>
            </div>
            """
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # حقل الإرسال المطور
        with st.form("chat_system", clear_on_submit=True):
            in_col, btn_col = st.columns([6, 1])
            with in_col:
                new_msg = st.text_input("اكتب رسالتك الفنية أو الإدارية هنا...", label_visibility="collapsed")
            with btn_col:
                if st.form_submit_button("إرسال") and new_msg:
                    if send_chat_msg(new_msg):
                        st.rerun()
