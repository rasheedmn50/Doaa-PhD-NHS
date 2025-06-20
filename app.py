import streamlit as st
import requests
import pandas as pd
import gspread
from openai import OpenAI
from google.oauth2.service_account import Credentials
import json

# === 🔐 Load from secrets ===
GOOGLE_API_KEY = st.secrets["google"]["api_key"]
GOOGLE_CX = st.secrets["google"]["search_engine_id"]
OPENAI_API_KEY = st.secrets["openai_api_key"]
GOOGLE_SHEET_NAME = st.secrets["google"]["sheet_name"]
GCP_SERVICE_ACCOUNT = st.secrets["gcp_service_account"]

# === 🤖 OpenAI Client ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === Trusted Medical Sources ===
TRUSTED_SITES = [
    "site:nhs.uk",
    "site:nih.gov",
    "site:mayoclinic.org",
    "site:who.int",
    "site:cdc.gov",
    "site:clevelandclinic.org",
    "site:health.harvard.edu",
    "site:pubmed.ncbi.nlm.nih.gov",
    "site:webmd.com",
    "site:medlineplus.gov"
]

# === Google Search ===
def get_medical_snippets(query, num_results=5):
    domain_query = " OR ".join(TRUSTED_SITES)
    full_query = f"{query} ({domain_query})"
    params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": full_query, "num": num_results}
    try:
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        response.raise_for_status()
        items = response.json().get("items", [])
        items.sort(key=lambda x: 0 if "nhs.uk" in x.get("link", "") else 1)
        return [(item["title"], item["link"], item["snippet"]) for item in items]
    except Exception:
        return []

# === ChatGPT Answering ===
def answer_medical_question(question):
    snippets = get_medical_snippets(question)
    if not snippets:
        return "Sorry, I couldn't find reliable sources for this question right now.", []
    context = "\n".join(f"- **{title}**: {snippet}" for title, link, snippet in snippets)
    sources = [(title, link) for title, link, snippet in snippets]
    prompt = f"""
You are a helpful and friendly medical assistant.

Your job is to provide a clear and easy-to-understand answer using only the trusted snippets below. 
If the question describes symptoms, list possible causes, including both common and serious conditions where relevant. 
Use plain English with short sentences (5–7 sentences max). 
Avoid medical jargon, and explain in simple terms. 
Always include a safety reminder like "Talk to a doctor to be sure."

After the answer, include a short list of the sources used.

Snippets:
{context}

Question: {question}

Answer:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content.strip()
        return answer + "\n\n**Disclaimer:** This response is not a substitute for professional medical advice. Always consult your healthcare provider.", sources
    except Exception as e:
        return f"OpenAI API Error: {e}", []

# === Streamlit UI ===
st.set_page_config(page_title="AI Medical Assistant", page_icon="🩺", layout="centered")
st.title("🩺 AI-Powered Medical Assistant")
st.markdown("Ask your medical question and get a simple, reliable answer with trusted sources.")

if "history" not in st.session_state:
    st.session_state.history = []

user_age = st.sidebar.text_input("Your Age (optional)")
user_gender = st.sidebar.selectbox("Your Gender (optional)", ["Prefer not to say", "Male", "Female", "Other"])

tab1, tab2 = st.tabs(["🧠 Ask Question", "📜 History"])

with tab1:
    question = st.text_input("Enter your medical question:", placeholder="e.g. What are symptoms of vitamin D deficiency?")
    if st.button("Get Answer") and question:
        full_query = f"For a {user_age}-year-old {user_gender.lower()}, {question}" if user_age or user_gender != "Prefer not to say" else question
        with st.spinner("Searching trusted sources and generating response..."):
            answer, sources = answer_medical_question(full_query)

        st.markdown("### ✅ Answer")
        st.write(answer)
        if sources:
            st.markdown("### 📚 Sources")
            for title, link in sources:
                st.markdown(f"- [{title}]({link})")

        st.session_state.history.append({
            "Question": question,
            "Answer": answer,
            "Sources": sources
        })

with tab2:
    st.markdown("### 📜 Your Session History")
    if not st.session_state.history:
        st.info("You haven't asked any questions yet.")
    else:
        for i, entry in enumerate(reversed(st.session_state.history), 1):
            st.markdown(f"#### Q{i}: {entry['Question']}")
            st.markdown(f"**Answer:** {entry['Answer']}")
            st.markdown("**Sources:**")
            for title, link in entry["Sources"]:
                st.markdown(f"- [{title}]({link})")
            st.markdown("---")

        if st.button("📤 Export History to CSV"):
            flat_data = []
            for item in st.session_state.history:
                flat_data.append({
                    "Question": item["Question"],
                    "Answer": item["Answer"],
                    "Sources": "; ".join(link for _, link in item["Sources"])
                })
            df = pd.DataFrame(flat_data)
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, file_name="chat_history.csv", mime="text/csv")

# === Feedback Form ===
st.markdown("---")
st.markdown("### 💬 Leave Feedback")

creds = Credentials.from_service_account_info(GCP_SERVICE_ACCOUNT, scopes=[
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
gc = gspread.authorize(creds)
feedback_sheet = gc.open(GOOGLE_SHEET_NAME).sheet1

with st.form("feedback_form"):
    st.markdown("*(Optional)* Please rate your experience and provide feedback regarding the **accuracy of the information**, **reliability of the sources**, and your **overall experience** using this assistant.")
    
    # Star rating input
    rating = st.radio("How would you rate your experience?", ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], index=4, horizontal=True)
    
    # Feedback comments input
    comments = st.text_area("Your Feedback")
    
    if st.form_submit_button("Submit Feedback"):
        feedback_sheet.append_row([rating, comments])
        st.success("✅ Thank you for your feedback!")


# === Footer ===
st.markdown("---")
st.caption("Developed by Doaa Al-Turkey")
