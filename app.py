from flask import Flask, render_template, request, redirect, url_for
from models import db, ProductMonitor
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import check_product
from notifier import send_alert

def check_all_products(app):
    with app.app_context():
        products = ProductMonitor.query.all()
        for product in products:
            result = check_product(product.url, product.size, product.color)
            if result:
                product.current_price = result['current_price']
                product.original_price = result['original_price']
                product.is_on_sale = result['is_on_sale']
                product.last_checked = datetime.utcnow()

                if product.is_on_sale and product.original_price:
                    discount_percent = ((product.original_price - product.current_price) / product.original_price) * 100
                    if discount_percent >= product.target_discount_percent:
                        # Assume a default user email for this assignment, since we don't have user authentication
                        user_email = os.environ.get('USER_EMAIL', 'user@example.com')
                        send_alert(user_email, product)

        db.session.commit()

def create_app(database_uri='sqlite:///monitor.db'):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        products = ProductMonitor.query.all()
        return render_template('index.html', products=products)

    @app.route('/add', methods=['POST'])
    def add_product():
        name = request.form.get('name')
        url = request.form.get('url')
        size = request.form.get('size')
        color = request.form.get('color')
        target_discount = request.form.get('target_discount_percent')

        try:
            target_discount = float(target_discount) if target_discount else 0.0
        except ValueError:
            target_discount = 0.0

        if name and url:
            new_product = ProductMonitor(
                name=name,
                url=url,
                size=size,
                color=color,
                target_discount_percent=target_discount
            )
            db.session.add(new_product)
            db.session.commit()

        return redirect(url_for('index'))

    @app.route('/delete/<int:id>', methods=['POST'])
    def delete_product(id):
        product = ProductMonitor.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('index'))

    # Setup Scheduler - avoid duplicate in dev reloader
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=check_all_products, args=[app], trigger="interval", hours=24)
        scheduler.start()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't'), port=5000)
