import streamlit as st
import threading
import random
import time
import pandas as pd

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Train Booking System",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e0e0e0;
}

section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.05);
    border-right: 1px solid rgba(255,255,255,0.1);
}
section[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}

.hero {
    background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.3));
    border: 1px solid rgba(168,85,247,0.4);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
    backdrop-filter: blur(10px);
}
.hero h1 { margin:0; font-size:2rem; font-weight:700; color:#fff; }
.hero p  { margin:6px 0 0; color:#c4b5fd; font-size:0.95rem; }

.metric-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 14px;
    padding: 18px 22px;
    text-align: center;
    backdrop-filter: blur(8px);
    transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-3px); }
.metric-card .label { font-size:0.78rem; color:#a78bfa; text-transform:uppercase; letter-spacing:1px; }
.metric-card .value { font-size:2rem; font-weight:700; color:#fff; margin-top:4px; }

.log-box {
    background: rgba(0,0,0,0.45);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 14px 18px;
    height: 340px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    line-height: 1.7;
}
.log-book   { color: #6ee7b7; }
.log-cancel { color: #fca5a5; }
.log-fail   { color: #fbbf24; }
.log-info   { color: #93c5fd; }
.log-wait   { color: #6b7280; }

.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #c4b5fd;
    border-bottom: 1px solid rgba(168,85,247,0.3);
    padding-bottom: 6px;
    margin-bottom: 14px;
}

.badge {
    display:inline-block;
    padding: 5px 14px;
    border-radius: 999px;
    font-size:0.78rem;
    font-weight:600;
}
.badge-running { background:#7c3aed; color:#fff; }
.badge-done    { background:#059669; color:#fff; }
.badge-idle    { background:#374151; color:#9ca3af; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "running": False,
        "done": False,
        "logs": [],
        "available_seats": [],
        "stats": {"booked": 0, "cancelled": 0, "failed": 0, "inquiries": 0},
        "elapsed": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
#  SIDEBAR — CONFIGURATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    max_trains      = st.slider("🚂 Total Trains",               5,   100,  20, step=5)
    capacity        = st.slider("💺 Seats per Train",            50,  500, 200, step=50)
    max_threads     = st.slider("👥 Concurrent Users (Threads)", 2,    30,  10)
    max_concurrent  = st.slider("🔒 Max Simultaneous Access",    1,    10,   3)
    book_min        = st.slider("📉 Min Seats per Booking",      1,    10,   2)
    book_max        = st.slider("📈 Max Seats per Booking",      book_min, 20, 6)
    sim_seconds     = st.slider("⏱️ Simulation Duration (sec)",  5,    60,  15)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.78rem; color:#9ca3af; line-height:2'>
    🔐 <b>Semaphore</b> — limits global concurrent access<br>
    🔑 <b>Mutex per train</b> — prevents race conditions<br>
    🧵 <b>Threads</b> — simulate real concurrent users
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HERO HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🚂 Train Booking System</h1>
  <p>Multithreaded concurrent seat reservation simulation — powered by Mutex locks &amp; Semaphore synchronization</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SIMULATION ENGINE
# ─────────────────────────────────────────────
def run_simulation(max_trains, capacity, max_threads, max_concurrent,
                   book_min, book_max, sim_seconds):
    train_locks      = [threading.Lock() for _ in range(max_trains)]
    available_seats  = [capacity] * max_trains
    access_semaphore = threading.Semaphore(max_concurrent)
    log_lock         = threading.Lock()
    stats_lock       = threading.Lock()
    logs             = []
    stats            = {"booked": 0, "cancelled": 0, "failed": 0, "inquiries": 0}

    def add_log(tag, msg):
        with log_lock:
            logs.append((tag, msg))

    def worker(thread_num, end_time):
        while time.time() < end_time:
            time.sleep(random.uniform(0.05, 0.4))
            if time.time() >= end_time:
                break

            train_num = random.randint(0, max_trains - 1)
            op_type   = random.randint(1, 3)

            add_log("wait", f"Thread {thread_num:02d} ▸ waiting for system access...")
            access_semaphore.acquire()
            add_log("info", f"Thread {thread_num:02d} ▸ gained access → Train {train_num:03d}")

            try:
                with train_locks[train_num]:
                    if op_type == 1:
                        seats = available_seats[train_num]
                        add_log("info", f"Thread {thread_num:02d} ▸ INQUIRY   Train {train_num:03d} — {seats} seats available")
                        with stats_lock:
                            stats["inquiries"] += 1

                    elif op_type == 2:
                        num = random.randint(book_min, book_max)
                        if available_seats[train_num] >= num:
                            available_seats[train_num] -= num
                            add_log("book", f"Thread {thread_num:02d} ▸ BOOKED    {num} seats on Train {train_num:03d}  →  remaining: {available_seats[train_num]}")
                            with stats_lock:
                                stats["booked"] += num
                        else:
                            add_log("fail", f"Thread {thread_num:02d} ▸ FAILED    booking on Train {train_num:03d} — not enough seats")
                            with stats_lock:
                                stats["failed"] += 1

                    elif op_type == 3:
                        booked = capacity - available_seats[train_num]
                        if booked > 0:
                            num = random.randint(1, booked)
                            available_seats[train_num] += num
                            add_log("cancel", f"Thread {thread_num:02d} ▸ CANCELLED {num} seats on Train {train_num:03d}  →  remaining: {available_seats[train_num]}")
                            with stats_lock:
                                stats["cancelled"] += num
                        else:
                            add_log("info", f"Thread {thread_num:02d} ▸ SKIP CANCEL Train {train_num:03d} — no bookings to cancel")
            finally:
                access_semaphore.release()

    end_time = time.time() + sim_seconds
    threads  = [threading.Thread(target=worker, args=(i, end_time), daemon=True)
                for i in range(max_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    st.session_state.logs            = logs
    st.session_state.available_seats = available_seats
    st.session_state.stats           = stats
    st.session_state.running         = False
    st.session_state.done            = True
    st.session_state.elapsed         = sim_seconds


# ─────────────────────────────────────────────
#  CONTROL ROW
# ─────────────────────────────────────────────
col_btn1, col_btn2, col_status = st.columns([1, 1, 4])

with col_btn1:
    start_clicked = st.button("▶  Run Simulation", use_container_width=True,
                              disabled=st.session_state.running)
with col_btn2:
    reset_clicked = st.button("↺  Reset", use_container_width=True,
                              disabled=st.session_state.running)
with col_status:
    if st.session_state.running:
        st.markdown('<span class="badge badge-running">⚡ Running...</span>', unsafe_allow_html=True)
    elif st.session_state.done:
        st.markdown(
            f'<span class="badge badge-done">✅ Done — {len(st.session_state.logs)} events in {st.session_state.elapsed:.0f}s</span>',
            unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-idle">⬤ Idle — press Run to begin</span>', unsafe_allow_html=True)

if reset_clicked:
    for k in ["running", "done", "logs", "available_seats", "stats", "elapsed"]:
        if k in st.session_state:
            del st.session_state[k]
    init_state()
    st.rerun()

if start_clicked and not st.session_state.running:
    st.session_state.running = True
    st.session_state.done    = False
    st.session_state.logs    = []
    st.session_state.stats   = {"booked": 0, "cancelled": 0, "failed": 0, "inquiries": 0}

    with st.spinner(f"⏳ Simulation running for {sim_seconds} seconds..."):
        run_simulation(max_trains, capacity, max_threads, max_concurrent,
                       book_min, book_max, sim_seconds)
    st.rerun()


# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────
if st.session_state.done:
    st.markdown("<br>", unsafe_allow_html=True)
    stats = st.session_state.stats

    # Metrics row
    st.markdown('<div class="section-title">📊 Simulation Summary</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)

    def metric_card(col, label, value, color="#a78bfa"):
        col.markdown(f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value" style="color:{color}">{value:,}</div>
        </div>""", unsafe_allow_html=True)

    metric_card(m1, "Total Events",    len(st.session_state.logs), "#c4b5fd")
    metric_card(m2, "Seats Booked",    stats["booked"],             "#6ee7b7")
    metric_card(m3, "Seats Cancelled", stats["cancelled"],          "#fca5a5")
    metric_card(m4, "Failed Bookings", stats["failed"],             "#fbbf24")
    metric_card(m5, "Inquiries",       stats["inquiries"],          "#93c5fd")

    st.markdown("<br>", unsafe_allow_html=True)

    # Log + Chart side by side
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.markdown('<div class="section-title">📋 Activity Log</div>', unsafe_allow_html=True)
        tag_class = {"book": "log-book", "cancel": "log-cancel",
                     "fail": "log-fail",  "info":   "log-info", "wait": "log-wait"}
        log_html = "".join(
            f'<div class="{tag_class.get(tag, "log-info")}">{msg}</div>'
            for tag, msg in st.session_state.logs[-300:]
        )
        st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)
        st.caption(f"Showing last 300 of {len(st.session_state.logs)} total events.")

    with right_col:
        st.markdown('<div class="section-title">🪑 Seat Availability by Train</div>', unsafe_allow_html=True)
        seats = st.session_state.available_seats
        df = pd.DataFrame({
            "Train":           [f"T{i:02d}" for i in range(len(seats))],
            "Available Seats": seats,
            "Booked Seats":    [capacity - s for s in seats],
        }).set_index("Train")
        st.bar_chart(df[["Available Seats", "Booked Seats"]], height=320, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Full table
    with st.expander("🔍 Full Reservation Table"):
        seats = st.session_state.available_seats
        table_df = pd.DataFrame({
            "Train #":         list(range(len(seats))),
            "Available Seats": seats,
            "Booked Seats":    [capacity - s for s in seats],
            "Occupancy %":     [round((capacity - s) / capacity * 100, 1) for s in seats],
        })
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Occupancy %": st.column_config.ProgressColumn(
                    "Occupancy %", min_value=0, max_value=100, format="%.1f%%"
                )
            }
        )

else:
    st.markdown("""
    <br>
    <div style="text-align:center; padding:70px 20px; opacity:0.45;">
        <div style="font-size:5rem;">🚂</div>
        <div style="font-size:1.15rem; color:#a78bfa; margin-top:16px;">
            Configure parameters in the sidebar, then press <b>▶ Run Simulation</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
