from sqlalchemy import create_engine, text
import os

db_connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(db_connection_string, pool_recycle=3600, connect_args={'connect_timeout': 30}
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
  results = execute_query('SELECT * FROM positions WHERE asset_id = :asset_id', {'asset_id': asset_id})
  return results
  