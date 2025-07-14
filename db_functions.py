import psycopg2
import os
import pandas as pd
from datetime import datetime
import json

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
        # print("Connection successful!")

        # Create a cursor to execute SQL queries
        df = pd.read_sql(sql_query, connection)

        # Close the cursor and connection
        connection.close()
        # print("Connection closed.")
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
        #print("Connection successful!")

        # Create a cursor to execute SQL queries
        cursor = connection.cursor()

        # Example query
        cursor.execute(sql_query)
        connection.commit()
        #print("Data inserted")

        # Close the cursor and connection
        cursor.close()
        connection.close()
        #print("Connection closed.")

    except Exception as e:
        print(f"Failed to connect: {e}")

def add_new_user(username, password, name, surname):
    archive_status = {"Lab": 0, "CCTV": 0, "Police": 0, "Hospital": 0, "Operations": 0, "Evidence_Photos": 0}
    end_game = {"mc_1": "not_opened", "mc_2": "not_opened", "mc_3": "not_opened", "mc_4": "not_opened", "mc_5": "not_opened", "mc_6": "not_opened", "mc_7": "not_opened", "mc_8": "not_opened", "mc_9": "not_opened", "Comments": -99, "finished_time": -99, "solved":0, "answers":""}
    hierarchy_status = {"archive_child1": -99, "archive_child2": -99, "archive_parent": -99}
    cities_infected = {"Peja": 0, "Klina": 0, "Vitia": 0, "Artana": 0, "Burimi": 0, "Decani": 0, "Juniku": 0,
                       "Sharri": 0, "Shtime": 0, "Besiana": 0, "Dardana": 0, "Drenasi": 15, "Ferizaj": 0, "Gjakova": 0,
                       "Gjilani": 0, "Lipjani": 13, "Mamusha": 0, "Zvecani": 0, "Kacaniku": 0, "Kllokoti": 0, "Parteshi": 0,
                       "Prizreni": 0, "Rahoveci": 0, "Shterpca": 0, "Theranda": 0, "Gracanica": 0, "Kastrioti": 0,
                       "Malisheva": 0, "Mitrovica": 0, "Prishtina": 15, "Ranillugu": 0, "Skenderaj": 0, "Vushtrria": 0,
                       "Leposaviqi": 0, "Fushe Kosova": 0, "Zubin Potoku": 0, "Hani i Elezit": 0, "Mitrovica e Veriut": 0}
    popup_status = {"NOTE_1": 1, "NOTE_2": 0, "NOTE_4": 0, "NOTE_5": 0}
    pwd_remember = {"12": 0, "24": 0, "25": 0, "26": 0, "29": 0, "30": 0, "m 1": 0, "m 2": 0, "m 3": 0, "m 4": 0, "m 5": 0, "m 6": 0, "m 7": 0, "m 8": 0, "m 9": 0}
    user_metadata = {"time": "0 Mins", "money_left": "1000$", "cities_infected": 3, "last_touched_button": -99, "restart_timer_state": 0, "store_what_happened": -99, "should_we_call_popup": -99, "virus_infection_rate": 0.2, "archive_button_child1_3sec_delay": -99, "archive_button_clicked_3sec_delay": -99}
    cards_open = {}
    archives_open = {}
    help_data = {"mc_1": "not_opened", "mc_2": "not_opened", "mc_3": "not_opened", "mc_4": "not_opened", "mc_5": "not_opened", "mc_6": "not_opened", "mc_7": "not_opened", "mc_8": "not_opened", "mc_9": "not_opened"}
    sql_query = f'''
        INSERT INTO users VALUES ('{username}', '{password}', '{name}', '{surname}');
        INSERT INTO all_metadata VALUES ('{username}', 
                                          NOW(), 
                                          '{str(archive_status).replace("'", '"')}', 
                                          '{str(end_game).replace("'", '"')}', 
                                          '{str(hierarchy_status).replace("'", '"')}', 
                                          '{str(cities_infected).replace("'", '"')}', 
                                          '{str(popup_status).replace("'", '"')}', 
                                          '{str(pwd_remember).replace("'", '"')}', 
                                          '{str(user_metadata).replace("'", '"')}', 
                                          '{str(cards_open).replace("'", '"')}', 
                                          '{str(help_data).replace("'", '"')}')
                                          '{str(archives_open).replace("'", '"')}');
    '''
    insert_edit_sql_data(sql_query)

def save_data_logout(username, cities_infected, money_left, time, store_what_happened, virus_infection_rate, restart_timer_state, should_we_call_popup, popup_status, archive_status, nr_cities_infected, pwd_remember, cards_open, help_data, archives_open):
    hierarchy_status = {"archive_child1": -99, "archive_child2": -99, "archive_parent": -99}
    user_metadata = {"time": time, "money_left": money_left, "cities_infected": cities_infected, "last_touched_button": -99,
                     "restart_timer_state": 0, "store_what_happened": -99, "should_we_call_popup": -99,
                     "virus_infection_rate": virus_infection_rate, "archive_button_child1_3sec_delay": -99,
                     "archive_button_clicked_3sec_delay": -99}

    sql_query = f'''
        UPDATE all_metadata
        SET archive_status = '{str(archive_status).replace("'", '"')}',
            hierarchy_status = '{str(hierarchy_status).replace("'", '"')}',
            nr_cities_infected = '{str(nr_cities_infected).replace("'", '"')}',
            popup_status = '{str(popup_status).replace("'", '"')}',
            pwd_remember = '{str(pwd_remember).replace("'", '"')}',
            user_metadata = '{str(user_metadata).replace("'", '"')}',
            cards_open = '{str(cards_open).replace("'", '"')}',
            help_data = '{str(help_data).replace("'", '"')}',
            archives_open = '{str(archives_open).replace("'", '"')}'
        WHERE username = '{username}';
    '''
    insert_edit_sql_data(sql_query)



def read_user_data(username=None):

    if username != None:
        sql_query_user_mtd = f'''
                SELECT *
                FROM all_metadata um
--                 JOIN all_metadata am ON um.username = am.username
                WHERE um.username = '{username}'
        '''
    else:
        sql_query_user_mtd = f'''
                        SELECT *
                        FROM all_metadata um
--                         JOIN all_metadata am ON um.username = am.username
                '''

    dff = read_sql_data(sql_query_user_mtd)
    dff = dff.replace(-99, None)
    all_json_data = {}
    for i in range(0, len(dff)):
        df = dff.iloc[i]

        json_data = {}


        json_data['cards_open'] = df['cards_open']

        for col in df['user_metadata'].keys():
            json_data[col] = df['user_metadata'][col]

        json_data['nr_cities_infected'] = df['nr_cities_infected']


        json_data['popup_status'] = df['popup_status']
        json_data['hierarchy_status'] = df['hierarchy_status']
        json_data['archive_status'] = df['archive_status']
        json_data['passwords_remember'] = df['pwd_remember']
        json_data['help_data'] = df['help_data']
        json_data['archives_open'] = df['archives_open']


        all_json_data[df['username']] = json_data

    return all_json_data


def read_all_users():
    sql_query_user_mtd = f'''
            SELECT *
            FROM users
    '''


    df = read_sql_data(sql_query_user_mtd)

    return df


def save_help_data(username, help_data, comments, time_start, answers, solved):
    end_game = {
        "comments":comments,
        "finished_time":time_start,
        "solved":solved,
        "answers":';'.join(answers)
    }

    for mc_cards in list(help_data.keys()):
        end_game[mc_cards] = help_data[mc_cards]

    sql_query = f'''
        UPDATE all_metadata
        SET end_game = '{str(end_game).replace("'", '"')}'
        WHERE username = '{username}';
    '''
    insert_edit_sql_data(sql_query)