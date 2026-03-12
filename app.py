import streamlit as st
import pandas as pd
from utils.fetcher import fetch_sheet
from utils.extractor import extract_adit_ids, extract_edi_ids
from utils.comparator import compare_ids

st.set_page_config(page_title="ADIT vs EDI Comparator", page_icon="🔍", layout="wide")
st.title("🔍 ADIT vs EDI Comparator")
st.markdown("Google Sheet URLs paste karo aur IDs automatically compare ho jayengi.")
st.divider()

# ── URL Input ──────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 ADIT Report")
    adit_url = st.text_input("ADIT Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/...")
with col2:
    st.subheader("📋 EDI Report")
    edi_url = st.text_input("EDI Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/...")

st.divider()

# ── Fetch Button ───────────────────────────────────────────────
if st.button("📥 Fetch Sheets", use_container_width=True):
    if not adit_url.strip() or not edi_url.strip():
        st.error("⚠️ Dono URLs daalo pehle!")
        st.stop()

    with st.spinner("Sheets fetch ho rahi hain..."):
        try:
            st.session_state["adit_df"] = fetch_sheet(adit_url, "ADIT")
        except Exception as e:
            st.error(f"ADIT Sheet Error: {e}")
            st.stop()
        try:
            st.session_state["edi_df"] = fetch_sheet(edi_url, "EDI")
        except Exception as e:
            st.error(f"EDI Sheet Error: {e}")
            st.stop()

    st.success("✅ Sheets fetch ho gayi!")

# ── Column Selection + Compare ─────────────────────────────────
if "adit_df" in st.session_state and "edi_df" in st.session_state:
    adit_df = st.session_state["adit_df"]
    edi_df  = st.session_state["edi_df"]

    st.subheader("⚙️ Column Select Karo")
    cc1, cc2 = st.columns(2)

    with cc1:
        adit_col = st.selectbox(
            "ADIT — Patient ID Column",
            adit_df.columns.tolist(),
            index=next((i for i, c in enumerate(adit_df.columns) if "patient" in c.lower() or "stedi" in c.lower()), 0)
        )
        status_col = st.selectbox(
            "ADIT — Status Column (optional)",
            ["— None —"] + adit_df.columns.tolist(),
            index=next((i+1 for i, c in enumerate(adit_df.columns) if "status" in c.lower()), 0)
        )
        if status_col != "— None —":
            all_statuses = sorted(adit_df[status_col].dropna().unique().tolist())
            selected_statuses = st.multiselect("Status Filter (empty = saare)", all_statuses)
        else:
            selected_statuses = []

    with cc2:
        edi_col = st.selectbox(
            "EDI — Patient ID Column",
            edi_df.columns.tolist(),
            index=next((i for i, c in enumerate(edi_df.columns) if "patient" in c.lower() or "id" in c.lower()), 0)
        )

    st.divider()

    # ── Compare Button ─────────────────────────────────────────
    if st.button("🚀 Compare Now", use_container_width=True):

        # Apply status filter
        adit_filtered = adit_df.copy()
        if status_col != "— None —" and selected_statuses:
            adit_filtered = adit_filtered[adit_filtered[status_col].isin(selected_statuses)]

        # Extract IDs
        adit_ids = extract_adit_ids(adit_filtered, adit_col)
        edi_ids  = extract_edi_ids(edi_df, edi_col)

        # Compare
        result = compare_ids(adit_ids, edi_ids)
        st.session_state["result"]   = result
        st.session_state["adit_ids"] = adit_ids
        st.session_state["edi_ids"]  = edi_ids

# ── Results ────────────────────────────────────────────────────
if "result" in st.session_state:
    result   = st.session_state["result"]
    adit_ids = st.session_state["adit_ids"]
    edi_ids  = st.session_state["edi_ids"]

    st.divider()
    st.subheader("📊 Summary")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("ADIT Total",    len(adit_ids))
    s2.metric("EDI Total",     len(edi_ids))
    s3.metric("🔴 Only ADIT",  len(result["only_adit"]))
    s4.metric("🔵 Only EDI",   len(result["only_edi"]))
    s5.metric("🟢 Common",     len(result["common"]))

    st.divider()
    st.subheader("📋 Results")
    t1, t2, t3, t4 = st.columns(4)

    with t1:
        st.markdown(f"### 🔴 Only in ADIT ({len(result['only_adit'])})")
        st.caption("It is present in ADIT, but not in EDI.")
        if result["only_adit"]:
            df_show = pd.DataFrame(result["only_adit"], columns=["Stedi ID"])
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download", df_show.to_csv(index=False).encode(), "only_adit.csv", use_container_width=True)
        else:
            st.success("There is no difference")

    with t2:
        st.markdown(f"### 🔵 Only in EDI ({len(result['only_edi'])})")
        st.caption("It is present in EDI, but not in ADIT")
        if result["only_edi"]:
            df_show = pd.DataFrame(result["only_edi"], columns=["Patient ID"])
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download", df_show.to_csv(index=False).encode(), "only_edi.csv", use_container_width=True)
        else:
            st.success("There is no difference")

    with t3:
        st.markdown(f"### 🟢 Common ({len(result['common'])})")
        st.caption("It is available in both")
        if result["common"]:
            df_show = pd.DataFrame(result["common"], columns=["ID"])
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download", df_show.to_csv(index=False).encode(), "common.csv", use_container_width=True)
        else:
            st.info("Koi common ID nahi mili")

    with t4:
        st.markdown(f"### 🟡 Difference ({len(result['difference'])})")
        st.caption("ADIT and EDI unmatched records")
        if result["difference"]:
            df_show = pd.DataFrame(result["difference"], columns=["ID"])
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download", df_show.to_csv(index=False).encode(), "difference.csv", use_container_width=True)
        else:
            st.success("Koi difference nahi!")

    st.divider()
    with st.expander("🔎 Raw Sheet Preview"):
        p1, p2 = st.columns(2)
        with p1:
            st.markdown("**ADIT Sheet**")
            st.dataframe(adit_df, use_container_width=True)
        with p2:
            st.markdown("**EDI Sheet**")
            st.dataframe(edi_df, use_container_width=True)