import streamlit as st

pages={
    "Market App": [
        st.Page('pages/receipt_reader.py', title='Upload receipt'),
        st.Page('pages/dashboard.py', title='dashboard'),
    ]
}

pg = st.navigation(pages)
pg.run()