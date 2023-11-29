#imports
import psycopg2

from scripts.db_config import db_config
from scripts.load_database import load_database
from scripts.log_undo import perform_undo

def main():
  conn = None
  try:
    # conecta com banco de dados e cria cursor
    params = db_config()
    conn = psycopg2.connect(**params)
    cursor = conn.cursor()

	  # carrega o banco
    load_database(cursor)

    # recuperar log UNDO
    perform_undo(cursor)
	
    conn.commit()
	  # fecha conexão com banco
    cursor.close()
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)

  finally:
    if conn is not None:
      conn.close()


if __name__ == '__main__':
  main()
