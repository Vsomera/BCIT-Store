from database import db


class Product(db.Model):
    name = db.Column(db.String, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity
        }
    

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    products = db.relationship('ProductsOrder', back_populates='order')
    
class ProductsOrder(db.Model): 
    product_name = db.Column(db.ForeignKey("product.name"), primary_key=True) 
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False) 
 
    # Relationships and back  references for SQL Alchemy 
    product = db.relationship('Product') 
    order = db.relationship('Order', back_populates='products')    