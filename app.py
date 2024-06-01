import streamlit as st
import requests

# URL of your Google Cloud Function
url = "https://us-central1-alexberishltd.cloudfunctions.net/function-1"

def submit_form(data):
    response = requests.post(url, json=data)
    return response

st.title("Music Lesson Enquiry Form")

with st.form(key='music_lesson_form'):
    # Name fields
    st.subheader("Name (required)")
    first_name = st.text_input("First Name", placeholder="Enter your first name")
    last_name = st.text_input("Last Name", placeholder="Enter your last name (optional)", value="")

    # Email field
    st.subheader("Email (required)")
    email = st.text_input("Email", placeholder="Enter your email")

    # Phone number field
    st.subheader("Phone Number (required)")
    phone_number = st.text_input("Phone Number", placeholder="Enter your phone number")

    # Lesson types checkboxes
    st.subheader("Music Lesson Type/s (required)")
    st.write("What do you want to learn?")
    lesson_types = st.multiselect(
        '',
        [
            "Acoustic Guitar", "Electric Guitar", "Bass Guitar", 
            "Piano / Keyboard", "Voice (contemporary or classical)", 
            "Drums", "Cello", "Clarinet", "Flute", "Violin", 
            "Songwriting", "Saxophone", "Music production", 
            "Guitar for Singers & Songwriters", "Duo / Group Lessons", 
            "Bands / Ensemble Participation"
        ]
    )

    # Student type field
    st.subheader("Student Type (required)")
    student_type = st.selectbox(
        '',
        ["", "Child Student (under 18)", "Adult Student (over 18)"],
        format_func=lambda x: "Select an option" if x == "" else x
    )

    # Level field
    st.subheader("Level")
    level = st.selectbox(
        '',
        ["", "Beginner", "Intermediate", "Advanced"],
        format_func=lambda x: "Select an option" if x == "" else x
    )

    # Message field
    st.subheader("Message (required)")
    st.write("Tell us more about you! Include any relevant experience you have with music or your chosen instrument, preferred styles, etc.")
    message = st.text_area("Message", placeholder="Enter your message here")

    # How did you hear about us field
    st.subheader("How did you hear about us? (required)")
    how_heard = st.multiselect(
        '',
        [
            "Google/search engine", "Social media", 
            "Family/friend referral", 
            "Walked past us on the street!"
        ]
    )

    # Submit button
    submit_button = st.form_submit_button(label='Submit')

if submit_button:
    if not (first_name and email and phone_number and lesson_types and student_type and message and how_heard):
        st.error("Please fill out all required fields.")
    else:
        data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phoneNumber": phone_number,
            "lessonTypes": ", ".join(lesson_types),  # Joining multiple selections
            "studentType": student_type,
            "level": level,
            "message": message,
            "howHeard": ", ".join(how_heard)  # Joining multiple selections
        }
        response = submit_form(data)

        if response.status_code == 200:
            st.success("Form submitted successfully!")
        else:
            st.error(f"Error submitting form: {response.json()}")