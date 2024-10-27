import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def fetch_art_auction_data(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to fetch data. Status code: {response.status_code}")
            return pd.DataFrame()

        soup = BeautifulSoup(response.text, 'html.parser')
        art_data = []
        for item in soup.find_all('div', class_='art-item'):
            artist = item.find('span', class_='artist-name').get_text(strip=True) if item.find('span', class_='artist-name') else 'Unknown Artist'
            title = item.find('span', class_='art-title').get_text(strip=True) if item.find('span', class_='art-title') else 'Untitled'
            image_url = item.find('img')['src'] if item.find('img') else ''
            art_data.append({'Artist': artist, 'Title': title, 'Image URL': image_url})

        if not art_data:
            st.warning("No art items found. Please check the website structure.")
            return pd.DataFrame()

        return pd.DataFrame(art_data)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return pd.DataFrame()

def download_images(data, output_folder='images'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for idx, row in data.iterrows():
        image_url = row['Image URL']
        if not image_url:
            continue
        
        image_path = os.path.join(output_folder, f"{row['Artist'].replace('/', '_')}_{row['Title'].replace('/', '_')}.jpg")
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(image_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
            else:
                st.warning(f"Failed to download image from {image_url}. Status code: {response.status_code}")
        except Exception as e:
            st.warning(f"Failed to download image {image_url}: {e}")

st.title("Art Auction Data Scraper")

if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame()

auction_url = st.text_input("Enter the auction website URL:")

if st.button("Fetch Data"):
    if auction_url:
        with st.spinner("Fetching data..."):
            data = fetch_art_auction_data(auction_url)
            if not data.empty:
                st.session_state['data'] = data
                st.success("Data fetched successfully!")
            else:
                st.warning("No data found. Please check the URL or the website's structure.")
    else:
        st.error("Please enter a valid URL.")

if not st.session_state['data'].empty:
    st.dataframe(st.session_state['data'])

    if st.button("Download Images"):
        with st.spinner("Downloading images..."):
            download_images(st.session_state['data'])
            st.success("Images downloaded successfully!")

    if st.button("Export to CSV"):
        csv_file = 'art_auction_data.csv'
        st.session_state['data'].to_csv(csv_file, index=False)
        st.success(f"Data exported to {csv_file}")
        st.download_button(label="Download CSV", data=open(csv_file, "rb").read(), file_name=csv_file)
else:
    st.write("No data available. Please fetch the data first.")
