import streamlit as st
from src.database import create_db_engine, load_invoice_data
from src.dashboard_utils import (date_range_filter,
                                 plot_unitary_prices,
                                 plot_total_spend,
                                 plot_price_comparison,
                                 plot_monthly_spend,
                                 plot_price_comparison_by_month)

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
    view_option = st.sidebar.radio(
        "Spend by Supermarket:",
        ("Total", "Monthly")
    )
    #view_option='Total'
    if view_option == "Total":
        plot_total_spend(df_filtered, "supermarket_name", "Total Spend per Supermarket")
    else:
        plot_monthly_spend(df_filtered)

    st.subheader("Spend by Category")
    plot_total_spend(df_filtered, "category", "Total Spend per Category")

    # --- Product Comparison ---
    st.header("🏪 Product Price Comparison")

    product_supermarket_counts = df_filtered.groupby('product')['supermarket_name'].nunique()
    multi_supermarket_products = product_supermarket_counts[product_supermarket_counts > 1].index.tolist()
    with st.expander("📦 Products available in multiple supermarkets"):
        st.write(f"Found {len(multi_supermarket_products)} products sold in more than one supermarket.")
        st.write(multi_supermarket_products)

    products = sorted(df_filtered['product'].dropna().unique())
    selected_product = st.selectbox("Select a Product to Compare", products)

    view_comparison_option = st.sidebar.radio(
        "Product Comparison:",
        ("Monthly", "Over time")
    )
    #selected_product='Leite'
    df_product = df_filtered[df_filtered['product'] == selected_product]
    #view_comparison_option = 'teste'
    if view_comparison_option == "Over time":
        plot_price_comparison(df_product, selected_product)
    else:
        plot_price_comparison_by_month(df_product)



if __name__ == "__main__":
    main()
