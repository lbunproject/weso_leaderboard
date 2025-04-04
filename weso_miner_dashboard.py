import streamlit as st
import requests
import pandas as pd
import altair as alt
import urllib3

# Disable insecure request warnings (since we're skipping SSL verification)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set page configuration
st.set_page_config(page_title="WESO mining Leaderboard", layout="wide")

# Title
st.title("WESO mining Leaderboard")

# Define the data URL
url = "https://159.89.162.245:8185/leaderboard"

# Fetch the data from the API
try:
    response = requests.get(url, verify=False)
    response.raise_for_status()  # Raises an error for bad status codes
    data = response.json()
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# Create a DataFrame and drop the 'nft_multiplier' column if it exists
df = pd.DataFrame(data)
if 'nft_multiplier' in df.columns:
    df = df.drop(columns=['nft_multiplier'])

# Compute crypto earned as the sum of crypto_paid and crypto_pending
df['crypto_earned'] = df['crypto_paid'] + df['crypto_pending']

# Drop the msgs_received column if it exists
if 'msgs_received' in df.columns:
    df = df.drop(columns=['msgs_received'])

# Reorder columns
desired_columns = ['wallet_addr', 'blocks_won', 'crypto_earned', 'crypto_paid', 'crypto_pending', 'hashes_submitted']
df = df[desired_columns]

#Rename columns
df = df.rename(columns={'wallet_addr': 'Miner Wallet'})
df = df.rename(columns={'blocks_won': 'Blocks Won'})
df = df.rename(columns={'crypto_earned': 'WESO Earned'})
df = df.rename(columns={'crypto_paid': 'WESO Paid'})
df = df.rename(columns={'crypto_pending': 'WESO Pending'})
df = df.rename(columns={'hashes_submitted': 'Hashes Submitted'})

# Display the raw data (without the shortened wallet address)
st.subheader("Raw Leaderboard Data")
st.dataframe(df)

# Display key metrics
st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    total_blocks_won = df['Blocks Won'].sum()
    st.metric(label="Total Blocks Won", value=total_blocks_won)
with col2:
    total_crypto_earned = df['WESO Earned'].sum()
    st.metric(label="Total WESO Earned", value=round(total_crypto_earned, 6))
with col3:
    total_hashes_submitted = df['Hashes Submitted'].sum()
    st.metric(label="Total Hashes Submitted", value=total_hashes_submitted)

# Create a copy of the DataFrame for charts and add a shortened wallet address column.
df_chart = df.copy()
df_chart['short_wallet_addr'] = df_chart['Miner Wallet'].apply(
    lambda x: x[:7] + "..." + x[-5:] if len(x) > 12 else x
)

# Create horizontal bar charts using Altair

# 1. Blocks Won per Wallet Address
st.subheader("Blocks Won per Wallet Address")
blocks_chart = alt.Chart(df_chart).mark_bar(color='purple').encode(
    x=alt.X('Blocks Won:Q', title='Blocks Won'),
    y=alt.Y('short_wallet_addr:N', sort='-x', title='Wallet Address')
).properties(width=700, height=300)
st.altair_chart(blocks_chart, use_container_width=True)

# 2. Crypto Earned per Wallet Address
st.subheader("WESO Earned per Wallet Address")
crypto_chart = alt.Chart(df_chart).mark_bar(color='purple').encode(
    x=alt.X('WESO Earned:Q', title='WESO Earned'),
    y=alt.Y('short_wallet_addr:N', sort='-x', title='Wallet Address')
).properties(width=700, height=300)
st.altair_chart(crypto_chart, use_container_width=True)

# 3. Hashes Submitted per Wallet Address
st.subheader("Hashes Submitted per Wallet Address")
hashes_chart = alt.Chart(df_chart).mark_bar(color='purple').encode(
    x=alt.X('Hashes Submitted:Q', title='Hashes Submitted'),
    y=alt.Y('short_wallet_addr:N', sort='-x', title='Wallet Address')
).properties(width=700, height=300)
st.altair_chart(hashes_chart, use_container_width=True)
