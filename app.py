from flask import Flask, render_template, request, redirect, url_for
from database import (
    load_assets_from_db,
    load_positions_per_asset_from_db,
    get_asset_price,
    split_position,
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
 
@app.route('/split-position/<int:position_id>', methods=['POST'])
def split_position_route(position_id):
  # Get the form data
  split_value = request.form.get('split_value')
  split_percentage = request.form.get('split_percentage')

  # Validate form data (you may need additional validation)
  if not split_value and not split_percentage:
    return "Error: Split value or percentage is required"

  # Call the split_position function with the provided parameters
  try:
    split_value = float(split_value) if split_value else None
    split_percentage = float(split_percentage) if split_percentage else None
    split_position(position_id, split_value, split_percentage)
    return redirect(url_for('home'))  # Redirect to the home page after splitting
  except ValueError:
    return "Error: Invalid split value or percentage"
      

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
