import streamlit as st
import pandas as pd
import plotly.express as px

def date_range_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Displays date filter on sidebar and returns the filtered dataframe."""
    st.sidebar.header("Filters")
    start_date = st.sidebar.date_input("Start date", value=df['datetime'].min())
    end_date = st.sidebar.date_input("End date", value=df['datetime'].max())

    filtered_df = df[
        (df['datetime'] >= pd.to_datetime(start_date)) &
        (df['datetime'] <= pd.to_datetime(end_date))
    ]
    return filtered_df

def plot_unitary_prices(df: pd.DataFrame, category: str):
    """Plots unitary product prices over time for a category."""
    if df.empty:
        st.warning(f"No data for category {category}")
        return

    fig = px.line(
        df, x='datetime', y='unitary_value', color='product',
        title=f"Unitary Product Prices - {category}", markers=True
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Unitary Value (Price)")
    st.plotly_chart(fig, use_container_width=True)

def plot_total_spend(df: pd.DataFrame, group_col: str, title: str):
    """Plots total spend grouped by a specified column."""
    group_df = df.groupby(group_col)['total_value'].sum().reset_index()
    fig = px.bar(
        group_df, x=group_col, y='total_value', title=title, text_auto=True
    )
    fig.update_layout(xaxis_title=group_col.capitalize(), yaxis_title="Total Spend")
    st.plotly_chart(fig, use_container_width=True)

def plot_price_comparison(df: pd.DataFrame, product: str):
    """Plots price comparison of a product across supermarkets."""
    if df.empty:
        st.warning("No data for the selected product.")
        return

    fig = px.line(
        df, x='datetime', y='unitary_value', color='supermarket_name',
        title=f"Unitary Price Comparison - {product}", markers=True
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Unitary Value (Price)")
    st.plotly_chart(fig, use_container_width=True)