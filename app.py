from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# MongoDB setup
client = MongoClient("mongodb+srv://journal_user:journal123@cluster0.cxxqw5p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["journal_app"]
users_collection = db["users"]
entries_collection = db["entries"]

# Home - redirect based on login
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users_collection.find_one({'username': username}):
            return "Username already exists!"
        users_collection.insert_one({'username': username, 'password': password})
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

# Dashboard - show user's entries
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    search_query = request.args.get('q')
    filter_tag = request.args.get('tag')
    filter_date = request.args.get('date')

    query = {'username': username}
    if search_query:
        query['$or'] = [
            {'title': {'$regex': search_query, '$options': 'i'}},
            {'content': {'$regex': search_query, '$options': 'i'}}
        ]
    if filter_tag:
        query['tags'] = filter_tag
    if filter_date:
        query['date'] = filter_date

    entries = list(entries_collection.find(query))
    tags = entries_collection.distinct('tags', {'username': username})
    return render_template('dashboard.html', entries=entries, username=username, tags=tags)

# Add a journal entry
@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form.get('tags', '').split(',')
        date = request.form.get('date')
        entries_collection.insert_one({
            'username': session['username'],
            'title': title,
            'content': content,
            'tags': [tag.strip() for tag in tags if tag.strip()],
            'date': date
        })
        return redirect(url_for('dashboard'))
    return render_template('entry_form.html')

# Edit entry
@app.route('/edit/<entry_id>', methods=['GET'])
def edit_entry(entry_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    entry = entries_collection.find_one({'_id': ObjectId(entry_id), 'username': session['username']})
    if not entry:
        return "Entry not found"
    return render_template('entry_form.html', entry=entry)

@app.route('/update/<entry_id>', methods=['POST'])
def update_entry(entry_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    title = request.form['title']
    content = request.form['content']
    tags = request.form.get('tags', '').split(',')
    date = request.form.get('date')
    entries_collection.update_one(
        {'_id': ObjectId(entry_id), 'username': session['username']},
        {'$set': {
            'title': title,
            'content': content,
            'tags': [tag.strip() for tag in tags if tag.strip()],
            'date': date
        }}
    )
    return redirect(url_for('dashboard'))

# View full entry
@app.route('/entry/<entry_id>')
def view_entry(entry_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    entry = entries_collection.find_one({'_id': ObjectId(entry_id), 'username': session['username']})
    if not entry:
        return "Entry not found"
    return render_template('view_entry.html', entry=entry)

# Delete a journal entry
@app.route('/delete/<entry_id>', methods=['POST'])
def delete_entry(entry_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    entries_collection.delete_one({
        '_id': ObjectId(entry_id),
        'username': session['username']
    })
    return redirect(url_for('dashboard'))

# Profile page
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    total_entries = entries_collection.count_documents({'username': username})
    latest_entry = entries_collection.find({'username': username}).sort('date', -1).limit(1)
    return render_template('profile.html', username=username, total=total_entries, latest=list(latest_entry))

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 