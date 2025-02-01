import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet
from prophet.plot import plot_plotly
from statsmodels.tsa.seasonal import seasonal_decompose

# Dashboard configuration
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

# Title and sidebar
st.title("📈 Stock Price Forecasting Dashboard")
st.sidebar.header("User Input Parameters")

# Date selection
today = datetime.today().strftime("%Y-%m-%d")
start_date = st.sidebar.date_input("Start date", datetime(2020, 1, 1))
end_date = st.sidebar.date_input("End date", datetime.today())

# Stock selection
ticker = st.sidebar.text_input("Enter stock ticker", "AAPL")

# Fetch stock data
@st.cache_data
def load_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    data.reset_index(inplace=True)
    return data

try:
    df = load_data(ticker, start_date, end_date)
    
    if df.empty:
        st.error("No data found for this ticker symbol. Please try another.")
    else:
        # Display raw data
        st.subheader(f"📊 Historical Data for {ticker}")
        st.dataframe(df.tail(10), use_container_width=True)

        # Price chart
        st.subheader("📈 Price Movement")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Closing Price'))
        fig.update_layout(xaxis_title='Date', yaxis_title='Price', hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

        # Candlestick chart
        st.subheader("🕯️ Candlestick Chart")
        candlestick = go.Figure(data=[go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])
        candlestick.update_layout(xaxis_rangeslider_visible=False)
        st.plotly_chart(candlestick, use_container_width=True)

        # Time series decomposition
        st.subheader("⏳ Time Series Decomposition")
        decomposition = seasonal_decompose(df.set_index('Date')['Close'], model='additive', period=30)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write("**Original Series**")
            st.line_chart(df.set_index('Date')['Close'])
        with col2:
            st.write("**Trend Component**")
            st.line_chart(decomposition.trend)
        with col3:
            st.write("**Seasonal Component**")
            st.line_chart(decomposition.seasonal)
        with col4:
            st.write("**Residual Component**")
            st.line_chart(decomposition.resid)

        # Forecasting with Prophet
        st.subheader("🔮 Price Forecasting")
        periods = st.slider("Select number of days to forecast:", 30, 365, 90)
        
        # Prepare data for Prophet
        prophet_df = df[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
        
        # Create and fit model
        model = Prophet(daily_seasonality=True)
        model.fit(prophet_df)
        
        # Make future dataframe
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        # Show forecast plot
        st.write("Forecasted Prices")
        fig1 = plot_plotly(model, forecast)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Show forecast components
        st.write("Forecast Components")
        fig2 = model.plot_components(forecast)
        st.pyplot(fig2, use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")


