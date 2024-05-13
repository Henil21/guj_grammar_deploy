from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'  # SQLite database
app.config['SQLALCHEMY_BINDS'] = {
    'submit_data': 'sqlite:///datasamples.db'
}
db = SQLAlchemy(app)

import requests

API_URL = "https://api-inference.huggingface.co/models/Jayveersinh-Raj/guj-grammar-base"
headers = {"Authorization": "Bearer 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"}

def query(payload, max_length=500, max_retries=20):
    for _ in range(max_retries):
        data = {
            "inputs": payload["inputs"],
            "parameters": {"max_length": max_length},
        }
        response = requests.post(API_URL, headers=headers, json=data)
        
        # Check if the response has the expected structure
        if isinstance(response.json(), list) and response.json():
            return response.json()[0].get("generated_text", "Error: No generated text")
    
    return "Error: Model is still loading or encountered an issue please try again"
    

# Define Model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    feedback_text = db.Column(db.String(200), nullable = False)
    name = db.Column(db.String(100), nullable = True)

    def __repr__(self):
        return f"Feedback: {self.feedback_text}\nName: {self.name}"
    
# Define Model for Submit Data
class SubmitData(db.Model):
    __bind_key__ = 'submit_data'  # Binding to another database
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    incorrect_sentence = db.Column(db.String(500), nullable=False)
    correct_sentence = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"Incorrect Sentence: {self.incorrect_sentence}\nCorrect Sentence: {self.correct_sentence}"

with app.app_context():
    db.create_all() 

# Routes...
@app.route('/view_feedback')
def view_feedback():
    feedback_entries = Feedback.query.all()
    return render_template('view_feedback.html', feedback_entries=feedback_entries)

@app.route('/view_data')
def view_data():
    submitted_samples = SubmitData.query.all()
    return render_template('view_data.html', submitted_samples=submitted_samples)

# Handle Form Submission
@app.route('/feedback', methods=['GET', 'POST'])
def submit_feedback():
    if request.method == 'POST':
        feedback_text = request.form['feedback']
        name = request.form.get('name', '')  # Optional field

        # Create Feedback instance
        feedback = Feedback(feedback_text=feedback_text, name=name)

        # Add to database session and commit
        db.session.add(feedback)
        try:
            db.session.commit()
            return "Feedback added successfully"
        except Exception as e:
            db.session.rollback()
            return f"Commit failed exception: {e}"

    # If the request method is GET, render the feedback form HTML
    return render_template('feedback.html')

# Submit Data route
@app.route('/submit_data', methods=['GET', 'POST'])
def submit_data():
    if request.method == 'POST':
        incorrect_sentence = request.form['incorrect_sentence']
        correct_sentence = request.form['correct_sentence']

        # Create SubmitData instance
        data = SubmitData(incorrect_sentence=incorrect_sentence, correct_sentence=correct_sentence)

        # Add to database session and commit
        db.session.add(data)
        try:
            db.session.commit()
            return "Data submitted successfully"
        except Exception as e:
            db.session.rollback()
            return f"Commit failed exception: {e}"
    
    # If the request method is GET, render the submit data form HTML
    return render_template('submit_data.html')

   

# Route for the About Us page
@app.route('/about')
def about():
    return render_template('about.html')

# Home route
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # input_text = request.form['input_text']
        no_words = request.form['no_words']
        sentences = no_words.split(".")
        output = ""

        for sent in sentences:
           output+=query({"inputs":"<gec>"+ sent})
           
        return render_template('index.html', no_words=no_words,response=output)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
