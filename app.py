'''Главный модуль запуска программы'''

import streamlit as st
from api import get_tx
from analyzer import analyze
from visualizer import show_addresses, show_results, show_tx_graph

st.set_page_config(
    page_title="Bitcoin Privacy Analyzer",
    page_icon="🔒",
    layout="centered",
)

st.title("Bitcoin Privacy Analyzer")
st.caption("Оценка конфиденциальности транзакций в сети Bitcoin")


txid = st.text_input("TXID транзакции (64 символа)")

st.caption("Примеры для проверки:")
col_ex1, col_ex2 = st.columns(2)
with col_ex1:
    st.markdown("**Сатоши - Хэл Финни**")
    st.code("f4184fc596403b9d638783cf57adfe4c75c605f6356fbc91338530e9831e9e16")
with col_ex2:
    st.markdown("**CoinJoin транзакция**")
    st.code("eb5c93b28dc9a87ba22020593e1b008bfae6b5a0fcba9b4d1ed5b456b8129e9c")


if st.button("Анализировать", type="primary"):
    if not txid:
        st.warning("Введите TXID")
    elif len(txid.strip()) != 64:
        st.error("TXID должен содержать ровно 64 символа")
    else:
        with st.spinner("Запрашиваем blockchain.info…"):
            tx = get_tx(txid.strip())

        if tx is not None:
            result = analyze(tx)

            show_results(result)
            st.markdown("---")

            show_addresses(result)
            st.markdown("---")

            with st.expander("Граф транзакции", expanded=True):
                show_tx_graph(result, txid.strip())

            with st.expander("Пояснения метрик"):
                st.markdown(f"""
| Метрика | Значение | Пояснение |
|---|---|---|
| **CIO риск** | `{result.cio}` | Вероятность кластеризации входных адресов |
| **Change Detection** | `{result.change}` | Вероятность определения адреса сдачи |
| **Round Number** | `{result.round_risk}` | Доля круглых выходов (выдают платёж) |
| **CoinJoin** | `{result.coinjoin}` | Вероятность что TX является CoinJoin |
| **Anonymity Set** | `{result.anon_set}` | Число равных выходов (участников CJ) |
| **Entropy** | `{result.entropy}` | Однородность выходов (1 = все равны) |
                """)
