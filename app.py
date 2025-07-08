from flask import Flask, request, render_template_string
import google.generativeai as genai
import PyPDF2
import requests
from io import BytesIO

app = Flask(__name__)

# 💡 Configure Gemini
genai.configure(api_key="AIzaSyBZMgmYKkduWGWp_USHQ4SsiPOw1glOCmg")

# 📄 Your Google Drive PDF link (change FILE_ID)
pdf_drive_link = "https://drive.google.com/uc?export=download&id=1FNkl1Ny-mIKlxSLzWtwlUq-Hk9h4tD33"

# 📥 Function to download and extract PDF text
def extract_pdf_text(pdf_url):
    response = requests.get(pdf_url)
    pdf_file = BytesIO(response.content)

    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# 📝 Load the PDF text once when app starts
pdf_text = extract_pdf_text(pdf_drive_link)

# Create Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# 🔥 Web UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF Chatbot</title>
</head>
<body>
    <h2>Ask something from the PDF</h2>
    <form method="post">
        <input type="text" name="question" style="width: 400px;" required>
        <input type="submit" value="Ask">
    </form>
    {% if answer %}
        <h3>Answer:</h3>
        <p>{{ answer }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def chatbot():
    answer = None
    if request.method == "POST":
        question = request.form["question"]
        
        # Create prompt combining PDF content and question
        prompt = f"""
        You are an expert assistant. The following is content from a PDF document:

        {pdf_text[:12000]}  # Limit context to 12,000 characters to stay within prompt limits

        Based on this document, answer the question:
        {question}
        """

        response = model.generate_content(prompt)
        answer = response.text

    return render_template_string(HTML_TEMPLATE, answer=answer)

if __name__ == "__main__":
    app.run(debug=True)