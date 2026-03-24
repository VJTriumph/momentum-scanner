# my-momentum-scanner

📈 Momentum \& Valuation Quant Dashboard



A robust, data-driven dashboard built with Streamlit and Python to identify high-probability trading setups in the Indian Equity Market (NSE). 



This tool balances price momentum with fundamental valuation metrics to categorize stocks into actionable quadrants.



🚀 Key Features



Multi-Timeframe Momentum Scoring: Aggregates performance from 1-day to 1-year intervals into a single, weighted Score.



Breakout Detection (★): Automatically identifies "Breakout Stars" where the current price has surpassed the historical maximum of a given period (excluding current candles).



Valuation Quadrant Analysis: Visualizes stocks on a Log-Scale 



Scatter Plot:The Leader: Strong momentum + Fair valuation.



The Bubble: Strong momentum + Overextended valuation.



Turnaround: Improving price action from low valuation levels.



Value Trap: Declining price action despite low valuation.



High Conviction Engine: Filters for GARP (Growth at a Reasonable Price) setups using Forward Earnings Growth and PEG ratios.



RVOL Analysis: Tracks Relative Volume against the 20-day moving average to confirm breakout strength.



🛠️ Installation \& Setup



Clone the Repository:Bash

git clone https://github.com/mikado-1/my-momentum-scanner.git

cd momentum-scanner



Install Dependencies:Bash

pip install streamlit yfinance pandas matplotlib



Data Preparation:



Create a folder named data/ in the project root.



Add .csv files containing a Symbol column (e.g., RELIANCE, TCS, INFY).



Launch the Dashboard:Bash



streamlit run app.py



📊 Technical Logic Reference



1\. Momentum ScoreThe Score is a simple average of percentage returns across six intervals: 1D, 1W, 1M, 3M, 6M, and 1Y.



Positive Score: Indicates an overall uptrend.



Negative Score: Indicates an overall downtrend or heavy correction.



2\. The "Breakout Star" (★)A star is triggered only if:$$Current Price \\geq Max(Previous Prices in Interval)$$By using .iloc\[:-1].max(), the script ensures it is comparing today's price against a true historical ceiling, preventing false positives.



3\. Valuation FilteringE\_Growth: "YES" if Forward P/E is lower than Trailing P/E, suggesting expected earnings improvement.



PEG Ratio: High Conviction picks require $0 < PEG < 1.5$ to ensure you aren't overpaying for growth.



📂 Project StructurePlaintext

├── app.py              # Main Application Script

├── data/               # Local directory for watchlists (CSV)

└── requirements.txt    # List of required Python packages



📝 Requirements



Python 3.10



Active Internet Connection (for Yahoo Finance API)

