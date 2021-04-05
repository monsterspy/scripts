import streamlit as st
import numpy as np
import pandas as pd
import requests
import base64
from bs4 import BeautifulSoup

st.title('TradingView Analysis')

timeframe = st.selectbox("Choose TimeFrame: ", ['15', '25', '30', '60', '75', '120', '180', '240', '1D', '1W', '1M'], index=8)
pages = st.slider("Choose Pages: ", min_value=5,   max_value=50, value=5, step=1)

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="results.csv">Download csv file</a>'
    return href

def get_author_stats(url):
    session = requests.Session()
    session.max_redirects = 60
    req = session.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    
    stats = []
    for link in soup.find_all('span', attrs={'class' : 'tv-profile__social-item-value'}):
        stats.append(link.text)
        
#     stats_df = pd.DataFrame(stats)
#     stats_df.columns = ["REPUTATION", "IDEAS", "SCRIPTS", "LIKES", "FOLLOWERS"]
    return stats
    

url = "https://in.tradingview.com/markets/stocks-india/ideas/page-1/?sort=recent"
url = "https://in.tradingview.com/markets/stocks-india/ideas/?sort=recent"

res_data = []
# Add a placeholder
latest_iteration = st.empty()
bar = st.progress(0)
factor = 100//pages

for page in range(1, pages+1):
    data = []
    if page == 1:
        url = "https://in.tradingview.com/markets/stocks-india/ideas/?sort=recent"
    else:
        url = "https://in.tradingview.com/markets/stocks-india/ideas/page-"+str(page)+"/?sort=recent"
        
    
    session = requests.Session()
    session.max_redirects = 60
    req = session.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    
    for link in soup.find_all('div', attrs={'class' : 'tv-widget-idea__info-row'}):
        info = link.text.split("\n")
        ticker = info[1]
        
        if len(info) < 5:
            signal = "NA"
        else:
            signal = info[4]
        
        if signal == "Long":
            data.append([ticker, 1, 0])
        elif signal == "Short":
            data.append([ticker, 0, 1])
        else:
            data.append([ticker, 0, 0])
    
    idx = 0
    for link in soup.find_all('span', attrs={'class' : 'tv-widget-idea__timeframe'}):
        if link.text.strip() == ",":
            continue
        data[idx].append(link.text)
        idx = idx+1
    
    idx = 0
    for link in soup.find_all('span', attrs={'class' : 'tv-card-user-info__name'}):
        author_name = link.text
        a_url = "https://in.tradingview.com/u/"+author_name
        reputation = get_author_stats(a_url)[0]
        data[idx].append(reputation)
        idx = idx+1
    bar.progress(page*factor)
    res_data = res_data+data
    
df = pd.DataFrame(res_data)
df.columns = ['TICKER', 'BUY', 'SELL', "TF", "REPO"]

df = df[(df.REPO != "0") & (df.TF == timeframe) & ((df.BUY != 0) | (df.SELL != 0))].reset_index(drop=True)

sub = df.groupby(['TICKER']).size().sort_values(ascending=False).reset_index()
sub.columns = ["TICKER", "ANALYSIS_COUNT"]
df = df.merge(sub, on=['TICKER'], how="inner").reset_index(drop=True)

df["REPO"] = df["REPO"].astype(int)

df.sort_values(by=["ANALYSIS_COUNT", "TICKER", "REPO"], ascending=False, inplace=True)
df = df.reset_index(drop=True)

st.write("Results")
st.write(df)

st.markdown(get_table_download_link(df), unsafe_allow_html=True)
