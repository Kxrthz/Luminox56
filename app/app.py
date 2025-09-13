from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3
import datetime
import random
import re
import json
import hashlib

app = Flask(__name__)
app.secret_key = 'luminox_secret_key_2024_auth'

# Profanity filter
PROFANITY_WORDS = ['damn', 'hell', 'stupid', 'idiot', 'hate', 'kill', 'die', 'murder', 'fuck', 'shit', 'bitch', 'asshole', 'bastard', 'crap']

def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            anon_id TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            emoji_reactions TEXT DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            anon_id TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            post_id INTEGER,
            comment_id INTEGER,
            vote_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create default admin user if it doesn't exist
    admin_email = 'admin@luminox.com'
    admin_password = hash_password('admin123')
    cursor.execute('SELECT id FROM users WHERE email = ?', (admin_email,))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (email, username, password_hash, role) 
            VALUES (?, ?, ?, ?)
        ''', (admin_email, 'admin', admin_password, 'admin'))
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_anon_id():
    """Generate a random anonymous ID"""
    return f"Anon #{random.randint(1000, 9999)}"

def filter_profanity(text):
    """Basic profanity filter"""
    words = text.lower().split()
    for word in words:
        clean_word = re.sub(r'[^a-zA-Z]', '', word)
        if clean_word in PROFANITY_WORDS:
            return False
    return True

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def home():
    """Landing page with login options"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and user['password_hash'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not all([email, username, password, confirm_password]):
            flash('Please fill in all fields', 'error')
            return render_template('login.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('login.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('login.html')
        
        conn = get_db_connection()
        
        # Check if email or username already exists
        existing = conn.execute('SELECT id FROM users WHERE email = ? OR username = ?', (email, username)).fetchone()
        if existing:
            flash('Email or username already exists', 'error')
            conn.close()
            return render_template('login.html')
        
        # Create new user
        password_hash = hash_password(password)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (email, username, password_hash, role) 
            VALUES (?, ?, ?, ?)
        ''', (email, username, password_hash, 'user'))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Auto login
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = 'user'
        
        flash('Registration successful! Welcome to Luminox!', 'success')
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def index():
    """Main confession board"""
    category = request.args.get('category', 'All')
    sort_by = request.args.get('sort', 'newest')
    
    conn = get_db_connection()
    
    if category == 'All':
        if sort_by == 'trending':
            posts = conn.execute('SELECT * FROM posts ORDER BY (upvotes - downvotes) DESC, timestamp DESC LIMIT 50').fetchall()
        else:
            posts = conn.execute('SELECT * FROM posts ORDER BY timestamp DESC LIMIT 50').fetchall()
    else:
        if sort_by == 'trending':
            posts = conn.execute('SELECT * FROM posts WHERE category = ? ORDER BY (upvotes - downvotes) DESC, timestamp DESC LIMIT 50', (category,)).fetchall()
        else:
            posts = conn.execute('SELECT * FROM posts WHERE category = ? ORDER BY timestamp DESC LIMIT 50', (category,)).fetchall()
    
    posts_with_comments = []
    for post in posts:
        comment_count = conn.execute('SELECT COUNT(*) as count FROM comments WHERE post_id = ?', (post['id'],)).fetchone()['count']
        posts_with_comments.append({
            'id': post['id'],
            'anon_id': post['anon_id'],
            'content': post['content'],
            'category': post['category'],
            'timestamp': post['timestamp'],
            'upvotes': post['upvotes'],
            'downvotes': post['downvotes'],
            'comment_count': comment_count,
            'score': post['upvotes'] - post['downvotes']
        })
    
    conn.close()
    
    categories = ['All', 'General', 'Funny', 'Exam Stress', 'Love', 'Family', 'Work', 'Other']
    
    return render_template('index.html', 
                         posts=posts_with_comments, 
                         categories=categories,
                         current_category=category,
                         current_sort=sort_by)

@app.route('/post/<int:post_id>')
@login_required
def view_post(post_id):
    """View individual post"""
    conn = get_db_connection()
    
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if not post:
        flash('Post not found!', 'error')
        conn.close()
        return redirect(url_for('index'))
    
    comments = conn.execute('SELECT * FROM comments WHERE post_id = ? ORDER BY timestamp DESC', (post_id,)).fetchall()
    conn.close()
    
    return render_template('post.html', post=post, comments=comments)

@app.route('/admin')
@admin_required
def admin_panel():
    """Admin panel"""
    conn = get_db_connection()
    
    # Get statistics
    total_posts = conn.execute('SELECT COUNT(*) as count FROM posts').fetchone()['count']
    total_comments = conn.execute('SELECT COUNT(*) as count FROM comments').fetchone()['count']
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = "user"').fetchone()['count']
    
    # Get recent posts
    recent_posts = conn.execute('SELECT * FROM posts ORDER BY timestamp DESC LIMIT 20').fetchall()
    
    # Get all users
    users = conn.execute('SELECT id, email, username, role, created_at FROM users ORDER BY created_at DESC').fetchall()
    
    conn.close()
    
    return render_template('admin.html', 
                         total_posts=total_posts,
                         total_comments=total_comments,
                         total_users=total_users,
                         recent_posts=recent_posts,
                         users=users)

@app.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    """Create new post"""
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        category = data.get('category', 'General')
        
        if not content:
            return jsonify({'success': False, 'message': 'Content cannot be empty'})
        
        if len(content) > 1000:
            return jsonify({'success': False, 'message': 'Content too long (max 1000 characters)'})
        
        if not filter_profanity(content):
            return jsonify({'success': False, 'message': 'Content contains inappropriate language'})
        
        anon_id = generate_anon_id()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO posts (user_id, anon_id, content, category) VALUES (?, ?, ?, ?)', 
                      (session['user_id'], anon_id, content, category))
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Confession posted successfully!', 'post_id': post_id})
    except Exception as e:
        print(f"Error in create_post: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@app.route('/api/vote', methods=['POST'])
@login_required
def vote():
    """Handle voting"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        comment_id = data.get('comment_id')
        vote_type = data.get('vote_type')
        user_id = session['user_id']
        
        if vote_type not in ['up', 'down']:
            return jsonify({'success': False, 'message': 'Invalid vote type'})
        
        conn = get_db_connection()
        
        if post_id:
            existing_vote = conn.execute('SELECT * FROM votes WHERE user_id = ? AND post_id = ?', (user_id, post_id)).fetchone()
        else:
            existing_vote = conn.execute('SELECT * FROM votes WHERE user_id = ? AND comment_id = ?', (user_id, comment_id)).fetchone()
        
        if existing_vote:
            conn.close()
            return jsonify({'success': False, 'message': 'You have already voted'})
        
        cursor = conn.cursor()
        if post_id:
            cursor.execute('INSERT INTO votes (user_id, post_id, vote_type) VALUES (?, ?, ?)', (user_id, post_id, vote_type))
            if vote_type == 'up':
                cursor.execute('UPDATE posts SET upvotes = upvotes + 1 WHERE id = ?', (post_id,))
            else:
                cursor.execute('UPDATE posts SET downvotes = downvotes + 1 WHERE id = ?', (post_id,))
            post = conn.execute('SELECT upvotes, downvotes FROM posts WHERE id = ?', (post_id,)).fetchone()
            upvotes, downvotes = post['upvotes'], post['downvotes']
        else:
            cursor.execute('INSERT INTO votes (user_id, comment_id, vote_type) VALUES (?, ?, ?)', (user_id, comment_id, vote_type))
            if vote_type == 'up':
                cursor.execute('UPDATE comments SET upvotes = upvotes + 1 WHERE id = ?', (comment_id,))
            else:
                cursor.execute('UPDATE comments SET downvotes = downvotes + 1 WHERE id = ?', (comment_id,))
            comment = conn.execute('SELECT upvotes, downvotes FROM comments WHERE id = ?', (comment_id,)).fetchone()
            upvotes, downvotes = comment['upvotes'], comment['downvotes']
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'upvotes': upvotes, 'downvotes': downvotes, 'score': upvotes - downvotes})
    except Exception as e:
        print(f"Error in vote: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@app.route('/api/comments', methods=['POST'])
@login_required
def add_comment():
    """Add comment"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'message': 'Comment cannot be empty'})
        
        if len(content) > 500:
            return jsonify({'success': False, 'message': 'Comment too long (max 500 characters)'})
        
        if not filter_profanity(content):
            return jsonify({'success': False, 'message': 'Content contains inappropriate language'})
        
        anon_id = generate_anon_id()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comments (post_id, user_id, anon_id, content) VALUES (?, ?, ?, ?)', 
                      (post_id, session['user_id'], anon_id, content))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Comment added successfully!'})
    except Exception as e:
        print(f"Error in add_comment: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@app.route('/api/emoji', methods=['POST'])
@login_required
def add_emoji_reaction():
    """Add emoji reaction"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        emoji = data.get('emoji')
        
        if not emoji or not post_id:
            return jsonify({'success': False, 'message': 'Invalid reaction'})
        
        conn = get_db_connection()
        post = conn.execute('SELECT emoji_reactions FROM posts WHERE id = ?', (post_id,)).fetchone()
        
        if not post:
            conn.close()
            return jsonify({'success': False, 'message': 'Post not found'})
        
        try:
            reactions = json.loads(post['emoji_reactions'])
        except:
            reactions = {}
        
        if emoji in reactions:
            reactions[emoji] += 1
        else:
            reactions[emoji] = 1
        
        cursor = conn.cursor()
        cursor.execute('UPDATE posts SET emoji_reactions = ? WHERE id = ?', (json.dumps(reactions), post_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'reactions': reactions})
    except Exception as e:
        print(f"Error in add_emoji_reaction: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@app.route('/api/admin/delete_post/<int:post_id>', methods=['DELETE'])
@admin_required
def delete_post(post_id):
    """Delete post (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete related comments first
        cursor.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
        # Delete related votes
        cursor.execute('DELETE FROM votes WHERE post_id = ?', (post_id,))
        # Delete the post
        cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Post deleted successfully'})
    except Exception as e:
        print(f"Error in delete_post: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@app.route('/api/admin/delete_all_posts', methods=['DELETE'])
@admin_required
def delete_all_posts():
    """Delete all posts (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete all comments
        cursor.execute('DELETE FROM comments')
        # Delete all votes
        cursor.execute('DELETE FROM votes')
        # Delete all posts
        cursor.execute('DELETE FROM posts')
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'All posts deleted successfully'})
    except Exception as e:
        print(f"Error in delete_all_posts: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})
    
if __name__ == '__main__':
    init_db()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)