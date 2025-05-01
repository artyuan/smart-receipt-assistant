import streamlit as st
from src.postgres_sql import create_db_engine, load_invoice_data
from src.dashboard_utils import date_range_filter, plot_unitary_prices, plot_total_spend, plot_price_comparison

def main():
    """Main Streamlit application."""
    st.set_page_config(
        layout="wide",
    )

    st.title("🛒 Supermarket Dashboard")

    # Load data
    engine = create_db_engine()
    df = load_invoice_data(engine)
    df_filtered = date_range_filter(df)

    # --- Unitary Prices ---
    st.header("📈 Unitary Product Prices Over Time")
    categories = sorted([str(cat) for cat in df_filtered['category'].dropna().unique()])
    tabs = st.tabs(categories)
    for tab, category in zip(tabs, categories):
        with tab:
            plot_unitary_prices(df_filtered[df_filtered['category'] == category], category)

    # --- Spend Analysis ---
    st.header("💸 Spend Analysis")
    st.subheader("Spend by Supermarket")
    plot_total_spend(df_filtered, "supermarket_name", "Total Spend per Supermarket")

    st.subheader("Spend by Category")
    plot_total_spend(df_filtered, "category", "Total Spend per Category")

    # --- Product Comparison ---
    st.header("🏪 Product Price Comparison")
    products = sorted(df_filtered['product'].dropna().unique())
    selected_product = st.selectbox("Select a Product to Compare", products)
    plot_price_comparison(df_filtered[df_filtered['product'] == selected_product], selected_product)


if __name__ == "__main__":
    main()
