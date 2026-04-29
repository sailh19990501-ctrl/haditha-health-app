# --- تبويب السجل العام والبحث (تعديل لعرض الكل تلقائياً) ---
    search_tab_idx = 0 if st.session_state.is_doctor else 1
    with main_tabs[search_tab_idx]:
        st.subheader("🔍 السجل العام للمراجعين")
        
        # حقل البحث
        search_term = st.text_input("ابحث عن اسم محدد هنا:")
        
        # جلب البيانات: إذا كان الحقل فارغاً يجلب الكل، وإذا فيه اسم يبحث عنه
        if search_term:
            query_res = supabase.table("patients").select("*").ilike("full_name", f"%{search_term}%").order("created_at", desc=True).execute()
        else:
            # جلب كافة السجلات تلقائياً وترتيبها من الأحدث للأقدم
            query_res = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if query_res.data:
            st.write(f"📊 إجمالي السجلات الموجودة: {len(query_res.data)}")
            st.write("---")
            
            for patient in query_res.data:
                with st.container():
                    # عرض الاسم كعنوان كما في الصورة
                    st.markdown(f"### 👤 {patient['full_name']}")
                    
                    # توزيع المعلومات في أعمدة مرتبة
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.markdown(f"📍 **السكن:** {patient['address']}")
                    with col_b:
                        st.markdown(f"🔬 **التشخيص:** {patient['infection_type']}")
                    with col_c:
                        st.markdown(f"📅 **التاريخ:** {patient['test_date']}")
                    
                    # ملاحظات والمركز الموثق
                    st.info(f"📝 **ملاحظات:** {patient['pcr_result']} | 🏢 **المركز الموثق:** {patient['entry_center']}")
                    st.divider() # خط فاصل بين كل مراجع والآخر
        else:
            if search_term:
                st.warning("لا يوجد سجل مطابق لهذا الاسم.")
            else:
                st.info("قاعدة البيانات فارغة حالياً.")
