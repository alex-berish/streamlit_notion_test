import streamlit as st
from notion_client import Client
from datetime import datetime
import os

# Get Notion API token from environment variables
notion_token = os.getenv("NOTION_API_TOKEN")

# Initialize the Notion client
notion = Client(auth=notion_token)

# Notion database IDs
teachers_db_id = "9f0e4ffc7c1449b1915ebd199e2d9655"
students_db_id = "83219e99ee3b4866a3f88c491a7d76c0"
tasks_db_id = "e058d21ab92d43a1bb44f173dff5d578"

# Function to get data from Notion database
def get_database_entries(database_id):
    response = notion.databases.query(database_id=database_id)
    return response['results']

# Function to create a new task in Notion
def create_task_in_notion(task_name, subtasks):
    task_page = notion.pages.create(parent={"database_id": tasks_db_id},
                                    properties={
                                        "Name": {
                                            "title": [
                                                {
                                                    "text": {
                                                        "content": task_name
                                                    }
                                                }
                                            ]
                                        }
                                    })

    for subtask in subtasks:
        notion.pages.create(parent={"page_id": task_page['id']},
                            properties={
                                "Name": {
                                    "title": [
                                        {
                                            "text": {
                                                "content": subtask
                                            }
                                        }
                                    ]
                                }
                            })

# Streamlit UI
st.title("Notion Task and Subtask Creator")

# Display loading spinner
with st.spinner('Fetching teachers data...'):
    teachers_data = get_database_entries(teachers_db_id)

# Extract teacher names for dropdown
teacher_names = [teacher['properties']['Name']['title'][0]['text']['content'] for teacher in teachers_data]

# Select Teacher Dropdown
selected_teacher = st.selectbox("Select Teacher", teacher_names)

# Date Picker for absence date
absence_date = st.date_input("Select Date of Absence")

# Create Tasks button
if st.button("Create Tasks"):
    with st.spinner('Creating tasks and subtasks...'):
        # Fetch students data
        students_data = get_database_entries(students_db_id)
        subtasks = []

        for student in students_data:
            main_teacher = student['properties']['Main Teacher']['select']['name']
            next_lesson = student['properties']['Next Lesson']['date']['start']

            if main_teacher == selected_teacher and next_lesson == str(absence_date):
                student_name = student['properties']['Name']['title'][0]['text']['content']
                subtasks.append(student_name)

        # Create task and subtasks in Notion
        create_task_in_notion(selected_teacher, subtasks)

    st.success('Tasks and subtasks created successfully!')
