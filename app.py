import random
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from database import db
from models import Product, Order, ProductsOrder

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
app.instance_path = Path(".").resolve()
db.init_app(app)


@app.route("/")
def home():
    data = Product.query.all()
    return render_template("index.html", products=data)


@app.route("/api/product/<string:name>", methods=["GET"])
def api_get_product(name):
    product = db.session.get(Product, name.lower())
    product_json = product.to_dict()
    return jsonify(product_json)


@app.route("/api/product", methods=["POST"]) # adds a product to the database
def api_create_product():
    data = request.json # sent data in raw json format
    # Check all data is provided
    for key in ("name", "price", "quantity"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400

    try:
        price = float(data["price"])
        quantity = int(data["quantity"])
        # Make sure they are positive
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        return (
            "Invalid values: price must be a positive float and quantity a positive integer",
            400,
        )

    product = Product(      # instance of a product object
        name=data["name"],
        price=price,
        quantity=quantity,
    )
    db.session.add(product)  # product added to the database
    db.session.commit()
    return "Item added to the database"


@app.route("/api/product/<string:name>", methods=["DELETE"]) # deletes product from db
    # TODO add validation to check if product exists in database before deletion (return with 404)

def api_delete_product(name):
    product = db.session.get(Product, name) # gets product from database
    db.session.delete(product)
    db.session.commit()
    return f"{name.lower()} deleted from database"



@app.route("/api/product/<string:name>", methods=["PUT"]) # edits product to db
def api_put_product(name):
    data = request.json  # data in raw json format

    for key in ("price", "quantity"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400

    try:
        price = float(data["price"])
        quantity = int(data["quantity"])
        # Make sure they are positive
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        return (
            "Invalid values: price must be a positive float and quantity a positive integer",
            400,
        )

    product = db.session.get(Product, name.lower()) # gets product from database
    product.price = price   # updates price
    product.quantity = quantity # updates quantity
    db.session.commit()
    return f"Product '{name.lower()}' has been Edited"

@app.route("/api/order/<int:order_id>", methods=["GET"])
def app_get_order(order_id):
    order = Order.query.get_or_404(order_id)
    products_order = ProductsOrder.query.all() # captures all queries in db
    products_list = []
    for products in products_order:
        if products.order_id == order_id:
            product_dict = {
                "name" : products.product_name,
                "quantity" : products.quantity,
            }
            products_list.append(product_dict)
    res = {
        "customer_name" : order.name,
        "customer_address" : order.address,
        "completed" : order.completed,
        "products" : products_list,
        # TODO "price" : sum(product["price"] for product in products_order)
    }
    return jsonify(res)

@app.route("/api/order", methods=["POST"])
def api_create_order():
    data = request.json # json request as a dictionary

    # TODO Validate json request data

    with app.app_context():
        new_order = Order(name=str(data["name"]), address=str(data["address"]))
        db.session.add(new_order)
        db.session.commit()
        print("New order, with ID", new_order.id)

        # adds five random products with random quantities to the order
        products = random.sample(Product.query.all(), k=5)

    for p in products:
        quantity = random.randint(1, 10)
        association = ProductsOrder(product=p, order=new_order, quantity=quantity)
        db.session.add(association)

    db.session.commit()

    return "Order added to the database"

@app.route("/api/product/<int:order_id>", methods=["PUT"])
def api_process_order(order_id):
    customer_order = db.session.get(Order, int(order_id))
    data = request.json # json request as a dictionary
    order_status = data["process"]

    if order_status.upper() != "TRUE":
        return f"The JSON provided is invalid (missing: {order_status})", 400
    
    # checks if order has already been processed
    if customer_order.completed == bool("TRUE"):
        return f"Customer order ID: {order_id} has already been processed"    

    
    products_order = ProductsOrder.query.all() # dict of all queries of the order in the db
    products_inventory = Product.query.all() # dict all queries of the order in the db

    order = [{ "name" : product.product_name, "quantity" : product.quantity } # Dict of products from order
                     for product in products_order]
    
    inventory = [ {"name" : product.name, "quantity" : product.quantity} # Dict of products from inventory
                      for product in products_inventory]
    
    
    # if the order contains more products than available, adjust the order accordingly. (manipulates order & inventory dicts)
    for item in order:
        product = next((p for p in inventory if p["name"] == item["name"]), None)
        if product:
            item_quantity = min(item["quantity"], product["quantity"])
            item["quantity"] = item_quantity
            product["quantity"] -= int(item_quantity)

    
    for item in inventory:
        for product in order:
                if product["name"] == item["name"]: 
                    # updates the changes in the database
                    products = db.session.get(Product, product["name"])
                    products.quantity = item["quantity"]
                    db.session.commit()


    # processes the order (changes completed to True)
    customer_order.completed = bool(order_status.upper()) 
    db.session.commit()

    return f"Order ID: {order_id} has been processed"


if __name__ == "__main__":
    app.run(debug=True)
