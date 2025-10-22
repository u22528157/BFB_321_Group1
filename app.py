from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash
import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'eece_components_secret_key_2025'  

# Database configuration
DATABASE = 'practical_management.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize database if it doesn't exist"""
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found. Please run init_db.py first.")
        return False
    return True

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM Student WHERE email_address = ?', (email,)
    ).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        # Login successful
        session['user_id'] = user['student_id']
        session['user_email'] = user['email_address']
        session['user_fullname'] = user['full_name']
        flash(f'Welcome back, {user["full_name"]}!', 'success')
        return redirect(url_for('main'))
    else:
        # Login failed
        flash('Invalid email or password. Please try again.', 'error')
        return redirect(url_for('home'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    fullname = request.form['fullname']
    email = request.form['email']
    password = request.form['password']
    
    # Validate input
    if not fullname or not email or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('signup'))
    
    if len(password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('signup'))
    
    conn = get_db_connection()
    
    # Check if user already exists
    existing_user = conn.execute(
        'SELECT * FROM Student WHERE email_address = ?', (email,)
    ).fetchone()
    
    if existing_user:
        flash('An account with this email already exists. Please login instead.', 'error')
        conn.close()
        return redirect(url_for('signup'))
    
    # Create new user
    try:
        password_hash = generate_password_hash(password)
        conn.execute(
            'INSERT INTO Student (full_name, email_address, password_hash) VALUES (?, ?, ?)',
            (fullname, email, password_hash)
        )
        conn.commit()
        
        # Get the new user's ID
        new_user = conn.execute(
            'SELECT * FROM Student WHERE email_address = ?', (email,)
        ).fetchone()
        
        # Log the user in automatically
        session['user_id'] = new_user['student_id']
        session['user_email'] = new_user['email_address']
        session['user_fullname'] = new_user['full_name']
        
        flash(f'Account created successfully! Welcome, {fullname}!', 'success')
        conn.close()
        return redirect(url_for('main'))
        
    except Exception as e:
        flash('An error occurred while creating your account. Please try again.', 'error')
        conn.close()
        return redirect(url_for('signup'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/main')
@login_required
def main():
    return render_template('main.html')

@app.route('/api/practicals')
@login_required
def get_practicals():
    """Get all practicals from database"""
    conn = get_db_connection()
    practicals = conn.execute('SELECT * FROM Practical ORDER BY prac_number').fetchall()
    conn.close()
    
    return jsonify([{
        'prac_number': p['prac_number'],
        'prac_name': p['prac_name']
    } for p in practicals])

@app.route('/api/practical/<int:prac_number>/components')
@login_required
def get_practical_components(prac_number):
    """Get components required for a specific practical"""
    conn = get_db_connection()
    
    # Get practical components with details
    components = conn.execute("""
        SELECT 
            pc.quantity,
            c.component_id,
            c.component_name,
            pc.alt_component_id,
            ac.alt_component_name
        FROM Practical_component pc
        JOIN Components c ON pc.component_id = c.component_id
        LEFT JOIN Alt_components ac ON pc.alt_component_id = ac.alt_component_id
        WHERE pc.practical_number = ?
        ORDER BY c.component_name
    """, (prac_number,)).fetchall()
    
    conn.close()
    
    return jsonify([{
        'component_id': comp['component_id'],
        'component_name': comp['component_name'],
        'quantity': comp['quantity'],
        'alt_component_id': comp['alt_component_id'],
        'alt_component_name': comp['alt_component_name']
    } for comp in components])

@app.route('/api/component/<int:component_id>/suppliers')
@login_required
def get_component_suppliers(component_id):
    """Get suppliers and pricing for a specific component"""
    conn = get_db_connection()
    
    suppliers = conn.execute("""
        SELECT 
            s.supplier_id,
            s.supplier_name,
            s.supplier_location,
            sc.quantity_in_stock,
            sc.price_component_per_supplier,
            c.component_name
        FROM Supplier_components sc
        JOIN Supplier s ON sc.supplier_id = s.supplier_id
        JOIN Components c ON sc.component_id = c.component_id
        WHERE sc.component_id = ?
        ORDER BY sc.price_component_per_supplier
    """, (component_id,)).fetchall()
    
    conn.close()
    
    return jsonify([{
        'supplier_id': sup['supplier_id'],
        'supplier_name': sup['supplier_name'],
        'supplier_location': sup['supplier_location'],
        'quantity_in_stock': sup['quantity_in_stock'],
        'price': float(sup['price_component_per_supplier']) if sup['price_component_per_supplier'] else 0,
        'component_name': sup['component_name'],
        'stock_status': 'In Stock' if sup['quantity_in_stock'] > 10 else f"{sup['quantity_in_stock']} left" if sup['quantity_in_stock'] > 0 else 'Out of Stock',
        'stock_level': 'high' if sup['quantity_in_stock'] > 10 else 'low' if sup['quantity_in_stock'] > 0 else 'out'
    } for sup in suppliers])

@app.route('/api/alt-component/<int:alt_component_id>/suppliers')
@login_required
def get_alt_component_suppliers(alt_component_id):
    """Get suppliers and pricing for alternative components"""
    conn = get_db_connection()
    
    suppliers = conn.execute("""
        SELECT 
            s.supplier_id,
            s.supplier_name,
            s.supplier_location,
            sac.alt_quantity_in_stock,
            sac.alt_price_component_per_supplier,
            ac.alt_component_name
        FROM Supplier_alt_components sac
        JOIN Supplier s ON sac.supplier_id = s.supplier_id
        JOIN Alt_components ac ON sac.alt_component_id = ac.alt_component_id
        WHERE sac.alt_component_id = ?
        ORDER BY sac.alt_price_component_per_supplier
    """, (alt_component_id,)).fetchall()
    
    conn.close()
    
    return jsonify([{
        'supplier_id': sup['supplier_id'],
        'supplier_name': sup['supplier_name'],
        'supplier_location': sup['supplier_location'],
        'quantity_in_stock': sup['alt_quantity_in_stock'],
        'price': float(sup['alt_price_component_per_supplier']) if sup['alt_price_component_per_supplier'] else 0,
        'component_name': sup['alt_component_name'],
        'stock_status': 'In Stock' if sup['alt_quantity_in_stock'] > 10 else f"{sup['alt_quantity_in_stock']} left" if sup['alt_quantity_in_stock'] > 0 else 'Out of Stock',
        'stock_level': 'high' if sup['alt_quantity_in_stock'] > 10 else 'low' if sup['alt_quantity_in_stock'] > 0 else 'out'
    } for sup in suppliers])

@app.route('/api/suppliers')
@login_required
def get_suppliers():
    """Get all suppliers"""
    conn = get_db_connection()
    suppliers = conn.execute('SELECT * FROM Supplier ORDER BY supplier_name').fetchall()
    conn.close()
    
    return jsonify([{
        'supplier_id': s['supplier_id'],
        'supplier_name': s['supplier_name'],
        'supplier_location': s['supplier_location']
    } for s in suppliers])

@app.route('/exit')
@login_required
def exit_page():
    user_email = session.get('user_email', 'student@example.com')
    cart_items = session.get('cart_items', [])
    return render_template('exit.html', user_email=user_email, cart_items=cart_items)

@app.route('/complete_practical', methods=['POST'])
@login_required
def complete_practical():
    # Get cart data from request
    data = request.get_json()
    if data and 'cart' in data:
        session['cart_items'] = data['cart']
    
    return jsonify({'success': True, 'redirect': '/exit'})

@app.route('/complete_redirect')
@login_required
def complete_redirect():
    return redirect(url_for('exit_page'))

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    try:
        # Get data from request
        data = request.get_json()
        rating = data.get('rating', 0)
        feedback = data.get('feedback', '')
        
        # Create customer_feedback directory if it doesn't exist
        feedback_dir = os.path.join(os.path.dirname(__file__), 'customer_feedback')
        os.makedirs(feedback_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'feedback_{timestamp}.txt'
        filepath = os.path.join(feedback_dir, filename)
        
        # Write feedback to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"COMPONENT COMPASS - Customer Feedback\n")
            f.write(f"================================\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"User: {session.get('user_fullname', 'Unknown')} ({session.get('user_email', 'Unknown')})\n")
            f.write(f"Rating: {rating}/5 stars\n")
            f.write(f"Feedback:\n{feedback}\n\n")
            f.write(f"---End of Feedback---\n")
        
        return jsonify({'success': True, 'message': 'Feedback saved successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving feedback: {str(e)}'}), 500

@app.route('/export_pdf', methods=['POST'])
@login_required
def export_pdf():
    try:
        # Get data from request
        data = request.get_json()
        components = data.get('components', [])
        student_email = session.get('user_email', 'student@example.com')
        
        # Create Reserved_components directory if it doesn't exist
        pdf_dir = os.path.join(os.path.dirname(__file__), 'Reserved_components')
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'reservation_{timestamp}.pdf'
        filepath = os.path.join(pdf_dir, filename)
        
        # Generate dates
        current_date = datetime.now().strftime('%B %d, %Y')
        collection_date = (datetime.now() + timedelta(days=3)).strftime('%B %d, %Y')
        
        # Calculate total cost
        total_cost = sum(component.get('price', 0) for component in components)
        
        if REPORTLAB_AVAILABLE:
            # Create PDF using ReportLab
            doc = SimpleDocTemplate(filepath, pagesize=letter, 
                                  rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=18)
            
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=10,
                alignment=0,  # Left alignment
                textColor=colors.black
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.black
            )

            # Enhanced Header with EE Logo styling
            from reportlab.platypus import KeepTogether
            from reportlab.lib.colors import HexColor
            
            # Create a table for the header with logo and title
            header_data = [
                [Paragraph('<para align="center" backColor="#8B5CF6" textColor="white" fontSize="18" fontName="Helvetica-Bold">EE</para>', styles['Normal']), 
                 Paragraph('ERS 220<br/>Component Reservation', title_style)]
            ]
            
            header_table = Table(header_data, colWidths=[0.8*inch, 4*inch])
            header_table.setStyle(TableStyle([
                # Logo cell styling (purple background, white text)
                ('BACKGROUND', (0, 0), (0, 0), HexColor('#8B5CF6')),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, 0), 18),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                
                # Title cell styling
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
                ('LEFTPADDING', (1, 0), (1, 0), 15),
                
                # Remove borders and add some styling
                ('BOX', (0, 0), (0, 0), 2, HexColor('#8B5CF6')),
                ('ROUNDEDCORNERS', (0, 0), (0, 0), [8, 8, 8, 8]),
            ]))
            
            story.append(header_table)
            story.append(Spacer(1, 30))
            
            # Header
            story.append(Paragraph('COMPONENT COMPASS', title_style))
            story.append(Paragraph('Reservations', title_style))
            story.append(Spacer(1, 20))
            
            # Student details table
            details_data = [
                ['Student:', session.get('user_fullname', 'Unknown')],
                ['Email:', student_email],
                ['Reservation Date:', current_date],
                ['Collection Deadline:', collection_date]
            ]
            
            details_table = Table(details_data, colWidths=[2*inch, 3*inch])
            details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(details_table)
            story.append(Spacer(1, 20))
            
            # Collection instructions
            story.append(Paragraph('Collection Instructions', header_style))
            story.append(Paragraph(
                'Please collect your reserved components within 3 days from the respective stores. '
                'Bring this reservation confirmation and your student ID.',
                styles['Normal']
            ))
            story.append(Spacer(1, 20))
            
            # Components table
            story.append(Paragraph('Reserved Components', header_style))
            
            # Table data
            table_data = [['Component Name', 'Store', 'Price']]
            
            for component in components:
                table_data.append([
                    component.get('name', ''),
                    component.get('store', ''),
                    f"${component.get('price', 0):.2f}"
                ])
            
            # Add total row
            table_data.append(['', 'Total Cost:', f'${total_cost:.2f}'])
            
            # Create table
            components_table = Table(table_data, colWidths=[3*inch, 2*inch, 1*inch])
            components_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.white]),
                
                # Total row
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                
                # All borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(components_table)
            story.append(Spacer(1, 30))
            
            # Good luck message
            story.append(Paragraph(
                'Good luck with your practical! We\'re excited to see what you\'ll build with these components.',
                ParagraphStyle('GoodLuck', parent=styles['Normal'], 
                             alignment=1, fontSize=12, textColor=colors.purple)
            ))
            story.append(Spacer(1, 20))
            
            # Disclaimer
            story.append(Paragraph(
                'Note: Components are reserved for 3 days only. Uncollected items will be released back to general stock.',
                ParagraphStyle('Disclaimer', parent=styles['Normal'], 
                             alignment=1, fontSize=10, textColor=colors.red, fontName='Helvetica-Oblique')
            ))
            
            # Build PDF
            doc.build(story)
            
        else:
            # Fallback: Create simple text file
            with open(filepath.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write("ERS 220 Component Reservation\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"Student: {session.get('user_fullname', 'Unknown')}\n")
                f.write(f"Email: {student_email}\n")
                f.write(f"Date: {current_date}\n")
                f.write(f"Collection Deadline: {collection_date}\n\n")
                f.write("Components:\n")
                f.write("-" * 50 + "\n")
                for component in components:
                    f.write(f"{component.get('name', '')} - {component.get('store', '')} - ${component.get('price', 0):.2f}\n")
                f.write("-" * 50 + "\n")
                f.write(f"Total: ${total_cost:.2f}\n")
        
        return jsonify({
            'success': True, 
            'message': f'PDF exported successfully! {"PDF" if REPORTLAB_AVAILABLE else "Text"} file created.',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating PDF: {str(e)}'}), 500

if __name__ == '__main__':
    # Initialize database on startup
    if not init_db():
        print("\nDatabase not found. Creating database...")
        # Run the database initialization script
        try:
            import subprocess
            import sys
            result = subprocess.run([sys.executable, 'init_db.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Database initialized successfully!")
            else:
                print("Database initialization failed:", result.stderr)
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    app.run(debug=True)


    @app.route('/exit')
def exit_page():
    user_email = session.get('user_email', 'student@example.com')
    cart_items = session.get('cart_items', [])
    return render_template('exit.html', user_email=user_email, cart_items=cart_items)

@app.route('/complete_practical', methods=['POST'])
def complete_practical():
    # Get cart data from request
    data = request.get_json()
    if data and 'cart' in data:
        session['cart_items'] = data['cart']
    
    return jsonify({'success': True, 'redirect': '/exit'})

@app.route('/complete_redirect')
def complete_redirect():
    return redirect(url_for('exit_page'))

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        # Get data from request
        data = request.get_json()
        rating = data.get('rating', 0)
        feedback = data.get('feedback', '')
        
        # Create customer_feedback directory if it doesn't exist
        feedback_dir = os.path.join(os.path.dirname(__file__), 'customer_feedback')
        os.makedirs(feedback_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'feedback_{timestamp}.txt'
        filepath = os.path.join(feedback_dir, filename)
        
        # Write feedback to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"COMPONENT COMPASS - Customer Feedback\n")
            f.write(f"================================\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Rating: {rating}/5 stars\n")
            f.write(f"Feedback:\n{feedback}\n\n")
            f.write(f"---End of Feedback---\n")
        
        return jsonify({'success': True, 'message': 'Feedback saved successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving feedback: {str(e)}'}), 500

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    try:
        # Get data from request
        data = request.get_json()
        components = data.get('components', [])
        student_email = data.get('student_email', 'student@example.com')
        
        # Create Reserved_components directory if it doesn't exist
        pdf_dir = os.path.join(os.path.dirname(__file__), 'Reserved_components')
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'reservation_{timestamp}.pdf'
        filepath = os.path.join(pdf_dir, filename)
        
        # Generate dates
        current_date = datetime.now().strftime('%B %d, %Y')
        collection_date = (datetime.now() + timedelta(days=3)).strftime('%B %d, %Y')
        
        # Calculate total cost
        total_cost = sum(component.get('price', 0) for component in components)
        
        if REPORTLAB_AVAILABLE:
            # Create PDF using ReportLab
            doc = SimpleDocTemplate(filepath, pagesize=letter, 
                                  rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=18)
            
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=10,
                alignment=0,  # Left alignment
                textColor=colors.black
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.black
            )

            # Enhanced Header with EE Logo styling
            from reportlab.platypus import KeepTogether
            from reportlab.lib.colors import HexColor
            
            # Create a table for the header with logo and title
            header_data = [
                [Paragraph('<para align="center" backColor="#8B5CF6" textColor="white" fontSize="18" fontName="Helvetica-Bold">EE</para>', styles['Normal']), 
                 Paragraph('ERS 220<br/>Component Reservation', title_style)]
            ]
            
            header_table = Table(header_data, colWidths=[0.8*inch, 4*inch])
            header_table.setStyle(TableStyle([
                # Logo cell styling (purple background, white text)
                ('BACKGROUND', (0, 0), (0, 0), HexColor('#8B5CF6')),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, 0), 18),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                
                # Title cell styling
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
                ('LEFTPADDING', (1, 0), (1, 0), 15),
                
                # Remove borders and add some styling
                ('BOX', (0, 0), (0, 0), 2, HexColor('#8B5CF6')),
                ('ROUNDEDCORNERS', (0, 0), (0, 0), [8, 8, 8, 8]),
            ]))
            
            story.append(header_table)
            story.append(Spacer(1, 30))
            
            # Header
            story.append(Paragraph('COMPONENT COMPASS', title_style))
            story.append(Paragraph('Reservations', title_style))
            story.append(Spacer(1, 20))
            
            # Student details table
            details_data = [
                ['Student Email:', student_email],
                ['Reservation Date:', current_date],
                ['Collection Deadline:', collection_date]
            ]
            
            details_table = Table(details_data, colWidths=[2*inch, 3*inch])
            details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(details_table)
            story.append(Spacer(1, 20))
            
            # Collection instructions
            story.append(Paragraph('Collection Instructions', header_style))
            story.append(Paragraph(
                'Please collect your reserved components within 3 days from the respective stores. '
                'Bring this reservation confirmation and your student ID.',
                styles['Normal']
            ))
            story.append(Spacer(1, 20))
            
            # Components table
            story.append(Paragraph('Reserved Components', header_style))
            
            # Table data
            table_data = [['Component Name', 'Store', 'Price']]
            
            for component in components:
                table_data.append([
                    component.get('name', ''),
                    component.get('store', ''),
                    f"${component.get('price', 0):.2f}"
                ])
            
            # Add total row
            table_data.append(['', 'Total Cost:', f'${total_cost:.2f}'])
            
            # Create table
            components_table = Table(table_data, colWidths=[3*inch, 2*inch, 1*inch])
            components_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.white]),
                
                # Total row
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                
                # All borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(components_table)
            story.append(Spacer(1, 30))
            
            # Good luck message
            story.append(Paragraph(
                'Good luck with your practical! We\'re excited to see what you\'ll build with these components.',
                ParagraphStyle('GoodLuck', parent=styles['Normal'], 
                             alignment=1, fontSize=12, textColor=colors.purple)
            ))
            story.append(Spacer(1, 20))
            
            # Disclaimer
            story.append(Paragraph(
                'Note: Components are reserved for 3 days only. Uncollected items will be released back to general stock.',
                ParagraphStyle('Disclaimer', parent=styles['Normal'], 
                             alignment=1, fontSize=10, textColor=colors.red, fontName='Helvetica-Oblique')
            ))
            
            # Build PDF
            doc.build(story)
            
        else:
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: #fafafa;
                        padding: 30px;
                    }}
                    
                    .pdf-preview {{
                        border: 2px solid #e1e8ed;
                        border-radius: 15px;
                        padding: 30px;
                        background: #fafafa;
                        margin-bottom: 30px;
                        position: relative;
                    }}
                    
                    .pdf-header {{
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                        margin-bottom: 30px;
                        padding-bottom: 20px;
                        border-bottom: 2px solid #e1e8ed;
                    }}
                    
                    .pdf-logo-section {{
                        display: flex;
                        align-items: center;
                    }}
                    
                    .pdf-logo {{
                        width: 50px;
                        height: 50px;
                        background-color: #8B5CF6;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 20px;
                        color: white;
                        margin-right: 15px;
                        border: 2px solid #8B5CF6;
                    }}
                    
                    .pdf-title {{
                        font-size: 22px;
                        font-weight: 700;
                        color: #2c3e50;
                        line-height: 1.2;
                    }}
                    
                    .student-details {{
                        text-align: right;
                        font-size: 14px;
                        color: #6b7280;
                    }}
                    
                    .collection-info {{
                        background: #f0f9ff;
                        border: 1px solid #0ea5e9;
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 20px;
                        font-size: 14px;
                        color: #0369a1;
                    }}
                    
                    .component-list {{
                        margin-bottom: 30px;
                    }}
                    
                    .component-item {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 15px;
                        border-bottom: 1px solid #e5e7eb;
                        font-size: 14px;
                    }}
                    
                    .component-name-store {{
                        flex: 1;
                    }}
                    
                    .component-name {{
                        font-weight: 600;
                        color: #2c3e50;
                    }}
                    
                    .component-store {{
                        color: #6b7280;
                        font-size: 12px;
                    }}
                    
                    .component-price {{
                        font-weight: 600;
                        color: #667eea;
                        min-width: 80px;
                        text-align: right;
                    }}
                    
                    .pdf-total {{
                        border-top: 2px solid #2c3e50;
                        padding-top: 15px;
                        margin-top: 20px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        font-size: 18px;
                        font-weight: 700;
                        color: #2c3e50;
                    }}
                    
                    .good-luck-message {{
                        background: #f0fdf4;
                        border: 1px solid #22c55e;
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 15px;
                        font-size: 14px;
                        color: #15803d;
                        text-align: center;
                    }}
                    
                    .disclaimer {{
                        font-size: 12px;
                        color: #6b7280;
                        text-align: center;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <div class="pdf-preview">
                    <div class="pdf-header">
                        <div class="pdf-logo-section">
                            <div class="pdf-logo">EE</div>
                            <div class="pdf-title">ERS 220<br>Component Reservation</div>
                        </div>
                        <div class="student-details">
                            <strong>Student Email:</strong> {student_email}<br>
                            <strong>Reservation Date:</strong> {current_date}<br>
                            <strong>Collection Deadline:</strong> {collection_date}
                        </div>
                    </div>

                    <div class="collection-info">
                        <strong>Collection Instructions:</strong> Please collect your reserved components within 3 days from the Electronics Lab (Room 201). Bring this reservation confirmation and your student ID.
                    </div>

                    <div class="component-list">
            """
            
            for component in components:
                html_content += f"""
                        <div class="component-item">
                            <div class="component-name-store">
                                <div class="component-name">{component.get('name', '')}</div>
                                <div class="component-store">{component.get('store', '')}</div>
                            </div>
                            <div class="component-price">${component.get('price', 0):.2f}</div>
                        </div>
                """
            
            html_content += f"""
                    </div>

                    <div class="pdf-total">
                        <span>Total Cost:</span>
                        <span>${total_cost:.2f}</span>
                    </div>

                    <div class="good-luck-message">
                        Good luck with your practical! We're excited to see what you'll build with these components.
                    </div>

                    <div class="disclaimer">
                        Note: Components are reserved for 3 days only. Uncollected items will be released back to general stock.
                    </div>
                </div>
            </body>
            </html>
            """
            
            # For now, save as HTML (can be printed to PDF by user)
            filepath = filepath.replace('.pdf', '.html')
            filename = filename.replace('.pdf', '.html')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return jsonify({
            'success': True, 
            'message': f'PDF exported successfully! {"PDF" if REPORTLAB_AVAILABLE else "HTML"} file created.',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating PDF: {str(e)}'}), 500

@app.route('/test_db')
def test_db():
    """Test database connection and data"""
    try:
        conn = get_db_connection()
        
        # Test tables exist
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [table['name'] for table in tables]
        
        # Test some data
        practicals = conn.execute('SELECT * FROM Practical').fetchall()
        components = conn.execute('SELECT * FROM Components').fetchall()
        suppliers = conn.execute('SELECT * FROM Supplier').fetchall()
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'tables': table_names,
            'practicals_count': len(practicals),
            'components_count': len(components),
            'suppliers_count': len(suppliers),
            'practicals': [dict(p) for p in practicals],
            'components': [dict(c) for c in components],
            'suppliers': [dict(s) for s in suppliers]
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
    