import streamlit as st
import requests
import pandas as pd
import altair as alt
import urllib3
import locale

# Disable insecure request warnings (since we're skipping SSL verification)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set page configuration
st.set_page_config(page_title="WESO mining Leaderboard", layout="wide")

# Set locale based on user preference
# For example, you can change the locale based on the user's region.
locale.setlocale(locale.LC_ALL, '')  # Use the default locale (e.g., based on the system)

# --- MODIFIED: Layout for Title and Dropdown ---
col_title, col_select = st.columns([3, 1])  # Create columns (adjust ratio if needed)

with col_title:
    st.title("WESO mining Leaderboard")  # Title in the left column

with col_select:
    # Dropdown in the right column, with session state to persist the selection
    if 'miner_type' not in st.session_state:
        st.session_state.miner_type = "Tap to Earn"  # Default value if not set

    miner_type = st.selectbox(
        "Miner Type",
        ("Tap to Earn", "Proof of Work"),
        index=0 if st.session_state.miner_type == "Tap to Earn" else 1,  # Set the default index based on session state
        key="miner_type_selector"  # Unique key for the widget
    )

    # Save the selected dropdown value to session_state to persist across refreshes
    st.session_state.miner_type = miner_type

# --- NEW: Determine the URL based on the dropdown selection ---
if st.session_state.miner_type == "Tap to Earn":
    url = "https://weso-tap.lbunproject.tech/leaderboard?window=all_time&limit=100"
    st.caption("Displaying data for: Tap to Earn")  # Optional feedback
else:  # Proof of Work
    url = "https://weso-pow.lbunproject.tech/leaderboard?window=all_time&limit=100"
    st.caption("Displaying data for: Proof of Work")  # Optional feedback

# --- Fetch the data using the selected URL ---
try:
    response = requests.get(url, verify=False, timeout=15)  # Added timeout
    response.raise_for_status()  # Raises an error for bad status codes (4xx or 5xx)
    data = response.json()
# --- MODIFIED: More specific error handling ---
except requests.exceptions.Timeout:
    st.error(f"Error: Request to {url} timed out.")
    st.stop()
except requests.exceptions.HTTPError as e:
    st.error(f"HTTP Error fetching data from {url}: Status code {e.response.status_code}")
    st.text(f"Response: {e.response.text[:500]}...")  # Show part of the server response
    st.stop()
except requests.exceptions.RequestException as e:
    st.error(f"Error fetching data from {url}: {e}")
    st.stop()  # Stop execution if data fetching fails
except ValueError as e:  # Catches JSONDecodeError
    st.error(f"Error decoding JSON data from {url}: {e}")
    st.text("Received content (first 500 chars):")
    st.code(response.text[:500] if 'response' in locals() and hasattr(response, 'text') else "Could not get response text.", language=None)
    st.stop()


# --- DataFrame processing (with added safety checks) ---
# Create a DataFrame
try:
    df = pd.DataFrame(data)

    # Drop the 'nft_multiplier' column if it exists
    if 'nft_multiplier' in df.columns:
        df = df.drop(columns=['nft_multiplier'])

    # Compute crypto earned - check if columns exist first
    if 'crypto_paid' in df.columns and 'crypto_pending' in df.columns:
        df['crypto_earned'] = df['crypto_paid'] + df['crypto_pending']
    else:
        st.warning("Could not calculate 'crypto_earned': 'crypto_paid' or 'crypto_pending' column missing.")
        df['crypto_earned'] = 0  # Assign default value or handle as appropriate

    # Drop the msgs_received column if it exists
    if 'msgs_received' in df.columns:
        df = df.drop(columns=['msgs_received'])

    # Reorder columns - dynamically include existing columns
    base_columns_order = ['wallet_addr', 'blocks_won', 'crypto_earned', 'crypto_paid', 'crypto_pending', 'hashes_submitted']
    # Only keep columns that actually exist in the dataframe
    existing_columns_in_order = [col for col in base_columns_order if col in df.columns]
    # Add any other columns from the dataframe that weren't in the base list
    other_existing_columns = [col for col in df.columns if col not in existing_columns_in_order]
    final_column_order = existing_columns_in_order + other_existing_columns
    df = df[final_column_order]


    # Rename columns - only rename columns that exist
    rename_map = {
        'wallet_addr': 'Miner Wallet',
        'blocks_won': 'Blocks Won',
        'crypto_earned': 'WESO Earned',
        'crypto_paid': 'WESO Paid',
        'crypto_pending': 'WESO Pending',
        'hashes_submitted': 'Hashes Submitted'
    }
    columns_to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=columns_to_rename)

except Exception as e:
    st.error(f"Error processing DataFrame: {e}")
    st.write("Raw data received:", data)  # Show raw data if processing fails
    st.stop()


# --- Fetch block data based on miner type selection ---
block_url = ""
if st.session_state.miner_type == "Tap to Earn":
    block_url = "https://weso-tap.lbunproject.tech/blocks?limit=20"
else:  # Proof of Work
    block_url = "https://weso-pow.lbunproject.tech/blocks?limit=20"

# Fetch block data
try:
    block_response = requests.get(block_url, verify=False, timeout=15)  # Added timeout
    block_response.raise_for_status()  # Raises an error for bad status codes (4xx or 5xx)
    block_data = block_response.json()
except requests.exceptions.Timeout:
    st.error(f"Error: Request to {block_url} timed out.")
    st.stop()
except requests.exceptions.HTTPError as e:
    st.error(f"HTTP Error fetching data from {block_url}: Status code {e.response.status_code}")
    st.text(f"Response: {e.response.text[:500]}...")  # Show part of the server response
    st.stop()
except requests.exceptions.RequestException as e:
    st.error(f"Error fetching data from {block_url}: {e}")
    st.stop()  # Stop execution if data fetching fails
except ValueError as e:  # Catches JSONDecodeError
    st.error(f"Error decoding JSON data from {block_url}: {e}")
    st.text("Received content (first 500 chars):")
    st.code(block_response.text[:500] if 'block_response' in locals() and hasattr(block_response, 'text') else "Could not get response text.", language=None)
    st.stop()


# --- DataFrame processing for blocks ---
try:
    block_df = pd.DataFrame(block_data)

    # Drop the 'hashes_submitted' and 'exact' columns if they exist
    if 'hashes_submitted' in block_df.columns:
        block_df = block_df.drop(columns=['hashes_submitted'])
    if 'exact' in block_df.columns:
        block_df = block_df.drop(columns=['exact'])

    # Rename columns
    block_rename_map = {
        'block_number': 'Block Number',
        'winner_wallet_addr': 'Winner',
        'active_miners': 'Active Miners',
        'block_hash': 'Block Hash'
    }
    block_df = block_df.rename(columns=block_rename_map)

    # Reorder the columns
    block_columns_order = ['Block Number', 'Winner', 'Block Hash', 'Active Miners']
    block_df = block_df[block_columns_order]

except Exception as e:
    st.error(f"Error processing Block Data: {e}")
    st.write("Raw data received:", block_data)  # Show raw data if processing fails
    st.stop()

# --- Format numbers with thousands separator ---
def format_with_thousands_separator(value):
    # Only apply formatting if the value is numeric
    if isinstance(value, (int, float)):
        return locale.format_string("%d", value, grouping=True)
    return value  # Return the value as-is if it's not numeric

st.subheader("Community Totals")
# --- Define columns for the metrics ---
col_m1, col_m2, col_m3 = st.columns(3)  # Define the columns for displaying metrics

# Define metrics safely - check if columns exist
metrics_to_display = {
    'Blocks Won': ('Total Blocks Won', 0),
    'WESO Earned': ('Total WESO Earned', 0.0),
    'Hashes Submitted': ('Total Hashes Submitted', 0)
}
metric_columns = [col_m1, col_m2, col_m3]

i = 0
for col_name, (label, default_value) in metrics_to_display.items():
    if i < len(metric_columns):  # Ensure we don't run out of columns
        with metric_columns[i]:
            if col_name in df.columns:
                value = df[col_name].sum()
                # Apply thousands separator formatting for integers or floats
                value = format_with_thousands_separator(value)
                # Apply rounding for float values (like WESO Earned)
                if isinstance(value, (int, float)):
                    value = round(value, 6)
            else:
                value = default_value
                label = f"{label} (N/A)"  # Indicate if data is missing
            st.metric(label=label, value=value)
        i += 1



# --- Display Table (with added safety checks) ---
st.subheader("Leaderboard Stats")
st.dataframe(df, use_container_width=True)

# --- NEW: Display Block Data ---
st.subheader("Last 20 blocks")
st.dataframe(block_df, use_container_width=True)

# --- Create a copy of the DataFrame for charts ---
df_chart = df.copy()

# --- Chart Creation (with added safety checks) ---
# Add shortened wallet address safely
if 'Miner Wallet' in df_chart.columns:
    # Ensure the column is treated as string before slicing
    df_chart['short_wallet_addr'] = df_chart['Miner Wallet'].astype(str).apply(
        lambda x: x[:7] + "..." + x[-5:] if len(x) > 12 else x
    )
    # Define Y-axis once
    y_axis = alt.Y('short_wallet_addr:N', sort='-x', title='Wallet Address')
    charts_possible = True
else:
    st.warning("Cannot create charts by wallet: 'Miner Wallet' column is missing.")
    charts_possible = False


if charts_possible:
    # 1. Blocks Won per Wallet Address
    if 'Blocks Won' in df_chart.columns:
        st.subheader("Blocks Won per Wallet Address")
        blocks_chart = alt.Chart(df_chart).mark_bar(color='purple').encode(
            x=alt.X('Blocks Won:Q', title='Blocks Won'),
            y=y_axis
        ).properties(width=700, height=300)
        st.altair_chart(blocks_chart, use_container_width=True)
    else:
        st.info("Info: 'Blocks Won' data not available for charting.")

    # 2. Crypto Earned per Wallet Address
    if 'WESO Earned' in df_chart.columns:
        st.subheader("WESO Earned per Wallet Address")
        crypto_chart = alt.Chart(df_chart).mark_bar(color='purple').encode(
            x=alt.X('WESO Earned:Q', title='WESO Earned'),
            y=y_axis
        ).properties(width=700, height=300)
        st.altair_chart(crypto_chart, use_container_width=True)
    else:
         st.info("Info: 'WESO Earned' data not available for charting.")

    # 3. Hashes Submitted per Wallet Address
    if 'Hashes Submitted' in df_chart.columns:
        st.subheader("Hashes Submitted per Wallet Address")
        hashes_chart = alt.Chart(df_chart).mark_bar(color='purple').encode(
            x=alt.X('Hashes Submitted:Q', title='Hashes Submitted'),
            y=y_axis
        ).properties(width=700, height=300)
        st.altair_chart(hashes_chart, use_container_width=True)
    else:
         st.info("Info: 'Hashes Submitted' data not available for charting.")


# Add a footer or separator if desired
st.markdown("---")
st.caption(f"Data fetched at: {pd.Timestamp.now(tz='America/Chicago').strftime('%Y-%m-%d %H:%M:%S %Z')}")


