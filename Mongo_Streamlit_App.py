import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from io import BytesIO
from pymongo import MongoClient

# MongoDB data loader
@st.cache_data
def load_data():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["airbnb_project"]
    collection = db["listings"]
    cursor = collection.find()
    df = pd.DataFrame(list(cursor))

    # Data cleaning and transformations applied inline
    df['longitude'] = df['address'].apply(lambda x: x.get('location', {}).get('coordinates', [None, None])[0])
    df['latitude'] = df['address'].apply(lambda x: x.get('location', {}).get('coordinates', [None, None])[1])
    df['city'] = df['address'].apply(lambda x: x.get('market') if isinstance(x, dict) and 'market' in x else x.get('city', None) if isinstance(x, dict) else None)
    df['country'] = df['address'].apply(lambda x: x.get('country', None) if isinstance(x, dict) else None)
    df['host_name'] = df['host'].apply(lambda x: x.get('host_name', None))
    df['host_id'] = df['host'].apply(lambda x: x.get('host_id', None))
    if 'review_scores' in df.columns:
        df['review_rating'] = df['review_scores'].apply(lambda x: x.get('review_scores_rating', None))
        df['review_accuracy'] = df['review_scores'].apply(lambda x: x.get('review_scores_accuracy', None))
        df['review_cleanliness'] = df['review_scores'].apply(lambda x: x.get('review_scores_cleanliness', None))

    # Convert dates
    df['last_review'] = pd.to_datetime(df['last_review'], errors='coerce')
    df['review_month'] = df['last_review'].dt.month

    return df

# Load data
df = load_data()

# Sidebar Navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", [
    "Home", "Map View", "Price Analysis", "Room Insights", "City Overview", "Availability Analysis", "Download & Raw Data"])

st.title("Airbnb Listings Dashboard")

if selection == "Home":
    st.markdown("""
    <h1>🏠 Airbnb Listings Dashboard</h1>

    Welcome to the **Airbnb Listings Dashboard** 📊

    Use the sidebar to explore:
    - Listings on map by price, room type, and city  
    - Price and room trends  
    - Availability patterns  
    - And more!

    <br>
    <span style='font-style: italic; color: grey;'>Note: All prices are assumed to be in USD. No currency standardization was applied due to missing currency code.</span>

    <br><br>

    **Created by Anvitha**  
    📧 anvithashetty06@gmail.com  
    🔗 [GitHub](https://github.com/Anvitha/Airbnb-Analysis) | [LinkedIn](https://www.linkedin.com/in/shettyanvitha/)
    """, unsafe_allow_html=True)

elif selection == "Map View":
    st.header("Listings on Map")
    city_filter = st.sidebar.multiselect("Select City", df['city'].dropna().unique(), default=df['city'].dropna().unique())
    price_filter = st.sidebar.slider("Price Range", int(df['price'].min()), int(df['price'].max()), (0, 1000))
    room_filter = st.sidebar.multiselect("Room Type", df['room_type'].unique(), default=df['room_type'].unique())

    filtered_df = df[(df['city'].isin(city_filter)) &
                     (df['price'] >= price_filter[0]) &
                     (df['price'] <= price_filter[1]) &
                     (df['room_type'].isin(room_filter))]

    if not filtered_df.empty:
        m = folium.Map(location=[filtered_df['latitude'].mean(), filtered_df['longitude'].mean()], zoom_start=11)
        for _, row in filtered_df.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=3,
                popup=f"${row['price']}, {row['room_type']}",
                color='green',
                fill=True,
                fill_opacity=0.6
            ).add_to(m)
        folium_static(m)
    else:
        st.warning("No listings match the selected filters.")

elif selection == "Price Analysis":
    st.header("Price Distribution (Under $1000)")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    sns.histplot(df[df['price'] < 1000]['price'], bins=40, kde=True, ax=ax1)
    ax1.set_xlabel("Price")
    ax1.set_ylabel("Listings Count")
    for p in ax1.patches:
        height = p.get_height()
        if height > 0:
            ax1.annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2., height), ha='center', va='bottom', color='grey')
    st.pyplot(fig1)

elif selection == "Room Insights":
    st.header("Listings by Room Type")
    room_counts = df['room_type'].value_counts()
    fig2, ax2 = plt.subplots()
    room_counts.plot(kind='bar', ax=ax2)
    for i, v in enumerate(room_counts):
        ax2.text(i, v + 2, str(v), ha='center', color='grey')
    st.pyplot(fig2)

    st.subheader("Average Price per Room Type")
    avg_price = df.groupby('room_type')['price'].mean()
    fig3, ax3 = plt.subplots()
    avg_price.plot(kind='bar', ax=ax3, color='skyblue')
    for i, v in enumerate(avg_price):
        ax3.text(i, v + 2, f"{v:.0f}", ha='center', color='grey')
    st.pyplot(fig3)

elif selection == "City Overview":
    st.header("Top 10 Cities with Most Listings")
    top_cities = df['city'].value_counts().nlargest(10)
    fig4, ax4 = plt.subplots()
    top_cities.plot(kind='bar', ax=ax4, color='coral')
    for i, v in enumerate(top_cities):
        ax4.text(i, v + 2, str(v), ha='center', color='grey')
    st.pyplot(fig4)

    st.subheader("Average Price by Top Cities")
    top_avg_price = df.groupby('city')['price'].mean().sort_values(ascending=False).head(10)
    fig5, ax5 = plt.subplots()
    top_avg_price.plot(kind='bar', ax=ax5, color='green')
    for i, v in enumerate(top_avg_price):
        ax5.text(i, v + 2, f"{v:.0f}", ha='center', color='grey')
    st.pyplot(fig5)

    st.subheader("Monthly Price Trend")
    monthly_avg = df.groupby('review_month')['price'].mean().dropna()
    fig6, ax6 = plt.subplots()
    monthly_avg.plot(kind='line', marker='o', ax=ax6)
    for i, (x, y) in enumerate(monthly_avg.items()):
        ax6.text(i, y + 2, f"{y:.0f}", ha='center', color='grey')
    st.pyplot(fig6)

elif selection == "Availability Analysis":
    st.header("Availability by Month")
    if 'availability' in df.columns and 'availability_365' in df['availability'].iloc[0]:
        df['availability_365'] = df['availability'].apply(lambda x: x.get('availability_365', None))
        monthly_avail = df.groupby('review_month')['availability_365'].mean().dropna()
        fig7, ax7 = plt.subplots()
        monthly_avail.plot(kind='line', marker='o', ax=ax7, color='purple')
        for i, (x, y) in enumerate(monthly_avail.items()):
            ax7.text(i, y + 2, f"{y:.0f}", ha='left', color='grey')
        st.pyplot(fig7)
    else:
        st.warning("Availability data not found in dataset.")

elif selection == "Download & Raw Data":
    st.header("Download Complete Dataset")
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    st.download_button(
        label="Download CSV",
        data=buffer,
        file_name="airbnb_data.csv",
        mime="text/csv"
    )

    if st.checkbox("Show Raw Data"):
        st.dataframe(df)
