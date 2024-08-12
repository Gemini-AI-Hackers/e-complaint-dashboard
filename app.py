import firebase_admin
from firebase_admin import credentials, firestore, auth
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from st_on_hover_tabs import on_hover_tabs
import streamlit as st
import os
from pandasai.llm import GoogleGemini
from pandasai import SmartDataframe
from pandasai.responses.response_parser import  ResponseParser
import matplotlib.pyplot as plt
from wordcloud import WordCloud

st.set_page_config(layout="wide")

class StreamLitResponse(ResponseParser):
        def __init__(self,context) -> None:
              super().__init__(context)
        def format_dataframe(self,result):
               st.dataframe(result['value'])
               return
        def format_plot(self,result):
               st.image(result['value'])
               return
        def format_other(self, result):
               st.write(result['value'])
               return

gemini_api_key = os.environ['Gemini']

def generateResponse(dataFrame,prompt):
        llm = GoogleGemini(api_key=gemini_api_key)
        pandas_agent = SmartDataframe(dataFrame,config={"llm":llm, "response_parser":StreamLitResponse})
        answer = pandas_agent.chat(prompt)
        return answer



# Initialize Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate("ecomplaintbook-firebase-adminsdk-4q5bo-1f83312d02.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

complaints_ref = db.collection('complaints')

complaints_list = []
for doc in complaints_ref.stream():
    a = doc.to_dict()
    complaints_list.append(a)

complaints_df = pd.DataFrame(complaints_list)

# Function to fetch user profile from Firebase
def fetch_user_profile_from_firebase(user_id):
    user_profile_ref = db.collection("users").document(user_id)
    user_profile = user_profile_ref.get().to_dict()
    return user_profile


# Function for user authentication
def user_authentication():
     # Add image and title
    st.image("ecomp.png", width=200)
    st.title("E-Complaint")

    st.header("Admin Dashboard")
    
   
        # If the user is an existing user, prompt for email and password
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        try:
            user = auth.get_user_by_email(email)
            st.success(f"Welcome back, {user.email}!")
            user_id = user.uid
            st.session_state.user_id = user_id
            st.rerun()
        except auth.UserNotFoundError:
            st.error("User not found. Please check your credentials or sign up.")
        except Exception as e:
                st.error(f"Error during sign-in: {e}")









# Main Streamlit app
def main():
    st.markdown('<style>' + open('./style.css').read() + '</style>', unsafe_allow_html=True)
    if "user_id" not in st.session_state:
        user_authentication()
        return

    
    st.title("E-Complaint")

    user_id = st.session_state.user_id


  

# Sidebar
    st.sidebar.title("E-complaint")
    st.sidebar.image("ecomp.png", use_column_width=True)

    with st.sidebar:
        tabs = on_hover_tabs(tabName=['Dashboard', 'Map', 'Chat'], 
                         iconName=['dashboard', 'map', 'chat'], default_choice=0)

    if tabs =='Dashboard':
        st.header("Complaints")

        # Create two columns
        col1, col2 = st.columns(2)
   
        with col1:
    # Pie Chart for Resolution Status
            fig, ax = plt.subplots()
            complaints_df['resolution_status'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax)
            ax.set_ylabel('')
            st.pyplot(fig)

    # Word Cloud for Complaint Description
        with col2:
            text = " ".join(complaints_df['complaint_description'])
            wordcloud = WordCloud(background_color='white', width=800, height=1000).generate(text)
            plt.figure(figsize=(8, 10))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            st.pyplot(plt)


        st.dataframe(complaints_df)

    elif tabs == 'Map':
        st.header("Google Maps view of eThekwini complaints")
        st.markdown("""" <iframe src="https://www.google.com/maps/d/u/0/embed?mid=16Fo-30K46Sq5NbHYW6d7pWtggO-QKAU&ehbc=2E312F" width="640" height="480"></iframe> """,
                    unsafe_allow_html=True)

    elif tabs == 'Chat':
        st.header("eThekwini Chat Powered by Gemini")
    

        # Display the data
        with st.expander("Preview"):
            st.write(complaints_df.head(3))

        # Plot the data
        user_input = st.text_input("Type your message here",placeholder="Ask me about complaints from eThekwini residents")
        if user_input:
            answer = generateResponse(dataFrame=complaints_df,prompt=user_input)
            st.write(answer)



       
    

    if st.button("Logout", key="logout_button"):
        del st.session_state["user_id"]
        st.rerun()

if __name__ == "__main__":
    main()