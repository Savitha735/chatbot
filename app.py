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
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Strata Assistant</title>
<style>
  /* Reset some default styles */
  * {
    box-sizing: border-box;
  }
  body {
    margin: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f0f2f5;
    color: #2c3e50;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  .navbar {
    background-color: #34495e;
    color: white;
    font-weight: 700;
    font-size: 1.8rem;
    padding: 1rem 0;
    text-align: center;
    letter-spacing: 1px;
    box-shadow: 0 3px 10px rgb(0 0 0 / 0.1);
  }
  .container {
    max-width: 700px;
    background: white;
    margin: 3rem auto 4rem auto;
    padding: 2.5rem 2rem;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgb(0 0 0 / 0.1);
  }
  h2 {
    margin-bottom: 1.5rem;
    font-weight: 700;
    font-size: 1.7rem;
    text-align: center;
    color: #2c3e50;
  }
  form {
    display: flex;
    gap: 0.8rem;
  }
  input[type="text"] {
    flex-grow: 1;
    padding: 0.9rem 1rem;
    font-size: 1rem;
    border: 2px solid #ddd;
    border-radius: 8px;
    transition: border-color 0.3s ease;
  }
  input[type="text"]:focus {
    outline: none;
    border-color: #2980b9;
    box-shadow: 0 0 6px #2980b9aa;
  }
  input[type="submit"] {
    padding: 0 1.3rem;
    background-color: #2980b9;
    color: white;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.3s ease;
  }
  input[type="submit"]:hover {
    background-color: #3498db;
  }
  .answer {
    margin-top: 2rem;
    background: #ecf0f1;
    border-radius: 10px;
    padding: 1.5rem 2rem;
    white-space: pre-wrap;
    line-height: 1.6;
    font-size: 1.1rem;
    color: #34495e;
  }
  /* Style bullets nicely */
  .answer ul {
    padding-left: 1.3rem;
    margin-top: 1rem;
  }
  .answer ul li {
    margin-bottom: 0.6rem;
  }

  /* Responsive */
  @media (max-width: 600px) {
    .container {
      margin: 2rem 1rem 3rem 1rem;
      padding: 1.8rem 1.5rem;
    }
    input[type="text"] {
      font-size: 0.9rem;
    }
    input[type="submit"] {
      font-size: 0.9rem;
      padding: 0 1rem;
    }
  }
</style>
</head>
<body>

<div class="navbar">Strata Assistant</div>

<div class="container">
  <h2>Ask anything!</h2>
  <form method="post">
    <input type="text" name="question" placeholder="Type your question here..." required autocomplete="off" />
    <input type="submit" value="Send" />
  </form>

  {% if answer %}
  <div class="answer">
    <strong>Answer:</strong>
    <br>
    {{ answer | safe }}
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
        **Do not use any HTML tags in your response. Only plain text.**
        
        Question:
        {question}
        """

        import re

        try:
           response = model.generate_content(prompt)
           answer = response.text

    # Remove any HTML tags
           answer = re.sub(r'<.*?>', '', answer)

    # Split and clean
           lines = answer.split("\n")
           cleaned_lines = []
           for line in lines:
              line = line.strip()
              if not line:
                continue
        # Remove starting numbering or bullets
              line = re.sub(r"^\s*\d+[\.\)]\s*", "", line)
              line = re.sub(r"^[\*\-]\s*", "", line)
              cleaned_lines.append(line)

    # ✅ Remove first line if it's an introduction
           if cleaned_lines and "topic" in cleaned_lines[0].lower():
              cleaned_lines = cleaned_lines[1:]

    # Add new numbering
           formatted_answer = ""
           for idx, line in enumerate(cleaned_lines, start=1):
              if idx == 1:
                 formatted_answer += f"{line}\n"  # First line without numbering
              else:
                 formatted_answer += f" • {line}\n"  # Numbering starts from 1 for the second line onwards
           answer = formatted_answer


        except Exception as e:
           answer = f"An error occurred: {str(e)}"
        
    return render_template_string(HTML_TEMPLATE, answer=answer)

if __name__ == "__main__":
    app.run(debug=True)
