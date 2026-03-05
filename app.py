from flask import Flask
from flask import render_template
from flask import request,redirect,url_for

app = Flask(__name__)

logs = []
next_id = 1

@app.route('/', methods=['GET', 'POST'])
def home():
    global next_id

    if request.method == 'POST':
        study_time = request.form['time']
        content = request.form['content']

        if study_time and content:
            logs.append({
                "id": next_id,
                "time": study_time,
                "content": content
            })
            next_id += 1

        return redirect(url_for('home'))
            
        # Handle form submission here
        
    

    return render_template('index.html', logs=logs)

@app.route("/delete/<int:log_id>", methods=["POST"])
def delete(log_id):
    global logs
    logs = [log for log in logs if log["id"] != log_id]
    return redirect(url_for("home"))

@app.route("/add")
def add():
    return "<h2>Add Study Log Page</h2>"

if __name__ == '__main__':
    app.run(debug=True)