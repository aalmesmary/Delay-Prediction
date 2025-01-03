import streamlit as st
import pandas as pd
import base64
from utils.pipline import prediction

# Configure page
st.set_page_config(page_title="Delay Prediction", page_icon="logo.png")


# Function to convert an image file to a base64 string
def get_base64_encoded_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        st.error(f"Image file not found: {image_path}")
        return None


# Path to the local image
image_path = "ADNOC.png"

# Encode image in base64 format
base64_image = get_base64_encoded_image(image_path)

if base64_image:
    # Custom CSS to use the base64 image as a background
    background_image_style = f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5)), 
                        url(data:image/png;base64,{base64_image});
            background-size: 40%;
            background-repeat: no-repeat;
            background-position: top right;
            background-attachment: scroll;
        }}
    </style>
    """
    # Embed custom CSS into the Streamlit app
    st.markdown(background_image_style, unsafe_allow_html=True)
else:
    st.write("Could not encode image")


# Function to load the CSV file and return a DataFrame
def load_data(file_buffer):
    try:
        df = pd.read_csv(file_buffer)
        prediction_df = prediction(df)
        return prediction_df
    except Exception as e:
        st.error(f"Error in loading the data: {e}")
        return pd.DataFrame()


# Function to apply row-wise styling based on 'Predicted_Delay_Status'
def highlight_delay(row):
    if row["Predicted_Delay_Status"] == "Delayed":
        return ["background-color: rgba(255, 0, 0, 0.3)"] * len(row)
    elif row["Predicted_Delay_Status"] == "On Time":
        return ["background-color: rgba(0, 255, 0, 0.3)"] * len(row)
    else:
        return [""] * len(row)


# Streamlit app
def main():
    st.title("Delay Prediction")

    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        # Load the data
        data = load_data(uploaded_file)

        # Ensure the correct columns are present
        expected_columns = {"Activity ID", "Predicted_Delay_Status"}
        if not expected_columns.issubset(data.columns):
            st.error(
                f"Expected columns: {expected_columns}. Found columns: {set(data.columns)}"
            )
        else:
            # Display the data
            st.dataframe(data.style.apply(highlight_delay, axis=1))


if __name__ == "__main__":
    main()
