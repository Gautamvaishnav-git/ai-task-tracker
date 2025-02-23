# pylint: disable=redefined-outer-name

import logging
import os
import sqlite3
import sys
from typing import List, Optional, Tuple

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL")

if not OLLAMA_URL:
    raise Exception("OLLAMA_URL not found")


DB_NAME = "tasks.db"


# Initialize SQLite Database
def init_db() -> None:
    """init db"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            developer TEXT NOT NULL,
            project TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            task_date DATE DEFAULT (DATE('now'))
        )
        """)


# Function to add task
def add_task(
    title: str, description: str, developer: str, project: str, task_date: str
) -> None:
    """add task"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, developer, project, task_date) VALUES (?, ?, ?, ?, ?)",
            (title, description, developer, project, task_date),
        )


# Function to fetch tasks
def get_tasks() -> List[Tuple[int, str, str, str, str, str, str]]:
    """get tasks"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks order by task_date desc")
        tasks = cursor.fetchall()
        return tasks


# Function to summarize tasks using AI
def summarize_tasks(
    tasks: List[Tuple[int, str, str, str, str, str, str]],
) -> Optional[str]:
    """Summarize tasks"""
    if not tasks:
        return "No tasks available."

    prompt_template = ChatPromptTemplate.from_template(
        """
        You are an expert Project Scrum Master. Your task is to summarize all user task items and present them in a table.

        ### Requirements:
        - The summary must be **professional and well-organized**.
        - The table must include the following mandatory columns: **Task Date, Task, Summary and Project**.
        - If multiple tasks exist for the same date, **group them into a single row** instead of creating multiple rows for the same day.
        - You may include additional fields if relevant.

        Context:
        {tasks}
        """
    )

    llm_model = ChatOllama(model="deepseek-r1:1.5b", base_url=OLLAMA_URL)
    task_texts = [
        f"Task: {t[1]}, Description: {t[2]}, Project: {t[4]}, Developer: {t[3]}, Task Date: {t[6]},"
        for t in tasks
    ]
    chain = RunnablePassthrough() | prompt_template | llm_model | StrOutputParser()
    logger.info("Generating response using the LLM.")
    return chain.invoke({"tasks": task_texts})


def update_task(task_id, title, description, developer, project):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks SET title = ?, description = ?, developer = ?, project = ? WHERE id = ?
        """,
            (title, description, developer, project, task_id),
        )


st.set_page_config(layout="wide")

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "add_task"


# Function to change route
def set_page(page_name: str):
    st.session_state.page = page_name


# Streamlit UI
st.title("AI Task Tracker")


col1, col2 = st.sidebar.columns(2)  # Create two equal-width columns

with col1:
    st.button("🏠 Home", on_click=set_page, args=("add_task",))

with col2:
    st.button("📝 Edit Task", on_click=set_page, args=("edit",))

# Initialize database on first run
init_db()

# Routing Logic
if st.session_state.page == "edit":
    st.title("Edit Tasks")
    tasks = get_tasks()
    if tasks:
        task_options = {f"{t[1]} | ({t[6]})": t for t in tasks}
        selected_task_name = st.selectbox(
            "Select a task to edit", list(task_options.keys())
        )

        if selected_task_name:
            selected_task = task_options[selected_task_name]
            task_id = selected_task[0]

            new_title = st.text_input("Title", selected_task[1])
            new_description = st.text_area("Description", selected_task[2])
            new_developer = st.text_input("Developer", selected_task[3])
            new_project = st.text_input("Project", selected_task[4])

            if st.button("Update Task"):
                update_task(
                    task_id, new_title, new_description, new_developer, new_project
                )
                st.success("Task updated successfully!")
                st.rerun()
    else:
        st.write("No tasks available to edit.")
elif st.session_state.page == "add_task":
    st.sidebar.header("Add New Task")
    title = st.sidebar.text_input("Task Title")
    description = st.sidebar.text_area("Task Description")
    task_date = st.sidebar.date_input("Task Date", "today")
    developer = st.sidebar.selectbox("Developer Name", ["GautamV"])
    project = st.sidebar.selectbox("Project Name", ["ODD", "Workbench", "Tareek"])

    if st.sidebar.button("Add Task"):
        if title and developer and project:
            add_task(title, description, developer, project, task_date)
            st.sidebar.success("Task added successfully!")
        else:
            st.sidebar.error("Please fill in all required fields.")

    # Display Tasks
    tasks = get_tasks()
    st.subheader("All Tasks")
    for task in tasks:
        st.write(
            f"{task[6]} | **{task[1]}** (Project: {task[4]}, Developer: {task[3]})"
        )
        st.write(f"_Description:_ {task[2]}")
        st.write(f"_Created At:_ ***{task[5]}***")
        st.write("---")

    # Summarization
    # if st.button("Summarize Tasks"):
    #     summary = summarize_tasks(tasks)
    #     st.subheader("Task Summary")
    #     st.write(summary)

    if st.button("Summarize Tasks"):
        with st.spinner("Summarizing tasks... Please wait ⏳"):
            summary = summarize_tasks(tasks)

        st.write(summary)


else:
    st.title("404 - Page Not Found")
