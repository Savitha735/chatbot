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
    <title>Strata Assistant</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }
        .navbar {
            background-color: #2c3e50;
            color: #fff;
            padding: 15px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }
        .container {
            margin: 50px auto;
            width: 60%;
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        h2 {
            text-align: center;
            color: #333;
        }
        form {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: 70%;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-right: 10px;
        }
        input[type="submit"] {
            padding: 12px 20px;
            background-color: #2980b9;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        input[type="submit"]:hover {
            background-color: #3498db;
        }
        .answer {
            margin-top: 20px;
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            line-height: 1.6;
        }
    </style>
</head>
<body>

    <div class="navbar">Strata Assistant</div>

    <div class="container">
        <h2>Ask anything!</h2>
        <form method="post">
            <input type="text" name="question" placeholder="Type your question here..." required>
            <input type="submit" value="Ask">
        </form>

        {% if answer %}
        <div class="answer" style="white-space: pre-wrap;">
            <strong>Answer:</strong><br>
            {{ answer }}
        </div>

        {% endif %}
    </div>

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

        Based on this document, answer the following question in a clear, detailed, and ordered manner. 
        Please structure your answer as a numbered list of points or steps, if appropriate.

        Question:
        {question}
        """

        response = model.generate_content(prompt)
        lines = answer.split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        formatted_answer = ""
        for idx, line in enumerate(lines, start=1):
          formatted_answer += f"{idx}. {line}\n"
        answer = formatted_answer 
    return render_template_string(HTML_TEMPLATE, answer=answer)

if __name__ == "__main__":
    app.run(debug=True)
