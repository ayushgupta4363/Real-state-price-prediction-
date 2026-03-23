import streamlit as st
import util

# Page configuration
st.set_page_config(page_title="Bangalore House Price Predictor", layout="centered")

def main():
    st.title("🏡 Bangalore House Price Predictor")
    st.write("Enter the details of the property to get an estimated price.")

    # Load artifacts once
    if 'data_loaded' not in st.session_state:
        st.write("Loading data for the first time...") # Debug line
        util.load_saved_artifacts()
        st.session_state['data_loaded'] = True
        st.session_state['locations'] = util.get_location_names()
        st.write("Data loaded successfully!") # Debug line
    # --- UI Components ---
    col1, col2 = st.columns(2)

    with col1:
        total_sqft = st.number_input("Total Square Feet", min_value=300, max_value=50000, value=1000)
        location = st.selectbox("Location", options=st.session_state['locations'])

    with col2:
        bhk = st.radio("BHK", options=[1, 2, 3, 4, 5], index=1, horizontal=True)
        bath = st.radio("Bathrooms", options=[1, 2, 3, 4, 5], index=1, horizontal=True)

    # --- Prediction Logic ---
    if st.button("Estimate Price"):
        try:
            price = util.get_estimated_price(location, total_sqft, bhk, bath)
            st.success(f"### The estimated price is ₹ {price} Lakhs")
        except Exception as e:
            st.error(f"Error in prediction: {e}")

if __name__ == "__main__":
    main()