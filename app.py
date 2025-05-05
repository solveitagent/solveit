import dash
from dash.dependencies import Input, Output, State, ALL
from dash import dash_table, dcc, html, no_update, callback_context
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash_mantine_components as dmc
from dash_player import DashPlayer
import pandas as pd
import time
import math
from uuid import uuid4
import random
import bcrypt
import json
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId
import base64
import os
from db_functions import read_user_data, save_data_logout, add_new_user, read_all_users, save_help_data


archive_culprits_table_df = pd.read_csv(
    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/culprits.csv')
archive_culprits_table_df[
    'Image'] = 'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/interviews/' + \
               archive_culprits_table_df['Image']
for col in ['ID', 'Name']:
    archive_culprits_table_df[col] = archive_culprits_table_df[col].str.lower()

cards = pd.read_csv('https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/Cards.csv')
for col in ['Code', 'Title']:
    cards[col] = cards[col].str.lower()

cities_info = pd.read_csv(
    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/cities_information.csv')
storyline_data = pd.read_csv(
    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/storylines.csv')
popup_info = pd.read_csv(
    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/popup_informations.csv')
markdown_lists = pd.read_csv(
    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/markdown_list.csv')
markdown_lists.password = markdown_lists.password.astype('str')
for col in ['title', 'password']:
    markdown_lists[col] = markdown_lists[col].str.lower()

archive_parent = pd.read_csv(
    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/ArchiveData_Parent.csv')
for col in ['id', 'pwd']:
    archive_parent[col] = archive_parent[col].str.lower()

archive_child1 = pd.read_csv(
    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/ArchiveData_Children1.csv')
archive_child2 = pd.read_csv(
    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/ArchiveData_Children2.csv')
for col in ['id']:
    archive_child1[col] = archive_child1[col].str.lower()
    archive_child2[col] = archive_child2[col].str.lower()

users = read_all_users()
for col in ['username']:
    users[col] = users[col].str.lower()

user_data = read_user_data(cities_info)

app_start_time = time.time()

cities_infected_beginning = {'Drenasi': 15, 'Prishtina': 15, 'Lipjani': 13}

for city in cities_info.City.tolist():
    if city in ['Drenasi', 'Prishtina', 'Lipjani']:
        continue
    ct = cities_info[cities_info == city].iloc[0]
    cities_infected_beginning[city] = 0

cities_info['Population rel'] = ((cities_info['Population'] - cities_info['Population'].min()) / (
            cities_info['Population'].max() - cities_info['Population'].min())) * (1 - 0.1) + 0.1

button_columns = [col for col in archive_parent.columns if col.startswith("has_button")]

# Extract non-empty values from these columns
archive_button_statuses = []
for col in button_columns:
    archive_button_statuses.extend(archive_parent[col][archive_parent[col] == archive_parent[col]].tolist())
    archive_button_statuses.extend(archive_child1[col][archive_child1[col] == archive_child1[col]].tolist())
archive_button_statuses_dict = {i: 0 for i in archive_button_statuses}

popup_statuses_dict = {i: 0 for i in popup_info['ID'].tolist()}

final_answers_dropdown_options = {
    "1. **_Where did the virus spread first?_**": [
        {"label": city, "value": city} for city in cities_info.City.tolist() + ['I dont know']
    ],
    "2. **_Who is Patient 0?_**": [
        {"label": culprit.title(), "value": culprit.title()} for culprit in
        archive_culprits_table_df.Name.unique().tolist() + ['I dont know']
    ],
    "3. **_How did the virus spread?_**": [
        {"label": "Through contact", "value": "Through contact"},
        {"label": "Aerosol transmission", "value": "Aerosol transmission"},
        {"label": "Waterborne", "value": "Waterborne"},
        {"label": "I dont know", "value": "I dont know"},
    ],
    "4. **_What is the name of the vaccine?_**": [
        {"label": "L-Serum", "value": "L-Serum"},
        {"label": "Nexora-Serum", "value": "Nexora-Serum"},
        {"label": "P-Serum", "value": "P-Serum"},
        {"label": "N-Serum", "value": "N-Serum"},
        {"label": "I dont know", "value": "I dont know"},
    ],
    "5. **_Who are the culprits?_**": [
        {"label": culprit.title(), "value": culprit.title()} for culprit in
        archive_culprits_table_df.Name.unique().tolist() + ['I dont know']
    ],
    "6. **_What was the motive?_**": [
        {"label": "Economic", "value": "Economic"},
        {"label": "Political", "value": "Political"},
        {"label": "Accidental", "value": "Accidental"},
        {"label": "I dont know", "value": "I dont know"},
    ],
}


help_data_start = {}
for crd in cards[cards.Code.str.contains('mc')].Code:
    help_data_start[crd] = 'not_opened'


app = dash.Dash(suppress_callback_exceptions=True, external_stylesheets=[dbc.icons.BOOTSTRAP, dbc.themes.BOOTSTRAP,
                                                                         'https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.css'],
                external_scripts=[
                    'https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.1/jquery.min.css',
                    'https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js'
                ]
                )
server = app.server

archive_layout = html.Div(
    [
        html.Div([
            html.Div([html.H6(id="time_sgs_archive", children='0 Mins'), html.P("Time since game started")],
                     className="mini_container mini_container_margin",
                     ),
            html.Div([html.H6(id="cities_outbreak_archive", children='3'), html.P("Outbreak Cities")],
                     className="mini_container mini_container_margin",
                     ),
            html.Div([html.H6(id="money_left_archive", children='1000$'), html.P("Money")],
                     className="mini_container mini_container_margin",
                     )
        ],
            className="row container-display",
        ),
        html.Div(
            [
                html.Div([
                    html.Div([
                        dcc.Input(
                            value='',
                            id="archive_input",
                            type="text",
                            placeholder="Search the archive",
                            style={
                                'flex': '1',
                                'marginRight': '10px',
                                'minWidth': '150px',
                            }
                        ),
                        html.Button(
                            'Submit',
                            id={"type": "archive_buttons", "index": 'INPUT'},
                            n_clicks=0,
                            disabled=False,
                            style={
                                'minWidth': '80px',
                            })],
                        style={
                            'display': 'flex',
                            'flexWrap': 'wrap',  # Allows wrapping of elements inside the div
                            'alignItems': 'center',  # Vertical alignment
                            'justifyContent': 'center',  # Horizontal alignment
                            'width': '100%',
                            'gap': '10px',  # Adds space between wrapped items
                            'padding': '10px',  # Adds some internal spacing
                            'boxSizing': 'border-box',  # Ensures padding is part of the width
                        }
                    ),
                ],
                    className="pretty_container twelve columns",
                ),

            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div([
                    html.Div(id='archive_input_button_div',
                             style={
                                 'display': 'flex',
                                 'flexWrap': 'wrap',  # Allows wrapping of elements inside the div
                                 'alignItems': 'center',  # Vertical alignment
                                 'justifyContent': 'center',  # Horizontal alignment
                                 'width': '100%',
                                 'gap': '10px',  # Adds space between wrapped items
                                 'padding': '10px',  # Adds some internal spacing
                                 'boxSizing': 'border-box',  # Ensures padding is part of the width
                             }),
                    html.Div(id='new-content')
                ],
                    className="pretty_container twelve columns",
                ),

            ],
            className="row flex-display",
        ),

    ],

)

interview_layout = html.Div(
    [
        html.Div([
            html.Div([html.H6(id="time_sgs_interview", children='0 Mins'), html.P("Time since game started")],
                     className="mini_container mini_container_margin",
                     ),
            html.Div([html.H6(id="cities_outbreak_interview", children='3'), html.P("Outbreak Cities")],
                     className="mini_container mini_container_margin",
                     ),
            html.Div([html.H6(id="money_left_interview", children='1000$'), html.P("Money")],
                     className="mini_container mini_container_margin",
                     )
        ],
            className="row container-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div([
                            dcc.Input(
                                value='',
                                id="suspects_input",
                                type="text",
                                placeholder="Please search for the interview",
                                style={
                                    'flex': '1',
                                    'marginRight': '10px',
                                    'minWidth': '150px',
                                }
                            ),
                            html.Button(
                                'Submit',
                                id='interview_button_clicked',
                                n_clicks=0,
                                disabled=False,
                                style={
                                    'minWidth': '80px',
                                })],
                            style={
                                'display': 'flex',
                                'flexWrap': 'wrap',  # Allows wrapping of elements inside the div
                                'alignItems': 'center',  # Vertical alignment
                                'justifyContent': 'center',  # Horizontal alignment
                                'width': '100%',
                                'gap': '10px',  # Adds space between wrapped items
                                'padding': '10px',  # Adds some internal spacing
                                'boxSizing': 'border-box',  # Ensures padding is part of the width
                            }
                        ),
                        html.Div(
                            html.Img(
                                id='image_layout',
                                src='https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/interviews/Unknown.png',
                                style={'width': '50%', 'height': 'auto', 'border-radius': '10%',
                                       'object-fit': 'cover'}),
                            style={'justifyContent': 'center', 'marginTop': '20px', 'display': 'flex'}
                        )
                    ],
                    className="pretty_container four columns",
                ),
                html.Div(
                    html.Div(
                        id='selected-row-output',
                        style={
                            'display': 'flex',
                            'flex-direction': 'column',
                            "max-height": "500px",  # Set maximum height in pixels (adjust as needed)
                            "overflow-y": "auto",  # Enables vertical scrolling if content exceeds max height
                            "padding": "10px",  # Optional: Add padding for better visual spacing
                        }
                    ),
                    className="pretty_container eight columns",
                ),

            ],
            className="row flex-display",
        ),

    ],

)

cards_layout = html.Div(
    [
        html.Div([
            html.Div([html.H6(id="time_sgs_cards", children='0 Mins'), html.P("Time since game started")],
                     className="mini_container mini_container_margin",
                     ),
            html.Div([html.H6(id="cities_outbreak_cards", children='3'), html.P("Outbreak Cities")],
                     className="mini_container mini_container_margin",
                     ),
            html.Div([html.H6(id="money_left_cards", children='1000$'), html.P("Money")],
                     className="mini_container mini_container_margin",
                     )
        ],
            className="row container-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div([
                            dcc.Input(
                                value='',
                                id="cards_input",
                                type="text",
                                placeholder="Please search for the card number",
                                style={
                                    'flex': '1',
                                    'marginRight': '10px',
                                    'minWidth': '150px',
                                }
                            ),
                            html.Button(
                                'Submit',
                                id={'type': 'cards_buttons_all', 'index': 'cards_button_clicked'},
                                n_clicks=0,
                                disabled=False,
                                style={
                                    'minWidth': '80px',
                                })],
                            style={
                                'display': 'flex',
                                'flexWrap': 'wrap',  # Allows wrapping of elements inside the div
                                'alignItems': 'center',  # Vertical alignment
                                'justifyContent': 'center',  # Horizontal alignment
                                'width': '100%',
                                'gap': '10px',  # Adds space between wrapped items
                                'padding': '10px',  # Adds some internal spacing
                                'boxSizing': 'border-box',  # Ensures padding is part of the width
                            }
                        ),
                    ],
                    className="pretty_container four columns",
                ),
                html.Div(
                    html.Div(
                        id='small_cards_grid',
                        style={
                            "display": "flex",
                            "flex-wrap": "wrap",  # Prevent wrapping to force horizontal scrolling
                            "gap": "20px",  # Space between cards
                            "height": "200px",  # Set height (adjust as needed)
                            "overflowY": "auto",  # Enable horizontal scrolling
                        },
                    ),
                    className="pretty_container eight columns",
                ),

            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            id='single_card_div',
                            style={'display': 'none', 'justify-content': 'center'},  # Center the card
                            children=[
                                html.Div(
                                    style={
                                        "width": "90%",  # Make it responsive by default
                                        "max-width": "600px",  # Prevent it from getting too wide
                                        "display": "flex",
                                        "align-items": "center",
                                        "justify-content": "center",
                                        "padding": "20px",
                                    },
                                    children=[
                                        dbc.Card(
                                            id='card_body_id',
                                            children=
                                            dbc.CardBody([
                                                html.H4(
                                                    id='single_card_title',
                                                    className="card-title",
                                                    style={
                                                        "text-align": "center",
                                                        "font-family": "'Libre Baskerville', serif",
                                                        "font-size": "clamp(1.4em, 2vw, 2.2em)",  # Responsive text
                                                        "font-weight": "bold",
                                                        "color": "#2d2b28",
                                                    }
                                                ),
                                                html.Hr(style={"border-top": "2px solid #2d2b28", "margin": "10px 0"}),
                                                html.Div(
                                                    children=[
                                                        html.Img(
                                                            id="single_card_thumbnail-img",
                                                            style={
                                                                "width": "100%",  # Always fit the container
                                                                "height": "auto",
                                                                "margin-bottom": "15px",
                                                                "border": "1px solid #2d2b28",
                                                                "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.2)",
                                                                "cursor": "pointer",
                                                                "object-fit": "cover",
                                                            }
                                                        ),
                                                        html.Img(
                                                            id="overlay_image",
                                                            src="https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/cards/magnifier.png",
                                                            style={
                                                                "position": "absolute",
                                                                "bottom": "10px",
                                                                "width": "clamp(20px, 5vw, 40px)",  # Responsive overlay
                                                                "height": "clamp(20px, 5vw, 40px)",
                                                                "opacity": "1",
                                                                "marginLeft": "-80%",
                                                                "marginBottom": "12px",
                                                            },
                                                        ),
                                                    ],
                                                    style={
                                                        "display": "flex",
                                                        "justify-content": "center",
                                                        "align-items": "center",
                                                        "height": "60%",
                                                        "overflow": "hidden",
                                                        "position": "relative",
                                                        "cursor": "pointer",
                                                    },
                                                    className="thumbnail-container"
                                                ),
                                                dcc.Markdown(
                                                    id='single_card_text',
                                                    className="card-text",
                                                    style={
                                                        "white-space": "pre-wrap",
                                                        "font-family": "'Courier New', monospace",
                                                        "font-size": "clamp(1em, 1.5vw, 1.2em)",  # Responsive font
                                                        "color": "#2d2b28",
                                                        "line-height": "1.6",
                                                    }
                                                ),
                                                html.Div(
                                                    [
                                                        dbc.Input(
                                                            id="cards_password",
                                                            placeholder="Please enter the Mystery Word!",
                                                            type="password",
                                                            style={
                                                                'background-color': 'rgba(0,0,0,0)',
                                                                'border': "1px solid #bbbbbb"
                                                            }
                                                        ),
                                                        html.Div(
                                                            html.Button(
                                                                'Submit', id='card_pwd_button',
                                                                style={
                                                                    'width': 'clamp(100px, 15vw, 150px)',  # Responsive button
                                                                    'alignItems': 'center'
                                                                }
                                                            ),
                                                            style={
                                                                'display': 'flex',
                                                                'alignItems': 'center',
                                                                'justifyContent': 'center',
                                                                'marginTop': '30px'
                                                            }
                                                        )
                                                    ],
                                                    style={'display': 'block'}
                                                ),
                                                html.Div(
                                                    style={"border-top": "1px solid #2d2b28", "margin-top": "10px"}
                                                ),
                                                dcc.Markdown(id='single_card_hint'),
                                            ]),
                                            style={
                                                "width": "100%",  # Adjust dynamically
                                                "max-width": "400px",  # Limit max width on larger screens
                                                "box-shadow": "0px 4px 8px rgba(0, 0, 0, 0.4)",
                                                "border": "2px solid #2d2b28",
                                                "border-radius": "5px",
                                                "background-color": "#fdf8e4",
                                                "background-image": "url('https://www.transparenttextures.com/patterns/cardboard.png')",
                                                "padding": "20px",
                                            },
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        html.Div(
                            style={
                                'display': 'flex',
                                'flexDirection': 'column',
                                'alignItems': 'center',
                                'justifyContent': 'center',
                                # 'height': '100vh',  # Optional: makes the parent div take the full viewport height
                            },
                            children=[
                                dcc.Markdown(id='markdown_text', style={'textAlign': 'left'}),
                                html.Div(
                                    children=[
                                        html.Button(
                                            "Can't find the password, help me!",
                                            id='markdown_text_help_more_button',
                                            style={'display': 'none'}
                                        )
                                    ],
                                    style={
                                        'display': 'flex',
                                        'justifyContent': 'center',
                                        'alignItems': 'center',
                                        'marginTop': '20px'  # Optional: adds space between the markdown and the button
                                    }
                                )
                            ]
                        )
                    ],
                    className="pretty_container twelve columns",
                ),

            ],
            className="row flex-display",
        )

    ],

)

final_answers_layout = html.Div(
    [

        html.Div(
            [
                html.Div([
                    dcc.Markdown('''
                            *The phone buzzes, and Commander Elira’s voice cuts through the tension.*

                            **Commander Elira**: Team, this is it. Time’s up, and Kosova is on the brink. I need answers—now.
                    '''),
                    html.Div([
                        html.Div(
                            [dcc.Markdown(question, style={'alignItems': 'center'}),
                             dcc.Dropdown(
                                 id=f"question_answer_input_{index}",  # Dynamic ID for each dropdown
                                 options=final_answers_dropdown_options[question],
                                 placeholder="Select an option",
                                 style={"flex": "2",  # Allocate space for the dropdown
                                        'backgroundColor': 'rgba(0,0,0,0)',
                                        "min-width": "200px", },
                             ),
                             ],
                            style={'display': 'flex',
                                   'alignItems': 'end',
                                   'flexWrap': 'wrap',  # Allows wrapping of elements inside the div
                                   'width': '100%',
                                   'gap': '10px',  # Adds space between wrapped items
                                   'padding': '2px',  # Adds some internal spacing
                                   'boxSizing': 'border-box', }
                        )
                        for index, question in enumerate(list(final_answers_dropdown_options.keys()))
                    ]

                    ),

                    dcc.Markdown('''
                    **Commander Elira**: No more delays. The fate of Kosova depends on this. Have you solved it? What’s your call?

                    *The line goes quiet, waiting for your response!*
                    '''),
                    html.Div(
                        children=[
                            dcc.Markdown('''
                            **Can you please share your impressions and comments about this game?**
                            ''', style={'alignItems': 'center'}),
                            dcc.Textarea(
                                id='comments_textarea',
                                placeholder='Comments!',
                                style={'width': '100%', 'height': 'auto', 'backgroundColor': 'rgba(0,0,0,0)'},
                            ),
                        ],
                        style={'marginTop':'15px'}
                    ),
                    html.Div(
                        html.Button('Submit', id='button_clicked', style={'width': '150px', 'alignItems': 'center'}),
                        style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                               'marginTop': '30px'}
                    )

                ],
                    className="pretty_container twelve columns",
                ),

            ],
            className="row flex-display",
        ),

    ],

)

main_screen = html.Div([
    html.Div(
        [
            # First div - Time button (left)
            html.Button(
                [
                    html.Img(
                        src='https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/main/menu_icon.png',
                        style={'height': '40px', 'width': '40px', 'marginRight': '5px'}),
                    html.P('Menu', style={'margin': '0px'})
                ],
                id='time_button',
                style={
                    'border': '0px solid #ddd',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'display': 'flex',
                    'width': 'auto',
                    'height': 'auto',
                    'marginLeft': '5px',
                    'padding': '0 0px',
                    'z-index': '2',
                    'flex-shrink': 0  # Prevent shrinking
                }
            ),

            # Second div - Title (centered)
            html.Div(
                [
                    html.H4(
                        "SolveIT",
                        style={"marginBottom": "0px"},
                    )
                ],
                style={'flex-grow': 1, 'textAlign': 'center', 'width': '100%', 'marginLeft': '-80px'}
                # Ensure it takes remaining space and centers text
            ),

            # Third div - Map button (right)
            html.Button(
                [
                    html.P('Map', style={'margin': '0px'}),
                    html.Img(
                        src='https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/main/map_icon.png',
                        style={'height': '40px', 'width': '40px', 'marginLeft': '5px'}),
                ],
                id='map_button',
                style={
                    'marginLeft': '-70px',
                    'border': '0px solid #ddd',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'display': 'flex',
                    'width': 'auto',
                    'height': 'auto',
                    'marginRight': '10px',
                    'padding': '0 0px',
                    'flex-shrink': 0  # Prevent shrinking
                }
            )
        ],
        className="header row",
        style={
            "margin-bottom": "25px",
            "display": "flex",
            'flex-wrap': 'nowrap',
            "justifyContent": "space-between",  # Space out the elements
            "alignItems": "center",  # Vertically align items
            "width": "100%",  # Make sure it takes the full width
        },
    ),
    dcc.Tabs(id='tab', children=[
        dcc.Tab(label='Archive', children=[archive_layout]),
        dcc.Tab(label='Interview', children=[interview_layout]),
        dcc.Tab(label='Cards', children=[cards_layout]),
        dcc.Tab(label='Final Answers', children=final_answers_layout),
    ]),
    dbc.Offcanvas(
        html.Div(
            [
                html.Div([
                    html.Div([
                        dcc.Input(id="lat_input", type="number", placeholder="Latitude"),
                        dcc.Input(id="lon_input", type="number", placeholder="Longitude"),
                        html.Button("Search Coordinates", id="search_long_lat_button", n_clicks=0)],
                        style={
                            'display': 'flex',
                            'flexWrap': 'wrap',  # Allows wrapping of elements inside the div
                            'alignItems': 'center',  # Vertical alignment
                            'justifyContent': 'center',  # Horizontal alignment
                            'width': '100%',
                            'gap': '10px',  # Adds space between wrapped items
                            'padding': '10px',  # Adds some internal spacing
                            'boxSizing': 'border-box',
                        }
                    )]
                ),
                html.Div(
                    dl.Map(
                        id="map",
                        children=[dl.TileLayer(),
                                  dl.DivMarker(
                                      position=[cities_info[cities_info.City == 'Drenasi']['Lat'].iloc[0],
                                                cities_info[cities_info.City == 'Drenasi']['Long'].iloc[0]],
                                      iconOptions=dict(
                                          html='<div><span>15</span></div>',
                                          className='marker-cluster marker-cluster-small',
                                          iconSize=[30, 30]
                                      )
                                  ),
                                  dl.DivMarker(
                                      position=[cities_info[cities_info.City == 'Prishtina']['Lat'].iloc[0],
                                                cities_info[cities_info.City == 'Prishtina']['Long'].iloc[0]],
                                      iconOptions=dict(
                                          html='<div><span>15</span></div>',
                                          className='marker-cluster marker-cluster-small',
                                          iconSize=[30, 30]
                                      )
                                  ),
                                  dl.DivMarker(
                                      position=[cities_info[cities_info.City == 'Lipjani']['Lat'].iloc[0],
                                                cities_info[cities_info.City == 'Lipjani']['Long'].iloc[0]],
                                      iconOptions=dict(
                                          html='<div><span>13</span></div>',
                                          className='marker-cluster marker-cluster-small',
                                          iconSize=[30, 30]
                                      )
                                  )

                                  ],
                        style={
                            "width": "98%",
                            "height": "80%",
                            "margin": "0px",
                            "padding": "0px",
                            'position': 'absolute'

                        },
                        center=[42.6026, 20.9030],  # Initial center
                        zoom=9  # Initial zoom level
                    ),
                    style={
                        'width': '100%',
                        'height': '80vh',  # Optional: Set a specific height for the container
                        'display': 'flex',
                        'justify-content': 'center',  # Centers the map horizontally in the div
                        'align-items': 'center',
                        'marginBottom': '10px'  # Centers the map vertically in the div
                    }
                )]
        ),
        id="offcanvas_scrollable",
        title="",
        style={"width": "60%"},
        placement='end',
        is_open=False,
        scrollable=False,
    ),
    dbc.Offcanvas(
        html.Div([
            # Buttons for Restart Game and Logout
            html.Div(
                [
                    dbc.Button("Restart Game", id="restart-game-button", color="secondary",
                               style={"marginRight": "10px", "marginBottom": "10px"}),
                    dbc.Button("Storyline Selection", id="logout-button", color="danger",
                               style={"marginRight": "10px", "marginBottom": "10px"}),
                    dbc.Button("Open tutorial video", id="open-video-button", color="primary",
                               style={"marginBottom": "10px"}),
                ],
                style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                       'flexWrap': 'wrap', 'maxWidth':'100%',
                       'marginBottom': '20px'}
            ),
            # Timer display
            html.Div(
                [
                    html.Span("⏱️", style={'fontSize': '48px', 'marginRight': '10px'}),
                    html.Div(
                        "120 seconds left",
                        id='timer-display',
                        style={'fontSize': '38px', 'fontWeight': 'bold'}
                    ),
                ],
                style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '20px'}
            ),
            # Start/Restart Button
            html.Div(
                [dbc.Button("Start timer", id='start-restart-button', color='primary', n_clicks=0,
                            style={'marginRight': '7px'}),
                 dbc.Button("Found it", id='found-word-button', color='primary', n_clicks=0,
                            style={'marginLeft': '7px'}),
                 ],
                style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}
            ),
        ]),
        id="offcanvas_scrollable_left",
        title="",
        style={"height": "50%"},
        placement='top',
        is_open=False,
        scrollable=False,
    ),
    # dcc.ConfirmDialog(
    #     id='confirm-dialog',
    #     message='',
    # ),
    dmc.Modal(
        id='confirm-dialog',
        zIndex=10000,
        title='Dr. Driton calls you and says',
        closeOnClickOutside=True,
        children=[
            dmc.Text(id='confirm-dialog_text'),
            dmc.Space(h=20),
        ]
    ),
    dcc.Interval(
        id='timer-interval',
        interval=1000,  # 1000 ms = 1 second
        n_intervals=0,  # Counter for intervals
        disabled=False  # Timer starts enabled
    ),
    dmc.Modal(
        id='alert_view',
        zIndex=10000,
        closeOnClickOutside=False,
        children=[
            dmc.Text(id='alert_text'),
            dmc.Space(h=20),
            dmc.Group([
                dmc.Button('Yes', id='alert_submit_button'),
                dmc.Button('No', color='red', variant='outline', id='alert_cancel_button')
            ])
        ]
    ),
    dmc.Modal(
        id='alert_view_other',
        zIndex=10000,
        title='Alert',
        closeOnClickOutside=True,
        children=[
            dmc.Text(id='alert_other_text'),
            dmc.Space(h=20),
        ]
    ),
    dmc.Modal(
        id='alert_more_help',
        zIndex=10000,
        title='Dr. Driton helps you with the investigation...',
        closeOnClickOutside=True,
        children=[
            dmc.Text(id='alert_more_help_text'),
            dmc.Space(h=20),
        ]
    ),
    dbc.Modal(
        [
            dbc.ModalBody(
                html.Img(
                    id='image_for_modal',  # Placeholder URL for image
                    style={
                        "width": "100%",  # Full size in the modal
                        "height": "auto",
                    }
                )
            ),
        ],
        id="image-modal",
        size="lg",  # Large modal
        is_open=False,
    ),
], style={'display': 'flex', 'flexDirection': 'column'})

login_screen = html.Div([
    # dcc.ConfirmDialog(
    #     id='confirm-dialog-login',
    #     message='',
    # ),
    dmc.Modal(
        id='confirm-dialog-login',
        zIndex=10000,
        title='Alert',
        closeOnClickOutside=True,
        children=[
            dmc.Text(id='confirm-dialog-login_text'),
            dmc.Space(h=20),
        ]
    ),
    html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "height": "100%",
            "width": "100%",
            "padding": "20px",
        },
        children=[
            # Logo at the top
            html.Img(
                src="https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/solveIT-logo.png",
                # Replace with the path to your logo image
                style={
                    "height": "100px",
                    "marginBottom": "20px",
                },
            ),
            # Input fields for username and password
            html.Div(
                style={"width": "300px", "textAlign": "center"},
                children=[
                    dbc.Input(
                        id="username_login",
                        value='',
                        placeholder="Enter your username",
                        type="text",
                        style={"marginBottom": "10px"},
                    ),
                    dbc.Input(
                        id="password_login",
                        value='',
                        placeholder="Enter your password",
                        type="password",
                        style={"marginBottom": "20px"},
                    ),
                ],
            ),
            # Login and Register buttons
            html.Div(
                style={"display": "flex", "gap": "10px", "justifyContent": "center"},
                children=[
                    dbc.Button("Login", id="login_btn_login", color="primary", n_clicks=0),
                    dbc.Button("Register", id="register_btn_login", color="secondary", n_clicks=0),
                ],
            ),
            dcc.Loading(
                id="loading_login",
                type="circle",  # Type of loader: 'circle', 'dot', 'default'
                children=html.Div(
                    id="message_login",
                    style={"marginTop": "50px", "color": "red", "fontWeight": "bold"},
                ),
            )
        ],
    )
], style={'display': 'flex', 'flexDirection': 'column'})

register_screen = html.Div([
    html.Div(
        [
            # First div - Time button (left)
            html.Button('Back',
                        id='back_button_register',
                        style={
                            'border': '1px solid #ddd',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'display': 'flex',
                            'width': '50px',
                            'marginLeft': '25px',
                            'padding': '0 0px',
                            'flex-shrink': 0  # Prevent shrinking
                        }
                        )
        ],
        className="header row",
        style={
            "margin-bottom": "25px",
            "display": "flex",
            'flex-wrap': 'nowrap',
            "justifyContent": "space-between",  # Space out the elements
            "alignItems": "center",  # Vertically align items
            "width": "100%",  # Make sure it takes the full width
        },
    ),
    # dcc.ConfirmDialog(
    #     id='confirm-dialog-register',
    #     message='',
    # ),
    dmc.Modal(
        id='confirm-dialog-register',
        zIndex=10000,
        title='Alert',
        closeOnClickOutside=True,
        children=[
            dmc.Text(id='confirm-dialog-register_text'),
            dmc.Space(h=20),
        ]
    ),
    html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "height": "100%",
            "height": "100%",
            "padding": "20px",
        },
        children=[
            # Logo
            html.Img(
                src="https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/solveIT-logo.png",
                # Replace with the path to your logo
                style={"height": "100px", "marginBottom": "20px"},
            ),
            # Title
            html.H2("Register Page", style={"marginBottom": "30px"}),

            # Input fields
            html.Div(
                style={"width": "300px", "textAlign": "center"},
                children=[
                    dbc.Input(
                        id="name_input_register",
                        placeholder="Enter your Name",
                        type="text",
                        style={"marginBottom": "10px"},
                    ),
                    dbc.Input(
                        id="surname_input_register",
                        placeholder="Enter your Surname",
                        type="text",
                        style={"marginBottom": "10px"},
                    ),
                    dbc.Input(
                        id="email_input_register",
                        placeholder="Enter your Email",
                        type="email",
                        style={"marginBottom": "10px"},
                    ),
                    dbc.Input(
                        id="password_input_register",
                        placeholder="Enter your Password",
                        type="password",
                        style={"marginBottom": "20px"},
                    ),
                ],
            ),

            # Submit Button
            dbc.Button(
                "Register", id="register_button_register", color="primary", n_clicks=0, style={"width": "100px"}
            ),
            dcc.Loading(
                id="loading_register",
                type="circle",  # Type of loader: 'circle', 'dot', 'default'
                children=html.Div(
                    id="message_register",
                    style={"marginTop": "50px", "color": "red", "fontWeight": "bold"},
                ),
            )

            # Output message
        ],
    )
], style={'display': 'flex', 'flexDirection': 'column'})


def storyline_func(storylines_returned):
    list_sl = []
    for i in range(len(storylines_returned)):
        if storylines_returned.iloc[i]['is_clickable']:
            is_displayed = False
            cursor_style = 'pointer'
            opacity_style = 1
            children_ = [
                html.H4(
                    storylines_returned.iloc[i]['name'],
                    style={
                        "color": "white",  # Text color
                        "backgroundColor": "rgba(0, 0, 0, 0.5)",  # Transparent black background
                        "padding": "10px",  # Padding inside the text block
                        "borderRadius": "5px",  # Optional: Rounded corners
                        "display": "inline-block",  # Ensures background fits the text width
                        "fontSize": "14px",
                    }
                ),
                html.P(
                    storylines_returned.iloc[i]['description'],
                    style={
                        "color": "white",  # Text color
                        "backgroundColor": "rgba(0, 0, 0, 0.5)",  # Transparent black background
                        "padding": "10px",  # Padding inside the text block
                        "borderRadius": "5px",  # Optional: Rounded corners
                        "marginTop": "10px",  # Spacing between elements
                        "display": "inline-block",  # Ensures background fits the text width
                        "fontSize": "10px",
                    }
                ),
            ]
        else:
            is_displayed = True
            cursor_style = 'not-allowed'
            opacity_style = 0.5
            children_ = []
        list_sl.append(
            dbc.Button(
                children=children_,
                className='mini_container',
                disabled=is_displayed,
                id={"type": "storyline_buttons", "index": storylines_returned.iloc[i]['id']},
                style={
                    "backgroundImage": f"url({storylines_returned.iloc[i]['image']})",  # Replace with your image URL
                    "backgroundSize": "cover",  # Ensures the image covers the entire div
                    "backgroundPosition": "center",  # Centers the image
                    "padding": "20px",  # Adds padding around the content
                    "borderRadius": "10px",  # Optional: Rounded corners
                    'height': '200px',
                    'cursor': cursor_style,
                    'opacity': opacity_style,
                    "overflowY": "auto",  # Enables vertical scrolling
                    "whiteSpace": "normal",  # Ensures text wraps to new lines
                    "wordWrap": "break-word",
		    "display":"flex",
		    "flexDirection":"column",
		    "alignItems":"center",
		    "overflowX": "hidden",
                    "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",  # Optional: Shadow for a card effect
                }
            )
        )
    return list_sl


storyline_screen = html.Div([
    html.Div(
        [
            # First div - Time button (left)
            html.Button('Log-Out',
                        id='back_button_storyline',
                        style={
                            'border': '1px solid #ddd',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'display': 'flex',
                            'width': '100px',
                            'marginLeft': '25px',
                            'padding': '0 0px',
                            'flex-shrink': 0  # Prevent shrinking
                        }
                        )
        ],
        className="header row",
        style={
            "margin-bottom": "25px",
            "display": "flex",
            'flex-wrap': 'nowrap',
            "justifyContent": "space-between",  # Space out the elements
            "alignItems": "center",  # Vertically align items
            "width": "100%",  # Make sure it takes the full width
        },
    ),
    # dcc.ConfirmDialog(
    #     id='confirm-dialog-storyline',
    #     message='',
    # ),
    dmc.Modal(
        id='confirm-dialog-storyline',
        zIndex=10000,
        title='Alert',
        closeOnClickOutside=True,
        children=[
            dmc.Text(id='confirm-dialog-storyline_text'),
            dmc.Space(h=20),
        ]
    ),
    dcc.Loading(
        id="fullscreen-loader",
        type="circle",  # Other options: "default", "dot"
        fullscreen=True,
        className="fullscreen-loader",
        children=[html.Div(id="show_loader_div")]
    ),
    html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "height": "100%",
            "height": "100%",
            "padding": "20px",
        },
        children=[
            html.H4('Select the storyline!'),
            dmc.SimpleGrid(
                cols=4,
                breakpoints=[
                    {'maxWidth': 1080, 'cols': 4},
                    {'maxWidth': 780, 'cols': 3},
                    {'maxWidth': 580, 'cols': 2},
                    {'maxWidth': 200, 'cols': 1},
                ],
                spacing='sm',
                verticalSpacing=2,
                style={'border': '1 px black'},
                children=storyline_func(storyline_data),
                id='storyline_div'
            )

            # Output message
        ],
    )
], style={'display': 'flex', 'flexDirection': 'column'})

app.layout = dmc.NotificationsProvider(
    html.Div([
        dcc.Store(id='initialized', data='/login', storage_type="local"),
        dcc.Store(id='store_money_cities_time', data={'time': '0 Mins', 'cities': '3', 'money': '1000$'},
                  storage_type="local"),
        dcc.Store(id='store_email', storage_type="local"),
        dcc.Store(id='store_what_happened', storage_type="local"),
        dcc.Store(id='nr_cities_infected', data=cities_infected_beginning, storage_type="local"),
        dcc.Store(id='virus_infection_rate', data=0.2, storage_type="local"),
        dcc.Store(id='restart_timer_state', data=0, storage_type="local"),
        dcc.Store(id='should_we_call_popup', data=None),
        dcc.Store(id='hierarchy_status', data={'archive_parent': None, 'archive_child1': None, 'archive_child2': None},
                  storage_type="local"),
        dcc.Store(id='popup_status', data=popup_statuses_dict, storage_type="local"),
        dcc.Store(id='archive_status', data=archive_button_statuses_dict, storage_type="local"),
        dcc.Store(id='archive_button_child1_3sec_delay', storage_type="local"),
        dcc.Store(id='archive_button_clicked_3sec_delay', storage_type="local"),
        dcc.Store(id='cards_open', data={}, storage_type="local"),
        dcc.Store(id='last_touched_button', storage_type="local"),
        dcc.Store(id="help_data", data=help_data_start, storage_type="local"),
        dcc.Store(id="previous_url", data=''),
        dcc.Interval(
            id='interval-component',
            interval=60 * 1000,  # Update every minute (in milliseconds)
            n_intervals=0  # Number of times the interval has been triggered
        ),
        dcc.Location(id="url", refresh=False),  # For routing
        html.Div(id='loginscreen', children=login_screen, style={'display': 'block'}),
        html.Div(id='registerscreen', children=register_screen, style={'display': 'none'}),
        html.Div(id='storylinescreen', children=storyline_screen, style={'display': 'none'}),
        html.Div(id='mainscreen', children=main_screen, style={'display': 'none'}),
        dbc.Modal(
            [
                dbc.ModalHeader("Don't forget to look at your email, and check your spam folder!"),
                dbc.ModalBody(
                    html.Div(
                        DashPlayer(
                            id="player",
                            url="https://youtu.be/2CDrKvceYPI",
                            controls=True,
                            width="100%",
                            height="100%",  # Ensures it takes full height
                        ),
                        # html.Video(
                        #    src="/assets/video/tutorial.mp4",
                        #    controls=True,
                        #    style={"width": "79%"}
                        # ),
                        style={
                            "width": "100%",
                            "height": "80vh",  # Adjust the height dynamically (change as needed)
                            "display": "flex",
                            "justify-content": "center",
                            "align-items": "center"
                        }
                    ),
                    style={"height": "auto"}  # Let modal body adjust naturally
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal", className="ml-auto")
                ),
            ],
            id="video-modal",
            is_open=False,
            size="xl",
            backdrop="static"
        ),

    ], id='mainContainer',
        style={'display': 'flex', 'flexDirection': 'column'})
)


def send_email(receiver_email):
    # Load and encode the Word Document
    response = requests.get('https://github.com/solveitagent/solveit/raw/refs/heads/main/data/RuleBook.pdf')
    doc_data = response.content
    encoded_doc = base64.b64encode(doc_data).decode()

    # HTML Email Content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }
            .header { text-align: center; margin-bottom: 20px; }
            .header h1 { color: #007BFF; }
            .content { margin-bottom: 30px; }
            .footer { text-align: center; margin-top: 20px; }
            .logo { max-width: 150px; height: auto; }
            .btn { display: inline-block; padding: 10px 20px; color: white; background-color: #007BFF; text-decoration: none; border-radius: 5px; }
            .btn:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Urgent Mission Briefing</h1>
            </div>
            <div class="content">
                <h2>Commander Elira's Mission Briefing</h2>
                <p><strong>Commander Elira</strong> stands at the front of the room, her expression hard and focused. She starts with the mission briefing:</p>

                <h2>Dear Agents,</h2>
                <p>The situation is critical. A highly contagious virus is spreading rapidly. Your expertise and sharp instincts are vital to contain this threat before it escalates further in all the municipalities of Kosovo.</p>

                <h2>Investigation Objectives</h2>
                <p>Throughout the investigation stages, your primary objectives are to answer the following questions:</p>
                <ul>
                    <li>Where did the virus spread first?</li>
                    <li>Who is Patient 0?</li>
                    <li>How did the virus spread?</li>
                    <li>What is the name of the vaccine?</li>
                    <li>Who are the culprits?</li>
                    <li>Who broke into the lab?</li>
                    <li>What was the motive?</li>
                </ul>

                <h2>Resources and Budget</h2>
                <p><strong>Commander Elira continues:</strong></p>
                <p>You have a budget of <strong>1000$</strong>—spend it wisely. Every time you change locations or invest in stopping the virus, you spend <strong>100$</strong>.</p>
                <p>Keep in mind you get <strong>3 free</strong> hints from an expert, each extra costs <strong>100$</strong>. Follow the <strong>Rule Book</strong> for more information.</p>

                <p class="warning">The fate of Kosovo is in your hands. Proceed with caution but act decisively. Time is not on our side.</p>
                
                <p>If you want to train-before the mission, open <strong>SC 1</strong>. If you want to start the mission directly open <strong>SC 5</strong>.</p>
            </div>
            <div class="footer">
                <p>Stay sharp, Agents. Kosovo is counting on you.</p>
                <img src="https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/solveIT-logo.png" alt="SolveIT Logo" class="logo">
            </div>
        </div>
    </body>
    </html>
    """

    # Create Word Document Attachment
    doc_attachment = Attachment(
        FileContent(encoded_doc),
        FileName('RuleBook.pdf'),
        FileType('application/pdf'),
        Disposition('attachment')  # This will be a downloadable attachment
    )

    # Create the email message
    message = Mail(
        from_email=os.getenv('email_sender'),
        to_emails=receiver_email,
        subject='Urgent Mission Briefing - Kosovo Virus Threat',
        html_content=html_content
    )

    # Attach the logo image
    message.attachment = doc_attachment

    # Send the email
    try:
        sg = SendGridAPIClient(os.getenv('sendgrid_api'))
        response = sg.send(message)
        print(f"Email sent! Status Code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send email: {e}")


@app.callback(
    Output({"type": "archive_buttons", "index": 'INPUT'}, "n_clicks"),
    Input("archive_input", "n_submit"),
    State({"type": "archive_buttons", "index": 'INPUT'}, "n_clicks"),
    prevent_initial_call=True
)
def trigger_button(n_submit, n_clicks):
    return n_clicks + 1


@app.callback(
    Output('interview_button_clicked', "n_clicks"),
    Input("suspects_input", "n_submit"),
    State('interview_button_clicked', "n_clicks"),
    prevent_initial_call=True
)
def trigger_button(n_submit, n_clicks):
    return n_clicks + 1


@app.callback(
    Output({'type': 'cards_buttons_all', 'index': 'cards_button_clicked'}, "n_clicks"),
    Input("cards_input", "n_submit"),
    State({'type': 'cards_buttons_all', 'index': 'cards_button_clicked'}, "n_clicks"),
    prevent_initial_call=True
)
def trigger_button(n_submit, n_clicks):
    return n_clicks + 1


@app.callback(
    Output('login_btn_login', "n_clicks"),
    Input("password_login", "n_submit"),
    State('login_btn_login', "n_clicks"),
    prevent_initial_call=True
)
def trigger_button(n_submit, n_clicks):
    return n_clicks + 1


@app.callback(
    Output('register_button_register', "n_clicks"),
    Input("password_input_register", "n_submit"),
    State('register_button_register', "n_clicks"),
    prevent_initial_call=True
)
def trigger_button(n_submit, n_clicks):
    return n_clicks + 1


@app.callback(
    Output("search_long_lat_button", "n_clicks"),
    Input("lon_input", "n_submit"),
    State("search_long_lat_button", "n_clicks"),
    prevent_initial_call=True
)
def trigger_button(n_submit, n_clicks):
    """Simulates a button click when Enter is pressed in the input field."""
    return n_clicks + 1


@app.callback(
    Output("card_pwd_button", "n_clicks"),
    Input("cards_password", "n_submit"),
    State("card_pwd_button", "n_clicks"),
    prevent_initial_call=True
)
def trigger_button(n_submit, n_clicks):
    """Simulates a button click when Enter is pressed in the input field."""
    if n_clicks:
        return n_clicks + 1
    else:
        return 1


def hash_password(password: str) -> str:
    salt = os.getenv('password_salt').encode()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


@app.callback(
    Output("loginscreen", "style"),
    Output("registerscreen", "style"),
    Output("storylinescreen", "style"),
    Output("mainscreen", "style"),
    Output('initialized', 'data'),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname == "/main":
        return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'block'}, '/main'
    elif pathname == '/register':
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, '/register'
    elif pathname == '/storyline':
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}, {'display': 'none'}, '/storyline'
    else:
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, '/login'


@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output('confirm-dialog-login_text', 'children'),
    Output('confirm-dialog-login', 'opened'),
    Output("store_email", "data", allow_duplicate=True),
    Output('message_login', 'children'),
    Output('previous_url', 'data', allow_duplicate=True),
    [Input("login_btn_login", "n_clicks")],
    [State("username_login", "value"), State("password_login", "value"), State("url", "pathname")],
    prevent_initial_call=True,
)
def handle_login(login_clicks, username, password, previous_url):
    if login_clicks:
        if username and password:
            password_hashed = hash_password(password)
            user_name_check = users[(users['username'] == username.lower()) & (users['password'] == password_hashed)]
            if len(user_name_check) == 1:
                #our_user = read_user_data(cities_info, username)[username]
                #button_, style_ = switch_between_input_and_back_button_archive('back_button')
                return (
                '/storyline', '', False, {'name': user_name_check.iloc[0]['name'], 'email': username}, '', previous_url)

            return no_update, 'Wrong username or password', True, no_update, no_update, no_update
    return no_update


@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output('previous_url', 'data', allow_duplicate=True),
    Input("register_btn_login", "n_clicks"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def handle_login_register(register_clicks, previous_url):
    if register_clicks > 0:
        return '/register', previous_url
    return no_update


@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output('confirm-dialog-register_text', 'children'),
    Output('confirm-dialog-register', 'opened'),
    Output("store_email", "data", allow_duplicate=True),
    Output('message_register', 'children'),
    Output('previous_url', 'data', allow_duplicate=True),
    Input("register_button_register", "n_clicks"),
    State("name_input_register", "value"),
    State("surname_input_register", "value"),
    State("email_input_register", "value"),
    State("password_input_register", "value"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def handle_register(n_clicks, name, surname, email, password, previous_url):
    if n_clicks:
        if all([name, surname, email, password]):
            global users
            if email.lower() not in users['username'].tolist():
                password_hashed = hash_password(password)
                new_data = pd.DataFrame(
                    {"username": [email.lower()], "password": [password_hashed], "name": [name], "surname": [surname]})
                users = pd.concat([users, new_data], ignore_index=True)
                new_element_key = email.lower()
                new_element_value = {"cities_infected": '3',
                                     "money_left": '1000$',
                                     "time": '0 Mins',
                                     "store_what_happened": None,
                                     "nr_cities_infected": cities_infected_beginning,
                                     "virus_infection_rate": 0.2,
                                     "restart_timer_state": 0,
                                     "should_we_call_popup": None,
                                     "hierarchy_status": {"archive_parent": None, "archive_child1": None,
                                                          "archive_child2": None},
                                     "popup_status": {"NOTE_1": 0, "NOTE_2": 0, "NOTE_4": 0, "NOTE_5": 0},
                                     "archive_status": {"Hospital": 0, "Police": 0, "CCTV": 0, "Operations": 0,
                                                        "Lab": 0, "Evidence Photos": 0},
                                     "archive_button_child1_3sec_delay": None,
                                     "archive_button_clicked_3sec_delay": None,
                                     "cards_open": {},
                                     "last_touched_button": None,
                                     }

                global user_data
                user_data[new_element_key] = new_element_value

                add_new_user(email.lower(), password_hashed, name, surname)

                return ('/storyline', '', False, {'name': name, 'email': email}, '', previous_url)
            else:
                return no_update, "This email already exists!", True, no_update, no_update, no_update
        else:
            return no_update, "Please fill in all fields.", True, no_update, no_update, no_update
    return no_update


@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output('previous_url', 'data', allow_duplicate=True),
    Input("back_button_register", "n_clicks"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def handle_login(back_button_register, previous_url):
    if back_button_register:
        return '/login', previous_url
    return no_update


# Logout and save state

@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("offcanvas_scrollable_left", 'is_open', allow_duplicate=True),
    Output('previous_url', 'data', allow_duplicate=True),
    Input("logout-button", "n_clicks"),
    State('time_sgs_archive', 'children'),
    State('cities_outbreak_archive', 'children'),
    State('money_left_archive', 'children'),
    State('store_what_happened', 'data'),
    State('nr_cities_infected', 'data'),
    State('virus_infection_rate', 'data'),
    State('restart_timer_state', 'data'),
    State('should_we_call_popup', 'data'),
    State('hierarchy_status', 'data'),
    State('popup_status', 'data'),
    State('archive_status', 'data'),
    State('archive_button_child1_3sec_delay', 'data'),
    State('archive_button_clicked_3sec_delay', 'data'),
    State('cards_open', 'data'),
    State('last_touched_button', 'data'),
    State('store_email', 'data'),
    State('url', 'pathname'),
    prevent_initial_call=True,
)
def handle_logout(logout_button, time, cities_infected, money_left, store_what_happened, nr_cities_infected,
                  virus_infection_rate,
                  restart_timer_state, should_we_call_popup, hierarchy_status, popup_status, archive_status,
                  archive_button_child1_3sec_delay,
                  archive_button_clicked_3sec_delay, cards_open, last_touched_button, store_email, previous_url):
    if logout_button:
        new_element_key = store_email['email']
        new_element_value = {"cities_infected": cities_infected,
                             "money_left": money_left,
                             "time": time,
                             "store_what_happened": store_what_happened,
                             "nr_cities_infected": nr_cities_infected,
                             "virus_infection_rate": virus_infection_rate,
                             "restart_timer_state": restart_timer_state,
                             "should_we_call_popup": None,
                             "hierarchy_status": hierarchy_status,
                             "popup_status": popup_status,
                             "archive_status": archive_status,
                             "archive_button_child1_3sec_delay": None,
                             "archive_button_clicked_3sec_delay": None,
                             "cards_open": cards_open,
                             "last_touched_button": last_touched_button,
                             }
        global user_data
        user_data[new_element_key] = new_element_value

        save_data_logout(store_email['email'], cities_infected, money_left, time, store_what_happened, virus_infection_rate, restart_timer_state, should_we_call_popup, popup_status, archive_status, nr_cities_infected)

        return '/storyline', False, previous_url
    return no_update


# Restart game
@app.callback(
    Output('interval-component', 'n_intervals', allow_duplicate=True),
    Output('time_sgs_archive', 'children', allow_duplicate=True),
    Output('time_sgs_interview', 'children', allow_duplicate=True),
    Output('time_sgs_cards', 'children', allow_duplicate=True),
    Output('cities_outbreak_archive', 'children', allow_duplicate=True),
    Output('cities_outbreak_interview', 'children', allow_duplicate=True),
    Output('cities_outbreak_cards', 'children', allow_duplicate=True),
    Output('money_left_archive', 'children', allow_duplicate=True),
    Output('money_left_interview', 'children', allow_duplicate=True),
    Output('money_left_cards', 'children', allow_duplicate=True),
    Output('store_what_happened', 'data', allow_duplicate=True),
    Output('nr_cities_infected', 'data', allow_duplicate=True),
    Output('help_data', 'data', allow_duplicate=True),
    Output('virus_infection_rate', 'data', allow_duplicate=True),
    Output('restart_timer_state', 'data', allow_duplicate=True),
    Output('should_we_call_popup', 'data', allow_duplicate=True),
    Output('hierarchy_status', 'data', allow_duplicate=True),
    Output('popup_status', 'data', allow_duplicate=True),
    Output('archive_status', 'data', allow_duplicate=True),
    Output('archive_button_child1_3sec_delay', 'data', allow_duplicate=True),
    Output('archive_button_clicked_3sec_delay', 'data', allow_duplicate=True),
    Output('cards_open', 'data', allow_duplicate=True),
    Output('last_touched_button', 'data', allow_duplicate=True),
    Output('selected-row-output', 'children', allow_duplicate=True),
    Output('image_layout', 'src', allow_duplicate=True),
    Output('new-content', 'children', allow_duplicate=True),
    Output('archive_input_button_div', 'children', allow_duplicate=True),
    Output('archive_input_button_div', 'style', allow_duplicate=True),
    Input("restart-game-button", "n_clicks"),
    prevent_initial_call=True,
)
def handle_restartgame(restart_button):
    if restart_button:
        button_, style_ = switch_between_input_and_back_button_archive('back_button')
        return (0, '0 Mins', '0 Mins', '0 Mins', '3', '3', '3', '1000$', '1000$', '1000$', None,
                cities_infected_beginning, help_data_start, 0.2,
                -1, None, {"archive_parent": None, "archive_child1": None, "archive_child2": None},
                {"NOTE_1": 0, "NOTE_2": 0, "NOTE_4": 0, "NOTE_5": 0},
                {"Hospital": 0, "Police": 0, "CCTV": 0, "Operations": 0, "Lab": 0, "Evidence Photos": 0}, None, None,
                {}, None, [], 'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/interviews/Unknown.png', [],
                button_, style_)
    return no_update


@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output('previous_url', 'data', allow_duplicate=True),
    Input("back_button_storyline", "n_clicks"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def handle_login(back_button_storyline, previous_url):
    if back_button_storyline:
        return '/login', previous_url
    return no_update


@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output('interval-component', 'n_intervals', allow_duplicate=True),
    Output('time_sgs_archive', 'children', allow_duplicate=True),
    Output('time_sgs_interview', 'children', allow_duplicate=True),
    Output('time_sgs_cards', 'children', allow_duplicate=True),
    Output('cities_outbreak_archive', 'children', allow_duplicate=True),
    Output('cities_outbreak_interview', 'children', allow_duplicate=True),
    Output('cities_outbreak_cards', 'children', allow_duplicate=True),
    Output('money_left_archive', 'children', allow_duplicate=True),
    Output('money_left_interview', 'children', allow_duplicate=True),
    Output('money_left_cards', 'children', allow_duplicate=True),
    Output('store_what_happened', 'data', allow_duplicate=True),
    Output('nr_cities_infected', 'data', allow_duplicate=True),
    Output('virus_infection_rate', 'data', allow_duplicate=True),
    Output('restart_timer_state', 'data', allow_duplicate=True),
    Output('should_we_call_popup', 'data', allow_duplicate=True),
    Output('hierarchy_status', 'data', allow_duplicate=True),
    Output('popup_status', 'data', allow_duplicate=True),
    Output('archive_status', 'data', allow_duplicate=True),
    Output('archive_button_child1_3sec_delay', 'data', allow_duplicate=True),
    Output('archive_button_clicked_3sec_delay', 'data', allow_duplicate=True),
    Output('cards_open', 'data', allow_duplicate=True),
    Output('last_touched_button', 'data', allow_duplicate=True),
    Output('selected-row-output', 'children', allow_duplicate=True),
    Output('image_layout', 'src', allow_duplicate=True),
    Output('new-content', 'children', allow_duplicate=True),
    Output('archive_input_button_div', 'children', allow_duplicate=True),
    Output('archive_input_button_div', 'style', allow_duplicate=True),
    Output('store_money_cities_time', 'data', allow_duplicate=True),
    Output('previous_url', 'data', allow_duplicate=True),
    Output('show_loader_div', 'children'),
    Output('help_data', 'data', allow_duplicate=True),
    Input({"type": "storyline_buttons", "index": ALL}, "n_clicks"),
    State("store_email", "data"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def handle_storyline(storyline_buttons, store_email, previous_url):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if ('storyline_buttons' not in triggered_id):
        return no_update
    else:
        button_index = json.loads(triggered_id)['index']
        if button_index == 'virus_storyline':
            user_data = read_user_data(cities_info, store_email['email'].lower())

            our_user = user_data[store_email['email'].lower()]
            button_, style_ = switch_between_input_and_back_button_archive('back_button')
            try:
                print('Sent email')
                send_email(store_email['email'].lower())
            except Exception as e:
                print(f'No Internet connection or {e}')
            # import time
            # time.sleep(50)
            return ('/main', int(our_user['time'].split(' ')[0]),
                    our_user['time'], our_user['time'], our_user['time'],
                    our_user['cities_infected'], our_user['cities_infected'], our_user['cities_infected'],
                    our_user['money_left'], our_user['money_left'], our_user['money_left'],
                    our_user['store_what_happened'], our_user['nr_cities_infected'], our_user['virus_infection_rate'],
                    our_user['restart_timer_state'],
                    our_user['should_we_call_popup'], our_user['hierarchy_status'], our_user['popup_status'],
                    our_user['archive_status'], our_user['archive_button_child1_3sec_delay'],
                    our_user['archive_button_clicked_3sec_delay'], our_user['cards_open'],
                    our_user['last_touched_button'], [],
                    'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/interviews/Unknown.png', [], button_,
                    style_,
                    {'time': our_user['time'], 'cities': our_user['cities_infected'], 'money': our_user['money_left']},
                    previous_url, '', help_data_start)

    return no_update


@app.callback(
    Output("store_money_cities_time", "data"),
    Input('time_sgs_archive', 'children'),
    Input('cities_outbreak_archive', 'children'),
    Input('money_left_archive', 'children'),
)
def on_initial_load(time_sgs_archive, cities_outbreak_archive, money_left_archive):
    if time_sgs_archive and cities_outbreak_archive and money_left_archive:
        return {'time': time_sgs_archive, 'cities': cities_outbreak_archive, 'money': money_left_archive}
    return no_update


@app.callback(
    Output('interval-component', 'n_intervals', allow_duplicate=True),
    Output('time_sgs_archive', 'children', allow_duplicate=True),
    Output('time_sgs_interview', 'children', allow_duplicate=True),
    Output('time_sgs_cards', 'children', allow_duplicate=True),
    Output('cities_outbreak_archive', 'children', allow_duplicate=True),
    Output('cities_outbreak_interview', 'children', allow_duplicate=True),
    Output('cities_outbreak_cards', 'children', allow_duplicate=True),
    Output('money_left_archive', 'children', allow_duplicate=True),
    Output('money_left_interview', 'children', allow_duplicate=True),
    Output('money_left_cards', 'children', allow_duplicate=True),
    Output('should_we_call_popup', 'data', allow_duplicate=True),
    Output('archive_button_child1_3sec_delay', 'data', allow_duplicate=True),
    Output('archive_button_clicked_3sec_delay', 'data', allow_duplicate=True),
    Output('last_touched_button', 'data', allow_duplicate=True),
    Output('selected-row-output', 'children', allow_duplicate=True),
    Output('image_layout', 'src', allow_duplicate=True),
    Output('new-content', 'children', allow_duplicate=True),
    Output('archive_input_button_div', 'children', allow_duplicate=True),
    Output('archive_input_button_div', 'style', allow_duplicate=True),
    Output('cards_open', 'data', allow_duplicate=True),
    Input("url", "pathname"),
    State("store_money_cities_time", "data"),
    State("cards_open", "data"),
    prevent_initial_call='initial_duplicate',
)
def on_initial_load(url, store_money_cities_time, cards_open):
    if url == "/main":
        button_, style_ = switch_between_input_and_back_button_archive('back_button')
        if len(cards_open) == 0:
            cd = {}
        else:
            cd = cards_open
        return (int(store_money_cities_time['time'].split(' ')[0]),
                store_money_cities_time['time'], store_money_cities_time['time'], store_money_cities_time['time'],
                store_money_cities_time['cities'], store_money_cities_time['cities'], store_money_cities_time['cities'],
                store_money_cities_time['money'], store_money_cities_time['money'], store_money_cities_time['money'],
                None, None, None, None, [],
                'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/interviews/Unknown.png', [], button_,
                style_, cd)
    return no_update


@app.callback(
    Output("video-modal", "is_open"),
    [
        Input("url", "pathname"),
        Input("close-modal", "n_clicks"),
        Input("open-video-button", 'n_clicks'),
    ],
    [
        State("video-modal", "is_open"),
        State('previous_url', 'data'),
    ]
)
def toggle_modal(url, close_click, open_video_click, is_open, previous_url):
    if (close_click or open_video_click):
        if (previous_url == '/storyline'):
            return not is_open
    if (url == "/main") & (previous_url == '/storyline'):
        return not is_open
    return is_open


@app.callback(
    Output("map", "children", allow_duplicate=True),
    Output('nr_cities_infected', 'data', allow_duplicate=True),
    Output('confirm-dialog', 'opened', allow_duplicate=True),
    Output('confirm-dialog', 'title', allow_duplicate=True),
    Output('confirm-dialog_text', 'children', allow_duplicate=True),
    Output('cities_outbreak_archive', 'children', allow_duplicate=True),
    Output('cities_outbreak_interview', 'children', allow_duplicate=True),
    Output('cities_outbreak_cards', 'children', allow_duplicate=True),
    Input('interval-component', 'n_intervals'),
    Input('nr_cities_infected', 'data'),
    State('cities_outbreak_archive', 'children'),
    State('virus_infection_rate', 'data'),
    prevent_initial_call=True
)
def update_time_since_start(n, nr_cities_infected, cities_outbreak, virus_infection_rate):
    # Calculate the time since the app started in minutes
    elapsed_time = n  # (time.time() - app_start_time) / 60  # Convert to minutes
    show_alert = False
    message_alert = ''
    cities_infected = int(cities_outbreak)
    if elapsed_time % 10 == 0 and elapsed_time != 0:
        print('Infect a new city every 10 mins!')
        keys_with_zero = [key for key, value in nr_cities_infected.items() if value == 0]

        # Randomly select one key and change its value to 1
        if keys_with_zero:
            selected_key = random.choice(keys_with_zero)
            nr_cities_infected[selected_key] = 1
            show_alert = True
            message_alert = f'Unfortunately you couldnt contain the virus and the virus spread in {selected_key}'
            cities_infected = int(cities_outbreak) + 1

    if elapsed_time % 3 == 0 and elapsed_time != 0:
        for city, value in nr_cities_infected.items():
            if value > 0:
                print('MACAAAA:',city)
                new_nr_infected = value + math.ceil(
                    value * virus_infection_rate * cities_info[cities_info.City == city]['Population rel'].iloc[0])
                if cities_info[cities_info.City == city].iloc[0].Population >= new_nr_infected:
                    nr_cities_infected[city] = new_nr_infected
            else:
                nr_cities_infected[city] = 0

    filtered_dict = {key: int(value) for key, value in nr_cities_infected.items() if int(value) > 0}

    to_add = [dl.TileLayer()]
    for city in filtered_dict.keys():
        icon = dict(
            # str(filtered_dict[city])
            html='<div><span>' + str(filtered_dict[city]) + '</span></div>',
            className='marker-cluster marker-cluster-small',
            iconSize=[30, 30]
        )
        new_marker = dl.DivMarker(
            position=[cities_info[cities_info.City == city]['Lat'].iloc[0],
                      cities_info[cities_info.City == city]['Long'].iloc[0]],
            iconOptions=icon
        )
        to_add.append(new_marker)

    return to_add, nr_cities_infected, show_alert, 'Dr. Driton calls you and says:', message_alert, str(
        cities_infected), str(cities_infected), str(cities_infected)


@app.callback(
    Output('time_sgs_archive', 'children'),
    Output('time_sgs_interview', 'children'),
    Output('time_sgs_cards', 'children'),
    Input('interval-component', 'n_intervals'),
    State('nr_cities_infected', 'data'),
    prevent_initial_call=True
)
def update_time_since_start(n, nr_cities_infected):
    # Calculate the time since the app started in minutes
    elapsed_time = n
    elapsed_timee = f'{elapsed_time:.0f} Mins'
    return elapsed_timee, elapsed_timee, elapsed_timee


@app.callback(
    Output('offcanvas_scrollable', 'is_open'),
    Input('map_button', 'n_clicks'),
    State('offcanvas_scrollable', 'is_open'),
)
def toggle_offcanvas_scrollable(map_button, is_open):
    if map_button:
        return not is_open
    return is_open


@app.callback(
    Output('offcanvas_scrollable_left', 'is_open'),
    Output('found-word-button', 'n_clicks'),
    Input('time_button', 'n_clicks'),
    State('offcanvas_scrollable_left', 'is_open'),
    State('found-word-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_offcanvas_scrollable(map_button, is_open, n_clicks):
    if map_button:
        return not is_open, n_clicks + 1
    return no_update


@app.callback(
    Output("map", "zoom"),
    Input("search_long_lat_button", "n_clicks"),
    State("lat_input", "value"),
    State("lon_input", "value"),
)
def update_map_center(n_clicks, lat, lon):
    if n_clicks > 0 and lat and lon:
        return 18
    return no_update


@app.callback(
    [
        Output("map", "children"),
        Output("map", "center"),
        Output("lat_input", "value"),
        Output("lon_input", "value"),
    ],
    Input("map", "zoom"),
    State("lat_input", "value"),
    State("lon_input", "value"),
    State('nr_cities_infected', 'data'),
    State("map", "children"),
)
def update_map_center(zoom, lat, lon, nr_cities_infected, to_add):
    if lat and lon:
        lat = float(lat)
        lon = float(lon)

        coords = [lat, lon]
        new_marker = dl.Marker(
            position=coords,
            children=[dl.Tooltip(f"Selected Coordinates  {lat}, {lon}")]
        )

        to_add.append(new_marker)
        return to_add, coords, '', ''
    return no_update


@app.callback(
    [
        Output('timer-display', 'children', allow_duplicate=True),
        Output('timer-interval', 'n_intervals', allow_duplicate=True),
        Output('timer-interval', 'disabled', allow_duplicate=True),
        Output('start-restart-button', 'children', allow_duplicate=True),
        Output('restart_timer_state', 'data', allow_duplicate=True),
        Output('money_left_archive', 'children', allow_duplicate=True),
        Output('money_left_interview', 'children', allow_duplicate=True),
        Output('money_left_cards', 'children', allow_duplicate=True),
    ],
    [
        Input('timer-interval', 'n_intervals'),
        Input('start-restart-button', 'n_clicks'),
        Input('found-word-button', 'n_clicks')
    ],
    State('money_left_archive', 'children'),
    State('timer-interval', 'disabled'),
    State('restart_timer_state', 'data'),
    prevent_initial_call=True
)
def update_timer(n_intervals, n_clicks_start, n_clicks_found, money_left, is_disabled, n_clicks_last):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'found-word-button':
        return "120 seconds left", 0, True, "Start timer", no_update, no_update, no_update, no_update

    # If button is clicked, reset timer and start
    if n_clicks_start == 0:
        return "120 seconds left", 0, True, "Start timer", n_clicks_start, no_update, no_update, no_update

    if n_clicks_start > 0:
        if button_id == 'start-restart-button':  # if n_clicks_start>n_clicks_last:
            return "120 seconds left", 0, False, "Restart timer", n_clicks_start, no_update, no_update, no_update

    # Countdown logic
    seconds_left = 120 - n_intervals
    if seconds_left <= 0:
        money_left = int(money_left.split('$')[0])
        money_left = money_left - 100
        money_left = str(money_left) + '$'
        return "Time's up!", 0, True, "Start timer", n_clicks_start, money_left, money_left, money_left

    return f"{seconds_left} seconds left", n_intervals, False, "Restart timer", n_clicks_start, no_update, no_update, no_update


@app.callback(
    Output('alert_view', 'opened', allow_duplicate=True),
    Output('alert_text', 'children', allow_duplicate=True),
    Output('alert_submit_button', 'disabled', allow_duplicate=True),
    Output('alert_submit_button', 'children'),
    Output('alert_cancel_button', 'children'),
    Input('should_we_call_popup', 'data'),
    State('money_left_archive', 'children'),
    prevent_initial_call=True
)
def display_click_data(should_we_call_popup, money_left):
    if should_we_call_popup:
        popup_data = popup_info[popup_info['ID'] == should_we_call_popup]
        if len(popup_data) > 0:
            popup_data = popup_data.iloc[0]
            money_left = int(money_left.split('$')[0])
            disbld = False

            if money_left < 100:
                disbld = True

            return True, dcc.Markdown(popup_data['TEXT'], style={'width': '100%', 'fontSize': '12px'}), disbld, \
                   popup_data['YES'], popup_data['NO']

    return no_update


@app.callback(
    Output('alert_view', 'opened', allow_duplicate=True),
    Output('money_left_archive', 'children', allow_duplicate=True),
    Output('money_left_interview', 'children', allow_duplicate=True),
    Output('money_left_cards', 'children', allow_duplicate=True),
    Output('alert_view_other', 'opened', allow_duplicate=True),
    Output('alert_other_text', 'children', allow_duplicate=True),
    Output('virus_infection_rate', 'data'),
    Input('alert_submit_button', 'n_clicks'),
    Input('alert_cancel_button', 'n_clicks'),
    State('should_we_call_popup', 'data'),
    State('money_left_archive', 'children'),
    State('virus_infection_rate', 'data'),
    prevent_initial_call=True
)
def display_click_data(alert_submit_button, alert_cancel_button, should_we_call_popup, money_left,
                       virus_infection_rate):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0]

    if should_we_call_popup:
        popup_data = popup_info[popup_info['ID'] == should_we_call_popup]
        if len(popup_data) > 0:
            popup_data = popup_data.iloc[0]
            money_left = int(money_left.split('$')[0])

            if trigger == 'alert_submit_button':
                money_left = money_left - 100
                money_left = str(money_left) + '$'
                message_to_show = dcc.Markdown(popup_data['YES Msg'], style={'width': '100%', 'fontSize': '12px'})
            elif trigger == 'alert_cancel_button':
                money_left = no_update
                virus_infection_rate += 0.1
                message_to_show = dcc.Markdown(popup_data['NO Msg'], style={'width': '100%', 'fontSize': '12px'})
            else:
                return no_update

            return False, money_left, money_left, money_left, True, message_to_show, virus_infection_rate
    return no_update


def switch_between_input_and_back_button_archive(clicked):
    input_div = []

    back_button_div = [
        html.Button(
            'Go Back',
            id={"type": "archive_buttons", "index": 'BACK'},
            n_clicks=0,
            disabled=False,
            style={
                'minWidth': '80px',
                'marginBottom': '20px'
            })
    ]
    if clicked == 'input_button':
        style = {
            'display': 'block',
            'alignItems': 'left',  # Vertical alignment
            'justifyContent': 'center',  # Horizontal alignment
            'width': '100%',
        }
        return back_button_div, style
    else:
        style = {
            'display': 'flex',
            'flexWrap': 'wrap',  # Allows wrapping of elements inside the div
            'alignItems': 'center',  # Vertical alignment
            'justifyContent': 'center',  # Horizontal alignment
            'width': '100%',
            'gap': '10px',  # Adds space between wrapped items
            'padding': '10px',  # Adds some internal spacing
            'boxSizing': 'border-box',  # Ensures padding is part of the width
        }
        return input_div, style


def get_parent_div_children(parent_id):
    parent_id = parent_id.iloc[0].dropna()
    buttons_ = parent_id.index[parent_id.index.str.contains('has_button')]
    if 'markdown_id' in list(parent_id.index):
        response = requests.get(
            'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/markdown files/archive/' +
            parent_id['markdown_id'])
        content = response.text

        div_return = [dcc.Markdown(children=content, style={'width': '100%'})]
        children = []
    else:
        div_return = []
        children = []

    for i in range(len(buttons_)):
        image_with_text = html.Div(
            id={'type': 'archive_button_child1', 'index': str(i)},
            children=[
                html.Img(
                    src='https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/archive/file.png',
                    style={'width': '90%', 'height': '90%', 'margin': '10px', 'display': 'block'}
                ),
                html.Div(
                    parent_id[buttons_[i]],
                    style={
                        'position': 'absolute',
                        'top': '55%',
                        'left': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'color': 'black',
                        'padding': '5px 10px',
                        'border-radius': '5px',
                        'font-size': '16px',
                        'text-align': 'center',
                    }
                ),
            ],
            style={
                'cursor': 'pointer',
                'position': 'relative',
                'display': 'inline-block',
                'width': '30%',  # Match the image width
                'margin': '10px'
            }
        )
        children.append(image_with_text)
    div_return.append(html.Div(children, style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}))
    return html.Div(children=div_return)


@app.callback(
    [
        Output('new-content', 'children'),
        Output('hierarchy_status', 'data'),
        Output("archive_button_clicked_3sec_delay", "data"),
        Output('archive_input_button_div', 'children'),
        Output('archive_input_button_div', 'style'),
        Output('confirm-dialog', 'opened', allow_duplicate=True),
        Output('confirm-dialog', 'title', allow_duplicate=True),
        Output('confirm-dialog_text', 'children', allow_duplicate=True),
        Output('should_we_call_popup', 'data', allow_duplicate=True),
        Output('popup_status', 'data', allow_duplicate=True),

    ],
    [
        Input({"type": "archive_buttons", "index": 'INPUT'}, 'n_clicks'),
        State('archive_input', 'value'),
        State('hierarchy_status', 'data'),
        State('popup_status', 'data'),
    ],
    prevent_initial_call=True
)
def toggle_content(n_clicks, archive_input, hierarchy_status, popup_status):
    if n_clicks:
        parent_id = archive_parent[archive_parent['pwd'] == archive_input.lower()]
        if len(parent_id) > 0:
            new_content_div = get_parent_div_children(parent_id)
            button_, style_ = switch_between_input_and_back_button_archive('input_button')
            if (archive_input.lower() == 'Police and Lab Records'.lower()) & (popup_status['NOTE_4'] == 0):
                should_we_call_popup = 'NOTE_4'
                popup_status['NOTE_4'] = 1
            else:
                should_we_call_popup = no_update
            return new_content_div, {'archive_parent': parent_id['id'].iloc[0], 'archive_child1': None,
                                     'archive_child2': None}, time.time(), button_, style_, False, '', '', should_we_call_popup, popup_status
        else:
            button_, style_ = switch_between_input_and_back_button_archive('back_button')
            return [], no_update, no_update, button_, style_, True, 'Alert', 'Wrong code provided', no_update, no_update
    return no_update


def get_child_div_children(child1):
    child1 = child1.iloc[0].dropna()
    buttons_ = child1.index[child1.index.str.contains('has_button')]
    response = requests.get(
        'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/markdown files/archive/' + child1[
            'markdown_id'])
    content = response.text

    div_return = [dcc.Markdown(children=content, style={'width': '100%'})]
    children = []
    if len(buttons_) > 0:
        for i in range(len(buttons_)):
            image_with_text = html.Div(
                id={'type': 'archive_button_child2', 'index': str(i)},
                children=[
                    html.Img(
                        src='https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/archive/file.png',
                        style={'width': '90%', 'height': '90%', 'margin': '10px', 'display': 'block'}
                    ),
                    html.Div(
                        child1[buttons_[i]],
                        style={
                            'position': 'absolute',
                            'top': '55%',
                            'left': '50%',
                            'transform': 'translate(-50%, -50%)',
                            'color': 'black',
                            'padding': '5px 10px',
                            'border-radius': '5px',
                            'font-size': 'clamp(5px, 2vw, 20px)',  # Dynamically adjusts font size
                            'text-align': 'center',
                            'white-space': 'normal',  # Allows text to wrap into multiple lines
                            'word-wrap': 'break-word',  # Ensures long words are broken properly
                            'overflow': 'hidden',  # Prevents overflow
                            'display': 'flex',
                            'align-items': 'center',
                            'justify-content': 'center',
                            'width': '100%',  # Ensures it scales with the parent
                            'height': '100%',  # Adjust based on the div size
                            'margin-left':'7px'
                        }
                    ),
                ],
                style={
                    'cursor': 'pointer',
                    'position': 'relative',
                    'display': 'inline-block',
                    'width': '10%',  # Match the image width
                    'margin': '10px'
                }
            )
            children.append(image_with_text)
    div_return.append(html.Div(children, style={'display': 'block'}))
    return div_return


@app.callback(
    Output('new-content', 'children', allow_duplicate=True),
    Output('hierarchy_status', 'data', allow_duplicate=True),
    Output('archive_button_child1_3sec_delay', 'data'),
    Output('money_left_archive', 'children', allow_duplicate=True),
    Output('money_left_interview', 'children', allow_duplicate=True),
    Output('money_left_cards', 'children', allow_duplicate=True),
    Output('archive_status', 'data', allow_duplicate=True),
    Output('confirm-dialog', 'opened', allow_duplicate=True),
    Output('confirm-dialog', 'title', allow_duplicate=True),
    Output('confirm-dialog_text', 'children', allow_duplicate=True),
    Input({'type': 'archive_button_child1', 'index': ALL}, "n_clicks"),
    State("archive_button_clicked_3sec_delay", "data"),
    State('hierarchy_status', 'data'),
    State('money_left_archive', 'children'),
    State('archive_status', 'data'),
    prevent_initial_call=True
)
def handle_dynamic_button(n_clicks, archive_button_clicked_3sec_delay, hierarchy_status, money_left, archive_status):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    current_time = time.time()
    if archive_button_clicked_3sec_delay and current_time - archive_button_clicked_3sec_delay < 0.5:
        return no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if ('archive_button_child1' not in triggered_id):
        return no_update
    else:
        parent_id = hierarchy_status['archive_parent'].lower()
        button_index = int(json.loads(triggered_id)['index'])

        child1 = archive_child1[
            (archive_child1['id'] == parent_id) & (archive_child1['button_clicked'] == button_index + 1)]
        if len(child1) > 0:
            div_return = get_child_div_children(child1)
            this_is_the_parent_button_clicked = \
            archive_parent[archive_parent.id == parent_id]['has_button' + str(button_index + 1)].iloc[0]
            if archive_status[this_is_the_parent_button_clicked] == 0:
                if int(money_left.split('$')[0]) < 100:
                    return no_update, no_update, no_update, no_update, no_update, no_update, no_update, True, 'Alert', 'No Money left!'
                money_left = str(int(money_left.split('$')[0]) - 100) + '$'
                archive_status[this_is_the_parent_button_clicked] = 1
            else:
                money_left = no_update

            return div_return, {'archive_parent': parent_id, 'archive_child1': str(button_index + 1),
                                'archive_child2': None}, time.time(), money_left, money_left, money_left, archive_status, False, '', ''
    return no_update


@app.callback(
    Output('new-content', 'children', allow_duplicate=True),
    Output('hierarchy_status', 'data', allow_duplicate=True),
    Output('money_left_archive', 'children', allow_duplicate=True),
    Output('money_left_interview', 'children', allow_duplicate=True),
    Output('money_left_cards', 'children', allow_duplicate=True),
    Output('archive_status', 'data', allow_duplicate=True),
    Output('confirm-dialog', 'opened', allow_duplicate=True),
    Output('confirm-dialog', 'title', allow_duplicate=True),
    Output('confirm-dialog_text', 'children', allow_duplicate=True),
    Input({'type': 'archive_button_child2', 'index': ALL}, "n_clicks"),
    State("archive_button_child1_3sec_delay", "data"),
    State('hierarchy_status', 'data'),
    State('money_left_archive', 'children'),
    State('archive_status', 'data'),
    prevent_initial_call=True
)
def handle_dynamic_button(n_clicks, archive_button_child1_3sec_delay, hierarchy_status, money_left, archive_status):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    current_time = time.time()
    if archive_button_child1_3sec_delay and current_time - archive_button_child1_3sec_delay < 0.5:
        return no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if ('archive_button_child2' not in triggered_id):
        return no_update
    else:
        parent_id = hierarchy_status['archive_parent'].lower()
        archive_child1_id = hierarchy_status['archive_child1']
        button_index = int(json.loads(triggered_id)['index'])

        child2 = archive_child2[
            (archive_child2['id'] == parent_id) & (archive_child2['h1 button clicked'] == int(archive_child1_id)) & (
                        archive_child2['h2 button clicked'] == button_index + 1)]
        if len(child2) > 0:
            child2 = child2.iloc[0].dropna()
            response = requests.get(
                'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/markdown files/archive/' +
                child2['markdown_id'])
            content = response.text

            div_return = [dcc.Markdown(id='markdown_content', children=content, style={'width': '100%'})]

            this_is_the_parent_button_clicked = archive_child1[
                (archive_child1['id'] == parent_id) & (archive_child1['button_clicked'] == int(archive_child1_id))][
                'has_button' + str(button_index + 1)].iloc[0]
            if archive_status[this_is_the_parent_button_clicked] == 0:
                if int(money_left.split('$')[0]) < 100:
                    return no_update, no_update, no_update, no_update, no_update, no_update, True, 'Alert', 'No Money left!'
                money_left = str(int(money_left.split('$')[0]) - 100) + '$'
                archive_status[this_is_the_parent_button_clicked] = 1
            else:
                money_left = no_update
            return div_return, {'archive_parent': parent_id, 'archive_child1': archive_child1_id, 'archive_child2': str(
                button_index + 1)}, money_left, money_left, money_left, archive_status, False, '', ''
    return no_update


@app.callback(
    Output('hierarchy_status', 'data', allow_duplicate=True),
    Output('new-content', 'children', allow_duplicate=True),
    Output('archive_input_button_div', 'children', allow_duplicate=True),
    Output('archive_input_button_div', 'style', allow_duplicate=True),
    Output("archive_button_clicked_3sec_delay", "data", allow_duplicate=True),
    Output('archive_button_child1_3sec_delay', 'data', allow_duplicate=True),
    Input({"type": "archive_buttons", "index": ALL}, "n_clicks"),
    State('hierarchy_status', 'data'),
    State('archive_button_clicked_3sec_delay', 'data'),
    prevent_initial_call=True
)
def handle_dynamic_button_click(n_clicks_list, hierarchy_status, archive_back_button_clicked_3sec_delay):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    current_time = time.time()
    if archive_back_button_clicked_3sec_delay and current_time - archive_back_button_clicked_3sec_delay < 0.5:
        return no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if ('archive_buttons' not in triggered_id):
        return no_update
    else:
        button_index = json.loads(triggered_id)['index']

        if button_index == 'BACK':
            if hierarchy_status['archive_child2'] is not None:
                print('Go to 1st child')
                child1 = archive_child1[(archive_child1['id'] == hierarchy_status['archive_parent']) & (
                            archive_child1['button_clicked'] == int(hierarchy_status['archive_child1']))]
                new_content_div = get_child_div_children(child1)
                button_, style_ = switch_between_input_and_back_button_archive('input_button')
                return {'archive_parent': hierarchy_status['archive_parent'],
                        'archive_child1': str(hierarchy_status['archive_child1']),
                        'archive_child2': None}, new_content_div, button_, style_, no_update, time.time()

            elif hierarchy_status['archive_child1'] is not None:
                parent_id = archive_parent[archive_parent['pwd'] == hierarchy_status['archive_parent']]
                new_content_div = get_parent_div_children(parent_id)
                button_, style_ = switch_between_input_and_back_button_archive('input_button')
                return {'archive_parent': parent_id['id'].iloc[0], 'archive_child1': None,
                        'archive_child2': None}, new_content_div, button_, style_, time.time(), no_update

            else:
                button_, style_ = switch_between_input_and_back_button_archive('back_button')
                return {'archive_parent': None, 'archive_child1': None,
                        'archive_child2': None}, [], button_, style_, no_update, no_update
        else:
            return no_update


def generate_interview_divs(current_speaker, current_message_part, suspect_image, agent_name):
    container_style = {
        'display': 'flex',
        'justify-content': 'flex-start' if current_speaker == "Agent" else 'flex-end',
        'marginBottom': '10px',
        'maxWidth': '60%',
        'align-self': 'flex-start' if current_speaker == "Agent" else 'flex-end',
        'align-items': 'center'}

    div_style = {
        'padding': '10px',
        'backgroundColor': '#f0f0f0' if current_speaker == "Agent" else '#d0e0f0',
        'border': '1px solid #ddd',
        'borderRadius': '5px'
    }
    image_style = {'width': '40px', 'height': '40px', 'borderRadius': '50%', 'marginLeft': '10px'}
    current_speaker_name = current_speaker if current_speaker != 'Agent' else agent_name
    image_to_show = 'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/interviews/Agent.png' if current_speaker == "Agent" else suspect_image

    if current_speaker == 'Comment':
        new_message_div = html.Div([
            html.P("(" + current_message_part + ")",
                   style={'fontStyle': 'italic', 'textAlign': 'center', 'marginBottom': '10px'})
        ])
    elif current_speaker == 'Agent':
        new_message_div = html.Div([
            html.Img(src=f'{image_to_show}', style=image_style),
            html.Div([
                html.P(f"{current_speaker_name}:", style={'fontWeight': 'bold', 'margin': '0'}),
                html.P(current_message_part, style={'margin': '0'})
            ], style=div_style)
        ],
            style=container_style)
    elif current_speaker == 'Hint':
        new_message_div = dcc.Markdown(
            children=current_message_part,
            style={'marginTop': '20px', "font-size": "12px"})

    else:
        new_message_div = html.Div([
            html.Div([
                html.P(f"{current_speaker_name}:", style={'fontWeight': 'bold', 'margin': '0'}),
                html.P(current_message_part, style={'margin': '0'})
            ], style=div_style),
            html.Img(src=f'{image_to_show}', style=image_style),
        ],
            style=container_style)

    return new_message_div




# Callback to handle row click data
@app.callback(
    Output('selected-row-output', 'children', allow_duplicate=True),
    Output('confirm-dialog', 'opened', allow_duplicate=True),
    Output('confirm-dialog', 'title', allow_duplicate=True),
    Output('confirm-dialog_text', 'children', allow_duplicate=True),
    Output('image_layout', 'src', allow_duplicate=True),
    Output('should_we_call_popup', 'data', allow_duplicate=True),
    Output('popup_status', 'data', allow_duplicate=True),
    Input('interview_button_clicked', 'n_clicks'),
    State('suspects_input', 'value'),
    State('store_email', 'data'),
    State('popup_status', 'data'),
    prevent_initial_call=True
)
def update_output(bt_archive, suspects_input, store_email, popup_status):
    if bt_archive:
        selectedRows = archive_culprits_table_df[archive_culprits_table_df['ID'] == suspects_input.lower()]
        if (len(selectedRows) > 0):

            suspect_image = selectedRows['Image'].iloc[0]
            content = pd.read_csv('https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/culprits/' + suspects_input.title().replace(' ','%20') + '.csv')

            if (suspects_input.lower() == 'Taulant Gashi 383'.lower()) & (popup_status['NOTE_2'] == 0):
                should_we_call_popup = 'NOTE_2'
                popup_status['NOTE_2'] = 1
            elif (suspects_input.lower() == 'Taulant Gashi'.lower()) & (popup_status['NOTE_5'] == 0):
                should_we_call_popup = 'NOTE_5'
                popup_status['NOTE_5'] = 1
            else:
                should_we_call_popup = no_update

            displayed = []

            for index in range(len(content)):
                current_message = content.iloc[index]["message"]
                current_speaker = content.iloc[index]["speaker"]



                current_message_part = current_message

                new_message_div = generate_interview_divs(current_speaker, current_message_part, suspect_image,
                                                          store_email['name'].split(' ')[0])
                displayed.append(new_message_div)
            return displayed, False, no_update, no_update, suspect_image, no_update, no_update
        else:
            return no_update, True, 'Alert', f'Wrong submitted code "{suspects_input}"!', '/assets/img/interviews/Unknown.png', no_update, no_update
    return no_update


# Callback to toggle the modal
@app.callback(
    Output("image-modal", "is_open"),
    [Input("single_card_thumbnail-img", "n_clicks")],
    [State("image-modal", "is_open")]
)
def toggle_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


@app.callback(
    Output('small_cards_grid', 'children'),
    Input('cards_open', 'data')
)
def toggle_modal(cards_open):
    if len(cards_open) > 0:
        list_of_buttons_to_return = []
        for card in cards_open.values():
            if "mc" in card.lower():
                bcg_color = 'rgb(69, 155, 196)'
            else:
                bcg_color = 'rgb(162, 138, 208)'
            button = dbc.Button(
                card,
                className="card-title",
                style={
                    'width': '100px',
                    'height': '180px',
                    "fontFamily": "'Libre Baskerville', serif",
                    "fontSize": "10px",
                    "color": "#2d2b28",
                    "textAlign": "center",
                    "borderRadius": "5px",
                    "borderColor": "black",
                    "borderWidth": "1px",
                    "fontWeight": "bold",
                    "backgroundColor": bcg_color,
                    "backgroundImage": "url('https://www.transparenttextures.com/patterns/cardboard.png')",
                    "padding": "10px"},
                # id='btn_'+card
                id={'type': 'cards_buttons_all', 'index': card}
            )
            list_of_buttons_to_return.append(button)
        return list_of_buttons_to_return
    return []


@app.callback(
    Output('single_card_div', 'style', allow_duplicate=True),
    Input('cards_open', 'data'),
    prevent_initial_call=True
)
def button_pressed(cards_open):
    if len(cards_open) == 0:
        return {'display': 'none'}
    else:
        return {'display': 'flex', 'justify-content': 'center'}


# THIS cards_buttons_all IS GETTING PRESSED
@app.callback(
    Output('single_card_div', 'style'),
    Output('markdown_text', 'style'),
    Output('markdown_text_help_more_button', 'style'),
    Output('single_card_title', 'children'),
    Output('single_card_thumbnail-img', 'src'),
    Output('single_card_thumbnail-img', 'style'),
    Output('overlay_image', 'style'),
    Output('single_card_text', 'children'),
    Output('single_card_hint', 'children'),
    Output('image_for_modal', 'src'),
    Output('cards_open', 'data'),
    Output('confirm-dialog', 'opened', allow_duplicate=True),
    Output('confirm-dialog', 'title', allow_duplicate=True),
    Output('confirm-dialog_text', 'children', allow_duplicate=True),
    Output('last_touched_button', 'data'),
    Output('cards_input', 'value'),
    Output('cards_password', 'style'),
    Output('card_pwd_button', 'style'),
    Output('cards_password', 'value'),
    Output('cards_password', 'placeholder'),
    Output('help_data', 'data', allow_duplicate=True),
    Output('card_body_id', 'style'),
    [Input({'type': 'cards_buttons_all', 'index': ALL}, 'n_clicks')],
    State('small_cards_grid', 'children'),
    State('cards_input', 'value'),
    State('cards_open', 'data'),
    State('help_data', 'data'),
    prevent_initial_call=True
)
def button_pressed(button_clicks, small_cards_grid, cards_input, cards_open, help_data):
    ctx = dash.callback_context
    if small_cards_grid:
        nr_of_children = len(small_cards_grid)
    else:
        nr_of_children = 0

    if not ctx.triggered:
        return no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if ('cards_buttons_all' not in triggered_id):
        return no_update
    else:
        button_index = json.loads(triggered_id)['index']

        if button_index == 'cards_button_clicked':
            selectedRows = cards[cards['Code'] == cards_input.lower()]
            if len(selectedRows) == 0:
                if cards_input == '':
                    return no_update
                return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, True, 'Alert', f'Wrong submitted code "{cards_input}"!', no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            else:
                card_data = selectedRows.iloc[0]
                image = f"https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/cards/{card_data['Img']}"

                if card_data['Code'].lower().startswith("mc"):
                    placeholder = 'Please enter the mystery word'
                    color_cardbutton = 'rgb(69, 155, 196)'
                else:
                    placeholder = 'Please enter the password'
                    color_cardbutton = 'rgb(162, 138, 208)'

                card_buton_style = {
                    "width": "100%",  # Adjust dynamically
                    "max-width": "400px",  # Limit max width on larger screens
                    "box-shadow": "0px 4px 8px rgba(0, 0, 0, 0.4)",
                    "border": "2px solid #2d2b28",
                    "border-radius": "5px",
                    "background-color": color_cardbutton,
                    "background-image": "url('https://www.transparenttextures.com/patterns/cardboard.png')",
                    "padding": "20px",
                }

                if (card_data.hasPassword == False):
                    style_input_pwd = {'width': '100%', 'display': 'none'}
                    style_button_pwd = {'width': '100%', 'maxWidth': '200px', 'display': 'none'}
                else:
                    style_input_pwd = {'width': '100%', 'display': 'block', 'backgroundColor': 'rgba(0,0,0,0)',
                                       'border': "1px solid #bbbbbb"}
                    style_button_pwd = {'width': '100%', 'maxWidth': '200px', 'display': 'block',
                                        'backgroundColor': '#F5F5F5'}
                if card_data['Code'] not in cards_open.values():
                    cards_open = cards_open | {str(uuid4()): card_data['Code']}
                    help_data[card_data['Code'].lower()] = 'opened'

                if (card_data['Img'] == False) | (card_data['Img'].lower() == 'false'):
                    image = f"https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/interviews/Unknown.png"
                    style = {'display': 'none'}
                    style_layover = {'display': 'none'}
                else:
                    style={
                        "width": "100%",  # Always fit the container
                        "height": "auto",
                        "margin-bottom": "15px",
                        "border": "1px solid #2d2b28",
                        "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.2)",
                        "cursor": "pointer",
                        "object-fit": "cover",
                    }
                    style_layover = {
                        "position": "absolute",
                        "bottom": "10px",
                        "width": "clamp(20px, 5vw, 40px)",  # Responsive overlay
                        "height": "clamp(20px, 5vw, 40px)",
                        "opacity": "1",
                        "marginLeft": "-80%",
                        "marginBottom": "12px",
                    }

                return {'display': 'flex', 'justify-content': 'center'}, {'display': 'none'}, {'display': 'none'}, card_data[
                    'Title'].upper(), image, style, style_layover, card_data['Text'], card_data[
                           'Hint'], image, cards_open, False, no_update, no_update, {
                           0: cards_input}, '', style_input_pwd, style_button_pwd, '', placeholder, help_data, card_buton_style
        elif button_index in cards['Code'].tolist():
            card_data = cards[cards.Code == button_index].iloc[0]
            image = f"https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/cards/{card_data['Img']}"

            if card_data['Code'].lower().startswith("mc"):
                placeholder = 'Please enter the mystery word'
                color_cardbutton = 'rgb(69, 155, 196)'
            else:
                placeholder = 'Please enter the password'
                color_cardbutton = 'rgb(162, 138, 208)'

            card_buton_style = {
                "width": "100%",  # Adjust dynamically
                "max-width": "400px",  # Limit max width on larger screens
                "box-shadow": "0px 4px 8px rgba(0, 0, 0, 0.4)",
                "border": "2px solid #2d2b28",
                "border-radius": "5px",
                "background-color": color_cardbutton,
                "background-image": "url('https://www.transparenttextures.com/patterns/cardboard.png')",
                "padding": "20px",
            }
            if (card_data.hasPassword == False):
                style_input_pwd = {'width': '100%', 'display': 'none'}
                style_button_pwd = {'width': '100%', 'maxWidth': '200px', 'display': 'none'}
            else:
                style_input_pwd = {'width': '100%', 'display': 'block'}
                style_button_pwd = {'width': '100%', 'maxWidth': '200px', 'display': 'block',
                                    'backgroundColor': '#F5F5F5'}
            if (card_data['Img'] == False) | (card_data['Img'].lower() == 'false'):
                image = f"https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/assets/img/interviews//Unknown.png"
                style = {'display': 'none'}
                style_layover = {'display': 'none'}
            else:
                style={
                        "width": "100%",  # Always fit the container
                        "height": "auto",
                        "margin-bottom": "15px",
                        "border": "1px solid #2d2b28",
                        "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.2)",
                        "cursor": "pointer",
                        "object-fit": "cover",
                    }
                style_layover = {
                        "position": "absolute",
                        "bottom": "10px",
                        "width": "clamp(20px, 5vw, 40px)",  # Responsive overlay
                        "height": "clamp(20px, 5vw, 40px)",
                        "opacity": "1",
                        "marginLeft": "-80%",
                        "marginBottom": "12px",
                    }
            return {'display': 'flex', 'justify-content': 'center'}, {'display': 'none'}, {'display': 'none'}, card_data[
                'Title'].upper(), image, style, style_layover, card_data['Text'], card_data[
                       'Hint'], image, cards_open, False, no_update, no_update, {
                       0: button_index}, no_update, style_input_pwd, style_button_pwd, '', placeholder, no_update, card_buton_style
        else:
            return no_update


@app.callback(
    Output('confirm-dialog', 'opened', allow_duplicate=True),
    Output('confirm-dialog', 'title', allow_duplicate=True),
    Output('confirm-dialog_text', 'children', allow_duplicate=True),
    Output('cards_password', 'value', allow_duplicate=True),
    Output('single_card_div', 'style', allow_duplicate=True),
    Output('markdown_text_help_more_button', 'style', allow_duplicate=True),
    Output('markdown_text', 'style', allow_duplicate=True),
    Output('markdown_text', 'children'),
    Output('should_we_call_popup', 'data', allow_duplicate=True),
    Output('popup_status', 'data', allow_duplicate=True),
    Input('card_pwd_button', 'n_clicks'),
    State('cards_password', 'value'),
    State('single_card_title', 'children'),
    State('popup_status', 'data'),
    prevent_initial_call=True
)
def display_click_data(card_pwd_button, cards_password, single_card_title, popup_status):
    if card_pwd_button:
        markdown_single_file = markdown_lists[(markdown_lists['title'] == single_card_title.lower()) & (
                    markdown_lists['password'] == cards_password.lower())]
        if len(markdown_single_file) > 0:
            txt_file_name = markdown_single_file.iloc[0]['id']
            response = requests.get(
                'https://raw.githubusercontent.com/solveitagent/solveit/refs/heads/main/data/markdown files/cards/' + txt_file_name)
            content = response.text

            if 'mc' in single_card_title.lower():
                help_button_style = {'width': '350px'}
            else:
                help_button_style = {'display': 'none'}

            if (single_card_title.lower() == 'CC K'.lower()) & (popup_status['NOTE_1'] == 0):
                should_we_call_popup = 'NOTE_1'
                popup_status['NOTE_1'] = 1
            else:
                should_we_call_popup = no_update

            return False, '', '', '', {'display': 'none'}, help_button_style, {
                'textAlign': 'left'}, content, should_we_call_popup, popup_status
        else:

            return True, 'Alert', 'Wrong password, please try again!', '', no_update, no_update, no_update, no_update, no_update, no_update
    return no_update, no_update, no_update, '', no_update, no_update, no_update, no_update, no_update, no_update


@app.callback(
    Output('alert_more_help', 'opened', allow_duplicate=True),
    Output('alert_more_help_text', 'children', allow_duplicate=True),
    Output('help_data', 'data', allow_duplicate=True),
    Input('markdown_text_help_more_button', 'n_clicks'),
    State('single_card_title', 'children'),
    State('help_data', 'data'),
    prevent_initial_call=True
)
def display_click_data(markdown_text_help_more_button, single_card_title, help_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'markdown_text_help_more_button':

        markdown_single_file = markdown_lists[(markdown_lists['title'] == single_card_title.lower())]
        if len(markdown_single_file) > 0:
            markdown_single_file = markdown_single_file['hint'].iloc[0]
            help_data[single_card_title.lower()] = 'help'
            return True, markdown_single_file, help_data
    return no_update


@app.callback(
    Output('alert_view_other', 'opened'),
    Output('alert_other_text', 'children'),
    Input("button_clicked", "n_clicks"),
    State('time_sgs_archive', 'children'),
    State('help_data', 'data'),
    State('comments_textarea', 'value'),
    State('store_email', 'data'),
    [State(f"question_answer_input_{index}", "value") for index in range(len(final_answers_dropdown_options.keys()))],
    # Inputs for all questions
)
def collect_answers(n_clicks, time, help_data, comments_textarea, store_email, *answers):
    if n_clicks:
        result = [answers[i] for i in range(len(answers)) if answers[i]]
        real_answers = ['Drenasi', 'Taulant Gashi', 'Through contact', 'N-Serum', 'Taulant Gashi', 'Accidental']
        if not result:
            return True, 'Wrong, try again!'

        incorrect_answers = {}
        for i in range(len(result)):
            if result[i].lower() != real_answers[i].lower():
                incorrect_answers[list(final_answers_dropdown_options.keys())[i]] = result[i]

        if len(incorrect_answers) == 0:

            save_help_data(store_email['email'], help_data, comments_textarea, int(time.split(' ')[0]))
            return True, 'Congrats, you solved the case in ' + time + '!'
        else:
            to_return_text = [dcc.Markdown('**Wrong answers**'), html.Br()]
            for key, value in incorrect_answers.items():
                to_return_text.append(dcc.Markdown(f'{key} : **{value}**'))
                to_return_text.append(html.Br())
            return True, html.Div(to_return_text)
    return no_update




if __name__ == "__main__":
    app.run_server(debug=True)