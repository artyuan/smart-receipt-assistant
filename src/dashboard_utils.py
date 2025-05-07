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
    df = df.groupby(['invoice_id', 'supermarket_name', 'datetime', 'description']).last().reset_index()

    fig = px.line(
        df, x='datetime', y='unitary_value', color='full_product_name',
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

def plot_monthly_spend(df: pd.DataFrame):
    """Plots monthly spend per supermarket."""
    df['month'] = df['datetime'].dt.strftime('%B')
    group_df = df.groupby(['month', 'supermarket_name'])['total_value'].sum().reset_index()

    fig = px.bar(
        group_df,
        x='month',
        y='total_value',
        color='supermarket_name',
        barmode='group',
        title="Monthly Spend by Supermarket",
        text_auto=True
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Total Spend")
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


def plot_price_comparison_by_month(df: pd.DataFrame):
    """Plots unit price per product per month, colored by supermarket."""
    # Ensure datetime is in datetime format
    df['month'] = df['datetime'].dt.strftime('%b')  # Short month name like 'Jan'

    # Create combined label for x-axis: Month + Product
    df['month_product'] = df['month'] + ' - ' + df['full_product_name']

    # Group to get latest price per month-product-supermarket
    group_df = (
        df.groupby(['month_product', 'month', 'full_product_name', 'supermarket_name'])['unitary_value']
        .last()
        .reset_index()
    )

    fig = px.bar(
        group_df,
        x='month_product',
        y='unitary_value',
        color='supermarket_name',
        barmode='group',
        title="Monthly Price Comparison by Product and Supermarket",
        text_auto=True
    )

    fig.update_layout(
        xaxis_title="Month - Product",
        yaxis_title="Unit Price",
        xaxis_tickangle=45,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
