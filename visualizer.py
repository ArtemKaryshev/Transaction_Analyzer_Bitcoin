'''Модуль отрисовки интерфейса и диаграмм'''

import io
import textwrap
import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st
import networkx as nx

matplotlib.use("Agg")


def _score_color(score: int):
    if score >= 70:
        return "#00c853"
    elif score >= 40:
        return "#ff9800"
    return "#f44336"


def _short_addr(addr: str, n: int = 12):
    if len(addr) <= n * 2 + 3:
        return addr
    return f"{addr[:n]}…{addr[-6:]}"


def show_results(r):
    st.markdown(
        f"""<div style="background:#f0f7ff;border-left:4px solid #2196f3;
        border-radius:8px;padding:14px 20px;margin-bottom:16px">
        <span style="font-size:0.85rem;color:#666">Сумма транзакции</span><br>
        <span style="font-size:1.9rem;font-weight:700;color:#1565c0">{r.total_out_btc} BTC</span>
        &nbsp;&nbsp;<span style="font-size:1rem;color:#888">
        вход: {r.total_in_btc} BTC &nbsp;·&nbsp; комиссия: {r.fee_btc} BTC
        </span></div>""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Privacy Score", f"{r.score} / 100")
    c2.metric("Входов / Выходов", f"{r.num_inputs} / {r.num_outputs}")
    c3.metric("Anonymity Set", r.anon_set)
    c4.metric("Размер TX", f"{r.size_bytes} байт")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=r.score,
            title={"text": "Privacy Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": _score_color(r.score)},
                "steps": [
                    {"range": [0, 40], "color": "#ffebee"},
                    {"range": [40, 70], "color": "#fff8e1"},
                    {"range": [70, 100], "color": "#e8f5e9"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    labels = ["CIO риск", "Change Detection", "Round Number", "Вероятность CoinJoin"]
    values = [r.cio, r.change, r.round_risk, r.coinjoin]
    fig2 = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=["#f44336", "#ff9800", "#ffc107", "#4caf50"],
            text=[str(round(v, 2)) for v in values],
            textposition="outside",
        )
    )
    fig2.update_layout(
        yaxis=dict(range=[0, 1.2], title="Значение (0 = безопасно, 1 = уязвимо)"),
        height=280,
        margin=dict(l=20, r=20, t=10, b=20),
    )
    st.plotly_chart(fig2, use_container_width=True)


def show_addresses(r):
    """
    Адреса транзакции. Каждая кнопка сохраняет адрес в session_state
    и вызывает rerun() — роутинг происходит в app.py.
    """
    st.markdown("#### Адреса транзакции")
    st.caption("Нажмите на адрес, чтобы просмотреть его историю транзакций")

    list_in_addr = [a["addr"] for a in r.in_addrs]
    btc_back_info = None

    col_in, col_out = st.columns(2)

    with col_in:
        st.markdown("**Входы (источники UTXO)**")
        for i, a in enumerate(r.in_addrs):
            addr = a["addr"]
            st.markdown(
                f"""<div style="background:#fff8e1;border-left:3px solid #ff9800;
                border-radius:6px;padding:6px 12px;margin-bottom:2px;font-size:0.82rem">
                <span style="color:#888">#{i+1}</span>&nbsp;
                <span style="color:#555">↳ {a["btc"]} BTC</span>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(
                f"{addr[:18]}…{addr[-6:]}",
                key=f"in_addr_{i}_{addr}",
                help=f"Полный адрес: {addr}",
                use_container_width=True,
            ):
                # Сохраняем текущий txid для возврата назад
                st.session_state["back_txid"] = st.session_state.get("txid_input", "")
                st.session_state["selected_addr"] = addr
                st.rerun()

    with col_out:
        st.markdown("**Выходы (новые UTXO)**")
        for i, b in enumerate(r.out_addrs):
            addr = b["addr"]
            is_change = addr in list_in_addr
            bg = "#fce4ec" if is_change else "#e8f5e9"
            border = "#e91e63" if is_change else "#4caf50"
            badge_text = "Сдача" if is_change else ""
            if is_change:
                btc_back_info = b

            st.markdown(
                f"""<div style="background:{bg};border-left:3px solid {border};
                border-radius:6px;padding:6px 12px;margin-bottom:2px;font-size:0.82rem">
                <span style="color:#888">#{i+1}</span>
                <span style="color:#c62828;font-size:0.75rem">{badge_text}</span>&nbsp;
                <span style="color:#555">↳ {b["btc"]} BTC</span>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(
                f"{addr[:18]}…{addr[-6:]}",
                key=f"out_addr_{i}_{addr}",
                help=f"Полный адрес: {addr}",
                use_container_width=True,
            ):
                st.session_state["back_txid"] = st.session_state.get("txid_input", "")
                st.session_state["selected_addr"] = addr
                st.rerun()

    if btc_back_info:
        co = btc_back_info
        st.markdown(
            f"""<div style="background:#fce4ec;border-left:4px solid #e91e63;
            border-radius:8px;padding:12px 16px;margin-top:8px">
            <b>Предполагаемая сдача</b><br>
            <span style="font-size:1.1rem;font-weight:700;color:#c62828">{co["btc"]} BTC</span>
            &nbsp;→&nbsp;<code style="font-size:0.8rem">{co["addr"]}</code>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.info("Сдача не определена однозначно")


def show_address_transactions(address: str, addr_data: dict):
    """
    Страница истории транзакций адреса.
    addr_data — ответ blockchain.info/rawaddr/{address}.
    Кнопка «Назад» и TXID-кнопки управляют session_state в app.py.
    """
    # Кнопка Назад
    back_txid = st.session_state.get("back_txid", "")
    back_label = f"Назад к транзакции {back_txid[:16]}…" if back_txid else "Назад"
    if st.button(back_label, key="btn_back_to_tx"):
        st.session_state["selected_addr"] = None
        # txid_input уже содержит нужное значение — просто rerun
        st.rerun()

    # Заголовок панели адреса
    st.markdown(
        f"""<div style="background:#f3e5f5;border-left:4px solid #9c27b0;
        border-radius:8px;padding:14px 20px;margin-bottom:12px">
        <span style="font-size:0.8rem;color:#888">Адрес</span><br>
        <code style="font-size:0.85rem;color:#6a1b9a;word-break:break-all">{address}</code>
        </div>""",
        unsafe_allow_html=True,
    )

    # Сводная статистика
    n_tx = addr_data.get("n_tx", 0)
    total_received = addr_data.get("total_received", 0) / 1e8
    total_sent = addr_data.get("total_sent", 0) / 1e8
    final_balance = addr_data.get("final_balance", 0) / 1e8
    txs = addr_data.get("txs", [])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего транзакций", n_tx)
    c2.metric("Получено BTC", f"{total_received:.6f}")
    c3.metric("Отправлено BTC", f"{total_sent:.6f}")
    c4.metric("Баланс BTC", f"{final_balance:.6f}")

    st.markdown(f"#### Последние транзакции адреса ({len(txs)} из {n_tx})")

    if not txs:
        st.info("Транзакции не найдены.")
        return

    # Список транзакций
    for tx in txs:
        is_sender = False
        for inp in tx.get("inputs", []):
            prev_out = inp.get("prev_out")
            if prev_out and prev_out.get("addr") == address:
                is_sender = True
                break

        is_receiver = False
        for out_item in tx.get("out", []):
            if out_item.get("addr") == address:
                is_receiver = True
                break

        txid = tx.get("hash", "")
        block_height = tx.get("block_height")
        block_label = f"Блок {block_height}" if block_height else "Не подтверждена"
        total_out_btc = sum(o.get("value", 0) for o in tx.get("out", [])) / 1e8
        num_inputs = len(tx.get("inputs", []))
        num_outputs = len(tx.get("out", []))

        if is_sender:
            bg_color = "#feffbe"
            role_text = "Отправка"
        elif is_receiver:
            bg_color = "#e0ffb5"
            role_text = "Получение"


        st.markdown(
            f"""<div style="background:{bg_color};border:1px solid #e0e0e0;
            border-radius:8px;padding:10px 14px;margin-bottom:4px">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;flex-wrap:wrap">
              <span style="font-size:0.78rem;color:#888">{block_label} · {role_text}</span>
              <span style="font-size:0.82rem;color:#333;font-weight:600">
                {total_out_btc:.6f} BTC
              </span>
            </div>
            <div style="font-size:0.75rem;color:#aaa;margin-top:2px">
              Входов: {num_inputs} &nbsp;·&nbsp; Выходов: {num_outputs}
            </div>
            </div>""",
            unsafe_allow_html=True,
        )

        short_txid = f"{txid[:20]}…{txid[-8:]}"
        if st.button(
            f"Анализировать: {short_txid}",
            key=f"txid_btn_{txid}",
            help=f"TXID: {txid}",
            use_container_width=True,
        ):
            st.session_state["txid_input"] = txid
            st.session_state["selected_addr"] = None
            st.session_state["back_txid"] = ""
            st.rerun()
    

def show_tx_graph(r, txid: str):
    G = nx.DiGraph()
    tx_node = "TX\n" + txid[:8] + "…"
    G.add_node(tx_node, color="#90a4ae", shape="s")

    change_addr = r.change_output["addr"] if r.change_output else None

    in_nodes = []
    for a in r.in_addrs:
        lbl = _short_addr(a["addr"])
        G.add_node(lbl, color="#ffb74d", shape="o")
        G.add_edge(lbl, tx_node, weight=a["btc"])
        in_nodes.append(lbl)

    out_nodes = []
    for b in r.out_addrs:
        lbl = _short_addr(b["addr"])
        color = "#ef9a9a" if b["addr"] == change_addr else "#81c784"
        G.add_node(lbl, color=color, shape="o")
        G.add_edge(tx_node, lbl, weight=b["btc"])
        out_nodes.append(lbl)

    pos = {}
    n_in = len(in_nodes)
    for i, node in enumerate(in_nodes):
        pos[node] = (-2, (i - (n_in - 1) / 2) * 1.2)
    pos[tx_node] = (0, 0)
    unique_out_nodes = [n for n in out_nodes if n not in pos]
    n_unique_out = len(unique_out_nodes)
    for i, node in enumerate(unique_out_nodes):
        pos[node] = (2, (i - (n_unique_out - 1) / 2) * 1.2)

    node_colors = [G.nodes[n].get("color", "#90a4ae") for n in G.nodes]
    edge_labels = {
        (u, v): f"{d['weight']:.4f} BTC" for u, v, d in G.edges(data=True)
    }

    fig, ax = plt.subplots(figsize=(14, max(4, max(n_in, n_unique_out) * 1.4)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=1800, alpha=0.95)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#cfd8dc",
                           arrows=True, arrowsize=20, width=1.5,
                           connectionstyle="arc3,rad=0.05")

    labels_wrapped = {n: "\n".join(textwrap.wrap(n, 14)) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=labels_wrapped, ax=ax,
                            font_size=6.5, font_color="white", font_weight="bold")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                 font_size=6.5, font_color="#eceff1",
                                 bbox=dict(alpha=0))

    legend_items = [
        mpatches.Patch(color="#ffb74d", label="Вход UTXO"),
        mpatches.Patch(color="#81c784", label="Выход UTXO"),
        mpatches.Patch(color="#ef9a9a", label="Возможная сдача"),
        mpatches.Patch(color="#90a4ae", label="Транзакция"),
    ]
    ax.legend(handles=legend_items, loc="upper left",
              facecolor="#1a1a2e", labelcolor="white", fontsize=8)
    ax.axis("off")
    ax.set_title(f"Граф транзакции {txid[:16]}",
                 color="white", fontsize=11, pad=10)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, caption="Граф транзакции", use_container_width=True)


def get_recommendations(r):
    tips = []

    if r.change == 0.99:
        tips.append(
            "❗Address Reuse: адрес сдачи совпадает с входным. "
            "Используйте новый адрес для каждой транзакции."
        )
    if r.change >= 0.75 and r.round_risk > 0:
        tips.append(
            "❗Round Number: сумма платежа круглая - сдача легко вычисляется. "
            "Разбейте платёж на несколько транзакций с некруглыми суммами."
        )
    if r.cio >= 0.5:
        tips.append(
            "❗CIO: несколько входных адресов из одного кошелька раскрывают "
            "ваш баланс. Используйте CoinJoin перед консолидацией UTXO."
        )
    if r.coinjoin < 0.3 and r.anon_set == 1:
        tips.append(
            "❗Anonymity Set = 1: получатель определяется однозначно. "
            "Используйте CoinJoin (Wasabi Wallet, JoinMarket) - это повысит "
            "Anonymity Set и скроет реального получателя."
        )
    if r.entropy < 0.5 and r.num_outputs >= 2:
        tips.append(
            "❗Низкая энтропия выходов: суммы сильно различаются, "
            "платёж очевиден. Рассмотрите Lightning Network для небольших платежей."
        )
    if not tips or r.score >= 80:
        tips = ["✅Транзакция не содержит явных признаков деанонимизации."]
    return tips


def show_recommendations(r):
    tips = get_recommendations(r)
    st.markdown("Рекомендации по повышению конфиденциальности")
    for tip in tips:
        st.warning(tip) if tip.startswith("❗") else st.info(tip)