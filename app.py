"""
Touché Royale — Upstream Cost & Compliance Decision Model (Streamlit)

A decision-support tool, NOT a forecast. It models cost structure, not sales,
and contains no revenue or profit projection. Every figure is one of three types:
  • Verified     — sourced rate / rule (5% duty, 5% VAT, CEPA 0%, Montaji fee)
  • Founder input — the base, finishing and fixed costs the founder enters
  • Derived      — calculated live from the two above
"""

import math
import pandas as pd
import altair as alt
import streamlit as st

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Touché Royale — Cost & Compliance Model",
    page_icon="💎",
    layout="wide",
)

VAT = 0.05

CONFIGS = [
    ("ddp", "DDP · India Export", "Fits: entry"),
    ("hyb", "Hybrid", "Fits: the bridge"),
    ("loc", "UAE Local Filling", "Fits: scale"),
]
COST_ROWS = [
    ("base",    "Base cost (juice, bottle, gem, metal)"),
    ("freight", "Inbound freight  (benchmark)"),
    ("finish",  "UAE finishing / filling"),
    ("tpl",     "3PL / fulfilment  (benchmark)"),
    ("fixed",   "Fixed cost / month (setup, overhead)"),
]

DEFAULTS = {
    "volume": 300.0,
    "cepa": "Standard 5% (HS 3303)",
    "base_ddp": 120.0, "base_hyb": 95.0,  "base_loc": 95.0,
    "freight_ddp": 18.0, "freight_hyb": 9.0, "freight_loc": 6.0,
    "finish_ddp": 0.0,  "finish_hyb": 22.0, "finish_loc": 16.0,
    "tpl_ddp": 9.0,     "tpl_hyb": 8.0,     "tpl_loc": 7.0,
    "fixed_ddp": 3000.0, "fixed_hyb": 9000.0, "fixed_loc": 22000.0,
}

COMPLIANCE = [
    ("ECAS Certificate of Conformity", "MoIAT · annual", 0.0, "2–4 wk"),
    ("Montaji product registration",   "Dubai Municipality · 5-yr", 275.0, "1–4 wk"),
    ("IFRA certificate",               "Supplier / lab", 0.0, "varies"),
    ("Heavy-metal leaching test",      "GSO 1943 · lab", 0.0, "1–3 wk"),
    ("CITES permit (if natural oud)",  "MoEFCC / MOCCAE", 0.0, "conditional"),
    ("Bilingual label artwork",        "One-off", 0.0, "1 wk"),
]

READINESS = [
    ("Sourcing (oud, gems, metals)", "Process fix"),
    ("Production / manual insertion", "Capex to close"),
    ("Packaging & labelling", "Process fix"),
    ("Quality control & authenticity", "Process fix"),
    ("Hazmat + secure warehousing", "Capex to close"),
    ("Regulatory registration", "Process fix"),
    ("Inbound logistics (DG, CEPA)", "Process fix"),
    ("Scalability", "Capex to close"),
]

# --------------------------------------------------------------------------
# State init
# --------------------------------------------------------------------------
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
for i, item in enumerate(COMPLIANCE):
    st.session_state.setdefault(f"comp_{i}", item[2])
st.session_state.setdefault("scenario_note", "Base case loaded.")

# --------------------------------------------------------------------------
# Model (pure functions)
# --------------------------------------------------------------------------
def duty_rate(cepa_label: str) -> float:
    return 0.0 if cepa_label.startswith("CEPA") else 0.05

def variable_pu(p: dict, cfg: str, duty: float) -> float:
    cif = p[f"base_{cfg}"] + p[f"freight_{cfg}"]
    d = cif * duty
    vat = (cif + d) * VAT
    return cif + d + vat + p[f"finish_{cfg}"] + p[f"tpl_{cfg}"]

def landed_pu(p: dict, cfg: str, vol: float, duty: float) -> float:
    vol = max(1.0, vol)
    return variable_pu(p, cfg, duty) + p[f"fixed_{cfg}"] / vol

def crossover(p: dict, a: str, b: str, duty: float):
    va, vb = variable_pu(p, a, duty), variable_pu(p, b, duty)
    denom = va - vb
    if abs(denom) < 1e-9:
        return None
    v = (p[f"fixed_{b}"] - p[f"fixed_{a}"]) / denom
    if v > 0 and math.isfinite(v):
        return int(round(v))
    return None

def read_params() -> dict:
    keys = ["volume"] + [f"{rk}_{ck}" for rk, _ in COST_ROWS for ck, _, _ in CONFIGS]
    return {k: float(st.session_state[k]) for k in keys}

# --------------------------------------------------------------------------
# Scenario callbacks (run before widgets instantiate — safe to set state)
# --------------------------------------------------------------------------
def scenario_base():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.session_state["scenario_note"] = "Base case loaded."

def scenario_gifting():
    scenario_base()
    st.session_state["volume"] = 500.0
    st.session_state["scenario_note"] = (
        "Corporate-gifting spike — a lumpy 500-unit order. Fixed costs amortise "
        "better (lower per-unit), but DDP's lead time is the real constraint on a "
        "deadline, which this cost view does not show. Illustrative."
    )

def scenario_range():
    scenario_base()
    st.session_state["finish_hyb"] = 30.0
    st.session_state["finish_loc"] = 24.0
    st.session_state["base_ddp"] = 140.0
    st.session_state["scenario_note"] = (
        "Range expansion — more SKUs raise finishing and base cost (more gem/oud "
        "variety, more manual insertion). Watch the manual step penalise the "
        "higher-touch configurations. Illustrative."
    )

def scenario_growth():
    scenario_base()
    st.session_state["volume"] = 1200.0
    st.session_state["scenario_note"] = (
        "Sustained growth — at 1,200/month the fixed-cost advantage of localising "
        "starts to pay; see the crossover chart. This is the volume logic behind "
        "moving to Hybrid / Local. Illustrative."
    )

def reset_all():
    scenario_base()
    for i, item in enumerate(COMPLIANCE):
        st.session_state[f"comp_{i}"] = item[2]
    st.session_state["scenario_note"] = "Reset to illustrative defaults."

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.title("💎 Touché Royale — Cost & Compliance Decision Model")
st.caption(
    "A decision model, not a forecast. Enter your own figures and the economics "
    "update live. External rates (duty, VAT, CEPA, registration) are sourced; "
    "nothing is assumed about your sales. There are no revenue or profit "
    "projections — only the cost structure of entering the UAE."
)
st.markdown(
    "<div style='display:flex;gap:22px;flex-wrap:wrap;font-size:0.9rem;'>"
    "<span>🟢 <b>Verified</b> — sourced rate / rule</span>"
    "<span>🔵 <b>Founder input</b> — you provide</span>"
    "<span>🟡 <b>Derived</b> — calculated live</span>"
    "</div>",
    unsafe_allow_html=True,
)
st.divider()

# --------------------------------------------------------------------------
# Sidebar — global inputs + scenarios
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Your inputs 🔵")
    st.number_input(
        "Target volume (bottles / month)",
        min_value=1.0, step=10.0, key="volume",
    )
    st.selectbox(
        "Duty basis 🟢",
        options=["Standard 5% (HS 3303)", "CEPA 0% — if origin rules met"],
        key="cepa",
    )
    st.caption(
        "Duty 5% and VAT 5% are verified UAE rates. CEPA 0% applies only if "
        "India-origin rules (≈40% value-add) are met — confirm per shipment."
    )
    st.divider()
    st.subheader("Quick scenarios 🟡")
    st.button("Reset to base", width="stretch", on_click=scenario_base)
    st.button("Corporate-gifting spike", width="stretch", on_click=scenario_gifting)
    st.button("Range expansion", width="stretch", on_click=scenario_range)
    st.button("Sustained growth", width="stretch", on_click=scenario_growth)
    st.divider()
    st.button("↺ Reset everything", width="stretch", on_click=reset_all)

st.info(st.session_state["scenario_note"], icon="🧭")

# --------------------------------------------------------------------------
# 2 · Per-unit cost inputs by configuration
# --------------------------------------------------------------------------
st.subheader("2 · Per-unit cost inputs by configuration 🔵")
st.caption(
    "The three supply-chain configurations from the analysis. Adjust any cell; "
    "totals recalculate. Freight & 3PL are benchmark ranges — refine with a "
    "forwarder / 3PL quote. Defaults are illustrative placeholders."
)
hdr = st.columns([2.4, 1, 1, 1])
hdr[0].markdown("**Cost component (AED / unit)**")
hdr[1].markdown("**DDP**")
hdr[2].markdown("**Hybrid**")
hdr[3].markdown("**Local**")
for rk, rlabel in COST_ROWS:
    row = st.columns([2.4, 1, 1, 1])
    row[0].markdown(rlabel)
    step = 50.0 if rk == "fixed" else 1.0
    for i, (ck, cname, _) in enumerate(CONFIGS):
        row[i + 1].number_input(
            f"{rlabel} — {cname}",
            min_value=0.0, step=step, key=f"{rk}_{ck}",
            label_visibility="collapsed", format="%.0f",
        )
st.caption("Duty (on cost + freight) and 5% VAT are applied automatically — don't enter them here.")
st.divider()

# --------------------------------------------------------------------------
# Compute
# --------------------------------------------------------------------------
p = read_params()
duty = duty_rate(st.session_state["cepa"])
volume = p["volume"]

# --------------------------------------------------------------------------
# 3 · Landed cost per unit
# --------------------------------------------------------------------------
st.subheader("3 · Landed cost per unit 🟡")
st.caption(f"At {int(volume):,} bottles/month. Lowest-cost configuration at this volume is flagged.")

landed = {ck: landed_pu(p, ck, volume, duty) for ck, _, _ in CONFIGS}
best = min(landed, key=landed.get)
cols = st.columns(3)
for col, (ck, cname, cfit) in zip(cols, CONFIGS):
    cif = p[f"base_{ck}"] + p[f"freight_{ck}"]
    d = cif * duty
    vat = (cif + d) * VAT
    fixed_pu = p[f"fixed_{ck}"] / max(1.0, volume)
    delta = "✓ lowest here" if ck == best else None
    col.metric(cname, f"AED {landed[ck]:,.1f}", delta=delta, delta_color="normal")
    col.caption(cfit)
    with col.expander("Cost breakdown"):
        st.write(f"Base + freight (CIF): **AED {cif:,.1f}**")
        st.write(f"Duty ({duty*100:.0f}%): **AED {d:,.1f}**")
        st.write(f"VAT (5%): **AED {vat:,.1f}**")
        st.write(f"Finishing: **AED {p[f'finish_{ck}']:,.1f}**")
        st.write(f"3PL / fulfilment: **AED {p[f'tpl_{ck}']:,.1f}**")
        st.write(f"Fixed ÷ volume: **AED {fixed_pu:,.1f}**")
st.divider()

# --------------------------------------------------------------------------
# 4 · Crossover chart
# --------------------------------------------------------------------------
st.subheader("4 · Where the configurations cross 🟡")
st.caption(
    "Landed cost per unit as monthly volume rises. Where the lines cross is the "
    "volume trigger to move to the next configuration — derived purely from your "
    "cost structure, not from any demand assumption."
)
max_vol = max(600.0, volume * 3.0)
vols = list(range(20, int(max_vol) + 1, max(1, int(max_vol / 60))))
rows = []
name_by_key = {ck: cname for ck, cname, _ in CONFIGS}
for v in vols:
    for ck, cname, _ in CONFIGS:
        rows.append({"Monthly volume": v, "Landed cost / unit (AED)": landed_pu(p, ck, v, duty), "Configuration": cname})
df = pd.DataFrame(rows)

line = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.6)
    .encode(
        x=alt.X("Monthly volume:Q"),
        y=alt.Y("Landed cost / unit (AED):Q", scale=alt.Scale(zero=False)),
        color=alt.Color("Configuration:N", legend=alt.Legend(orient="top")),
    )
)
rule = (
    alt.Chart(pd.DataFrame({"v": [volume]}))
    .mark_rule(strokeDash=[5, 4], color="#B8912E")
    .encode(x="v:Q")
)
st.altair_chart((line + rule).properties(width="container"))

c_dh = crossover(p, "ddp", "hyb", duty)
c_hl = crossover(p, "hyb", "loc", duty)
msgs = []
if c_dh:
    lo = "DDP" if landed_pu(p, "ddp", max(1, c_dh * 0.5), duty) < landed_pu(p, "hyb", max(1, c_dh * 0.5), duty) else "Hybrid"
    hi = "DDP" if landed_pu(p, "ddp", c_dh * 2, duty) < landed_pu(p, "hyb", c_dh * 2, duty) else "Hybrid"
    msgs.append(f"**DDP ↔ Hybrid** cross at ≈ **{c_dh:,} bottles/month** — below this {lo} is cheaper; above it {hi} wins.")
if c_hl:
    lo = "Hybrid" if landed_pu(p, "hyb", max(1, c_hl * 0.5), duty) < landed_pu(p, "loc", max(1, c_hl * 0.5), duty) else "Local"
    hi = "Hybrid" if landed_pu(p, "hyb", c_hl * 2, duty) < landed_pu(p, "loc", c_hl * 2, duty) else "Local"
    msgs.append(f"**Hybrid ↔ Local** cross at ≈ **{c_hl:,} bottles/month** — below this {lo} is cheaper; above it {hi} wins.")
if not msgs:
    msgs.append("At current inputs, one configuration stays cheapest across the whole range — no crossover. Adjust costs to explore triggers.")
st.markdown("  \n".join("• " + m for m in msgs))
st.caption("Crossover volumes are the illustrative “triggers to advance” in the phased plan — driven by cost structure, not demand.")
st.divider()

# --------------------------------------------------------------------------
# 5 · Compliance cost & timeline
# --------------------------------------------------------------------------
st.subheader("5 · Compliance cost & timeline 🟢")
st.caption(
    "The fixed cost and lead time of getting legal to sell — the part built on "
    "sourced requirements. Edit any cost; items marked ‘varies’ need a quote."
)
chdr = st.columns([3, 2.2, 1.4, 1.4])
chdr[0].markdown("**Requirement**")
chdr[1].markdown("**Basis**")
chdr[2].markdown("**Cost (AED)**")
chdr[3].markdown("**Lead time**")
comp_total = 0.0
for i, (name, basis, _default, lead) in enumerate(COMPLIANCE):
    r = st.columns([3, 2.2, 1.4, 1.4])
    r[0].markdown(name)
    r[1].caption(basis)
    r[2].number_input(name + " cost", min_value=0.0, step=25.0, key=f"comp_{i}",
                      label_visibility="collapsed", format="%.0f")
    r[3].caption(lead)
    comp_total += float(st.session_state[f"comp_{i}"])
st.markdown(f"**Total one-off compliance (entered):**  AED {comp_total:,.0f}  ·  ≈ 4–8 weeks total")
st.caption(
    "Sources: MoIAT (ECAS), Dubai Municipality (Montaji ≈ AED 230–300/SKU), "
    "GSO 1943, IFRA, CITES (conditional on natural oud). Fees not publicly fixed are left for you to quote."
)
st.divider()

# --------------------------------------------------------------------------
# 6 · Readiness gaps
# --------------------------------------------------------------------------
st.subheader("6 · Readiness gaps — which ones cost money")
st.caption("The eight-dimension readiness gaps, tagged by whether closing them needs capital or is a process fix.")
rdf = pd.DataFrame(READINESS, columns=["Dimension", "To close"])
st.dataframe(rdf, hide_index=True, width="stretch")
st.divider()

# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
st.markdown(
    "**How to read this:** a decision-support tool for structuring the conversation "
    "— not financial advice, and not a forecast of Touché Royale's performance. "
    "Every AED amount that isn't a sourced government rate is either your input or "
    "an illustrative placeholder to be replaced. The model deliberately contains no "
    "revenue or profit projection."
)
st.caption(
    "Verified: UAE import duty 5% & VAT 5% (HS 3303); India–UAE CEPA 0% (origin rules); "
    "Montaji ≈ AED 230–300/SKU; ECAS (MoIAT); GSO 1943; CITES Appendix II (agarwood). "
    "Benchmark: freight & 3PL are indicative ranges. Founder: all base, finishing and fixed-cost figures."
)
