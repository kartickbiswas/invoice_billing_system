from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from config import Config
from datetime import datetime


app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)


@app.route('/')
def home():
    if not CompanyDetails.query.first():
      return render_template('company.html')
    company_name = CompanyDetails.query.first().company_name
    total_customers = Customer.query.count()
    total_invoices = Invoice.query.count()
    total_products = Product.query.count()
    return render_template('home.html', company_name=company_name, total_customers=total_customers, total_invoices=total_invoices, total_products=total_products)


@app.route('/company', methods=['GET', 'POST'])
def company():
    if CompanyDetails.query.first():
        return render_template('company.html', company=CompanyDetails.query.first())

    if request.method == 'POST':
        company_name = request.form['company_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        gst_number = request.form['gst']
        company_details = CompanyDetails(company_name=company_name, email=email, phone=phone, address=address, gst_number=gst_number)
        db.session.add(company_details)
        db.session.commit()
    return render_template('company.html', company=CompanyDetails.query.first())

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        gst_number = request.form['gst']
        customer = Customer(name=name, email=email, phone=phone, address=address, gst_number=gst_number)
        db.session.add(customer)
        db.session.commit()

    all_customers = Customer.query.all()
    return render_template('customers.html', customers=all_customers)

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        tax_percent = float(request.form['tax_percent'])
        product = Product(name=name, description=description, price=price, tax_percent=tax_percent)
        db.session.add(product)
        db.session.commit()

    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/invoices', methods=['GET', 'POST'])
def invoices():
    if request.method == 'POST':
        invoice_number = request.form.get('invoice_number')
        customer_id = request.form.get('customer_id')
        status = request.form.get('status', 'Pending')
        date_created = request.form.get('date_created')
        
        if invoice_number and customer_id:
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            tax_percents = request.form.getlist('tax_percent[]')
            
            total_amount = 0
            total_tax = 0
            
            for i, product_id in enumerate(product_ids):
                if product_id:
                    qty = float(quantities[i]) if i < len(quantities) else 1
                    price = float(prices[i]) if i < len(prices) else 0
                    tax_percent = float(tax_percents[i]) if i < len(tax_percents) else 0
                    
                    item_total = price * qty
                    item_tax = item_total * (tax_percent / 100)
                    
                    total_amount += item_total
                    total_tax += item_tax
            
            invoice = Invoice(
                invoice_number=invoice_number,
                customer_id=int(customer_id),
                status=status,
                date_created=datetime.strptime(date_created, '%Y-%m-%d') if date_created else datetime.utcnow(),
                total_amount=total_amount,
                tax_amount=total_tax
            )
            db.session.add(invoice)
            db.session.flush()
            
            for i, product_id in enumerate(product_ids):
                if product_id:
                    qty = float(quantities[i]) if i < len(quantities) else 1
                    price = float(prices[i]) if i < len(prices) else 0
                    tax_percent = float(tax_percents[i]) if i < len(tax_percents) else 0
                    
                    item = InvoiceItem(
                        invoice_id=invoice.id,
                        product_id=int(product_id),
                        quantity=qty,
                        price=price,
                        tax_percent=tax_percent
                    )
                    db.session.add(item)
            
            db.session.commit()
            return render_template('invoice.html', invoices=Invoice.query.all(), customers=Customer.query.all(), products=Product.query.all(), message='Invoice created successfully!')
    
    all_invoices = Invoice.query.all()
    all_customers = Customer.query.all()
    all_products = Product.query.all()
    return render_template('invoice.html', invoices=all_invoices, customers=all_customers, products=all_products)

@app.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    return render_template('invoice.html', invoices=Invoice.query.all(), customers=Customer.query.all(), products=Product.query.all(), message='Invoice deleted successfully!')

@app.route('/invoices/<int:invoice_id>/print')
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    company = CompanyDetails.query.first()
    return render_template('invoice_print.html', invoice=invoice, company=company)



#Database Models

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Pending")

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    items = db.relationship('InvoiceItem', backref='invoice', lazy=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    gst_number = db.Column(db.String(50))

    invoices = db.relationship('Invoice', backref='customer', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    tax_percent = db.Column(db.Float, default=0)

class CompanyDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    gst_number = db.Column(db.String(50))
    logo = db.Column(db.String(200))

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    tax_percent = db.Column(db.Float, default=0)

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    
    product = db.relationship('Product', backref='invoice_items', lazy=True)

if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run(debug=True)
