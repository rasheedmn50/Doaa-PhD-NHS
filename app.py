import streamlit as st
import requests
import pandas as pd
import gspread
import json
from openai import OpenAI
from google.oauth2.service_account import Credentials

# === 🔐 API Keys ===
GOOGLE_API_KEY = "AIzaSyDXGkFH3sig39QGRKC_4ZKbyJnUshAIhQc"
GOOGLE_CX = "448129f9a26b540b0"
OPENAI_API_KEY = "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"

# === 📄 Google Sheets Feedback Setup ===
GOOGLE_SHEET_NAME = "App Feedback"
GOOGLE_SHEETS_CREDENTIALS = """
{
  "type": "service_account",
  "project_id": "doaa-phd",
  "private_key_id": "8593770af97b13b27737e0eb2d93be5913452f36",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDqKJtQLgY2Gltt\\nM13K4YwklkJ0XmA5VWhLLJ2htM2qaldikkMWktyA8w852dXlTlyLJDZnbQ+pW62i\\nWkXEJ5er8DTQ6YFPl2BcF7O8RHqmbRrZLnhjFRYiXtr69zmPldFBGLOipR6nt6FK\\nSdqA1c+l5hJRNAlQwr+hsr/jvJ3XX2k9lyyqwZq/FDVHgZeEUES/6T34DMvX2XZX\\nQR9WfbCTwc5kHgQfKFixFiyhh31a2pgS5xuprMocgDW/16d9pYDESdT/6UROW3kG\\n3UR3jZWBqJ/xbjOsZWds4ESeJlnW6mChVNrbJaV2F8Zwq7YXtRODbiPUxVkFrZZx\\n9dh8j/YdAgMBAAECggEAF4AASF16G5ttEgpN7zLQJwrafAXNt+tRpnvBjS1RV7lI\\n8FhX+c++6AUcwdRSImuJH6DAggRAxmEwTaMsLcnAb83RaycIJoX9cnihffNMcN/x\\nyhqfE+iVmlj1NqsxoG6re9JAEwJpz3C/M+6yCmyK5K4wp+wmRC/rXg3Lss4m9CqK\\nvkeb9LUxiJmoFvdsU8JE8JpkOACxkfpKH7ZnIHPyLRLCPqtckHweIeJem4OL/UZY\\n2tGokKpS5nlhRswRONmkfdsRfmp63zdg1K6fuXFvpYJ2YkCWdzXm4sHlw4fRxHUp\\niNZmqvSL1h5KCS/ID/QNwYXR+r/7X2lEJiwMLtMzyQKBgQD+QrhMgG99wsf+CE7K\\niQwIIMpNqfgqtte+dnf6y0afqq0irxUqEuaJPtVBPlUgcQVVqh4gl3gVr4WB2xCi\\n5g10DRGXY6xZsj+RokngIihPXtn4de27E/praCPDgifosin6rk1GR0M50dDnc7qt\\nfa2JEvVEKM1r1H0Bi4umMVY6yQKBgQDrwq7CQscGkJLVHCER7MEttaxKgFAZdaDx\\nw8mqKzYHlAJp5I3jTr0SZuDoquAZ4Iv5USYvIGC5Gq1uxV0Zv9+xHNy9pRz6vD+1\\n179yEgjmFBcpEKR5p3TqYXAIC45LxIKDMwKeHAQEr76FaPAW++T4SLrTuE7pmxJg\\nM7dQ/6I2tQKBgQDCyhqngT3o+vB8jaDPSW8OSxCxryWQk8N1Bw2j9VeFuxwpFjkA\\noro7Kwf1k+tjjzKnDk1GasR02KNPeKSmJ9jmr5xqftHrZcONrucp7wEyzVfwIWif\\nig6venjrrysj+lpu0lohHTdDdJq2ttKtVzs7aGq+bQPzODcMl/vEtsd5AQKBgGTn\\n9IhssGac5luUKItVe/EmetGATcg30mTn2Z6d1Ag2Tzoneps5ji8cHVM4H6aztvVE\\nyEUPZJaVVnm8u3ZT61gQ9GGvE9I1VEduSiB2m5xuKOOInfz7sUzH2312BLdlKj8h\\nTBOEBixDVBYhrfEIax3hcyU/E3dkyd6nA+UFJNapAoGACoM2vvJExfXgE73N2WDi\\nV/o7vGN4VpfaSylw/lys8JHCoxoDkwRvtESYwk4JL8m0EehNKo4FP+2FJ8OKC+LQ\\ntWEQv05T+gkGEp0K31wL2UuPQOHiwCSVds0m2CHiyy7LZeC4IDXYfXFD/wc/khKF\\nGro6quMkul+WMRwqxZ8/mM0=\\n-----END PRIVATE KEY-----\\n",
  "client_email": "streamlit-feedback-writer@doaa-phd.iam.gserviceaccount.com",
  "client_id": "104197787504251349745",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-feedback-writer%40doaa-phd.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
"""

# === 🔎 Trusted Medical Sources ===
TRUSTED_SITES = [
    "site:nhs.uk",  # NHS prioritized
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

# === 🤖 OpenAI Client ===
client = OpenAI(api_key="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")

# === Google Custom Search ===
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
    except Exception as e:
        return []

# === ChatGPT Answering ===
def answer_medical_question(question):
    snippets = get_medical_snippets(question)
    if not snippets:
        return "Sorry, I couldn't find reliable sources for this question right now.", []
    context = "\n".join(f"- **{title}**: {snippet}" for title, link, snippet in snippets)
    sources = [(title, link) for title, link, snippet in snippets]

    prompt = f"""You are a helpful medical assistant. Use only the following trusted sources to answer the user's question in simple English (5–6 short sentences). List the sources at the end.

Snippets:
{context}

Question: {question}
Answer:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content.strip()
        return answer, sources
    except Exception as e:
        return f"OpenAI API Error: {e}", []

# === Streamlit App ===
st.set_page_config(page_title="AI Medical Assistant", page_icon="🩺", layout="centered")
st.title("🩺 AI-Powered Medical Assistant")
st.markdown("Ask your medical question and get a simple, reliable answer with trusted sources.")

if "history" not in st.session_state:
    st.session_state.history = []

tab1, tab2 = st.tabs(["🧠 Ask Question", "📜 History"])

with tab1:
    question = st.text_input("Enter your medical question:", placeholder="e.g. What are symptoms of vitamin D deficiency?")
    if st.button("Get Answer") and question:
        with st.spinner("Searching trusted sources and generating response..."):
            answer, sources = answer_medical_question(question)

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

# === Feedback Section ===
st.markdown("---")
st.markdown("### 💬 Leave Feedback")

gcred = json.loads(GOOGLE_SHEETS_CREDENTIALS)
scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(gcred, scopes=scopes)
gc = gspread.authorize(creds)
feedback_sheet = gc.open(GOOGLE_SHEET_NAME).sheet1

with st.form("feedback_form"):
    name = st.text_input("Your name")
    comments = st.text_area("Your feedback")
    if st.form_submit_button("Submit Feedback"):
        feedback_sheet.append_row([name, comments])
        st.success("✅ Thank you for your feedback!")

# === Footer ===
st.markdown("---")
st.caption("Developed by Doaa Al-Turkey")
