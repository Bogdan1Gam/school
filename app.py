from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Judet
import os

app = Flask(__name__)

# URL-ul bazei de date (înlocuiește cu ce-ți dă Render)
DATABASE_URL = os.environ.get("DATABASE_URL")
# DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://schoolapi:SreJ22Sc7uVWu4G1hCBMt40lFVNAAtvH@dpg-d27rqveuk2gs73ejb530-a/schoolapi_738o")



# Setup SQLAlchemy
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

@app.route("/judete", methods=["GET"])
def get_judete():
    session = Session()
    judete = session.query(Judet).all()
    session.close()

    return jsonify({"judete": [j.nume for j in judete]})

if __name__ == "__main__":
    app.run()