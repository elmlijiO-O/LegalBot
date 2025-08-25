from flask import Flask, request, render_template
from classifier import classify_legal_query
import csv
import os
from datetime import datetime


app = Flask(__name__)
LOG_FILE = 'query_log.csv'
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'query', 'prediction', 'confidence', 'language'])


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():
    text = request.form.get('text', '')  

    if not text:
        return render_template('index.html', result={'error': 'No text provided'})

    try:
        result = classify_legal_query(text)
    except Exception as e:
        return render_template('index.html', result={'error': f'Error: {str(e)}'})


    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text, result['prediction'], result['confidence'], result['language']])
        
    # Pass result to template to display
    return render_template('index.html', result={
        'query': text,
        'category': result['prediction'],
        'confidence': result['confidence'],
        'language': result['language']
    })

if __name__ == '__main__':
    app.run(debug=True)
