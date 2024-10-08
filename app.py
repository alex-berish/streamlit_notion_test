import streamlit as st
from notion_client import Client, APIResponseError
from datetime import datetime, timedelta
import os
import dotenv
import pytz

# Load environment variables
print("Loading environment variables...")
dotenv.load_dotenv()
notion_token = os.getenv("NOTION_TOKEN")

if not notion_token:
    st.error(
        "Notion API token not found. Please set the NOTION_API_TOKEN environment variable."
    )
    st.stop()

print("Environment variables loaded successfully.")
print(f"Notion token: {'Set' if notion_token else 'Not set'}")

# Initialize the Notion client
print("Initializing Notion client...")
notion = Client(auth=notion_token)
print("Notion client initialized.")

# Notion database IDs
teachers_db_id = "9f0e4ffc7c1449b1915ebd199e2d9655"
students_db_id = "83219e99ee3b4866a3f88c491a7d76c0"
tasks_db_id = "1854209ee0d44027a3a18c9fa63016db"

# Function to get data from Notion database with pagination
def get_database_entries(database_id):
    print(f"Fetching data from Notion database: {database_id}")
    results = []
    has_more = True
    start_cursor = None

    while has_more:
        try:
            response = notion.databases.query(
                database_id=database_id, start_cursor=start_cursor
            )
            print(f"Query response received: {response}")
            results.extend(response["results"])
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor", None)
            print(f"Results length: {len(results)}, has_more: {has_more}, next_cursor: {start_cursor}")
        except APIResponseError as e:
            print(f"Failed to fetch data from Notion: {e}")
            st.error(f"Failed to fetch data from Notion: {e}")
            break

    return results


# Function to create a new task in Notion
def create_task_in_notion(task_name, subtasks):
    print(f"Creating main task in Notion: {task_name}")
    try:
        # Create the main task
        task_page = notion.pages.create(
            parent={"database_id": tasks_db_id},
            properties={"Name": {"title": [{"text": {"content": task_name}}]}},
        )
        print(f"Main task created: {task_page['id']}")
        subtask_ids = []
        for subtask in subtasks:
            print(f"Creating subtask for student: {subtask['name']}")
            # Create each subtask
            subtask_page = notion.pages.create(
                parent={"database_id": tasks_db_id},
                properties={
                    "Name": {
                        "title": [
                            {"text": {"content": f"Notify Student: {subtask['name']}"}}
                        ]
                    },
                    "Student": {"relation": [{"id": subtask["id"]}]},
                    "Parent task": {"relation": [{"id": task_page["id"]}]},
                },
            )
            subtask_ids.append(subtask_page["id"])
            print(f"Subtask created: {subtask_page['id']} for student: {subtask['name']}")

        # Update the main task to include the subtask relations
        notion.pages.update(
            page_id=task_page["id"],
            properties={
                "Sub-task": {
                    "relation": [{"id": subtask_id} for subtask_id in subtask_ids]
                }
            },
        )
        print(f"Main task updated with subtasks: {subtask_ids}")
    except APIResponseError as e:
        print(f"Failed to create task or subtask in Notion: {e}")
        st.error(f"Failed to create task or subtask in Notion: {e}")


# Streamlit UI
st.title("Teacher Absence Manager")

# Fetch teachers data once and store in session state
if "teachers_data" not in st.session_state:
    print("Fetching teachers data...")
    with st.spinner("Fetching teachers data..."):
        st.session_state.teachers_data = get_database_entries(teachers_db_id)
    print("Teachers data fetched and stored in session state.")

teachers_data = st.session_state.teachers_data

# Extract teacher names for dropdown
if teachers_data:
    try:
        print("Extracting teacher names for dropdown...")
        teacher_names = sorted(
            [
                teacher["properties"]["teacher"]["title"][0]["text"]["content"]
                for teacher in teachers_data
                if "properties" in teacher
                and "teacher" in teacher["properties"]
                and "title" in teacher["properties"]["teacher"]
                and teacher["properties"]["teacher"]["title"]
            ]
        )
        print(f"Teacher names extracted: {teacher_names}")

        # Select Teacher Dropdown
        selected_teacher = st.selectbox("Select Teacher", teacher_names)
        print(f"Selected teacher: {selected_teacher}")

        # Get current date and time in Australia/Melbourne time zone
        melbourne_tz = pytz.timezone("Australia/Melbourne")
        melbourne_now = datetime.now(melbourne_tz)
        tomorrow_date = melbourne_now + timedelta(days=1)
        print(f"Current time in Melbourne: {melbourne_now}, Tomorrow's date: {tomorrow_date}")

        # Date Picker for absence date with pre-selected date as tomorrow
        absence_date = st.date_input("Select Date of Absence", tomorrow_date.date())
        print(f"Selected absence date: {absence_date}")

        # Create Tasks button
        if st.button("Create Tasks"):
            print("Create Tasks button clicked.")
            with st.spinner("Creating tasks and subtasks..."):
                # Fetch students data
                students_data = get_database_entries(students_db_id)
                print(f"Fetched students data: {students_data}")
                subtasks = []

                for student in students_data:
                    try:
                        main_teacher = student["properties"].get("Main Teacher")
                        next_lesson = student["properties"].get("Next Lesson")

                        if (
                            main_teacher is None
                            or "rich_text" not in main_teacher
                            or not main_teacher["rich_text"]
                        ):
                            continue

                        main_teacher_name = main_teacher["rich_text"][0].get(
                            "plain_text", None
                        )
                        if main_teacher_name is None:
                            continue

                        if (
                            next_lesson is None
                            or "date" not in next_lesson
                            or next_lesson["date"] is None
                        ):
                            continue

                        next_lesson_date = next_lesson["date"].get("start", None)
                        if next_lesson_date is None:
                            continue

                        # Extract the date part of next_lesson_date
                        next_lesson_date = next_lesson_date.split("T")[0]

                        # Check if the teacher and date match the selected criteria
                        if (
                            main_teacher_name == selected_teacher
                            and next_lesson_date == str(absence_date)
                        ):
                            student_name = student["properties"]["Student"]["title"][0][
                                "text"
                            ]["content"]
                            subtasks.append({"name": student_name, "id": student["id"]})
                            print(f"Subtask added for student: {student_name}, ID: {student['id']}")
                    except (AttributeError, KeyError, TypeError) as e:
                        print(f"Skipping a student due to error: {e}")
                        continue

                if subtasks:
                    print(f"Subtasks to be created: {subtasks}")

                    # Create task and subtasks in Notion
                    create_task_in_notion(
                        f"{selected_teacher} - {absence_date}", subtasks
                    )
                    st.success("Tasks and subtasks created successfully - See \"Teacher Absences\" in Admin Dashboard.")
                else:
                    print("No students found for the selected teacher and date.")
                    st.info("No students found for the selected teacher and date.")
    except KeyError as e:
        print(f"Key error: {e}. Please check the structure of your Notion database.")
        st.error(f"Key error: {e}. Please check the structure of your Notion database.")
else:
    print("No teachers found in the database.")
    st.error("No teachers found in the database.")
