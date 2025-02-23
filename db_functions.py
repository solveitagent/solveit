import psycopg2
import os
import pandas as pd

def read_sql_data(sql_query):
    USER = os.getenv('db_user')
    PASSWORD = os.getenv('db_pwd')
    HOST = os.getenv('db_host')
    PORT = os.getenv('db_port')
    DBNAME = os.getenv('db_database')

    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("Connection successful!")

        # Create a cursor to execute SQL queries
        df = pd.read_sql(sql_query, connection)

        # Close the cursor and connection
        connection.close()
        print("Connection closed.")
        return df
    except Exception as e:
        print(f"Failed to connect: {e}")


def insert_edit_sql_data(sql_query):
    USER = os.getenv('db_user')
    PASSWORD = os.getenv('db_pwd')
    HOST = os.getenv('db_host')
    PORT = os.getenv('db_port')
    DBNAME = os.getenv('db_database')

    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("Connection successful!")

        # Create a cursor to execute SQL queries
        cursor = connection.cursor()

        # Example query
        cursor.execute(sql_query)
        connection.commit()
        print("Data inserted")

        # Close the cursor and connection
        cursor.close()
        connection.close()
        print("Connection closed.")

    except Exception as e:
        print(f"Failed to connect: {e}")

def add_new_user(username, password, name, surname):
    sql_query = f'''
        INSERT INTO users VALUES ('{username}', '{password}', '{name}', '{surname}');
        INSERT INTO users_metadata VALUES ('{username}', '3', '1000$', '0 Mins', NULL, 0.2, 0, NULL, NULL, NULL, NULL);
        INSERT INTO popup_status VALUES ('{username}', '0', '0', '0', '0');
        INSERT INTO nr_cities_infected VALUES ('{username}', '15', '15', '13');
        INSERT INTO hierarchy_status VALUES ('{username}', NULL, NULL, NULL);
        INSERT INTO archive_status VALUES ('{username}', '0', '0', '0', '0', '0', '0');
    '''
    insert_edit_sql_data(sql_query)

def save_data_logout(username, cities_infected, money_left, time, store_what_happened, virus_infection_rate, restart_timer_state, should_we_call_popup, popup_status, archive_status, nr_cities_infected):
    set_clause = ", ".join([f"<maca>{city.replace(' ', '_')}<maca> = '{nr_cities_infected[city]}'" for city in nr_cities_infected.keys()])
    set_clause = set_clause.replace('<maca>','"')
    store_what_happened = 'NULL' if store_what_happened == None else "'"+store_what_happened+"'"
    sql_query = f'''
        UPDATE users_metadata
        SET cities_infected = '{cities_infected}',
            money_left = '{money_left}',
            time = '{time}',
            store_what_happened = {store_what_happened},
            virus_infection_rate = {virus_infection_rate},
            restart_timer_state = {restart_timer_state},
            should_we_call_popup = '{should_we_call_popup}'
        WHERE username = '{username}';
        
        UPDATE popup_status 
        SET "NOTE_1" = '{popup_status['NOTE_1']}',
            "NOTE_2" = '{popup_status['NOTE_2']}',
            "NOTE_4" = '{popup_status['NOTE_4']}',
            "NOTE_5" = '{popup_status['NOTE_5']}'
        WHERE username = '{username}';
            
        UPDATE archive_status 
        SET "Hospital" = '{archive_status['Hospital']}',
            "Police" = '{archive_status['Police']}',
            "CCTV" = '{archive_status['CCTV']}',
            "Operations" = '{archive_status['Operations']}',
            "Lab" = '{archive_status['Lab']}',
            "Evidence_Photos" = '{archive_status['Evidence Photos']}'
        WHERE username = '{username}';  
        
        UPDATE nr_cities_infected
        SET {set_clause}
        WHERE username = '{username}';
        
        
    '''
    print(sql_query)
    insert_edit_sql_data(sql_query)



def read_user_data(cities, username=None):

    if username != None:
        sql_query_user_mtd = f'''
                SELECT *
                FROM users_metadata um
                JOIN popup_status ps ON um.username = ps.username
                JOIN nr_cities_infected nci ON um.username = nci.username
                JOIN archive_status arcs ON um.username = arcs.username
                WHERE um.username = '{username}'
        '''
    else:
        sql_query_user_mtd = f'''
                        SELECT *
                        FROM users_metadata um
                        JOIN popup_status ps ON um.username = ps.username
                        JOIN nr_cities_infected nci ON um.username = nci.username
                        JOIN archive_status arcs ON um.username = arcs.username
                '''

    dff = read_sql_data(sql_query_user_mtd)
    all_json_data = {}
    for i in range(0, len(dff)):
        df = dff.iloc[i]

        json_data = {}

        json_data['restart_timer_state'] = 0
        json_data['should_we_call_popup'] = None
        json_data['archive_button_child1_3sec_delay'] = None
        json_data['archive_button_clicked_3sec_delay'] = None
        json_data['cards_open'] = {}
        json_data['last_touched_button'] = None

        for col in ['time', 'money_left', 'store_what_happened', 'cities_infected', 'virus_infection_rate']:
            json_data[col] = df[col]


        cities = pd.read_csv('data/cities_information.csv')

        nr_cities_infected = {}
        for col in cities.City.tolist():
            nr_cities_infected[col] = df[col.replace(' ', '_')]

        json_data['nr_cities_infected'] = nr_cities_infected

        popup_status = {}
        for col in ['NOTE_1', 'NOTE_2', 'NOTE_4', 'NOTE_5']:
            popup_status[col] = df[col]

        json_data['popup_status'] = popup_status

        hierarchy_status = {}
        for col in ['archive_parent', 'archive_child1', 'archive_child2']:
            hierarchy_status[col] = None

        json_data['hierarchy_status'] = hierarchy_status

        archive_status = {}
        for col in ['Hospital', 'Police', 'CCTV', 'Operations', 'Lab']:
            archive_status[col] = df[col]

        archive_status['Evidence Photos'] = df['Evidence_Photos']
        json_data['archive_status'] = archive_status

        all_json_data[df['username'].iloc[0]] = json_data
    return all_json_data


def read_all_users():
    sql_query_user_mtd = f'''
            SELECT *
            FROM users
    '''

    print(sql_query_user_mtd)

    df = read_sql_data(sql_query_user_mtd)

    return df