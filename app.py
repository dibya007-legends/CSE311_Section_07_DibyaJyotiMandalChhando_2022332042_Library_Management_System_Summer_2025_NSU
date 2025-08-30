from flask import Flask, render_template, flash, redirect, url_for, request
from wtforms import Form, validators, StringField, FloatField, IntegerField, DateField, SelectField
from datetime import datetime
import pymysql
import urllib
import requests

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='librarydb',
        unix_socket='/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock',
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/members')
def members():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM members")
    members = cur.fetchall()
    conn.close()
    if members:
        return render_template('members.html', members=members)
    else:
        return render_template('members.html', warning='No Members Found')


@app.route('/member/<string:id>')
def viewMember(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM members WHERE id=%s", [id])
    member = cur.fetchone()
    conn.close()
    if member:
        return render_template('view_member_details.html', member=member)
    else:
        return render_template('view_member_details.html', warning='This Member Does Not Exist')


class AddMember(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.length(min=6, max=50)])


@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    form = AddMember(request.form)
    if request.method == 'POST' and form.validate():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
    "INSERT INTO members (name, email, outstanding_debt, amount_spent) VALUES (%s, %s, %s, %s)",
    (form.name.data, form.email.data, 0, 0)
)
        conn.commit()
        conn.close()
        flash("New Member Added", "success")
        return redirect(url_for('members'))
    return render_template('add_member.html', form=form)


@app.route('/edit_member/<string:id>', methods=['GET', 'POST'])
def edit_member(id):
    form = AddMember(request.form)
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST' and form.validate():
        cur.execute("UPDATE members SET name=%s, email=%s WHERE id=%s", (form.name.data, form.email.data, id))
        conn.commit()
        conn.close()
        flash("Member Updated", "success")
        return redirect(url_for('members'))
    cur.execute("SELECT name,email FROM members WHERE id=%s", [id])
    member = cur.fetchone()
    conn.close()
    return render_template('edit_member.html', form=form, member=member)


@app.route('/delete_member/<string:id>', methods=['POST'])
def delete_member(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM members WHERE id=%s", [id])
        conn.commit()
        flash("Member Deleted", "success")
    except Exception as e:
        flash("Member could not be deleted", "danger")
        flash(str(e), "danger")
    finally:
        conn.close()
    return redirect(url_for('members'))


# ------------------------------------------------
# Books
# ------------------------------------------------
class AddBook(Form):
    id = StringField('Book ID', [validators.Length(min=1, max=11)])
    title = StringField('Title', [validators.Length(min=2, max=255)])
    author = StringField('Author(s)', [validators.Length(min=2, max=255)])
    average_rating = FloatField('Average Rating', [validators.NumberRange(min=0, max=5)])
    isbn = StringField('ISBN', [validators.Length(min=10, max=10)])
    isbn13 = StringField('ISBN13', [validators.Length(min=13, max=13)])
    language_code = StringField('Language', [validators.Length(min=1, max=3)])
    num_pages = IntegerField('No. of Pages', [validators.NumberRange(min=1)])
    ratings_count = IntegerField('No. of Ratings', [validators.NumberRange(min=0)])
    text_reviews_count = IntegerField('No. of Text Reviews', [validators.NumberRange(min=0)])
    publication_date = DateField('Publication Date', [validators.InputRequired()])
    publisher = StringField('Publisher', [validators.Length(min=2, max=255)])
    total_quantity = IntegerField('Total No. of Books', [validators.NumberRange(min=1)])

@app.route('/books')
def books():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id,title,author,total_quantity,available_quantity,rented_count FROM books ORDER BY id ASC")
    books = cur.fetchall()
    conn.close()
    if books:
        return render_template('books.html', books=books)
    else:
        return render_template('books.html', warning='No Books Found')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = AddBook(request.form)
    if request.method == 'POST' and form.validate():
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM books WHERE id=%s", (form.id.data,))
        if cur.fetchone():
            conn.close()
            return render_template('add_book.html', form=form, error='Book with that ID already exists')

        cur.execute("""INSERT INTO books
            (id,title,author,average_rating,isbn,isbn13,language_code,num_pages,
             ratings_count,text_reviews_count,publication_date,publisher,total_quantity,available_quantity,rented_count)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (form.id.data, form.title.data, form.author.data, form.average_rating.data,
             form.isbn.data, form.isbn13.data, form.language_code.data, form.num_pages.data,
             form.ratings_count.data, form.text_reviews_count.data, form.publication_date.data,
             form.publisher.data, form.total_quantity.data, form.total_quantity.data, 0))
        conn.commit()
        conn.close()
        flash("New Book Added", "success")
        return redirect(url_for('books'))
    return render_template('add_book.html', form=form)

@app.route('/book/<string:id>')
def viewBook(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cur.fetchone()
    conn.close()
    if book:
        return render_template('view_book_details.html', book=book)
    return render_template('view_book_details.html', warning='This Book Does Not Exist')

@app.route('/edit_book/<string:id>', methods=['GET', 'POST'])
def edit_book(id):
    form = AddBook(request.form)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cur.fetchone()

    if request.method == 'POST' and form.validate():
        # Prevent duplicate ID
        if form.id.data != id:
            cur.execute("SELECT id FROM books WHERE id=%s", (form.id.data,))
            if cur.fetchone():
                conn.close()
                return render_template('edit_book.html', form=form, error='Book with that ID already exists', book=form.data)

        # Normalize date
        try:
            d = datetime.strptime(str(form.publication_date.data), "%m/%d/%Y")
            normalized_date = d.strftime("%Y-%m-%d")
        except Exception:
            normalized_date = form.publication_date.data

        available_quantity = book['available_quantity'] + (form.total_quantity.data - book['total_quantity'])

        try:
            cur.execute("""UPDATE books SET id=%s,title=%s,author=%s,average_rating=%s,isbn=%s,isbn13=%s,language_code=%s,
                           num_pages=%s,ratings_count=%s,text_reviews_count=%s,publication_date=%s,publisher=%s,total_quantity=%s,
                           available_quantity=%s WHERE id=%s""",
                        (form.id.data, form.title.data, form.author.data, form.average_rating.data,
                         form.isbn.data, form.isbn13.data, form.language_code.data, form.num_pages.data,
                         form.ratings_count.data, form.text_reviews_count.data, normalized_date,
                         form.publisher.data, form.total_quantity.data, available_quantity, id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(str(e), "danger")
            return render_template('edit_book.html', form=form, book=book)

        conn.close()
        flash("Book Updated", "success")
        return redirect(url_for('books'))

    conn.close()
    return render_template('edit_book.html', form=form, book=book)

# ✅ SINGLE DELETE (with FK check)
@app.route('/delete_book/<string:id>', methods=['POST'])
def delete_book(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # check if the book is referenced in transactions
        cur.execute("SELECT id FROM transactions WHERE book_id=%s", (id,))
        if cur.fetchone():
            flash("This book cannot be deleted because it has existing transactions", "warning")
        else:
            cur.execute("DELETE FROM books WHERE id=%s", (id,))
            conn.commit()
            flash("Book Deleted", "success")
    except Exception as e:
        conn.rollback()
        flash(str(e), "danger")
    finally:
        conn.close()
    return redirect(url_for('books'))

# ✅ MULTI-DELETE ROUTE (delete selected books)
@app.route('/books/delete_selected', methods=['POST'])
def delete_selected_books():
    ids = request.form.getlist('book_ids')
    if ids:
        conn = get_db_connection()
        cur = conn.cursor()
        skipped = []

        for book_id in ids:
            # check if there is a transaction for this book
            cur.execute("""
                SELECT transactions.id
                FROM transactions
                INNER JOIN books ON books.id = transactions.book_id
                WHERE transactions.book_id=%s
            """, (book_id,))
            if cur.fetchone():
                # get title
                cur.execute("SELECT title FROM books WHERE id=%s", (book_id,))
                title = cur.fetchone()['title']
                skipped.append(title)
            else:
                cur.execute("DELETE FROM books WHERE id=%s", (book_id,))

        conn.commit()
        conn.close()

        deleted_count = len(ids) - len(skipped)
        if deleted_count:
            flash(f"Deleted {deleted_count} book(s)", "success")
        if skipped:
            flash("These book(s) could not be deleted because of existing transactions: "
                 + ', '.join(skipped), "warning")

    return redirect(url_for('books'))
# ------------------------------------------------
# Transactions
# ------------------------------------------------
class IssueBook(Form):
    book_id = SelectField('Book ID', choices=[])
    member_id = SelectField('Member ID', choices=[])
    per_day_fee = FloatField('Per Day Renting Fee', [validators.NumberRange(min=1)])


@app.route('/transactions')
def transactions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions")
    transactions = cur.fetchall()
    conn.close()
    for transaction in transactions:
        for key, value in transaction.items():
            if value is None:
                transaction[key] = "-"
    if transactions:
        return render_template('transactions.html', transactions=transactions)
    else:
        return render_template('transactions.html', warning='No Transactions Found')


@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    form = IssueBook(request.form)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id,title FROM books")
    books = [(book['id'], book['title']) for book in cur.fetchall()]
    cur.execute("SELECT id,name FROM members")
    members = [(m['id'], m['name']) for m in cur.fetchall()]
    form.book_id.choices = books
    form.member_id.choices = members

    if request.method == 'POST' and form.validate():
        cur.execute("SELECT available_quantity FROM books WHERE id=%s", [form.book_id.data])
        available_quantity = cur.fetchone()['available_quantity']
        if available_quantity < 1:
            conn.close()
            return render_template('issue_book.html', form=form, error='No copies of this book are available')
        cur.execute("INSERT INTO transactions (book_id,member_id,per_day_fee) VALUES (%s,%s,%s)",
                    (form.book_id.data, form.member_id.data, form.per_day_fee.data))
        cur.execute("UPDATE books SET available_quantity=available_quantity-1, rented_count=rented_count+1 WHERE id=%s",
                    [form.book_id.data])
        conn.commit()
        conn.close()
        flash("Book Issued", "success")
        return redirect(url_for('transactions'))

    conn.close()
    return render_template('issue_book.html', form=form)


class ReturnBook(Form):
    amount_paid = FloatField('Amount Paid', [validators.NumberRange(min=0)])


@app.route('/return_book/<string:transaction_id>', methods=['GET', 'POST'])
def return_book(transaction_id):
    form = ReturnBook(request.form)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE id=%s", [transaction_id])
    transaction = cur.fetchone()
    date = datetime.now()
    days = (date - transaction['borrowed_on']).days
    total_charge = days * transaction['per_day_fee']

    if request.method == 'POST' and form.validate():
        cur.execute("SELECT outstanding_debt,amount_spent FROM members WHERE id=%s", [transaction['member_id']])
        result = cur.fetchone()
        if result['outstanding_debt'] + (total_charge - form.amount_paid.data) > 500:
            conn.close()
            return render_template('return_book.html', form=form, transaction=transaction,
                                   total_charge=total_charge, difference=days,
                                   error='Outstanding Debt Cannot Exceed Rs.500')
        cur.execute("UPDATE transactions SET returned_on=%s,total_charge=%s,amount_paid=%s WHERE id=%s",
                    (date, total_charge, form.amount_paid.data, transaction_id))
        cur.execute("UPDATE members SET outstanding_debt=%s, amount_spent=%s WHERE id=%s",
                    (result['outstanding_debt'] + (total_charge - form.amount_paid.data),
                     result['amount_spent'] + form.amount_paid.data, transaction['member_id']))
        cur.execute("UPDATE books SET available_quantity=available_quantity+1 WHERE id=%s", [transaction['book_id']])
        conn.commit()
        conn.close()
        flash("Book Returned", "success")
        return redirect(url_for('transactions'))

    conn.close()
    return render_template('return_book.html', form=form, transaction=transaction,
                           total_charge=total_charge, difference=days)


class SearchBook(Form):
    title = StringField('Title', [validators.Length(min=2, max=255)])
    author = StringField('Author(s)', [validators.Length(min=2, max=255)])


@app.route('/search_book', methods=['GET', 'POST'])
def search_book():
    form = SearchBook(request.form)
    if request.method == 'POST' and form.validate():
        conn = get_db_connection()
        cur = conn.cursor()
        title = '%' + form.title.data + '%'
        author = '%' + form.author.data + '%'
        cur.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s", (title, author))
        books = cur.fetchall()
        conn.close()
        if books:
            flash("Results Found", "success")
            return render_template('search_book.html', form=form, books=books)
        else:
            return render_template('search_book.html', form=form, warning='No Results Found')
    return render_template('search_book.html', form=form)


@app.route('/reports')
def reports():
    conn = get_db_connection()
    cur = conn.cursor()

    # Get highest paying customers (top 5)
    cur.execute("SELECT id,name,amount_spent FROM members ORDER BY amount_spent DESC LIMIT 5")
    members = cur.fetchall()

    # Get most popular books (top 5 by rented_count)
    cur.execute("SELECT id,title,author,total_quantity,available_quantity,rented_count FROM books ORDER BY rented_count DESC LIMIT 5")
    books = cur.fetchall()

    conn.close()
    return render_template('reports.html', members=members, books=books)


class ImportBooks(Form):
    no_of_books = IntegerField('No. of Books*', [validators.NumberRange(min=1)])
    quantity_per_book = IntegerField('Quantity Per Book*', [validators.NumberRange(min=1)])
    title = StringField('Title', [validators.Optional(), validators.Length(min=2, max=255)])
    author = StringField('Author(s)', [validators.Optional(), validators.Length(min=2, max=255)])
    isbn = StringField('ISBN', [validators.Optional(), validators.Length(min=10, max=10)])
    publisher = StringField('Publisher', [validators.Optional(), validators.Length(min=2, max=255)])

@app.route('/import_books', methods=['GET', 'POST'])
def import_books():
    form = ImportBooks(request.form)

    if request.method == 'POST' and form.validate():
        url = 'https://frappe.io/api/method/frappe-library?'
        parameters = {'page': 1}

        # Optional filters
        if form.title.data:
            parameters['title'] = form.title.data
        if form.author.data:
            parameters['author'] = form.author.data
        if form.isbn.data:
            parameters['isbn'] = form.isbn.data
        if form.publisher.data:
            parameters['publisher'] = form.publisher.data

        conn = get_db_connection()
        cur  = conn.cursor()

        no_of_books_imported = 0

        while no_of_books_imported < form.no_of_books.data:
            r   = requests.get(url + urllib.parse.urlencode(parameters))
            res = r.json()

            if not res['message']:
                break

            for book in res['message']:

                # (1) Skip if same ID already exists
                cur.execute("SELECT id FROM books WHERE id=%s", [book['bookID']])
                id_exists = cur.fetchone()

                # (2) Skip if same title+author already exists
                cur.execute("SELECT id FROM books WHERE title=%s AND author=%s",
                            (book['title'], book['authors']))
                duplicate_book = cur.fetchone()

                if not id_exists and not duplicate_book:

                    # Convert publication_date → YYYY-mm-dd (MySQL format)
                    pub_date = book['publication_date']
                    try:
                        d = datetime.strptime(pub_date, "%m/%d/%Y")
                        pub_date = d.strftime("%Y-%m-%d")
                    except:
                        pass

                    # Insert new book
                    cur.execute("""INSERT INTO books
                        (id,title,author,average_rating,isbn,isbn13,language_code,num_pages,
                         ratings_count,text_reviews_count,publication_date,publisher,total_quantity,available_quantity,rented_count)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (book['bookID'], book['title'], book['authors'], book['average_rating'],
                         book['isbn'], book['isbn13'], book['language_code'], book['  num_pages'],
                         book['ratings_count'], book['text_reviews_count'], pub_date,
                         book['publisher'], form.quantity_per_book.data, form.quantity_per_book.data, 0))

                    no_of_books_imported += 1

                    # Stop if limit reached
                    if no_of_books_imported == form.no_of_books.data:
                        break

            parameters['page'] += 1

        conn.commit()
        conn.close()
        flash(f"{no_of_books_imported} books imported", "success")
        return redirect(url_for('books'))

    return render_template('import_books.html', form=form)

if __name__ == '__main__':
    app.secret_key = "secret"
    app.run(debug=True)