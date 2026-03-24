import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Momentum & Valuation Dashboard", layout="wide")

st.title("📈 Momentum vs. Valuation Dashboard")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Settings")
source_option = st.sidebar.radio("Select Input Method:", ("Project CSVs", "Upload New CSV"))

DATA_FOLDER = "data"
selected_file = None

if source_option == "Project CSVs":
    if os.path.exists(DATA_FOLDER):
        files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]
        if files:
            selected_file_name = st.sidebar.selectbox("Choose a preset file:", files)
            selected_file = os.path.join(DATA_FOLDER, selected_file_name)
else:
    uploaded_file = st.sidebar.file_uploader("Upload your Symbol CSV", type="csv")
    if uploaded_file:
        selected_file = uploaded_file

# --- QUADRANT PLOTTING FUNCTION ---
def plot_quadrant_st(df):
    if df.empty: return
    plot_df = df[df['T_PE'] > 0].copy()
    if plot_df.empty: 
        st.warning("No stocks with valid T_PE found to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    pe_threshold = plot_df['T_PE'].median()
    momentum_threshold = 0

    # FIX: Set a fixed size (s=100) instead of using RVOL for bubble size
    ax.scatter(plot_df['T_PE'], plot_df['Score'], 
               s=100, alpha=0.7, 
               c='dodgerblue', edgecolors='black')

    for i, row in plot_df.iterrows():
        ax.annotate(row['Stock'], (row['T_PE'], row['Score']), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8, fontweight='bold')

    ax.axvline(x=pe_threshold, color='red', linestyle='--', alpha=0.3)
    ax.axhline(y=momentum_threshold, color='red', linestyle='--', alpha=0.3)

    # Quadrant Labels
    ax.text(pe_threshold*0.5, plot_df['Score'].max(), 'THE LEADER', color='green', fontweight='bold', ha='center')
    ax.text(pe_threshold*2.0, plot_df['Score'].max(), 'THE BUBBLE', color='orange', fontweight='bold', ha='center')
    ax.text(pe_threshold*0.5, plot_df['Score'].min(), 'TURNAROUND', color='blue', fontweight='bold', ha='center')
    ax.text(pe_threshold*2.0, plot_df['Score'].min(), 'VALUE TRAP', color='red', fontweight='bold', ha='center')

    ax.set_xscale('log')
    ax.set_xlabel('Trailing P/E Ratio (Log Scale)')
    ax.set_ylabel('Momentum Score')
    ax.grid(True, which="both", ls="-", alpha=0.1)
    st.pyplot(fig)

# --- DATA PROCESSING ENGINE ---
def generate_unified_dashboard(ticker_list):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=450)
    
    try:
        raw_data = yf.download(ticker_list, start=start_date, end=end_date, auto_adjust=False, progress=False)
        if raw_data.empty: return None
        
        prices_df = raw_data['Adj Close'] if len(ticker_list) > 1 else raw_data['Adj Close'].to_frame(name=ticker_list[0])
        volume_df = raw_data['Volume'] if len(ticker_list) > 1 else raw_data['Volume'].to_frame(name=ticker_list[0])
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return None

    intervals = {'1D': 2, '1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365}
    results = []

    progress_bar = st.progress(0)
    for idx, ticker in enumerate(ticker_list):
        if ticker in prices_df.columns:
            prices = prices_df[ticker].dropna()
            volumes = volume_df[ticker].dropna()
            if len(prices) < 22: continue

            curr_price = prices.iloc[-1]
            row = {'Stock': ticker.replace('.NS', '')}

            # Fundamentals logic
            try:
                t_obj = yf.Ticker(ticker)
                info = t_obj.info
                t_pe = info.get('trailingPE', 0)
                f_pe = info.get('forwardPE', 0)
                t_eps = info.get('trailingEps', 0)
                f_eps = info.get('forwardEps', 0)
                yf_peg = info.get('pegRatio', 0)

                row['T_PE'] = float(t_pe) if t_pe else 0
                row['F_PE'] = float(f_pe) if f_pe else 0
                row['T_EPS'] = float(t_eps)
                row['F_EPS'] = float(f_eps)

                growth = ((row['F_EPS'] / row['T_EPS']) - 1) * 100 if row['T_EPS'] > 0 and row['F_EPS'] > 0 else 0
                row['PEG'] = float(yf_peg) if yf_peg else (row['T_PE'] / growth if growth > 0 else 0)
                row['E_Growth (Forward < Trailing)'] = "YES" if (0 < row['F_PE'] < row['T_PE']) else "NO"
                
                time.sleep(0.05) # Minor delay for API
            except:
                row.update({'T_PE': 0, 'F_PE': 0, 'PEG': 0, 'T_EPS': 0, 'F_EPS': 0, 'E_Growth (Forward < Trailing)': "N/A"})

            row['RVOL'] = round(volumes.iloc[-1] / volumes.iloc[-21:-1].mean(), 2) if len(volumes) > 21 else 0
            
            all_rets = []
            for label, days in intervals.items():
                ref_date = end_date - timedelta(days=days)
                prev_price = prices.asof(ref_date)
                if label == '1D' and len(prices) >= 2: prev_price = prices.iloc[-2]
                
                ret = round(((curr_price / prev_price) - 1) * 100, 2) if pd.notna(prev_price) and prev_price != 0 else 0
                row[f'{label}%'] = ret
                all_rets.append(ret)
                
                # FIX: STAR LOGIC - compare against max of PREVIOUS closes in the period
                period_data = prices[prices.index >= ref_date]
                if len(period_data) > 1:
                    historical_max = period_data.iloc[:-1].max() # Exclude today
                    row[f'{label}BO'] = "★" if curr_price >= historical_max else "-"
                else:
                    row[f'{label}BO'] = "-"

            row['Score'] = round(sum(all_rets) / len(all_rets), 2)
            results.append(row)
            progress_bar.progress((idx + 1) / len(ticker_list))

    return pd.DataFrame(results).sort_values(by='Score', ascending=False)

# --- EXECUTION ---
if selected_file:
    input_df = pd.read_csv(selected_file)
    if st.button("🚀 Run Analysis"):
        symbols = [str(s).strip().upper() for s in input_df['Symbol'].dropna()]
        symbols = [s if s.endswith('.NS') else f"{s}.NS" for s in symbols]
        
        with st.spinner("Processing..."):
            res_df = generate_unified_dashboard(symbols)

        if res_df is not None:
            st.subheader("Momentum vs. Valuation Quadrant")
            plot_quadrant_st(res_df)

            st.subheader("🔥 High Conviction Picks")
            high_conv = res_df[(res_df['Score'] > 0) & (res_df['E_Growth (Forward < Trailing)'] == "YES") & (res_df['PEG'] > 0) & (res_df['PEG'] < 1.5)]
            st.dataframe(high_conv, use_container_width=True, hide_index=True)

            st.subheader("Full Dashboard")
            st.dataframe(res_df.style.background_gradient(subset=['Score', '1M%', '3M%'], cmap='RdYlGn'), use_container_width=True, hide_index=True)