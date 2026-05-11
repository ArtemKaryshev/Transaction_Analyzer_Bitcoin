'''Модуль расчетов'''

import math
from collections import Counter
from dataclasses import dataclass, field

@dataclass
class AnalysisResult:
    num_inputs: int
    num_outputs: int
    unique_inputs: int
    total_in_btc: float
    total_out_btc: float
    fee_btc: float
    size_bytes: int
    cio: float
    change: float
    round_risk: float
    coinjoin: float
    anon_set: int
    entropy: float
    score: int

    in_addrs: list = field(default_factory=list)
    out_addrs: list = field(default_factory=list)
    input_addr_set: set = field(default_factory=set)
    change_output: dict | None = None
    change_method: str | None = None

def analyze(tx: dict):
    inputs = tx.get("inputs", [])
    outputs = tx.get("out", [])
    input_addrs: list[str] = []
    total_in = 0
    for inp in inputs:
        prev = inp.get("prev_out", {})
        addr = prev.get("addr", "")
        val = prev.get("value", 0)
        total_in += val
        if addr:
            input_addrs.append(addr)

    output_values = [out.get("value", 0) for out in outputs]
    total_out = sum(output_values)
    num_inputs = len(inputs)
    num_outputs = len(outputs)
    unique_input_addrs = len(set(input_addrs))
    fee = (total_in - total_out) / 100000000
    input_addr_set = set(input_addrs)

# CIO
    if num_inputs <= 1:
        cio_risk = 0
    elif unique_input_addrs == 1:
        cio_risk = 0.3
    else:
        uniq_percent = unique_input_addrs / num_inputs
        scale = math.log2(unique_input_addrs + 1) / math.log2(10)
        cio_risk = round(min(uniq_percent * scale * 1.5, 1), 3)
    if num_outputs == 1 and num_inputs >= 3:
        cio_risk = max(cio_risk, 0.5)

# Round number
    round_outputs = sum(1 for v in output_values if v > 0 and v % 100000 == 0)
    round_risk = round(round_outputs / max(num_outputs, 1), 3)
    round_risk = 1 if round_risk == 1.0 else round_risk

# Change Detection
    same_addr = sum(1 for out in outputs if out.get("addr", "") in input_addr_set)
    if num_outputs == 1:
        change_risk = 0
    elif same_addr == 1:
        change_risk = 1
    elif same_addr > 1:
        change_risk = 0.50
    elif num_inputs == 1 and num_outputs == 2 and same_addr == 0:
        change_risk = 0.20
    elif num_inputs >= 2 and num_outputs == 2 and same_addr == 0:
        change_risk = 0.80 if round_outputs == 1 else 0.50
    elif num_outputs == 2 and round_outputs == 1:
        change_risk = 0.75
    elif num_outputs == 2:
        change_risk = 0.40
    else:
        change_risk = round(min(0.3 + (round_outputs / num_outputs) * 0.3, 1), 3)

# CoinJoin
    counter = Counter(output_values)
    max_same_outputs = max(counter.values()) if counter else 1
    coinjoin_prob = 0
    if max_same_outputs >= 2:
        coinjoin_prob += 0.40 * min(max_same_outputs / num_outputs, 1)
    if num_inputs >= 3:
        coinjoin_prob += 0.20
    if unique_input_addrs > 1:
        coinjoin_prob += 0.15
    if num_outputs >= 4:
        coinjoin_prob += 0.10
    if max_same_outputs > 3 and num_inputs > 3 and unique_input_addrs > 1:
        coinjoin_prob = 1
    coinjoin_prob = round(min(coinjoin_prob, 1), 3)

    anon_set = max_same_outputs

# Энтропия
    entropy = 0
    if len(output_values) > 1:
        total = sum(output_values)
        probs = [v / total for v in output_values if v > 0]
        raw_entropy = -sum(p * math.log2(p) for p in probs)
        entropy = round(raw_entropy / math.log2(len(output_values)), 3)

# Оценка конфиденциальности
    score = 30
    score += coinjoin_prob * 45
    score += entropy * 15
    score += min(math.log2(max(anon_set, 1)) * 8, 20)
    score -= change_risk * 20
    if coinjoin_prob >= 0.5:
        score -= cio_risk * 5
        score -= round_risk * 3
    else:
        score -= cio_risk * 20
        score -= round_risk * 12
    score = max(0, min(100, int(score)))

    in_addrs_list = [
        {
            "addr": inp.get("prev_out", {}).get("addr", "неизвестен"),
            "btc": round(inp.get("prev_out", {}).get("value", 0) / 100000000, 8),
        }
        for inp in inputs
    ]
    out_addrs_list = [
        {
            "addr": out.get("addr", "неизвестен"),
            "btc": round(out.get("value", 0) / 100000000, 8),
        }
        for out in outputs
    ]

    change_output = None
    change_method = None
    for out in out_addrs_list:
        if out["addr"] in input_addr_set:
            change_output = out
            change_method = "address_reuse"
            break
    if change_output is None and num_outputs == 2 and round_outputs == 1:
        for out in out_addrs_list:
            if int(round(out["btc"] * 100000000)) % 100_000 != 0:
                change_output = out
                change_method = "round_number"
                break

    return AnalysisResult(
        num_inputs=num_inputs,
        num_outputs=num_outputs,
        unique_inputs=unique_input_addrs,
        total_in_btc=round(total_in / 100000000, 8),
        total_out_btc=round(total_out / 100000000, 8),
        fee_btc=round(fee, 8),
        size_bytes=tx.get("size", 0),
        cio=cio_risk,
        change=change_risk,
        round_risk=round_risk,
        coinjoin=coinjoin_prob,
        anon_set=anon_set,
        entropy=entropy,
        score=score,
        in_addrs=in_addrs_list,
        out_addrs=out_addrs_list,
        input_addr_set=input_addr_set,
        change_output=change_output,
        change_method=change_method,
    )