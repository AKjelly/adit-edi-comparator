import streamlit as st
import pandas as pd
from utils.fetcher import fetch_sheet
from utils.extractor import extract_adit_ids, extract_edi_ids
from utils.comparator import compare_ids

st.set_page_config(page_title="ADIT vs EDI Comparator", page_icon="🔍", layout="wide")
st.title("🔍 ADIT vs EDI Comparator")
st.markdown("Paste the Google Sheet URLs, and the system will automatically compare the IDs.")
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

    with st.spinner("Fetching sheets...."):
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

    st.success("✅ Sheets fetched")

# ── Column Selection + Compare ─────────────────────────────────
if "adit_df" in st.session_state and "edi_df" in st.session_state:
    adit_df = st.session_state["adit_df"]
    edi_df  = st.session_state["edi_df"]

    st.subheader("⚙️ Select Columns")
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
    with st.expander("📊 Daily Report Dashboard", expanded=True):

        adit_df = st.session_state["adit_df"]
        edi_df  = st.session_state["edi_df"]

        # ── EDI Status Counts ──────────────────────────────────
        edi_success    = 0
        edi_failed     = 0
        edi_inprogress = 0

        if status_col != "— None —" and status_col in edi_df.columns:
            edi_status_counts = edi_df[status_col].str.strip().str.lower().value_counts()
            edi_success    = edi_status_counts.get("success", 0)
            edi_failed     = edi_status_counts.get("failed", 0)
            edi_inprogress = edi_status_counts.get("in progress", 0)

        # ── ADIT Status Counts ─────────────────────────────────
        verified      = 0
        hard_verified = 0
        failed_new    = 0
        app_failed    = 0
        app_inprogress= 0
        skip          = 0

        if status_col != "— None —" and status_col in adit_df.columns:
            adit_status_counts = adit_df[status_col].str.strip().str.lower().value_counts()
            verified       = adit_status_counts.get("verified", 0)
            hard_verified  = adit_status_counts.get("hard verified", 0)
            failed_new     = adit_status_counts.get("failed new", 0)
            app_failed     = adit_status_counts.get("failed", 0)
            app_inprogress = adit_status_counts.get("in progress", 0)
            skip           = adit_status_counts.get("skip", 0)

        # ── Computed Values ────────────────────────────────────
        only_adit_count = len(result["only_adit"])
        only_edi_count  = len(result["only_edi"])
        diff_count      = len(result["difference"])
        total_trigger   = len(adit_df) + len(edi_df)

        # ── Row 1: Trigger & Difference ────────────────────────
        st.markdown("#### 🔁 Trigger & Difference Summary")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Total Trigger",          f"{total_trigger:,}")
        d2.metric("Total Difference Count", f"{diff_count:,}")
        d3.metric("🔴 Diff - App Report",   f"{only_adit_count:,}")
        d4.metric("🔵 Diff - EDI Report",   f"{only_edi_count:,}")

        st.divider()

        # ── Row 2: EDI Summary ─────────────────────────────────
        st.markdown("#### 📨 EDI Summary")
        e1, e2, e3, e4, e5 = st.columns(5)
        e1.metric("EDI Total Received", f"{len(edi_df):,}")
        e2.metric("Stedi Total Count",  f"{len(edi_df):,}")
        e3.metric("✅ Success",         f"{edi_success:,}")
        e4.metric("❌ Failed",          f"{edi_failed:,}")
        e5.metric("⏳ In Progress",     f"{edi_inprogress:,}")

        st.divider()

        # ── Row 3: App Summary ─────────────────────────────────
        st.markdown("#### 📱 App Summary")
        a1, a2, a3, a4, a5, a6, a7 = st.columns(7)
        a1.metric("App Total",       f"{len(adit_df):,}")
        a2.metric("✅ Verified",     f"{verified:,}")
        a3.metric("💎 Hard Verified",f"{hard_verified:,}")
        a4.metric("🆕 Failed New",   f"{failed_new:,}")
        a5.metric("❌ Failed",       f"{app_failed:,}")
        a6.metric("⏳ In Progress",  f"{app_inprogress:,}")
        a7.metric("⏭ Skip",         f"{skip:,}")
    
