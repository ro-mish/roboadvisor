import os
import requests
import streamlit as st
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def clean_response_text(text: str) -> str:
    """Clean response text for better display in Streamlit"""
    if not text:
        return text
    
    # Remove any weird Unicode characters that might cause display issues
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix paragraph breaks
    text = re.sub(r'\.\s+', '.\n\n', text)
    text = re.sub(r'\n\n+', '\n\n', text)
    
    return text.strip()

def ask_roboadvisor(query: str) -> dict:
    try:
        response = requests.post(f"{API_BASE_URL}/chat", json={"query": query}, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

st.set_page_config(page_title="AI Wealth Advisor", page_icon="💼")
st.title("💼 AI Wealth Advisor")

# Initialize chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hi! I'm your AI Wealth Advisor. Ask me about any stock!"}
    ]

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.write(clean_response_text(message["content"]))
        else:
            st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask about any stock..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_roboadvisor(prompt)
        
        if "error" in response:
            error_msg = f"❌ Error: {response['error']}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            # Clean and display the main response
            cleaned_response = clean_response_text(response["response"])
            st.write(cleaned_response)
            st.session_state.messages.append({"role": "assistant", "content": cleaned_response})
            
            # Store the latest response data for the data tab
            st.session_state.latest_response = response

# Sidebar
with st.sidebar:
    st.header("💡 Examples")
    examples = [
        "How is Tesla performing?",
        "Should I buy Apple?",
        "NVIDIA analysis please",
        "Microsoft outlook?"
    ]
    
    for query in examples:
        if st.button(query, key=query):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()
    
    if st.button("Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 Hi! I'm your AI Wealth Advisor. Ask me about any stock!"}
        ]
        st.rerun()

# Data tab at the bottom
if hasattr(st.session_state, 'latest_response') and st.session_state.latest_response:
    st.markdown("---")
    st.header("📊 Market Data Analysis")
    
    response_data = st.session_state.latest_response
    
    # Create tabs for different data views
    tab1, tab2, tab3 = st.tabs(["📈 Stock Data", "🔍 Comprehensive Data", "⚙️ Debug Info"])
    
    with tab1:
        if response_data.get("stock_data"):
            stock = response_data["stock_data"]
            
            # Convert to dict if it's a Pydantic model
            if hasattr(stock, 'dict'):
                stock_dict = stock.dict()
            elif hasattr(stock, 'model_dump'):
                stock_dict = stock.model_dump()
            else:
                stock_dict = stock
            
            # Safely get values with defaults
            price = stock_dict.get('price', 0) or 0
            change = stock_dict.get('change', 0) or 0
            volume = stock_dict.get('volume', 0) or 0
            previous_close = stock_dict.get('previous_close', 0) or 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Price", f"${price:.2f}")
            with col2:
                st.metric("Change", f"${change:.2f}", delta=f"{change:.2f}")
            with col3:
                st.metric("Volume", f"{volume:,}")
            
            st.subheader("Stock Details")
            try:
                st.json({
                    "Symbol": stock_dict.get("symbol", "N/A"),
                    "Price": f"${price:.2f}",
                    "Previous Close": f"${previous_close:.2f}",
                    "Change": f"${change:.2f}",
                    "Change %": str(stock_dict.get('change_percent', 'N/A')),
                    "Volume": f"{volume:,}",
                    "Source": str(stock_dict.get('source', 'N/A'))
                })
            except Exception as e:
                st.error(f"Error displaying stock details: {e}")
                st.write("Raw stock data:")
                st.write(stock_dict)
        else:
            st.info("No stock data available for the latest query.")
    
    with tab2:
        if response_data.get("comprehensive_context"):
            context = response_data["comprehensive_context"]
            
            if context and isinstance(context, dict):
                st.subheader(f"Comprehensive Data for {context.get('symbol', 'N/A')}")
                
                # Show data sources
                data_sources = context.get("data_sources", [])
                if data_sources and isinstance(data_sources, list):
                    st.write("**Data Sources Available:**", ", ".join(data_sources))
                    
                    # Display each data source
                    for source in data_sources:
                        if source in context and context[source]:
                            with st.expander(f"📊 {source.replace('_', ' ').title()}"):
                                try:
                                    st.json(context[source])
                                except Exception as e:
                                    st.error(f"Error displaying {source}: {e}")
                                    st.write(context[source])
                else:
                    st.info("No data sources available in comprehensive context.")
            else:
                st.error("Invalid comprehensive context format.")
        else:
            st.info("No comprehensive data available for the latest query.")
    
    with tab3:
        st.subheader("Debug Information")
        
        # Safely extract comprehensive context info
        comprehensive_context = response_data.get("comprehensive_context")
        data_sources = []
        if comprehensive_context and isinstance(comprehensive_context, dict):
            data_sources = comprehensive_context.get("data_sources", [])
        
        debug_info = {
            "Query": response_data.get("original_query", "N/A"),
            "Structured Query": response_data.get("structured_query", {}),
            "User Level": response_data.get("user_level", "N/A"),
            "Has Stock Data": bool(response_data.get("stock_data")),
            "Has Comprehensive Context": bool(comprehensive_context),
            "Data Sources": data_sources,
            "Comprehensive Context Type": str(type(comprehensive_context).__name__) if comprehensive_context else "None"
        }
        
        try:
            st.json(debug_info)
        except Exception as e:
            st.error(f"Error displaying debug info: {e}")
            st.write("Raw debug info:")
            st.write(debug_info)