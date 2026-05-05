import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from energy_scheduler import demo_and_compare

st.set_page_config(page_title="CPU Scheduling Dashboard", layout="wide")

st.title("⚡ Energy-Efficient CPU Scheduling Dashboard")

# ==============================
# GET DATA
# ==============================
results = demo_and_compare()

ee = results['ee_results']
fcfs = results['fcfs_results']
rr = results['rr_results']

# ==============================
# 🔥 KPI CARDS
# ==============================
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("⚡ EE Energy (mJ)", f"{ee['total_energy']:.2f}")
col2.metric("🧱 FCFS Energy (mJ)", f"{fcfs['total_energy']:.2f}")
col3.metric("🔁 RR Energy (mJ)", f"{rr['total_energy']:.2f}")

# Energy Saving Highlight
energy_saved = ((fcfs['total_energy'] - ee['total_energy']) / fcfs['total_energy']) * 100
st.success(f"⚡ Energy Saved vs FCFS: {energy_saved:.2f}%")

st.divider()

# ==============================
# 📊 TABLE
# ==============================
data = {
    "Algorithm": ["Energy Efficient", "FCFS", "Round Robin"],
    "Energy (mJ)": [ee['total_energy'], fcfs['total_energy'], rr['total_energy']],
    "Avg Wait Time": [ee['avg_wait_time'], fcfs['avg_wait_time'], rr['avg_wait_time']],
    "Avg Turnaround": [ee['avg_turnaround_time'], fcfs['avg_turnaround_time'], rr['avg_turnaround_time']]
}

df = pd.DataFrame(data)

st.subheader("📊 Performance Comparison")
st.dataframe(df, width='stretch')

# ==============================
# 📈 PREMIUM CHARTS
# ==============================
st.subheader("📈 Visual Insights")

def style_chart(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.3)

# Row layout like Power BI
col1, col2 = st.columns(2)

# 🔥 ENERGY CHART
with col1:
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.bar(df["Algorithm"], df["Energy (mJ)"], color="#4CAF50")
    plt.xticks(rotation=0)
    ax1.set_title("Energy Comparison", fontweight='bold')
    style_chart(ax1)
    plt.tight_layout()
    st.pyplot(fig1)

# 🔥 WAIT TIME CHART
with col2:
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.bar(df["Algorithm"], df["Avg Wait Time"], color="#2196F3")
    plt.xticks(rotation=0)
    ax2.set_title("Avg Wait Time", fontweight='bold')
    style_chart(ax2)
    plt.tight_layout()
    st.pyplot(fig2)

# 🔥 TURNAROUND CHART (full width)
fig3, ax3 = plt.subplots(figsize=(8, 4))
ax3.bar(df["Algorithm"], df["Avg Turnaround"], color="#FF9800")
plt.xticks(rotation=0)
ax3.set_title("Avg Turnaround Time", fontweight='bold')
style_chart(ax3)
plt.tight_layout()
st.pyplot(fig3)

# ==============================
# 🧩 GANTT CHART
# ==============================
st.subheader("🧩 Execution Timeline (Gantt Chart)")

def plot_gantt(schedule_log):
    fig, ax = plt.subplots(figsize=(10, 3))

    colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#009688']

    for entry in schedule_log:
        if 'process' in entry:
            pid = entry['process']
            ax.barh(
                f"P{pid}",
                entry["duration"],
                left=entry["start_time"],
                color=colors[pid % len(colors)]
            )

    ax.set_xlabel("Time")
    ax.set_ylabel("Process")
    ax.set_title("Process Execution Timeline", fontweight='bold')

    style_chart(ax)

    return fig

st.pyplot(plot_gantt(ee['schedule_log']))

# ==============================
# ⚙️ EXTRA DETAILS
# ==============================
st.subheader("⚙️ Scheduler Details")

col1, col2, col3 = st.columns(3)

col1.metric("CPU Utilization", f"{ee['cpu_utilization']:.2f}%")
col2.metric("Frequency Changes", ee['frequency_changes'])
col3.metric("Idle Time", ee['idle_time'])