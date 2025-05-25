import streamlit as st
import pandas as pd
from src.database import create_db_engine, load_invoice_data

# Sample data: replace this with your actual DataFrame loading
engine = create_db_engine()
df = load_invoice_data(engine)
df = df.sort_values('datetime', ascending=False)
df = (
    df.drop_duplicates(subset=['supermarket_name', 'full_product_name'])
    .loc[:, ['supermarket_name', 'product','full_product_name', 'unitary_value', 'datetime', 'volume','category']]

)

st.set_page_config(page_title="Smart Cart", layout="wide")
st.title("🛒 Smart Cart")

st.markdown("""
Plan your grocery list and find the **best prices** based on your past receipts.
Select the products and quantities you'd like to buy, and we'll calculate:
- 💸 Total cost at each supermarket
- 🧠 The **cheapest combination** across markets
""")

# Get unique full products
unique_products = sorted(df['full_product_name'].dropna().unique())
selected_products = st.multiselect("Choose products to add to your cart:", unique_products)

user_cart = []
for product in selected_products:
    quantity = st.sidebar.number_input(f"Quantity for {product}:", min_value=1.0, step=0.5, key=product)
    if quantity > 0:
        user_cart.append({"full_product_name": product, "quantity": quantity})

if user_cart:
    cart_df = pd.DataFrame(user_cart)

    # Merge with unit prices
    merged = pd.merge(cart_df, df[['full_product_name', 'supermarket_name', 'unitary_value']],
                      on='full_product_name', how='left')

    # Drop duplicates to get the cheapest price per supermarket
    merged = merged.drop_duplicates(subset=['full_product_name', 'supermarket_name', 'unitary_value'])

    # Calculate total per supermarket
    merged['estimated_cost'] = merged['quantity'] * merged['unitary_value']

    SUMMARY = ['SUMMARY']
    supermarket_names = sorted([str(cat) for cat in df['supermarket_name'].dropna().unique()])
    supermarket_names = supermarket_names + SUMMARY

    st.subheader("💰 Total Cost Per Supermarket")
    tabs = st.tabs(supermarket_names)
    for tab, name in zip(tabs, supermarket_names):
        with (tab):
            if name == 'SUMMARY':
                summary = merged.groupby('supermarket_name')['estimated_cost'].sum().sort_values().reset_index()
                st.dataframe(summary)
            else:
                shopping_list = merged[merged['supermarket_name'] == name]
                total_cost = shopping_list['estimated_cost'].sum()
                st.dataframe(shopping_list)
                st.success(
                    f"🟢 Total if you buy at {name}: R$ {total_cost:.2f}")

    # Find best price per item regardless of market
    cheapest_total = (
        merged.sort_values('unitary_value')
        .groupby('full_product_name')
        .first()
        .reset_index()
    )
    cheapest_total['estimated_cost'] = cheapest_total['quantity'] * cheapest_total['unitary_value']

    st.subheader("🧠 Optimal Cheapest Combination")
    st.dataframe(cheapest_total[['full_product_name', 'quantity', 'supermarket_name', 'unitary_value', 'estimated_cost']])
    st.success(f"🟢 Total if you buy each item at the cheapest market: R$ {cheapest_total['estimated_cost'].sum():.2f}")
else:
    st.info("Select products and quantities to see price comparisons.")