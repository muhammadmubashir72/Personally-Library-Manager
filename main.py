import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import random
import json

# Set page configuration
st.set_page_config(
    page_title="Personal Library Manager",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better design
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .stExpander {
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .book-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
    }
    .book-card:hover {
        transform: translateY(-5px);
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .css-1d391kg {
        padding-top: 3.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e0e5f0;
    }
    .stProgress > div > div {
        background-color: #1E3A8A;
    }
    .goal-card {
        background-color: #e0e5f0;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .stat-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .wishlist-item {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1E3A8A;
    }
    .loan-card {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #e63946;
    }
    .collection-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        background-color: #1E3A8A;
        color: white;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #152a5f;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Books table
    c.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        genre TEXT,
        status TEXT,
        rating INTEGER,
        date_added TEXT,
        notes TEXT,
        cover_image BLOB,
        total_pages INTEGER,
        pages_read INTEGER,
        isbn TEXT,
        publication_year INTEGER,
        publisher TEXT,
        collections TEXT
    )
    ''')
    
    # Wishlist table
    c.execute('''
    CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        priority TEXT,
        notes TEXT,
        date_added TEXT
    )
    ''')
    
    # Loans table
    c.execute('''
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        borrower_name TEXT NOT NULL,
        date_loaned TEXT,
        expected_return_date TEXT,
        returned BOOLEAN,
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
    ''')
    
    # Reading goals table
    c.execute('''
    CREATE TABLE IF NOT EXISTS reading_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER,
        target_books INTEGER,
        target_pages INTEGER
    )
    ''')
    
    # Collections table
    c.execute('''
    CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        date_created TEXT
    )
    ''')
    
    # Reading history table
    c.execute('''
    CREATE TABLE IF NOT EXISTS reading_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        date_started TEXT,
        date_finished TEXT,
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Image handling functions
def convert_image_to_bytes(uploaded_file):
    if uploaded_file is not None:
        try:
            # Open the uploaded image
            image = Image.open(uploaded_file)
            
            # Resize image to save space
            max_size = (300, 450)
            image.thumbnail(max_size)
            
            # Convert to bytes
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=80)
            img_bytes = buffered.getvalue()
            return img_bytes
        except Exception as e:
            st.error(f"Error processing image: {e}")
            return None
    return None

def get_image_base64(image_bytes):
    if image_bytes:
        encoded = base64.b64encode(image_bytes).decode()
        return f"data:image/jpeg;base64,{encoded}"
    return None

# Database operations for books
def add_book(title, author, genre, status, rating, notes, cover_image, total_pages, pages_read, isbn, publication_year, publisher, collections):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    date_added = datetime.now().strftime("%Y-%m-%d")
    
    # Convert collections list to JSON string
    collections_json = json.dumps(collections) if collections else "[]"
    
    c.execute('''
    INSERT INTO books (title, author, genre, status, rating, date_added, notes, cover_image, 
                      total_pages, pages_read, isbn, publication_year, publisher, collections)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, author, genre, status, rating, date_added, notes, cover_image, 
         total_pages, pages_read, isbn, publication_year, publisher, collections_json))
    
    book_id = c.lastrowid
    
    # If status is "Read", add to reading history
    if status == "Read":
        c.execute('''
        INSERT INTO reading_history (book_id, date_started, date_finished)
        VALUES (?, ?, ?)
        ''', (book_id, date_added, date_added))
    # If status is "Currently Reading", add start date
    elif status == "Currently Reading":
        c.execute('''
        INSERT INTO reading_history (book_id, date_started)
        VALUES (?, ?)
        ''', (book_id, date_added))
    
    conn.commit()
    conn.close()
    return book_id

def get_all_books():
    conn = sqlite3.connect('library.db')
    books = pd.read_sql_query("SELECT * FROM books", conn)
    conn.close()
    return books

def update_book(book_id, title, author, genre, status, rating, notes, cover_image, total_pages, pages_read, isbn, publication_year, publisher, collections):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Get current book data
    c.execute("SELECT status, cover_image FROM books WHERE id = ?", (book_id,))
    current_data = c.fetchone()
    current_status = current_data[0]
    current_cover = current_data[1]
    
    # Only update cover if a new one is provided
    if cover_image is None:
        cover_image = current_cover
    
    # Convert collections list to JSON string
    collections_json = json.dumps(collections) if collections else "[]"
    
    c.execute('''
    UPDATE books
    SET title = ?, author = ?, genre = ?, status = ?, rating = ?, notes = ?, cover_image = ?,
        total_pages = ?, pages_read = ?, isbn = ?, publication_year = ?, publisher = ?, collections = ?
    WHERE id = ?
    ''', (title, author, genre, status, rating, notes, cover_image, 
         total_pages, pages_read, isbn, publication_year, publisher, collections_json, book_id))
    
    # Update reading history if status changed
    if current_status != status:
        if status == "Read" and current_status == "Currently Reading":
            # Book finished - update with finish date
            c.execute('''
            UPDATE reading_history 
            SET date_finished = ?
            WHERE book_id = ? AND date_finished IS NULL
            ''', (datetime.now().strftime("%Y-%m-%d"), book_id))
        elif status == "Currently Reading" and current_status != "Currently Reading":
            # Started reading - add to history
            c.execute('''
            INSERT INTO reading_history (book_id, date_started)
            VALUES (?, ?)
            ''', (book_id, datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Delete related reading history
    c.execute("DELETE FROM reading_history WHERE book_id = ?", (book_id,))
    
    # Delete related loans
    c.execute("DELETE FROM loans WHERE book_id = ?", (book_id,))
    
    # Delete the book
    c.execute("DELETE FROM books WHERE id = ?", (book_id,))
    
    conn.commit()
    conn.close()

def search_books(search_term, search_by):
    conn = sqlite3.connect('library.db')
    
    if search_by == "Title":
        query = "SELECT * FROM books WHERE title LIKE ?"
    elif search_by == "Author":
        query = "SELECT * FROM books WHERE author LIKE ?"
    elif search_by == "Genre":
        query = "SELECT * FROM books WHERE genre LIKE ?"
    elif search_by == "ISBN":
        query = "SELECT * FROM books WHERE isbn LIKE ?"
    
    results = pd.read_sql_query(query, conn, params=('%' + search_term + '%',))
    conn.close()
    return results

# Wishlist operations
def add_to_wishlist(title, author, priority, notes):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    date_added = datetime.now().strftime("%Y-%m-%d")
    
    c.execute('''
    INSERT INTO wishlist (title, author, priority, notes, date_added)
    VALUES (?, ?, ?, ?, ?)
    ''', (title, author, priority, notes, date_added))
    
    conn.commit()
    conn.close()

def get_wishlist():
    conn = sqlite3.connect('library.db')
    wishlist = pd.read_sql_query("SELECT * FROM wishlist", conn)
    conn.close()
    return wishlist

def delete_from_wishlist(item_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("DELETE FROM wishlist WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# Loan operations
def add_loan(book_id, borrower_name, expected_return_date):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    date_loaned = datetime.now().strftime("%Y-%m-%d")
    
    c.execute('''
    INSERT INTO loans (book_id, borrower_name, date_loaned, expected_return_date, returned)
    VALUES (?, ?, ?, ?, ?)
    ''', (book_id, borrower_name, date_loaned, expected_return_date, False))
    
    conn.commit()
    conn.close()

def get_loans(include_returned=False):
    conn = sqlite3.connect('library.db')
    
    if include_returned:
        query = '''
        SELECT l.*, b.title, b.author 
        FROM loans l
        JOIN books b ON l.book_id = b.id
        '''
    else:
        query = '''
        SELECT l.*, b.title, b.author 
        FROM loans l
        JOIN books b ON l.book_id = b.id
        WHERE l.returned = 0
        '''
    
    loans = pd.read_sql_query(query, conn)
    conn.close()
    return loans

def mark_as_returned(loan_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("UPDATE loans SET returned = 1 WHERE id = ?", (loan_id,))
    conn.commit()
    conn.close()

# Reading goals operations
def set_reading_goal(year, target_books, target_pages):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Check if goal for year exists
    c.execute("SELECT id FROM reading_goals WHERE year = ?", (year,))
    existing = c.fetchone()
    
    if existing:
        c.execute('''
        UPDATE reading_goals
        SET target_books = ?, target_pages = ?
        WHERE year = ?
        ''', (target_books, target_pages, year))
    else:
        c.execute('''
        INSERT INTO reading_goals (year, target_books, target_pages)
        VALUES (?, ?, ?)
        ''', (year, target_books, target_pages))
    
    conn.commit()
    conn.close()

def get_reading_goal(year):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM reading_goals WHERE year = ?", (year,))
    goal = c.fetchone()
    
    conn.close()
    
    if goal:
        return {"year": goal[1], "target_books": goal[2], "target_pages": goal[3]}
    return None

def get_reading_progress(year):
    conn = sqlite3.connect('library.db')
    
    # Books finished this year
    query_books = '''
    SELECT COUNT(*) as books_read
    FROM reading_history
    WHERE date_finished LIKE ?
    '''
    
    # Pages read this year
    query_pages = '''
    SELECT SUM(b.total_pages) as pages_read
    FROM reading_history rh
    JOIN books b ON rh.book_id = b.id
    WHERE rh.date_finished LIKE ?
    '''
    
    year_pattern = f"{year}%"
    
    books_read = pd.read_sql_query(query_books, conn, params=(year_pattern,))
    pages_read = pd.read_sql_query(query_pages, conn, params=(year_pattern,))
    
    conn.close()
    
    return {
        "books_read": int(books_read["books_read"].iloc[0]) if not books_read.empty and not pd.isna(books_read["books_read"].iloc[0]) else 0,
        "pages_read": int(pages_read["pages_read"].iloc[0]) if not pages_read.empty and not pd.isna(pages_read["pages_read"].iloc[0]) else 0
    }

# Collection operations
def add_collection(name, description):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    date_created = datetime.now().strftime("%Y-%m-%d")
    
    c.execute('''
    INSERT INTO collections (name, description, date_created)
    VALUES (?, ?, ?)
    ''', (name, description, date_created))
    
    conn.commit()
    conn.close()

def get_collections():
    conn = sqlite3.connect('library.db')
    collections = pd.read_sql_query("SELECT * FROM collections", conn)
    conn.close()
    return collections

# Statistics functions
def get_reading_stats():
    conn = sqlite3.connect('library.db')
    
    # Total books
    total_books = pd.read_sql_query("SELECT COUNT(*) as count FROM books", conn).iloc[0]['count']
    
    # Books by status
    status_counts = pd.read_sql_query(
        "SELECT status, COUNT(*) as count FROM books GROUP BY status", 
        conn
    )
    
    # Books by genre
    genre_counts = pd.read_sql_query(
        "SELECT genre, COUNT(*) as count FROM books GROUP BY genre ORDER BY count DESC LIMIT 5", 
        conn
    )
    
    # Average rating
    avg_rating = pd.read_sql_query(
        "SELECT AVG(rating) as avg_rating FROM books WHERE rating > 0", 
        conn
    ).iloc[0]['avg_rating']
    
    # Reading velocity (books per month this year)
    current_year = datetime.now().year
    year_pattern = f"{current_year}%"
    
    monthly_reads = pd.read_sql_query(
        '''
        SELECT strftime('%m', date_finished) as month, COUNT(*) as count
        FROM reading_history
        WHERE date_finished LIKE ?
        GROUP BY month
        ''',
        conn,
        params=(year_pattern,)
    )
    
    conn.close()
    
    # Calculate reading velocity
    if not monthly_reads.empty:
        months_with_data = len(monthly_reads)
        total_books_read = monthly_reads['count'].sum()
        reading_velocity = total_books_read / max(months_with_data, 1)
    else:
        reading_velocity = 0
    
    return {
        "total_books": total_books,
        "status_counts": status_counts,
        "genre_counts": genre_counts,
        "avg_rating": avg_rating if not pd.isna(avg_rating) else 0,
        "reading_velocity": reading_velocity
    }

# Book recommendations
def get_book_recommendations(num_recommendations=3):
    conn = sqlite3.connect('library.db')
    
    # Get user's favorite genres (top 3)
    favorite_genres = pd.read_sql_query(
        '''
        SELECT genre, COUNT(*) as count 
        FROM books 
        WHERE rating >= 4 
        GROUP BY genre 
        ORDER BY count DESC 
        LIMIT 3
        ''',
        conn
    )
    
    # Get favorite authors
    favorite_authors = pd.read_sql_query(
        '''
        SELECT author, COUNT(*) as count 
        FROM books 
        WHERE rating >= 4 
        GROUP BY author 
        ORDER BY count DESC 
        LIMIT 3
        ''',
        conn
    )
    
    # Get books the user hasn't read yet
    unread_books = pd.read_sql_query(
        '''
        SELECT * FROM books 
        WHERE status = 'To Read'
        ''',
        conn
    )
    
    conn.close()
    
    recommendations = []
    
    # If we have favorite genres and unread books
    if not favorite_genres.empty and not unread_books.empty:
        for _, genre_row in favorite_genres.iterrows():
            genre = genre_row['genre']
            # Find unread books in favorite genres
            genre_recommendations = unread_books[unread_books['genre'] == genre]
            if not genre_recommendations.empty:
                recommendations.append(genre_recommendations.iloc[0])
                if len(recommendations) >= num_recommendations:
                    break
    
    # If we still need more recommendations, add random unread books
    while len(recommendations) < num_recommendations and not unread_books.empty:
        if len(unread_books) > len(recommendations):
            random_idx = random.randint(0, len(unread_books) - 1)
            if unread_books.iloc[random_idx]['id'] not in [r['id'] for r in recommendations]:
                recommendations.append(unread_books.iloc[random_idx])
    
    return recommendations

# Import/Export functions
def export_library():
    books = get_all_books()
    wishlist = get_wishlist()
    loans = get_loans(include_returned=True)
    
    # Convert to dict for JSON serialization
    export_data = {
        "books": books.to_dict(orient='records'),
        "wishlist": wishlist.to_dict(orient='records'),
        "loans": loans.to_dict(orient='records')
    }
    
    # Remove binary image data for JSON export
    for book in export_data["books"]:
        if book.get("cover_image") is not None:
            book["cover_image"] = "BINARY_DATA"
    
    return json.dumps(export_data)

# Initialize the database
init_db()

# Sidebar for navigation
st.sidebar.title("📚 Library Manager")
st.sidebar.image("https://img.icons8.com/fluency/96/000000/book-shelf.png", width=100)

# Navigation
page = st.sidebar.radio("Navigate", [
    "📊 Dashboard", 
    "📖 My Library", 
    "➕ Add Book", 
    "🔍 Search Books",
    "🎯 Reading Goals",
    "📋 Wishlist",
    "🤝 Loan Tracker",
    "📚 Collections",
    "📤 Import/Export"
])

# Dashboard Page
if page == "📊 Dashboard":
    st.title("📊 Library Dashboard")
    
    # Get statistics
    stats = get_reading_stats()
    current_year = datetime.now().year
    progress = get_reading_progress(current_year)
    goal = get_reading_goal(current_year)
    
    # Top row stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats["total_books"]}</div>', unsafe_allow_html=True)
        st.markdown('Total Books', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        read_count = 0
        for _, row in stats["status_counts"].iterrows():
            if row["status"] == "Read":
                read_count = row["count"]
                break
        st.markdown(f'<div class="stat-number">{read_count}</div>', unsafe_allow_html=True)
        st.markdown('Books Read', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats["avg_rating"]:.1f}</div>', unsafe_allow_html=True)
        st.markdown('Average Rating', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats["reading_velocity"]:.1f}</div>', unsafe_allow_html=True)
        st.markdown('Books/Month', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Reading goal progress
    if goal:
        st.subheader(f"📈 {current_year} Reading Goal Progress")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="goal-card">', unsafe_allow_html=True)
            books_progress = min(100, int((progress["books_read"] / goal["target_books"]) * 100)) if goal["target_books"] > 0 else 0
            st.markdown(f"**Books Goal:** {progress['books_read']} of {goal['target_books']} ({books_progress}%)")
            st.progress(books_progress / 100)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="goal-card">', unsafe_allow_html=True)
            pages_progress = min(100, int((progress["pages_read"] / goal["target_pages"]) * 100)) if goal["target_pages"] > 0 else 0
            st.markdown(f"**Pages Goal:** {progress['pages_read']} of {goal['target_pages']} ({pages_progress}%)")
            st.progress(pages_progress / 100)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Book recommendations
    st.markdown("---")
    st.subheader("📚 Recommended Next Reads")
    
    recommendations = get_book_recommendations()
    
    if recommendations:
        cols = st.columns(len(recommendations))
        for i, book in enumerate(recommendations):
            with cols[i]:
                st.markdown('<div class="book-card">', unsafe_allow_html=True)
                
                # Display cover image if available
                if book.get('cover_image'):
                    img_b64 = get_image_base64(book['cover_image'])
                    if img_b64:
                        st.markdown(f'<img src="{img_b64}" style="width:100%; max-width:150px; display:block; margin:0 auto 10px auto;">', unsafe_allow_html=True)
                else:
                    # Display placeholder
                    st.image("https://via.placeholder.com/150x200?text=No+Cover", width=150)
                
                st.markdown(f"**{book['title']}**")
                st.markdown(f"by {book['author']}")
                st.markdown(f"Genre: {book['genre']}")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Add more books to your library to get personalized recommendations!")
    
    # Charts
    st.markdown("---")
    st.subheader("📊 Library Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution pie chart
        if not stats["status_counts"].empty:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(
                stats["status_counts"]["count"], 
                labels=stats["status_counts"]["status"],
                autopct='%1.1f%%',
                startangle=90,
                colors=['#4CAF50', '#2196F3', '#FFC107', '#F44336']
            )
            ax.axis('equal')
            plt.title("Books by Reading Status")
            st.pyplot(fig)
        else:
            st.info("Add books to see status distribution")
    
    with col2:
        # Genre distribution bar chart
        if not stats["genre_counts"].empty:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.barh(
                stats["genre_counts"]["genre"],
                stats["genre_counts"]["count"],
                color='#1E3A8A'
            )
            plt.title("Top Genres in Your Library")
            plt.xlabel("Number of Books")
            st.pyplot(fig)
        else:
            st.info("Add books to see genre distribution")

# My Library Page
elif page == "📖 My Library":
    st.title("📖 My Library")
    
    books = get_all_books()
    
    if not books.empty:
        # Add filter options
        st.subheader("Filter Books")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_option = st.selectbox("Filter by", ["None", "Genre", "Status", "Rating", "Collection"])
        
        filter_value = None
        if filter_option != "None":
            with col2:
                if filter_option == "Genre":
                    unique_genres = books['genre'].unique()
                    filter_value = st.selectbox("Select Genre", unique_genres)
                elif filter_option == "Status":
                    unique_statuses = books['status'].unique()
                    filter_value = st.selectbox("Select Status", unique_statuses)
                elif filter_option == "Rating":
                    filter_value = st.slider("Minimum Rating", 0, 5, 0)
                elif filter_option == "Collection":
                    collections = get_collections()
                    if not collections.empty:
                        collection_names = collections['name'].tolist()
                        filter_value = st.selectbox("Select Collection", collection_names)
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Title", "Author", "Date Added", "Rating", "Publication Year"])
        
        # Apply filters
        filtered_books = books
        if filter_option != "None" and filter_value is not None:
            if filter_option == "Genre":
                filtered_books = books[books['genre'] == filter_value]
            elif filter_option == "Status":
                filtered_books = books[books['status'] == filter_value]
            elif filter_option == "Rating":
                filtered_books = books[books['rating'] >= filter_value]
            elif filter_option == "Collection":
                # Filter by collection (need to check JSON strings)
                filtered_books = books.copy()
                filtered_rows = []
                for i, book in filtered_books.iterrows():
                    if book['collections']:
                        try:
                            collections_list = json.loads(book['collections'])
                            if filter_value in collections_list:
                                filtered_rows.append(i)
                        except:
                            pass
                filtered_books = filtered_books.loc[filtered_rows]
        
        # Apply sorting
        if sort_by == "Title":
            filtered_books = filtered_books.sort_values(by="title")
        elif sort_by == "Author":
            filtered_books = filtered_books.sort_values(by="author")
        elif sort_by == "Date Added":
            filtered_books = filtered_books.sort_values(by="date_added", ascending=False)
        elif sort_by == "Rating":
            filtered_books = filtered_books.sort_values(by="rating", ascending=False)
        elif sort_by == "Publication Year":
            filtered_books = filtered_books.sort_values(by="publication_year", ascending=False)
        
        # Display books in a grid
        st.subheader("Book Collection")
        
        # Create rows of 3 books each
        for i in range(0, len(filtered_books), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(filtered_books):
                    book = filtered_books.iloc[i + j]
                    with cols[j]:
                        st.markdown('<div class="book-card">', unsafe_allow_html=True)
                        
                        # Display cover image if available
                        if book['cover_image'] is not None:
                            img_b64 = get_image_base64(book['cover_image'])
                            if img_b64:
                                st.markdown(f'<img src="{img_b64}" style="width:100%; max-width:150px; display:block; margin:0 auto 10px auto;">', unsafe_allow_html=True)
                        else:
                            # Display placeholder
                            st.image("https://via.placeholder.com/150x200?text=No+Cover", width=150)
                        
                        # Book details
                        st.markdown(f"**{book['title']}**")
                        st.markdown(f"by {book['author']}")
                        
                        # Reading progress
                        if book['total_pages'] and book['pages_read'] is not None:
                            progress_pct = min(100, int((book['pages_read'] / book['total_pages']) * 100))
                            st.progress(progress_pct / 100)
                            st.markdown(f"Progress: {book['pages_read']}/{book['total_pages']} pages ({progress_pct}%)")
                        
                        # Rating
                        st.markdown(f"Rating: {'⭐' * int(book['rating'])}")
                        
                        # Status badge
                        status_colors = {
                            "Read": "#4CAF50",
                            "Currently Reading": "#2196F3",
                            "To Read": "#FFC107",
                            "DNF (Did Not Finish)": "#F44336"
                        }
                        status_color = status_colors.get(book['status'], "#1E3A8A")
                        st.markdown(f'<span style="background-color:{status_color}; color:white; padding:3px 8px; border-radius:4px;">{book["status"]}</span>', unsafe_allow_html=True)
                        
                        # Collections badges
                        if book['collections']:
                            try:
                                collections_list = json.loads(book['collections'])
                                if collections_list:
                                    st.markdown("**Collections:**")
                                    for collection in collections_list:
                                        st.markdown(f'<span class="collection-badge">{collection}</span>', unsafe_allow_html=True)
                            except:
                                pass
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("View Details", key=f"view_{book['id']}"):
                                st.session_state['view_book_id'] = book['id']
                        with col2:
                            if st.button("Edit", key=f"edit_{book['id']}"):
                                st.session_state['edit_book_id'] = book['id']
                                st.session_state['edit_title'] = book['title']
                                st.session_state['edit_author'] = book['author']
                                st.session_state['edit_genre'] = book['genre']
                                st.session_state['edit_status'] = book['status']
                                st.session_state['edit_rating'] = book['rating']
                                st.session_state['edit_notes'] = book['notes']
                                st.session_state['edit_total_pages'] = book['total_pages']
                                st.session_state['edit_pages_read'] = book['pages_read']
                                st.session_state['edit_isbn'] = book['isbn']
                                st.session_state['edit_publication_year'] = book['publication_year']
                                st.session_state['edit_publisher'] = book['publisher']
                                try:
                                    st.session_state['edit_collections'] = json.loads(book['collections'])
                                except:
                                    st.session_state['edit_collections'] = []
                        
                        st.markdown('</div>', unsafe_allow_html=True)
        
        # Book details view
        if 'view_book_id' in st.session_state:
            book_id = st.session_state['view_book_id']
            book = books[books['id'] == book_id].iloc[0]
            
            st.markdown("---")
            st.subheader(f"Book Details: {book['title']}")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Display cover image if available
                if book['cover_image'] is not None:
                    img_b64 = get_image_base64(book['cover_image'])
                    if img_b64:
                        st.markdown(f'<img src="{img_b64}" style="width:100%; max-width:200px;">', unsafe_allow_html=True)
                else:
                    # Display placeholder
                    st.image("https://via.placeholder.com/200x300?text=No+Cover", width=200)
                
                # Loan button
                if st.button("Loan This Book"):
                    st.session_state['loan_book_id'] = book_id
                    st.session_state['loan_book_title'] = book['title']
            
            with col2:
                st.markdown(f"**Title:** {book['title']}")
                st.markdown(f"**Author:** {book['author']}")
                st.markdown(f"**Genre:** {book['genre']}")
                st.markdown(f"**Status:** {book['status']}")
                st.markdown(f"**Rating:** {'⭐' * int(book['rating'])}")
                
                if book['isbn']:
                    st.markdown(f"**ISBN:** {book['isbn']}")
                
                if book['publication_year']:
                    st.markdown(f"**Publication Year:** {book['publication_year']}")
                
                if book['publisher']:
                    st.markdown(f"**Publisher:** {book['publisher']}")
                
                if book['total_pages']:
                    st.markdown(f"**Total Pages:** {book['total_pages']}")
                
                if book['pages_read'] is not None and book['total_pages']:
                    progress_pct = min(100, int((book['pages_read'] / book['total_pages']) * 100))
                    st.markdown(f"**Reading Progress:** {book['pages_read']}/{book['total_pages']} pages ({progress_pct}%)")
                    st.progress(progress_pct / 100)
                
                st.markdown(f"**Date Added:** {book['date_added']}")
                
                # Collections
                if book['collections']:
                    try:
                        collections_list = json.loads(book['collections'])
                        if collections_list:
                            st.markdown("**Collections:**")
                            for collection in collections_list:
                                st.markdown(f'<span class="collection-badge">{collection}</span>', unsafe_allow_html=True)
                    except:
                        pass
                
                # Notes
                if book['notes']:
                    st.markdown("**Notes:**")
                    st.markdown(f">{book['notes']}")
                
                # Close button
                if st.button("Close Details"):
                    del st.session_state['view_book_id']
                    st.rerun()

        
        # Loan book form
        if 'loan_book_id' in st.session_state:
            st.markdown("---")
            st.subheader(f"Loan Book: {st.session_state['loan_book_title']}")
            
            borrower_name = st.text_input("Borrower Name")
            expected_return_date = st.date_input("Expected Return Date")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Loan"):
                    if borrower_name:
                        add_loan(
                            st.session_state['loan_book_id'],
                            borrower_name,
                            expected_return_date.strftime("%Y-%m-%d")
                        )
                        st.success(f"Book loaned to {borrower_name}")
                        del st.session_state['loan_book_id']
                        del st.session_state['loan_book_title']
                        st.rerun()

                    else:
                        st.error("Please enter borrower name")
            
            with col2:
                if st.button("Cancel Loan"):
                    del st.session_state['loan_book_id']
                    del st.session_state['loan_book_title']
                    st.rerun()

        
        # Edit book form
        if 'edit_book_id' in st.session_state:
            st.markdown("---")
            st.subheader("Edit Book")
            
            col1, col2 = st.columns(2)
            
            with col1:
                edit_title = st.text_input("Title", st.session_state['edit_title'])
                edit_author = st.text_input("Author", st.session_state['edit_author'])
                edit_genre = st.selectbox("Genre", ["Fiction", "Non-Fiction", "Science Fiction", 
                                                  "Fantasy", "Mystery", "Thriller", "Romance", 
                                                  "Biography", "History", "Self-Help", "Other"],
                                         index=["Fiction", "Non-Fiction", "Science Fiction", 
                                               "Fantasy", "Mystery", "Thriller", "Romance", 
                                               "Biography", "History", "Self-Help", "Other"].index(st.session_state['edit_genre']))
                edit_status = st.selectbox("Status", ["Read", "Currently Reading", "To Read", "DNF (Did Not Finish)"],
                                         index=["Read", "Currently Reading", "To Read", "DNF (Did Not Finish)"].index(st.session_state['edit_status']))
                edit_rating = st.slider("Rating", 0, 5, int(st.session_state['edit_rating']))
            
            with col2:
                edit_total_pages = st.number_input("Total Pages", min_value=0, value=st.session_state['edit_total_pages'] if st.session_state['edit_total_pages'] else 0)
                edit_pages_read = st.number_input("Pages Read", min_value=0, max_value=edit_total_pages, value=st.session_state['edit_pages_read'] if st.session_state['edit_pages_read'] else 0)
                edit_isbn = st.text_input("ISBN", st.session_state['edit_isbn'] if st.session_state['edit_isbn'] else "")
                edit_publication_year = st.number_input("Publication Year", min_value=1000, max_value=datetime.now().year, value=st.session_state['edit_publication_year'] if st.session_state['edit_publication_year'] else 2000)
                edit_publisher = st.text_input("Publisher", st.session_state['edit_publisher'] if st.session_state['edit_publisher'] else "")
            
            # Collections
            collections = get_collections()
            if not collections.empty:
                collection_names = collections['name'].tolist()
                edit_collections = st.multiselect("Collections", collection_names, default=st.session_state['edit_collections'])
            else:
                edit_collections = []
            
            edit_notes = st.text_area("Notes", st.session_state['edit_notes'] if st.session_state['edit_notes'] else "")
            
            # Cover image upload
            st.markdown("**Cover Image** (Leave empty to keep current image)")
            uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
            edit_cover_image = convert_image_to_bytes(uploaded_file) if uploaded_file else None
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Save Changes"):
                    update_book(
                        st.session_state['edit_book_id'], 
                        edit_title, 
                        edit_author, 
                        edit_genre, 
                        edit_status, 
                        edit_rating, 
                        edit_notes,
                        edit_cover_image,
                        edit_total_pages,
                        edit_pages_read,
                        edit_isbn,
                        edit_publication_year,
                        edit_publisher,
                        edit_collections
                    )
                    st.success("Book updated successfully!")
                    del st.session_state['edit_book_id']
                    st.rerun()

            
            with col2:
                if st.button("Cancel"):
                    del st.session_state['edit_book_id']
                    st.rerun()

            
            with col3:
                if st.button("Delete Book"):
                    delete_book(st.session_state['edit_book_id'])
                    st.success("Book deleted successfully!")
                    del st.session_state['edit_book_id']
                    st.rerun()

    else:
        st.info("Your library is empty. Add some books to get started!")

# Add Book Page
elif page == "➕ Add Book":
    st.title("➕ Add a New Book")
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("Title*")
        author = st.text_input("Author*")
        genre = st.selectbox("Genre", ["Fiction", "Non-Fiction", "Science Fiction", 
                                      "Fantasy", "Mystery", "Thriller", "Romance", 
                                      "Biography", "History", "Self-Help", "Other"])
        status = st.selectbox("Status", ["Read", "Currently Reading", "To Read", "DNF (Did Not Finish)"])
        rating = st.slider("Rating", 0, 5, 0)
    
    with col2:
        total_pages = st.number_input("Total Pages", min_value=0, value=0)
        pages_read = st.number_input("Pages Read", min_value=0, max_value=total_pages if total_pages > 0 else 0, value=0)
        isbn = st.text_input("ISBN")
        publication_year = st.number_input("Publication Year", min_value=1000, max_value=datetime.now().year, value=datetime.now().year)
        publisher = st.text_input("Publisher")
    
    # Collections
    collections = get_collections()
    selected_collections = []
    if not collections.empty:
        collection_names = collections['name'].tolist()
        selected_collections = st.multiselect("Add to Collections", collection_names)
    
    notes = st.text_area("Notes")
    
    # Cover image upload
    st.markdown("**Cover Image**")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if st.button("Add Book"):
        if title and author:
            # Process cover image if uploaded
            cover_image = convert_image_to_bytes(uploaded_file) if uploaded_file else None
            
            # Add book to database
            book_id = add_book(
                title, 
                author, 
                genre, 
                status, 
                rating, 
                notes, 
                cover_image,
                total_pages,
                pages_read if status == "Currently Reading" else (total_pages if status == "Read" else 0),
                isbn,
                publication_year,
                publisher,
                selected_collections
            )
            
            st.success(f"Added '{title}' by {author} to your library!")
            
            # Clear form
            st.rerun()

        else:
            st.error("Title and Author are required fields.")

# Search Books Page
elif page == "🔍 Search Books":
    st.title("🔍 Search Books")
    
    search_by = st.selectbox("Search by", ["Title", "Author", "Genre", "ISBN"])
    search_term = st.text_input("Enter search term")
    
    if search_term:
        results = search_books(search_term, search_by)
        
        if not results.empty:
            st.subheader(f"Found {len(results)} results")
            
            for i, book in results.iterrows():
                with st.expander(f"{book['title']} by {book['author']}"):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        # Display cover image if available
                        if book['cover_image'] is not None:
                            img_b64 = get_image_base64(book['cover_image'])
                            if img_b64:
                                st.markdown(f'<img src="{img_b64}" style="width:100%; max-width:150px;">', unsafe_allow_html=True)
                        else:
                            # Display placeholder
                            st.image("https://via.placeholder.com/150x200?text=No+Cover", width=150)
                    
                    with col2:
                        st.markdown(f"**Genre:** {book['genre']}")
                        st.markdown(f"**Status:** {book['status']}")
                        st.markdown(f"**Rating:** {'⭐' * int(book['rating'])}")
                        
                        if book['total_pages']:
                            st.markdown(f"**Pages:** {book['total_pages']}")
                        
                        if book['publication_year']:
                            st.markdown(f"**Published:** {book['publication_year']}")
                        
                        if book['isbn']:
                            st.markdown(f"**ISBN:** {book['isbn']}")
                        
                        st.markdown(f"**Added on:** {book['date_added']}")
                        
                        if book['notes']:
                            st.markdown("**Notes:**")
                            st.markdown(f">{book['notes']}")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("View Details", key=f"search_view_{book['id']}"):
                                st.session_state['view_book_id'] = book['id']
                                st.rerun()

                        
                        with col2:
                            if st.button("Edit", key=f"search_edit_{book['id']}"):
                                st.session_state['edit_book_id'] = book['id']
                                st.session_state['edit_title'] = book['title']
                                st.session_state['edit_author'] = book['author']
                                st.session_state['edit_genre'] = book['genre']
                                st.session_state['edit_status'] = book['status']
                                st.session_state['edit_rating'] = book['rating']
                                st.session_state['edit_notes'] = book['notes']
                                st.session_state['edit_total_pages'] = book['total_pages']
                                st.session_state['edit_pages_read'] = book['pages_read']
                                st.session_state['edit_isbn'] = book['isbn']
                                st.session_state['edit_publication_year'] = book['publication_year']
                                st.session_state['edit_publisher'] = book['publisher']
                                try:
                                    st.session_state['edit_collections'] = json.loads(book['collections'])
                                except:
                                    st.session_state['edit_collections'] = []
                                st.rerun()

                        
                        with col3:
                            if st.button("Delete", key=f"search_delete_{book['id']}"):
                                delete_book(book['id'])
                                st.success(f"Deleted '{book['title']}' from your library!")
                                st.rerun()

        else:
            st.info(f"No books found matching '{search_term}' in {search_by}.")

# Reading Goals Page
elif page == "🎯 Reading Goals":
    st.title("🎯 Reading Goals")
    
    current_year = datetime.now().year
    selected_year = st.selectbox("Select Year", range(current_year - 5, current_year + 6), index=5)
    
    # Get current goal if exists
    goal = get_reading_goal(selected_year)
    
    # Set up form
    st.subheader(f"Set Reading Goal for {selected_year}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_books = st.number_input(
            "Target Number of Books", 
            min_value=1, 
            value=goal["target_books"] if goal else 12
        )
    
    with col2:
        target_pages = st.number_input(
            "Target Number of Pages", 
            min_value=1, 
            value=goal["target_pages"] if goal else 3600
        )
    
    if st.button("Save Goal"):
        set_reading_goal(selected_year, target_books, target_pages)
        st.success(f"Reading goal for {selected_year} saved!")
    
    # Show progress if it's the current year
    if goal:
        st.markdown("---")
        st.subheader("Current Progress")
        
        progress = get_reading_progress(selected_year)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="goal-card">', unsafe_allow_html=True)
            books_progress = min(100, int((progress["books_read"] / goal["target_books"]) * 100)) if goal["target_books"] > 0 else 0
            st.markdown(f"**Books Goal:** {progress['books_read']} of {goal['target_books']} ({books_progress}%)")
            st.progress(books_progress / 100)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="goal-card">', unsafe_allow_html=True)
            pages_progress = min(100, int((progress["pages_read"] / goal["target_pages"]) * 100)) if goal["target_pages"] > 0 else 0
            st.markdown(f"**Pages Goal:** {progress['pages_read']} of {goal['target_pages']} ({pages_progress}%)")
            st.progress(pages_progress / 100)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Calculate reading pace
        days_in_year = 366 if (selected_year % 4 == 0 and selected_year % 100 != 0) or (selected_year % 400 == 0) else 365
        
        if selected_year == current_year:
            # For current year, calculate based on days passed
            start_date = datetime(selected_year, 1, 1)
            today = datetime.now()
            days_passed = (today - start_date).days + 1
            days_remaining = days_in_year - days_passed
            
            # Books pace
            books_remaining = goal["target_books"] - progress["books_read"]
            books_per_day_needed = books_remaining / max(days_remaining, 1) if books_remaining > 0 else 0
            books_per_week_needed = books_per_day_needed * 7
            
            # Pages pace
            pages_remaining = goal["target_pages"] - progress["pages_read"]
            pages_per_day_needed = pages_remaining / max(days_remaining, 1) if pages_remaining > 0 else 0
            
            st.markdown("---")
            st.subheader("Reading Pace")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.markdown(f"To reach your books goal, you need to read:")
                st.markdown(f'<div class="stat-number">{books_per_week_needed:.1f}</div>', unsafe_allow_html=True)
                st.markdown("books per week")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="stat-card">', unsafe_allow_html=True)
                st.markdown(f"To reach your pages goal, you need to read:")
                st.markdown(f'<div class="stat-number">{pages_per_day_needed:.0f}</div>', unsafe_allow_html=True)
                st.markdown("pages per day")
                st.markdown('</div>', unsafe_allow_html=True)

# Wishlist Page
elif page == "📋 Wishlist":
    st.title("📋 Book Wishlist")
    
    # Add to wishlist form
    st.subheader("Add to Wishlist")
    
    col1, col2 = st.columns(2)
    
    with col1:
        wish_title = st.text_input("Title*")
        wish_author = st.text_input("Author*")
    
    with col2:
        wish_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        wish_notes = st.text_input("Notes")
    
    if st.button("Add to Wishlist"):
        if wish_title and wish_author:
            add_to_wishlist(wish_title, wish_author, wish_priority, wish_notes)
            st.success(f"Added '{wish_title}' to your wishlist!")
            st.rerun()

        else:
            st.error("Title and Author are required fields.")
    
    # Display wishlist
    st.markdown("---")
    st.subheader("Your Wishlist")
    
    wishlist = get_wishlist()
    
    if not wishlist.empty:
        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        wishlist['priority_order'] = wishlist['priority'].map(priority_order)
        wishlist = wishlist.sort_values(by=['priority_order', 'date_added'])
        
        for i, item in wishlist.iterrows():
            priority_colors = {"High": "#F44336", "Medium": "#FFC107", "Low": "#4CAF50"}
            priority_color = priority_colors.get(item['priority'], "#1E3A8A")
            
            st.markdown(f'<div class="wishlist-item">', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{item['title']}** by {item['author']}")
                st.markdown(f'<span style="background-color:{priority_color}; color:white; padding:3px 8px; border-radius:4px;">{item["priority"]} Priority</span>', unsafe_allow_html=True)
                if item['notes']:
                    st.markdown(f"Note: {item['notes']}")
                st.markdown(f"Added on: {item['date_added']}")
            
            with col2:
                if st.button("Remove", key=f"remove_wish_{item['id']}"):
                    delete_from_wishlist(item['id'])
                    st.success(f"Removed '{item['title']}' from your wishlist!")
                    st.rerun()

                
                if st.button("Add to Library", key=f"add_lib_{item['id']}"):
                    st.session_state['add_from_wishlist'] = True
                    st.session_state['wish_title'] = item['title']
                    st.session_state['wish_author'] = item['author']
                    st.session_state['wish_id'] = item['id']
                    st.rerun()

            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Add from wishlist to library form
        if 'add_from_wishlist' in st.session_state and st.session_state['add_from_wishlist']:
            st.markdown("---")
            st.subheader(f"Add to Library: {st.session_state['wish_title']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                genre = st.selectbox("Genre", ["Fiction", "Non-Fiction", "Science Fiction", 
                                            "Fantasy", "Mystery", "Thriller", "Romance", 
                                            "Biography", "History", "Self-Help", "Other"])
                status = st.selectbox("Status", ["Read", "Currently Reading", "To Read", "DNF (Did Not Finish)"])
                rating = st.slider("Rating", 0, 5, 0)
            
            with col2:
                total_pages = st.number_input("Total Pages", min_value=0, value=0)
                isbn = st.text_input("ISBN")
                publication_year = st.number_input("Publication Year", min_value=1000, max_value=datetime.now().year, value=datetime.now().year)
            
            notes = st.text_area("Notes")
            
            # Cover image upload
            st.markdown("**Cover Image**")
            uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Add to Library"):
                    # Process cover image if uploaded
                    cover_image = convert_image_to_bytes(uploaded_file) if uploaded_file else None
                    
                    # Add book to database
                    add_book(
                        st.session_state['wish_title'], 
                        st.session_state['wish_author'], 
                        genre, 
                        
                        st.session_state['wish_author'],
                        genre,
                        status,
                        rating,
                        notes,
                        cover_image,
                        total_pages,
                        total_pages if status == "Read" else 0,
                        isbn,
                        publication_year,
                        "",
                        []
                    )
                    
                    # Remove from wishlist
                    delete_from_wishlist(st.session_state['wish_id'])
                    
                    st.success(f"Added '{st.session_state['wish_title']}' to your library and removed from wishlist!")
                    
                    # Clear form
                    del st.session_state['add_from_wishlist']
                    del st.session_state['wish_title']
                    del st.session_state['wish_author']
                    del st.session_state['wish_id']
                    st.rerun()

            
            with col2:
                if st.button("Cancel"):
                    del st.session_state['add_from_wishlist']
                    del st.session_state['wish_title']
                    del st.session_state['wish_author']
                    del st.session_state['wish_id']
                    st.rerun()

    else:
        st.info("Your wishlist is empty. Add books you want to read in the future.")

# Loan Tracker Page
elif page == "🤝 Loan Tracker":
    st.title("🤝 Book Loan Tracker")
    
    # Display active loans
    st.subheader("Active Loans")
    
    loans = get_loans(include_returned=False)
    
    if not loans.empty:
        for i, loan in loans.iterrows():
            st.markdown(f'<div class="loan-card">', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{loan['title']}** by {loan['author']}")
                st.markdown(f"Borrowed by: **{loan['borrower_name']}**")
                st.markdown(f"Loaned on: {loan['date_loaned']}")
                st.markdown(f"Expected return: {loan['expected_return_date']}")
                
                # Check if overdue
                expected_date = datetime.strptime(loan['expected_return_date'], "%Y-%m-%d")
                if expected_date < datetime.now():
                    st.markdown(f'<span style="color:#F44336; font-weight:bold;">OVERDUE</span>', unsafe_allow_html=True)
            
            with col2:
                if st.button("Mark as Returned", key=f"return_{loan['id']}"):
                    mark_as_returned(loan['id'])
                    st.success(f"Marked '{loan['title']}' as returned!")
                    st.rerun()

            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No active loans. All your books are safe at home!")
    
    # Show loan history
    show_history = st.checkbox("Show Loan History")
    
    if show_history:
        st.subheader("Loan History")
        
        history = get_loans(include_returned=True)
        returned_loans = history[history['returned'] == 1]
        
        if not returned_loans.empty:
            for i, loan in returned_loans.iterrows():
                st.markdown(f'<div style="background-color:#f0f2f6; border-radius:8px; padding:1rem; margin-bottom:0.5rem; border-left:4px solid #4CAF50;">', unsafe_allow_html=True)
                st.markdown(f"**{loan['title']}** by {loan['author']}")
                st.markdown(f"Borrowed by: {loan['borrower_name']}")
                st.markdown(f"Loaned on: {loan['date_loaned']}")
                st.markdown(f"Expected return: {loan['expected_return_date']}")
                st.markdown(f'<span style="color:#4CAF50; font-weight:bold;">RETURNED</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No loan history yet.")

# Collections Page
elif page == "📚 Collections":
    st.title("📚 Book Collections")
    
    # Create new collection form
    st.subheader("Create New Collection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        collection_name = st.text_input("Collection Name*")
    
    with col2:
        collection_description = st.text_input("Description")
    
    if st.button("Create Collection"):
        if collection_name:
            add_collection(collection_name, collection_description)
            st.success(f"Created new collection: {collection_name}")
            st.rerun()

        else:
            st.error("Collection name is required.")
    
    # Display collections
    st.markdown("---")
    st.subheader("Your Collections")
    
    collections = get_collections()
    
    if not collections.empty:
        for i, collection in collections.iterrows():
            with st.expander(f"{collection['name']}"):
                st.markdown(f"**Description:** {collection['description']}")
                st.markdown(f"**Created on:** {collection['date_created']}")
                
                # Get books in this collection
                conn = sqlite3.connect('library.db')
                books = pd.read_sql_query("SELECT * FROM books", conn)
                conn.close()
                
                collection_books = []
                for _, book in books.iterrows():
                    if book['collections']:
                        try:
                            collections_list = json.loads(book['collections'])
                            if collection['name'] in collections_list:
                                collection_books.append(book)
                        except:
                            pass
                
                if collection_books:
                    st.markdown("**Books in this collection:**")
                    
                    # Display books in a grid
                    cols = st.columns(3)
                    for j, book in enumerate(collection_books):
                        with cols[j % 3]:
                            st.markdown('<div class="book-card">', unsafe_allow_html=True)
                            
                            # Display cover image if available
                            if book['cover_image'] is not None:
                                img_b64 = get_image_base64(book['cover_image'])
                                if img_b64:
                                    st.markdown(f'<img src="{img_b64}" style="width:100%; max-width:100px; display:block; margin:0 auto 10px auto;">', unsafe_allow_html=True)
                            else:
                                # Display placeholder
                                st.image("https://via.placeholder.com/100x150?text=No+Cover", width=100)
                            
                            st.markdown(f"**{book['title']}**")
                            st.markdown(f"by {book['author']}")
                            st.markdown(f"Rating: {'⭐' * int(book['rating'])}")
                            
                            if st.button("View Details", key=f"coll_view_{book['id']}"):
                                st.session_state['view_book_id'] = book['id']
                                st.rerun()

                            
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info(f"No books in the '{collection['name']}' collection yet.")
    else:
        st.info("You haven't created any collections yet.")

# Import/Export Page
elif page == "📤 Import/Export":
    st.title("📤 Import/Export Library")
    
    st.subheader("Export Library")
    st.markdown("Download your library data as a JSON file.")
    
    if st.button("Export Library Data"):
        export_data = export_library()
        
        # Create download link
        b64 = base64.b64encode(export_data.encode()).decode()
        export_filename = f"library_export_{datetime.now().strftime('%Y%m%d')}.json"
        href = f'<a href="data:file/json;base64,{b64}" download="{export_filename}">Download Export File</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Import Library")
    st.markdown("⚠️ **Warning:** Importing will not overwrite existing books, but may create duplicates.")
    
    uploaded_file = st.file_uploader("Upload JSON export file", type=["json"])
    
    if uploaded_file is not None:
        try:
            import_data = json.load(uploaded_file)
            
            if st.button("Import Data"):
                # Process books
                if "books" in import_data:
                    imported_count = 0
                    for book in import_data["books"]:
                        # Skip books with binary data placeholder
                        if book.get("cover_image") == "BINARY_DATA":
                            book["cover_image"] = None
                        
                        # Add book to database
                        add_book(
                            book.get("title", "Unknown Title"),
                            book.get("author", "Unknown Author"),
                            book.get("genre", "Fiction"),
                            book.get("status", "To Read"),
                            book.get("rating", 0),
                            book.get("notes", ""),
                            book.get("cover_image"),
                            book.get("total_pages", 0),
                            book.get("pages_read", 0),
                            book.get("isbn", ""),
                            book.get("publication_year", 2000),
                            book.get("publisher", ""),
                            book.get("collections", [])
                        )
                        imported_count += 1
                    
                    st.success(f"Successfully imported {imported_count} books!")
                    st.rerun()

                else:
                    st.error("Invalid import file format. No books found.")
        except Exception as e:
            st.error(f"Error importing data: {e}")

# Run the app
if __name__ == "__main__":
    print("Enhanced Personal Library Manager is running!")