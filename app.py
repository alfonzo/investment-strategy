from flask import Flask, render_template
from database import (
    load_assets_from_db,
    load_positions_per_asset_from_db,
    get_asset_price,
    retrieve_and_update_asset_prices
)

app = Flask(__name__)


@app.route('/')
def home():
  assets = load_assets_from_db()
  
  # Get prices for all assets
  asset_prices = {asset['pair']: get_asset_price(asset['pair']) for asset in assets}
  
  return render_template(
      'home.html',
      assets=assets,
      load_positions_per_asset_from_db=load_positions_per_asset_from_db,
      asset_prices=asset_prices
  )
 

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
