import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import json

# Set the base URL for your Spring Boot backend
BASE_URL = "http://localhost:8080/api/trader"

def get_instrument(instrument_id):
    try:
        response = requests.get(f"{BASE_URL}/instrument/{instrument_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_available_instruments():
    try:
        response = requests.get(f"{BASE_URL}/instruments")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return []

def create_approval_request(instrument_id):
    data = {"instrumentId": instrument_id, "status": "PENDING"}
    try:
        response = requests.post(f"{BASE_URL}/approval-request", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_available_limit(counterparty):
    try:
        response = requests.get(f"{BASE_URL}/limit/{counterparty}")
        response.raise_for_status()
        limit_data = response.json()
        if isinstance(limit_data, (int, float)):
            return limit_data
        elif isinstance(limit_data, dict) and 'availableLimit' in limit_data:
            return limit_data['availableLimit']
        else:
            return {"error": "Unexpected response format"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from server"}
    except Exception as e:
        return {"error": f"Unknown error: {str(e)}"}

def execute_trade(instrument_id, counterparty, amount):
    data = {
        "instrumentId": instrument_id,
        "counterparty": counterparty,
        "amount": amount,
        "confirmed": True
    }
    try:
        response = requests.post(f"{BASE_URL}/trade", json=data)
        response.raise_for_status()

        # Try to parse as JSON first
        try:
            return response.json()
        except json.JSONDecodeError:
            # If JSON parsing fails, return the text content
            return {"message": response.text.strip()}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

st.title("Trading System Dashboard")

# Instrument Search
col1, col2 = st.columns(2)
with col1:
    st.subheader("Instrument Search")
    instrument_id = st.text_input("Enter Instrument ID", key="search_instrument_id")
    if st.button("Search Instrument"):
        result = get_instrument(instrument_id)
        if "error" not in result:
            st.json(result)
        else:
            st.warning(f"Error: {result['error']}")
            if st.button("Submit Approval Request"):
                approval_result = create_approval_request(instrument_id)
                if "error" not in approval_result:
                    st.json(approval_result)
                else:
                    st.error(f"Error submitting approval request: {approval_result['error']}")

# Available Limit
with col2:
    st.subheader("Available Limit")
    counterparty = st.text_input("Enter Counterparty")
    if st.button("Get Available Limit"):
        limit = get_available_limit(counterparty)
        if isinstance(limit, (int, float)):
            st.write(f"Available Limit: {limit}")
        elif isinstance(limit, dict) and "error" in limit:
            st.error(f"Error fetching limit: {limit['error']}")
        else:
            st.error("Unexpected response format for available limit")

# Trade Execution Section
st.subheader("Execute Trade")

# Fetch available instruments
available_instruments = get_available_instruments()

# Create a dropdown for available instruments
selected_instrument = st.selectbox(
    "Select Instrument",
    ["Custom"] + available_instruments,
    key="instrument_dropdown"
)

# If "Custom" is selected, show a text input for custom instrument ID
if selected_instrument == "Custom":
    trade_instrument_id = st.text_input("Enter Custom Instrument ID", key="custom_instrument_id")
else:
    trade_instrument_id = selected_instrument

trade_counterparty = st.text_input("Counterparty for Trade")
trade_amount = st.number_input("Trade Amount", min_value=0.0)

if st.button("Execute Trade"):
    with st.spinner("Executing trade..."):
        instrument_check = get_instrument(trade_instrument_id)
        if "error" not in instrument_check:
            trade_result = execute_trade(trade_instrument_id, trade_counterparty, trade_amount)
            if "error" in trade_result:
                st.error(f"Trade execution failed: {trade_result['error']}")
            elif "message" in trade_result:
                st.warning(f"Trade result: {trade_result['message']}")
            else:
                st.success(f"Trade executed successfully: {json.dumps(trade_result, indent=2)}")
        else:
            st.warning("Instrument not found. Do you want to submit an approval request and proceed?")
            if st.button("Confirm and Proceed"):
                approval_result = create_approval_request(trade_instrument_id)
                if "error" not in approval_result:
                    st.json(approval_result)
                    trade_result = execute_trade(trade_instrument_id, trade_counterparty, trade_amount)
                    if "error" in trade_result:
                        st.error(f"Trade execution failed: {trade_result['error']}")
                    elif "message" in trade_result:
                        st.warning(f"Trade result: {trade_result['message']}")
                    else:
                        st.success(f"Trade executed successfully: {json.dumps(trade_result, indent=2)}")
                else:
                    st.error(f"Error submitting approval request: {approval_result['error']}")

# The rest of your Streamlit code (recent trades display, etc.) remains the same
