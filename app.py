
import streamlit as st
import requests
import json
from datetime import datetime
from calendar import monthrange

from materials import MATERIAL_PRICING
from defaults import HEADER_DEFAULTS

# Session ID on refresh
@st.cache_resource(show_spinner=False)
def get_session_id():
    try:
        response = requests.post("http://dev2poci.co.doterra.net:50000/RESTAdapter/getSessionId")
        return response.json().get("SESSION", "NO_SESSION")
    except:
        return "NO_SESSION"

# UI setup
st.set_page_config(page_title="dōTERRA Test Order Creator", layout="wide")

st.markdown("""
    <style>
        body {
            background: linear-gradient(to right, #a1c4fd, #c2e9fb);
            font-family: 'Segoe UI', sans-serif;
        }
        .block-container {
            padding-top: 2rem;
        }
        .stAlert {
            background-color: #fff3cd;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📦 dōTERRA Test Order Creator")

# Env and session setup
environments = {
    "DE2": "http://dev2poci.co.doterra.net:50000/RESTAdapter/OrderSubmission"
}
env = st.selectbox("Select Environment", list(environments.keys()))
api_url = environments[env]
session_id = get_session_id()
st.info(f"Session ID: `{session_id}`")

# Data entry mode
data_mode = st.toggle("Full Data Entry Mode")

if not data_mode:
    with st.expander("📦 Basic Setup", expanded=True):
        order_start = st.text_input("Starting Order Number", max_chars=10, help="First Sales Order number. Will increment for additional orders.")
        num_orders = st.number_input("Number of Orders", min_value=1, max_value=10, value=1)

        currency = st.selectbox("Currency", ["USD", "CAD"])
        country = st.selectbox("Country", ["US", "CA"])

        ship_options = HEADER_DEFAULTS[f"ShipCondition_{country}"]
        priority_options = HEADER_DEFAULTS[f"ShippingPriority_{country}"]
        ship_method = st.selectbox("Shipping Method", ship_options)
        delivery_priority = st.selectbox("Delivery Priority", priority_options)

    with st.expander("👤 Customer & Ship-to", expanded=True):
        name1 = st.text_input("First Name", "George")
        name2 = st.text_input("Last Name", "Washington")
        street = st.text_input("Street Address 1", "1600 Pennsylvania Ave NW")
        street2 = st.text_input("Street Address 2", "")
        city = st.text_input("City", "Washington")
        state = st.text_input("State", "DC")
        zipcode = st.text_input("ZIP", "20500")
        email = st.text_input("Email", "gwashington@usa.gov")

        match_sold = st.checkbox("Sold-to Details Match Ship-to Details", value=True)
        match_bill = st.checkbox("Bill-to Details Match Ship-to Details", value=True)

    with st.expander("💳 Payment Details", expanded=False):
        card_type = st.selectbox("Card Type", ["MASTER", "VISA"])
        card_name = st.text_input("Cardholder Name", "George Washington")
        card_token = st.text_input("Card Token", "-E803-5004-N7D3CBYP3Z3K5A")

        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Expiration Month", list(range(1, 13)))
        with col2:
            year = st.selectbox("Expiration Year", list(range(datetime.now().year, datetime.now().year + 6)))
        last_day = monthrange(year, month)[1]
        exp_date = f"{year}{month:02d}{last_day}"

    st.subheader("📦 Items")
    item_data = []
    num_items = st.number_input("How many items?", min_value=1, max_value=10, value=1)

    for i in range(num_items):
        st.markdown(f"**Item {i+1}**")
        mat = st.text_input(f"Material {i+1}", key=f"mat{i}")
        qty = st.number_input(f"Quantity {i+1}", min_value=1, value=1, key=f"qty{i}")

        if mat not in MATERIAL_PRICING:
            st.warning(f"Material {mat} missing price info!", icon="⚠️")
            st.stop()

        item_data.append({
            "Quantity": str(qty),
            "Material": mat,
            "ItemPrice": MATERIAL_PRICING[mat]
        })

    if order_start:
        base_order = int(order_start)
        orders = []

        for i in range(num_orders):
            order_number = str(base_order + i)
            order = {
                "New_Update_Delete": "I",
                "SessionID": session_id,
                "OrderDetails": {
                    "Header": {
                        "SalesOrderNum": order_number,
                        "DocumentCurrency": currency,
                        "country": country,
                        "ShipCondition": ship_method,
                        "ShippingPriority": delivery_priority,
                        "CardType": card_type,
                        "CardHolder": card_name,
                        "CardNumber": card_token,
                        "ExpDate": exp_date,
                        "ShiptoPartyName1": name1,
                        "ShiptoPartyName2": name2,
                        "ShiptoPartyStr": street,
                        "ShiptoPartyStr1": street2,
                        "ShiptoPartyCity": city,
                        "ShiptoPartyCode": zipcode,
                        "ShipToPartyEmailId": email,
                        **{k: v for k, v in HEADER_DEFAULTS.items() if not k.startswith("ShipCondition_")}
                    },
                    "ItemDetails": item_data
                }
            }
            orders.append(order)

        col1, col2 = st.columns([1, 3])
        with col1:
            st.download_button(
                label="💾 Download Payload",
                data=json.dumps(orders, indent=2),
                file_name="test_orders_payload.json",
                mime="application/json"
            )
        with col2:
            if st.button("🚀 Generate"):
                for payload in orders:
                    res = requests.post(api_url, json=payload)
                    st.success(f"Order `{payload['OrderDetails']['Header']['SalesOrderNum']}` sent.")
                    st.json(res.json())

else:
    st.subheader("📋 Full Payload Editor")
    base_payload = {
        "New_Update_Delete": "I",
        "SessionID": session_id,
        "OrderDetails": {
            "Header": {**HEADER_DEFAULTS},
            "ItemDetails": []
        }
    }
    user_payload = st.text_area("Paste or edit full JSON payload", value=json.dumps(base_payload, indent=2), height=600)

    col1, col2 = st.columns([1, 3])
    with col1:
        st.download_button(
            label="💾 Download Payload",
            data=user_payload,
            file_name="custom_payload.json",
            mime="application/json"
        )
    with col2:
        if st.button("🚀 Generate"):
            payload = json.loads(user_payload)
            res = requests.post(api_url, json=payload)
            st.success("Order submitted")
            st.json(res.json())
