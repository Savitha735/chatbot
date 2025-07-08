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
        .qa-block {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .question {
            font-weight: bold;
        }
        .answer {
            margin-top: 5px;
        }
        .clear-btn {
            margin-top: 20px;
            display: block;
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
        }
        .clear-btn:hover {
            background-color: #c0392b;
        }
    </style>
</head>
<body>

    <div class="navbar">Strata Assistant</div>

    <div class="container">
        <h2>Ask anything!</h2>
        <form id="chat-form" method="post">
            <input type="text" id="question-input" name="question" placeholder="Type your question here..." required>
            <input type="submit" value="Ask">
        </form>

        <div id="history"></div>

        <button class="clear-btn" onclick="clearHistory()">Clear History</button>
    </div>

    <script>
        // Load existing history
        function loadHistory() {
            const history = JSON.parse(localStorage.getItem("qa_history")) || [];
            const historyDiv = document.getElementById("history");
            historyDiv.innerHTML = "";
            history.forEach(qa => {
                const block = document.createElement("div");
                block.className = "qa-block";
                block.innerHTML = "<div class='question'>Q: " + qa.question + "</div><div class='answer'>A: " + qa.answer + "</div>";
                historyDiv.appendChild(block);
            });
        }

        // Save new QA to local storage
        function saveQA(question, answer) {
            const history = JSON.parse(localStorage.getItem("qa_history")) || [];
            history.push({question: question, answer: answer});
            localStorage.setItem("qa_history", JSON.stringify(history));
        }

        // Clear history
        function clearHistory() {
            localStorage.removeItem("qa_history");
            loadHistory();
        }

        // After submitting, save and reload
        document.getElementById("chat-form").addEventListener("submit", function(e) {
            const questionInput = document.getElementById("question-input");
            const question = questionInput.value;
            const form = this;
            // Wait until the server returns
            setTimeout(() => {
                const answer = "{{ answer | safe }}";
                if (answer.trim() !== "") {
                    saveQA(question, answer);
                    loadHistory();
                    questionInput.value = "";
                }
            }, 500);
        });

        // Load on start
        window.onload = loadHistory;
    </script>

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
