from sqlalchemy import create_engine, text
import os
import requests
from datetime import datetime
import json

db_connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(
    db_connection_string,
    pool_recycle=3600,
    connect_args={'connect_timeout': 30}
)

def execute_query(query, values=None):
  with engine.connect() as conn:
    if values:
      result = conn.execute(text(query), values)
    else:
      result = conn.execute(text(query))
      
    results = []
    for row in result:
      results.append(row._asdict())
      
  return results

def load_assets_from_db():  
  results = execute_query("SELECT * FROM assets")
  return results

def load_positions_per_asset_from_db(asset_id):
  results = execute_query(
    'SELECT * FROM positions WHERE asset_id = :asset_id', 
    {'asset_id': asset_id})
  return results


def retrieve_and_update_asset_prices(update_existing=False):
  # Fetch pairs and ids from the assets table
  with engine.connect() as connection:
      query = text("SELECT id, pair FROM assets")
      result = connection.execute(query)
      asset_info = {row[1]: row[0] for row in result}

  
  # Retrieve asset data from the Gemini API
  base_url = "https://api.gemini.com/v1"
  response = requests.get(base_url + "/pricefeed")
  prices = response.json()
  
  # Get today's date
  today = datetime.today().date()
  
  with engine.connect() as connection:
    for price_data in prices:
      pair = price_data['pair']
 
      # Check if the pair is in the assets table
      if pair in asset_info:
        asset_id = asset_info[pair]
        price = float(price_data['price'])
        percent_change_24h = float(price_data['percentChange24h'])

        # Check if the price for today already exists in the prices table
        query = text(
            "SELECT COUNT(*) FROM prices "
            "WHERE asset_id = :asset_id AND date_created = :date"
        )

        result = connection.execute(query, {"asset_id": asset_id, "date": today})
        count = result.scalar()

        # If the price for today doesn't exist, insert it into the prices table
        if count == 0:
          insert_query = text(
            "INSERT INTO prices ("
              "asset_id, pair, price, percent_change_24h, date_created) "
            "VALUES (:asset_id, :pair, :price, :percent_change_24h, :date)"
          )

          connection.execute(insert_query, {
              "asset_id": asset_id,
              "pair": pair,
              "price": price,
              "percent_change_24h": percent_change_24h,
              "date": today
          })
          
        elif update_existing:
          # If update_existing is True, update existing prices for today
          update_query = text(
              "UPDATE prices SET price = :price, "
              "percent_change_24h = :percent_change_24h "
              "WHERE asset_id = :asset_id AND date_created = :date"
          )

          connection.execute(update_query, {
              "price": price,
              "percent_change_24h": percent_change_24h,
              "asset_id": asset_id,
              "date": today
          })

        # Commit the transaction
        connection.commit()
        
  print("Asset prices retrieved and updated successfully.")


def get_asset_price(asset_pair):
  # Get today's date
  today = datetime.today().date()

  with engine.connect() as connection:
      # Check if the price for today already exists in the prices table
      query = text("SELECT price FROM prices "
       "WHERE pair = :pair "
       "AND date_created = :date")
      result = connection.execute(query, {"pair": asset_pair, "date": today})
      price_row = result.fetchone()

      # If the price for today doesn't exist, 
      # call retrieve_and_update_asset_prices() to create it
      if price_row is None:
        retrieve_and_update_asset_prices()
        # Query the price again after updating
        result = connection.execute(query, {"pair": asset_pair, "date": today})
        price_row = result.fetchone()

      # Extract the price
      if price_row:
        price = price_row[0]
        return price
      else:
        # If price still doesn't exist, return None or handle the case accordingly
        return None


def split_position(position_id, split_value=None, split_percentage=None):
  if split_value is None and split_percentage is None:
    print("Error: Either split_value or split_percentage must be provided.")
    return

  # Connect to the database
  with engine.connect() as connection:
    # Retrieve the original position record
    select_query = text(
        "SELECT * FROM positions WHERE id = :position_id"
    )
    original_position = connection.execute(
        select_query, {"position_id": position_id}
    ).fetchone()

    # Check if the original position exists
    if original_position:
      # Calculate the size of the new position
      original_size = original_position[1]
      if split_value is not None:
          new_size = split_value
      elif split_percentage is not None:
          new_size = original_size * (split_percentage/100)
      else:
          new_size = original_size
      
      # Update the original position with the deducted size
      updated_size = original_size - new_size
      update_query = text(
          "UPDATE positions "
          "SET size = :updated_size "
          "WHERE id = :position_id"
      )
      connection.execute(update_query, {
          "updated_size": updated_size,
          "position_id": position_id
      })

      # Create the new position
      new_position_values = {
          "size": new_size,
          "notes": f"Position split from {position_id}",
          "date_created": datetime.now(),
          "asset_id": original_position[4],
          # Set the rest of the columns to null
          "buy_date": None,
          "buy_price": None,
          "sell_date": None,
          "sell_price": None,
          "stoploss_price": None,
          "profit_target": None,
          "fees": None
      }

      # Insert the new position record
      insert_query = text(
          "INSERT INTO positions (size, notes, date_created, asset_id, "
          "buy_date, buy_price, sell_date, "
          "sell_price, stoploss_price, profit_target, fees) "
          "VALUES (:size, :notes, :date_created, :asset_id, :buy_date, "
          ":buy_price, :sell_date, "
          ":sell_price, :stoploss_price, :profit_target, :fees)"
      )
      connection.execute(insert_query, new_position_values)

      # Commit the transaction
      connection.commit()
      
      print("Position split successfully.")
    else:
      print("Original position not found.")
