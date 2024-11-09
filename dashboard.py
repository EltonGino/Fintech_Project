import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
from ml_models import arima_forecast, prophet_forecast, lstm_forecast  # Import ML/DL functions
import statsmodels.api as sm
import prophet
import tensorflow as tf
import plotly.graph_objects as go

# Initialize database
def init_database():
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            timestamp TEXT,
            ticker TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (timestamp, ticker)
        )
    ''')
    conn.commit()
    conn.close()

# Load data from SQLite database or fetch if not available
def load_data(ticker, start_date, end_date):
    conn = sqlite3.connect('stock_data.db')
    query = '''
        SELECT * FROM stock_data
        WHERE ticker = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    '''
    data = pd.read_sql_query(query, conn, params=(ticker, start_date, end_date))
    conn.close()
    if data.empty:  # Fetch from yfinance if data is missing
        data = fetch_data_from_yfinance(ticker, start_date, end_date)
        if not data.empty:
            conn = sqlite3.connect('stock_data.db')
            data.to_sql('stock_data', conn, if_exists='append', index=False)
            conn.close()
    return data

# Fetch data from yfinance
def fetch_data_from_yfinance(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    data = stock.history(start=start_date, end=end_date)
    data.reset_index(inplace=True)
    data['ticker'] = ticker
    data = data.rename(columns={"Date": "timestamp", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    return data[['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'volume']]

# Get the most recent data for a given ticker
def get_most_recent_data(ticker):
    conn = sqlite3.connect('stock_data.db')
    query = '''
        SELECT * FROM stock_data
        WHERE ticker = ?
        ORDER BY timestamp DESC
        LIMIT 1
    '''
    most_recent_data = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return most_recent_data.iloc[0] if not most_recent_data.empty else None

# Map popular company names to tickers
company_ticker_map = {
    "Apple": "AAPL",
    "Nvidia": "NVDA",
    "Tesla": "TSLA",
    "Amazon": "AMZN",
    "AMD": "AMD",
    "Petrobras": "PETR4.SA",
    "Vale": "VALE3.SA",
    "Itaú Unibanco": "ITUB4.SA",
    "Bradesco": "BBDC4.SA",
    "Ambev": "ABEV3.SA",
    "Ford": "F",
    "Google": "GOOGL",
    "Facebook": "FB",
    "Microsoft": "MSFT",
    "Netflix": "NFLX",
    "Alibaba": "BABA",
    "Tencent": "TCEHY",
    "Sony": "SONY",
    "Samsung": "SSNLF",
    "NIO": "NIO",
    "General Motors": "GM",
    "Toyota": "TM",
    "Honda": "HMC",
    "BMW": "BMWYY",
    "Volkswagen": "VWAGY",
    "Mercedes-Benz": "DDAIF",
    "Pfizer": "PFE",
    "Moderna": "MRNA",
    "BioNTech": "BNTX",
    "Johnson & Johnson": "JNJ",
    "AstraZeneca": "AZN",
    "Sinovac": "SVA",
    "Sinopharm": "SHTDY",
    "PetroChina": "PTR",
    "Exxon Mobil": "XOM",
    "Chevron": "CVX",
    "Shell": "RDS-A"
}

# Retrieve ticker from company name
def get_ticker_from_name(company_name):
    return company_ticker_map.get(company_name.title())

# Streamlit UI
st.set_page_config(page_title="Stock Data Dashboard", layout="wide")
st.title("📈 Real-Time Stock Data Dashboard")
st.sidebar.header("Filter Options")

# Quick Select Ticker
st.sidebar.subheader("Quick Select Ticker")
quick_ticker = st.sidebar.selectbox("Choose a popular stock", list(company_ticker_map.values()))

# Custom Filter Options
st.sidebar.subheader("Custom Filter Options")
company_name = st.sidebar.text_input("Company Name (optional)", key="company_name")
ticker_input = st.sidebar.text_input("Ticker Symbol (e.g., AAPL)", key="ticker").upper()
ticker = get_ticker_from_name(company_name) or ticker_input or quick_ticker

# Multi-Stock Comparison
st.sidebar.subheader("Multi-Stock Comparison")
available_tickers = list(company_ticker_map.values()) + [ticker_input] if ticker_input else list(company_ticker_map.values())
selected_tickers = st.sidebar.multiselect("Select stocks to compare", options=available_tickers, default=[ticker])

# Ensure ticker_input is in selected_tickers if not in the predefined list
if ticker_input and ticker_input not in selected_tickers:
    selected_tickers.append(ticker_input)

# Date Inputs
start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=30), min_value=datetime(2019, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())

# Display chosen tickers
st.write(f"Chosen Ticker for Analysis: {ticker}")
st.write(f"Tickers for Comparison: {selected_tickers}")

# Fetch data for primary ticker and selected comparison tickers
data = load_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
combined_data = pd.DataFrame()
for selected_ticker in selected_tickers:
    stock_data = load_data(selected_ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if not stock_data.empty:
        combined_data = pd.concat([combined_data, stock_data], axis=0)

# Display most recent price for each selected ticker
for selected_ticker in selected_tickers:
    most_recent_data = get_most_recent_data(selected_ticker)
    if most_recent_data is not None:
        st.sidebar.metric(label=f"{selected_ticker} - Most Recent Price", value=f"${most_recent_data['close']:.2f}")
        st.sidebar.metric(label=f"{selected_ticker} - Most Recent Date", value=most_recent_data['timestamp'])

# Display data metrics at a glance for the primary ticker
if not data.empty:
    st.write(f"### Data for {ticker} from {start_date} to {end_date}")
    col1, col2, col3, col4 = st.columns(4)
    avg_close = data['close'].mean()
    price_change = data['close'].iloc[-1] - data['close'].iloc[0] if len(data) > 1 else 0
    volume_avg = data['volume'].mean()
    most_recent_data = get_most_recent_data(ticker)
    most_recent_price = most_recent_data['close'] if most_recent_data is not None else "N/A"
    most_recent_date = most_recent_data['timestamp'] if most_recent_data is not None else "N/A"

    col1.metric(label="Average Close Price", value=f"${avg_close:.2f}")
    col2.metric(label="Price Change", value=f"${price_change:.2f}")
    col3.metric(label="Average Volume", value=f"{volume_avg:.0f}")
    col4.metric(label="Most Recent Price", value=f"${most_recent_price:.2f}", delta=f"Date: {most_recent_date}")

    # Display raw data in an expandable section
    with st.expander("View Raw Data"):
        st.dataframe(data)

    # Interactive line chart for stock prices
    st.subheader("Price Movements")
    fig = px.line(data, x="timestamp", y=["open", "high", "low", "close"],
                  title="Stock Prices Over Time", labels={"timestamp": "Date"})
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig, use_container_width=True)

    # Volume bar chart
    st.subheader("Trading Volume")
    fig_vol = px.bar(data, x="timestamp", y="volume", title="Trading Volume Over Time",
                     labels={"timestamp": "Date", "volume": "Volume"})
    fig_vol.update_layout(bargap=0.1)
    st.plotly_chart(fig_vol, use_container_width=True)

    # Advanced Filtering and Sorting
    st.subheader("Advanced Filtering and Sorting")
    sort_by = st.selectbox("Sort Data By:", options=["timestamp", "open", "close", "high", "low", "volume"])
    ascending = st.checkbox("Sort in Ascending Order", value=True)
    sorted_data = data.sort_values(by=sort_by, ascending=ascending)
    st.write(f"Data sorted by {sort_by} ({'Ascending' if ascending else 'Descending'}):")
    st.dataframe(sorted_data)

    # Filter by price range
    st.subheader("Filter by Price Range")
    min_price, max_price = st.slider("Select Price Range (Close Price)", float(data['close'].min()),
                                     float(data['close'].max()),
                                     (float(data['close'].min()), float(data['close'].max())))
    filtered_data = sorted_data[(sorted_data['close'] >= min_price) & (sorted_data['close'] <= max_price)]
    st.write("Filtered Data:")
    st.dataframe(filtered_data)

# Comparison charts for selected tickers
if not combined_data.empty:
    st.write("### Comparison of Selected Stocks")
    fig_compare = px.line(combined_data, x="timestamp", y="close", color="ticker", title="Stock Price Comparison")
    st.plotly_chart(fig_compare, use_container_width=True)

    fig_vol_compare = px.bar(combined_data, x="timestamp", y="volume", color="ticker", title="Volume Comparison")
    fig_vol_compare.update_layout(bargap=0.1)
    st.plotly_chart(fig_vol_compare, use_container_width=True)

# Machine Learning & Deep Learning Forecasting Section
st.subheader("Machine Learning & Deep Learning Forecasting")
st.write("In this section, we provide forecasts using three different models: ARIMA, Prophet, and LSTM.")

forecast_period = st.slider("Forecast Period (days)", 1, 30, 7)

# Initialize model_metrics to store each model's results
model_metrics = []

if st.button("Run Forecast"):
    # ARIMA Forecast
    st.write("#### ARIMA Forecast")
    arima_forecast_df, arima_mse, arima_mae = arima_forecast(data, forecast_period)
    fig_arima = go.Figure()
    fig_arima.add_trace(go.Scatter(x=arima_forecast_df["Date"], y=arima_forecast_df["Forecast"],
                                   mode='lines', name='Forecast'))
    # Customize Plotly chart for ARIMA
    fig_arima.update_layout(title="ARIMA Forecast", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig_arima, use_container_width=True)
    st.write(f"**Mean Squared Error (MSE):** {arima_mse:.4f}")
    st.write(f"**Mean Absolute Error (MAE):** {arima_mae:.4f}")
    model_metrics.append({"Model": "ARIMA", "MSE": arima_mse, "MAE": arima_mae})

    # Prophet Forecast with confidence intervals
    st.write("#### Prophet Forecast")
    prophet_forecast_df, prophet_mse, prophet_mae = prophet_forecast(data, forecast_period)
    fig_prophet = go.Figure()
    fig_prophet.add_trace(go.Scatter(x=prophet_forecast_df["Date"], y=prophet_forecast_df["Forecast"],
                                     mode='lines', name='Forecast'))
    fig_prophet.add_trace(go.Scatter(x=prophet_forecast_df["Date"], y=prophet_forecast_df["Lower Bound"],
                                     mode='lines', fill=None, name='Lower Bound'))
    fig_prophet.add_trace(go.Scatter(x=prophet_forecast_df["Date"], y=prophet_forecast_df["Upper Bound"],
                                     mode='lines', fill='tonexty', name='Upper Bound'))
    # Customize Plotly chart for Prophet with confidence intervals
    fig_prophet.update_layout(title="Prophet Forecast", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig_prophet, use_container_width=True)
    st.write(f"**Mean Squared Error (MSE):** {prophet_mse:.4f}")
    st.write(f"**Mean Absolute Error (MAE):** {prophet_mae:.4f}")
    model_metrics.append({"Model": "Prophet", "MSE": prophet_mse, "MAE": prophet_mae})

    # LSTM Forecast
    st.write("#### LSTM Forecast")
    try:
        lstm_forecast_df, lstm_mse, lstm_mae = lstm_forecast(data, forecast_period)
        fig_lstm = go.Figure()
        fig_lstm.add_trace(go.Scatter(x=lstm_forecast_df["Date"], y=lstm_forecast_df["Forecast"],
                                      mode='lines', name='Forecast'))
        # Customize Plotly chart for LSTM
        fig_lstm.update_layout(title="LSTM Forecast", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig_lstm, use_container_width=True)
        st.write(f"**Mean Squared Error (MSE):** {lstm_mse:.4f}")
        st.write(f"**Mean Absolute Error (MAE):** {lstm_mae:.4f}")
        model_metrics.append({"Model": "LSTM", "MSE": lstm_mse, "MAE": lstm_mae})
    except ValueError as e:
        st.error(f"LSTM Forecast Error: {e}")
        st.write("LSTM models require more data for reliable predictions.")

# Display model metrics comparison
if model_metrics:
    comparison_df = pd.DataFrame(model_metrics)
    st.write("### Model Comparison")
    st.dataframe(comparison_df)
    fig_comparison = go.Figure(data=[
        go.Bar(name='MSE', x=comparison_df["Model"], y=comparison_df["MSE"]),
        go.Bar(name='MAE', x=comparison_df["Model"], y=comparison_df["MAE"])
    ])
    fig_comparison.update_layout(barmode='group', title="Model Comparison Metrics")
    st.plotly_chart(fig_comparison, use_container_width=True)

# Download option for filtered data
st.sidebar.subheader("Download Data")
csv = data.to_csv(index=False)
st.sidebar.download_button(label="Download CSV", data=csv, file_name=f"{ticker}_data.csv", mime="text/csv")

# Initialize the database
init_database()