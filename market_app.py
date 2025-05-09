import streamlit as st

pages={
    "Market App": [
        st.Page('pages/receipt_reader.py', title='Upload receipt'),
        st.Page('pages/dashboard.py', title='Dashboard'),
        st.Page('pages/report.py', title='Supermarket Spending Report'),
        st.Page('pages/smart_cart.py', title='Smart Cart'),
    ]
}

pg = st.navigation(pages)
pg.run()