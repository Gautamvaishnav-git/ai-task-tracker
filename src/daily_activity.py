import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

DB_NAME = "tasks.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS daily_log (
                    date TEXT PRIMARY KEY,
                    wake_up_time TEXT,
                    well_rested TEXT,
                    workout TEXT,
                    workout_type TEXT,
                    work_hours TEXT,
                    focus_level TEXT,
                    tasks_completed TEXT,
                    blockers TEXT,
                    learning_time TEXT,
                    satisfaction TEXT
                )""")
    conn.commit()
    conn.close()


def save_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO daily_log (date, wake_up_time, well_rested, workout, workout_type, 
        work_hours, focus_level, tasks_completed, blockers, learning_time, satisfaction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        data,
    )
    conn.commit()
    conn.close()


def show_form():
    with st.expander("Fill Your Daily Routine", expanded=True):
        st.write("### 🌅 Morning Routine")
        wake_up_time = st.time_input("What time did you wake up today?")
        well_rested = st.radio(
            "Did you feel well-rested?", ["Yes", "No", "Maybe"], horizontal=True
        )

        st.write("### 🏋️ Workout & Health")
        workout = st.radio(
            "Did you work out today?", ["Yes", "No", "Skipped"], horizontal=True
        )
        workout_type = st.multiselect(
            "What type of workout?", ["Gym", "Yoga", "Running", "Walking", "Other"]
        )

        st.write("### 💻 Work & Productivity")
        work_hours = st.selectbox(
            "How many hours did you work?", ["<2", "2-4", "4-6", "6-8", "8+"]
        )
        focus_level = st.radio(
            "How focused were you?", ["Low", "Moderate", "High"], horizontal=True
        )
        tasks_completed = st.radio(
            "Did you complete all planned tasks?",
            ["Yes", "No", "Partially"],
            horizontal=True,
        )
        blockers = st.radio(
            "Did you face any blockers?", ["Yes", "No", "Minor issues"], horizontal=True
        )

        st.write("### 📚 Learning & Self-Improvement")
        learning_time = st.selectbox(
            "How much time did you spend learning?",
            ["<30 min", "30 min-1 hr", "1-2 hrs", "More than 2 hrs"],
        )

        st.write("### 🌙 Evening & Reflection")
        satisfaction = st.radio(
            "How satisfied are you with today?",
            ["Not Satisfied", "Neutral", "Very Satisfied"],
            horizontal=True,
        )

        if st.button("Submit"):
            data = (
                datetime.today().strftime("%Y-%m-%d"),
                wake_up_time.strftime("%H:%M"),
                well_rested,
                workout,
                ",".join(workout_type),
                work_hours,
                focus_level,
                tasks_completed,
                blockers,
                learning_time,
                satisfaction,
            )
            save_to_db(data)
            st.success("Daily log saved successfully!")


def routine_tracker():
    """routine tracker"""
    st.title("📝 Daily Routine Tracker")
    init_db()
    show_form()

    st.write("## 📊 Past Entries")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM daily_log", conn)
    conn.close()
    st.dataframe(df)
