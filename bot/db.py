# Update clients table to include language field

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(10), nullable=False)  # New language field
    # Other fields as necessary
