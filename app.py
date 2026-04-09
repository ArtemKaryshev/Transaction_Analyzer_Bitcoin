'''Главный модуль запуска программы'''

import streamlit as st
from api import get_tx, get_address_txs
from analyzer import analyze
from visualizer import (
    show_addresses,
    show_results,
    show_tx_graph,
    show_recommendations,
    show_address_transactions,
)

st.set_page_config(
    page_title="Bitcoin Privacy Analyzer",
    page_icon="🔒",
    layout="centered",
)

# Инициализация session_state

if "txid_input" not in st.session_state:
    st.session_state["txid_input"] = ""
if "selected_addr" not in st.session_state:
    st.session_state["selected_addr"] = None
if "back_txid" not in st.session_state:
    st.session_state["back_txid"] = ""

if st.session_state["selected_addr"]:
    st.title("Bitcoin Privacy Analyzer")
    st.caption("Оценка конфиденциальности транзакций в сети Bitcoin")
    st.markdown("---")

    address = st.session_state["selected_addr"]
    with st.spinner(f"Загружаем транзакции для {address[:20]}…"):
        addr_data = get_address_txs(address)

    if addr_data is None:
        # Ошибка сети — показываем кнопку возврата
        if st.button("← Назад"):
            st.session_state["selected_addr"] = None
            st.rerun()
    else:
        show_address_transactions(address, addr_data)
    st.stop()


# Страница с вводом TXID и анализом транзакции

st.title("Bitcoin Privacy Analyzer")
st.caption("Оценка конфиденциальности транзакций в сети Bitcoin")


txid = st.text_input(
    "TXID транзакции (64 символа)",
    value=st.session_state["txid_input"],
    key="txid_input",
)

st.caption("Примеры для проверки:")
col_ex1, col_ex2 = st.columns(2)
with col_ex1:
    st.markdown("**Сатоши - Хэл Финни**")
    st.code("f4184fc596403b9d638783cf57adfe4c75c605f6356fbc91338530e9831e9e16")
with col_ex2:
    st.markdown("**CoinJoin транзакция**")
    st.code("eb5c93b28dc9a87ba22020593e1b008bfae6b5a0fcba9b4d1ed5b456b8129e9c")


_auto_run = (
    st.session_state["txid_input"] != ""
    and len(st.session_state["txid_input"].strip()) == 64
    and st.session_state.get("back_txid") == ""
)

if st.button("Анализировать", type="primary") or _auto_run:
    current_txid = st.session_state["txid_input"].strip()
    if not current_txid:
        st.warning("Введите TXID")
    elif len(current_txid) != 64:
        st.error("TXID должен содержать ровно 64 символа")
    else:
        st.session_state["selected_addr"] = None
        st.session_state["back_txid"] = ""

        with st.spinner("Запрашиваем blockchain.info…"):
            tx = get_tx(current_txid)

        if tx is not None:
            result = analyze(tx)

            show_results(result)
            st.markdown("---")

            show_recommendations(result)
            st.markdown("---")

            show_addresses(result)
            st.markdown("---")

            with st.expander("Граф транзакции", expanded=True):
                show_tx_graph(result, current_txid)

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
