
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
        user = st.secrets["session_api"]["user"]
        password = st.secrets["session_api"]["pass"]

        response = requests.post(
            "http://dev2poci.co.doterra.net:50000/RESTAdapter/getSessionId",
            auth=(user, password)
        )
        response.raise_for_status()
        return response.json().get("SESSION", "NO_SESSION")

    except Exception as e:
        st.error(f"Failed to get session ID: {e}")
        return "NO_SESSION"



# UI setup
st.set_page_config(page_title="dōTERRA Test Order Creator", layout="wide")
st.title("📦 dōTERRA Test Order Creator")

# Env and session setup
environments = {
    "DE2": "http://dev2poci.co.doterra.net:50000/RESTAdapter/OrderSubmission"
}
env = st.selectbox("Select Environment", list(environments.keys()))
api_url = environments[env]
session_id = get_session_id()
st.markdown("**Session ID:**")
st.code(session_id, language="text")

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

        match_sold = st.checkbox("Sold-to Details Match Ship-to Details", value=True, key="sold_match_in_expander")
        if not match_sold:
            st.markdown("**Sold-to Override Details**")
            sold_name1 = st.text_input("Sold-to First Name", "George", key="sold_name1")
            sold_name2 = st.text_input("Sold-to Last Name", "Washington", key="sold_name2")
            sold_street = st.text_input("Sold-to Street Address 1", "1600 Pennsylvania Ave NW", key="sold_street")
            sold_street2 = st.text_input("Sold-to Street Address 2", "", key="sold_street2")
            sold_city = st.text_input("Sold-to City", "Washington", key="sold_city")
            sold_state = st.text_input("Sold-to State", "DC", key="sold_state")
            sold_zip = st.text_input("Sold-to ZIP", "20500", key="sold_zip")
            sold_email = st.text_input("Sold-to Email", "gwashington@usa.gov", key="sold_email")

        match_bill = st.checkbox("Bill-to Details Match Ship-to Details", value=True, key="bill_match_in_expander")
        if not match_bill:
            st.markdown("**Bill-to Override Details**")
            bill_name1 = st.text_input("Bill-to First Name", "George", key="bill_name1")
            bill_name2 = st.text_input("Bill-to Last Name", "Washington", key="bill_name2")
            bill_street = st.text_input("Bill-to Street Address 1", "1600 Pennsylvania Ave NW", key="bill_street")
            bill_street2 = st.text_input("Bill-to Street Address 2", "", key="bill_street2")
            bill_city = st.text_input("Bill-to City", "Washington", key="bill_city")
            bill_state = st.text_input("Bill-to State", "DC", key="bill_state")
            bill_zip = st.text_input("Bill-to ZIP", "20500", key="bill_zip")
            bill_email = st.text_input("Bill-to Email", "gwashington@usa.gov", key="bill_email")

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
    st.caption("➕ Enter a Material and Quantity for each line, then press **Enter** to confirm your entry.")

    item_data = []
    missing_materials = []
    num_items = st.number_input("How many items?", min_value=1, max_value=10, value=1)

    for i in range(num_items):
        st.markdown(f"**Item {i+1}**")
        mat = st.text_input(f"Material {i+1}", key=f"mat{i}")
        qty = st.number_input(f"Quantity {i+1}", min_value=1, value=1, key=f"qty{i}")

        if mat and mat not in MATERIAL_PRICING:
            missing_materials.append(mat)
            st.markdown(f"⚠️ Material `{mat}` not found in pricing list.")

        if mat in MATERIAL_PRICING:
            item_data.append({
                "Quantity": str(qty),
                "Material": mat,
                "ItemPrice": MATERIAL_PRICING[mat]
            })

    # Show table of entered items
    st.subheader("🧾 Items Summary")
    if item_data:
        st.table([
            {"Material": item["Material"], "Quantity": item["Quantity"]}
            for item in item_data
        ])
    else:
        st.info("No items have been added yet. Enter materials above to populate the summary.")


    # Show alert if any materials are missing
    if missing_materials:
        st.error("🚫 One or more materials are missing pricing data. Please update your materials list to proceed.")
        with st.expander("❌ Missing Materials", expanded=True):
            for m in missing_materials:
                st.code(m, language="text")
        st.stop()

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
                        
                        "SoldtoPartyName1": sold_name1 if not match_sold else name1,
                        "SoldtoPartyName2": sold_name2 if not match_sold else name2,
                        "SoldtoPartyStr": sold_street if not match_sold else street,
                        "SoldtoPartyStr1": sold_street2 if not match_sold else street2,
                        "SoldtoPartyCity": sold_city if not match_sold else city,
                        "SoldtoPartyRegion": sold_state if not match_sold else state,
                        "SoldtoPartyCode": sold_zip if not match_sold else zipcode,
                        "SoldtoPartyEmailId": sold_email if not match_sold else email,
                        "BilltoPartyName1": bill_name1 if not match_bill else name1,
                        "BilltoPartyName2": bill_name2 if not match_bill else name2,
                        "BilltoPartyStr": bill_street if not match_bill else street,
                        "BilltoPartyStr1": bill_street2 if not match_bill else street2,
                        "BilltoPartyCity": bill_city if not match_bill else city,
                        "BilltoPartyRegion": bill_state if not match_bill else state,
                        "BilltoPartyCode": bill_zip if not match_bill else zipcode,
                        "BilltoPartyEmailId": bill_email if not match_bill else email,

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
                label="Download Payload",
                data=json.dumps(orders, indent=2),
                file_name="test_orders_payload.json",
                mime="application/json"
            )
        with col2:
            if st.button("Generate"):
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
