import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

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
            st.write(response["response"])
            st.session_state.messages.append({"role": "assistant", "content": response["response"]})

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