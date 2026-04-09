'''Модуль получения данных'''

import requests
import streamlit as st

@st.cache_data(ttl=300)
def get_tx(txid: str):
    try:
        url = f"https://blockchain.info/rawtx/{txid}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка при запросе с blockchain.info: {e}")
        return None

@st.cache_data(ttl=300)
def get_address_txs(address: str):
    try:
        url = f"https://blockchain.info/rawaddr/{address}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка при запросе адреса {address}: {e}")
        return None
