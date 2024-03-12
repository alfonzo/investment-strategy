from flask import Flask, render_template
from database import load_assets_from_db, load_positions_per_asset_from_db

app = Flask(__name__)

@app.route('/')
def home():
  assets = load_assets_from_db()
  return render_template('home.html', assets=assets, load_positions_per_asset_from_db=load_positions_per_asset_from_db)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
