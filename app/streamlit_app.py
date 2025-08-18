import streamlit as st
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

def get_stock_data(ticker):
    """Fetch stock data from our API"""
    try:
        response = requests.get(f"{API_BASE_URL}/stock/{ticker}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

# Streamlit UI
st.set_page_config(
    page_title="Stock Info App",
    page_icon="📈",
    layout="centered"
)

st.title("📈 Stock Information")
st.write("Enter a stock ticker to get real-time information")

# Input form
with st.form("stock_form"):
    # Use selected ticker from sidebar or let user type
    default_ticker = st.session_state.get('selected_ticker', '')
    ticker = st.text_input(
        "Stock Ticker", 
        value=default_ticker,
        placeholder="e.g., AAPL, TSLA, NVDA",
        help="Enter any stock symbol"
    ).upper()
    
    submitted = st.form_submit_button("Get Stock Info", type="primary")
    
    # Clear selected ticker after use
    if submitted:
        st.session_state.selected_ticker = ""

# Display results
if submitted and ticker:
    with st.spinner(f"Fetching data for {ticker}..."):
        data = get_stock_data(ticker)
    
    if "error" in data:
        st.error(f"❌ {data['error']}")
    else:
        # Success - display stock info
        st.success(f"✅ Data for {data['symbol']}")
        
        # Main metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Price", f"${data.get('price', 'N/A')}")
        with col2:
            st.metric("Previous Close", f"${data.get('previous_close', 'N/A')}")
        with col3:
            change = data.get('change')
            if change is not None:
                st.metric("Change", f"${change}", delta=f"{change}")
            else:
                st.metric("Change", "N/A")
        
        # Company info
        st.subheader("Company Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {data.get('name', 'N/A')}")
            st.write(f"**Sector:** {data.get('sector', 'N/A')}")
            st.write(f"**Industry:** {data.get('industry', 'N/A')}")
        with col2:
            st.write(f"**Volume:** {data.get('volume', 'N/A'):,}" if data.get('volume') else "**Volume:** N/A")
            st.write(f"**52W High:** ${data.get('52_week_high', 'N/A')}")
            st.write(f"**52W Low:** ${data.get('52_week_low', 'N/A')}")
        
        # Additional metrics
        if data.get('market_cap'):
            st.write(f"**Market Cap:** ${data['market_cap']:,}")
        if data.get('pe_ratio'):
            st.write(f"**P/E Ratio:** {data['pe_ratio']}")
        if data.get('dividend_yield'):
            st.write(f"**Dividend Yield:** {data['dividend_yield']}%")
        
        # Data source
        st.caption(f"Data source: {data.get('source', 'unknown')}")
        if data.get('note'):
            st.info(f"ℹ️ {data['note']}")
        
        # Raw data (expandable)
        with st.expander("View Raw Data"):
            st.json(data)

# Sidebar with examples
st.sidebar.title("Examples")
st.sidebar.write("Try these popular stocks:")

example_stocks = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "SPY"]

# Use session state for selected ticker
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

for stock in example_stocks:
    if st.sidebar.button(stock, key=f"btn_{stock}"):
        st.session_state.selected_ticker = stock
        st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("💡 This app uses your local stock API")
st.sidebar.caption("Make sure the server is running on localhost:8000")
