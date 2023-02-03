# ================================================================
# BIBLIOTECAS
# ================================================================

import json
import folium
import requests
import inflection

import pandas         as pd
import numpy          as np
import seaborn        as sns
import streamlit      as st
import plotly.express as px

from PIL                    import Image
from haversine              import haversine, Unit
from folium.plugins         import MarkerCluster
from streamlit_folium       import folium_static

# ================================================================
# CONFIGURAÇÃO DA PÁGINA
# ================================================================
st.set_page_config(page_title='Países', page_icon=':bar_chart:', layout='wide')

make_map_responsive= """
 <style>
 [title~="st.iframe"] { width: 100%}
 </style>
"""
st.markdown(make_map_responsive, unsafe_allow_html=True)

image = Image.open('img/logo_eat_out.png')
st.sidebar.image(image, use_column_width='auto')

# ================================================================
# BIBLIOTECA COMPLEMENTAR DE DADOS
# ================================================================
COUNTRIES = {
1: "India",
14: "Australia",
30: "Brazil",
37: "Canada",
94: "Indonesia",
148: "New Zeland",
162: "Philippines",
166: "Qatar",
184: "Singapure",
189: "South Africa",
191: "Sri Lanka",
208: "Turkey",
214: "United Arab Emirates",
215: "England",
216: "United States of America",
}

# ================================================================
# FUNÇÕES
# ================================================================

def clean_dataframe(df):
    """Esta função realiza a limpeza do dataframe a ser analisado
        
        Ações Executadas:
        1. Renomear as colunas
        2. Remover dados NaN
        3. Remover dados duplicados
        4. Nomear as variáveis da coluna 'rating_color'
        5. Classificar os valores na coluna 'cuisines'
        6. Selecionar apenas 1 valor da coluna 'cuisines'
        7. Renomear os dados da coluna 'currency'
        8. Criar as colunas 'country', 'exchange_rate' e 'price_brl'    
    """
    
    # renomeando as colunas
    df = rename_columns(df)
    
    # removendo dados NaN
    df = df.dropna()
    
    # removendo dados duplicados
    df = df.drop_duplicates(keep='first')
    
    # renomenado as cores
    df['rating_color'] = df['rating_color'].map({
                                                "3F7E00": "darkgreen",
                                                "5BA829": "green",
                                                "9ACD32": "lightgreen",
                                                "CDD614": "orange",
                                                "FFBA00": "red",
                                                "CBCBC8": "darkred",
                                                "FF7800": "darkred",
                                                })
    
    # classificando os pratos por valor
    df['price_range'] = df.loc[:, 'price_range'].apply(lambda x: create_price_type(x))
    
    # selecionando 1 tipo de culinária na coluna cuisines
    df['cuisines'] = df.loc[:, 'cuisines'].apply(lambda x: x.split(",")[0])
    
    # renomeando as siglas das moedas
    df['currency'] = df.loc[:, 'currency'].apply(lambda x: currency_type(x))
    
    # transformando os valores da coluna average cost for two para float
    df['average_cost_for_two'] = df['average_cost_for_two'].astype(float)
    
    # criação da coluna country
    df['country'] = df.loc[:, 'country_code'].apply(lambda x: country_name(x))
    
    # criação da coluna utilizando as informações da API Exchange Rates no arquivo JSON
    df['exchange_rate'] = df.loc[:, 'currency'].map(exchange_rate)

    # utilizando os valores do prato pelo valores de cotação do dia
    df['price_brl'] = df['average_cost_for_two'] / df['exchange_rate']

    return df

    
def rename_columns(dataframe):
    """ 
        Renomear as colunas do dataframe para snakecase substituindo os espaços entre as palavras para underscore
    """
    
    df = dataframe.copy()
    title = lambda x: inflection.titleize(x)
    snakecase = lambda x: inflection.underscore(x)
    spaces = lambda x: x.replace(" ", "")
    cols_old = list(df.columns)
    cols_old = list(map(title, cols_old))
    cols_old = list(map(spaces, cols_old))
    cols_new = list(map(snakecase, cols_old))
    df.columns = cols_new
    
    return df

def country_name(country_id):
    """
        Substitui os IDs dos países pelo seu nome conforme dicionário localizado na seção BIBLIOTECA COMPLEMENTAR DE DADOS
    """
    return COUNTRIES[country_id]

def create_price_type(price_range):
    if price_range == 1:
        return "cheap"
    elif price_range == 2:
        return "normal"
    elif price_range == 3:
        return "expensive"
    else:
        return "gourmet"
    
def currency_type(currency):
    if currency == 'Botswana Pula(P)':
        return 'BWP'
    elif currency == 'Brazilian Real(R$)':
        return 'BRL'
    elif currency == 'Dollar($)':
        return 'USD'
    elif currency == 'Emirati Diram(AED)':
        return 'AED'
    elif currency == 'Indian Rupees(Rs.)':
        return 'INR'
    elif currency == 'Indonesian Rupiah(IDR)':
        return 'IDR'
    elif currency == 'NewZealand($)':
        return 'NZD'
    elif currency == 'Pounds(£)':
        return 'GBP'
    elif currency == 'Qatari Rial(QR)':
        return 'QAR'
    elif currency == 'Rand(R)':
        return 'ZAR'
    elif currency == 'Sri Lankan Rupee(LKR)':
        return 'LKR'
    else:
        return 'TRY'

def restaurants_location(df1):
    """
        Esta função cria um mapa onde se cria um cluster com as localizações, além de fornecer informações destas localizações.
    """
    
    df_locations = (df1.loc[:, ['restaurant_name', 'address','cuisines', 'price_brl', 'aggregate_rating', 'rating_color', 'latitude', 'longitude']].reset_index())

    mapa = folium.Map(location=[df_locations.latitude.mean(), df_locations.longitude.mean()], zoom_start=3, control_scale=True)

    marker_cluster = MarkerCluster().add_to(mapa)

    for i, row in df_locations.iterrows():

        html = """<p style="font-family:helvetica;"><strong>Restaurante: </strong> <br /><em>{}</em></p>
                  <p style="font-family:helvetica;"><strong>Culinária: <br /></strong><em>{}</em></p>
                  <p style="font-family:helvetica;"><strong>Endere&ccedil;o: <br /></strong><em>{}</em></p>
                  <p style="font-family:helvetica;"><strong>Custo m&eacute;dio para 2 pessoas: <br /></strong><em>R${}</em></p>
                  <p style="font-family:helvetica;"><strong>Nota m&eacute;dia: <br /></strong><em>{}</em></p>""".format(
                                        df_locations['restaurant_name'][i],
                                        df_locations['cuisines'][i],
                                        df_locations['address'][i], 
                                        round(df_locations['price_brl'][i],2),
                                        df_locations['aggregate_rating'][i])
        iframe = folium.IFrame(html=html, width=300, height=300)
        popup = folium.Popup(iframe, max_width=2650)
        icon_color = df_locations['rating_color'][i]

        folium.Marker(location=[row['latitude'], row['longitude']], 
                      popup=popup,
                      icon=folium.Icon(color=icon_color, 
                                        icon='cutlery')).add_to(marker_cluster)

    folium_static(mapa, height=1000)

    return None
  
# --------------------------------- ESTRUTURA DO CÓDIGO ---------------------------------

# ================================================================
# CARREGANDO DADOS
# ================================================================
df = pd.read_csv('data/zomato.csv')

# carregando os dados do arquivo json para conversão de moeda
json_currency = pd.read_json('data/dict_currency,json')
exchange_rate = json_currency['conversion_rates']

# Limpeza dos dados
df1 = clean_dataframe(df)

# ================================================================
# BARRA LATERAL
# ================================================================
st.header('Eat Out Dashboard')

st.sidebar.markdown('# MENU')
st.sidebar.markdown("""---""")

# SELECIONE OS PAÍSES
st.sidebar.subheader('Selecione o(s) País(es)')
country_selection = st.sidebar.multiselect('Países', ['Australia', 'Brazil', 'Canada', 'England', 'India', 'Indonesia',
       'New Zeland', 'Philippines', 'Qatar', 'Singapure', 'South Africa',
       'Sri Lanka', 'Turkey', 'United Arab Emirates',
       'United States of America'], default=['Australia', 'Brazil', 'Canada', 'England', 'India', 'Indonesia',
       'New Zeland', 'Philippines', 'Qatar', 'Singapure', 'South Africa',
       'Sri Lanka', 'Turkey', 'United Arab Emirates',
       'United States of America'])

st.sidebar.markdown("""---""")

# FILTRO DE PAÍS
rows_selected = df1['country'].isin(country_selection)
df1 = df1.loc[rows_selected, :]


# ================================================================
# ABA DE VISÃO CULINÁRIAS
# ================================================================

with st.container():
    st.markdown('-----------------')    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('### Restaurante mais avaliado')
        rating_votes_high = (df1.loc[:, ['restaurant_name', 'aggregate_rating', 'votes']]
                              .groupby(['restaurant_name', 'aggregate_rating', 'votes'])
                              .mean()
                              .sort_values(by=['aggregate_rating', 'votes'], ascending=False)).reset_index()
        
        st.markdown('##### {}'.format(rating_votes_high['restaurant_name'][0]))
        st.markdown('##### {}/5.0'.format(rating_votes_high['aggregate_rating'][0]))
        
    with col2:
        st.markdown('### Restaurante menos avaliado')
        rating_votes_low = (df1.loc[:, ['restaurant_name', 'aggregate_rating', 'votes']]
                              .groupby(['restaurant_name', 'aggregate_rating', 'votes'])
                              .mean()
                              .sort_values(by=['aggregate_rating', 'votes'], ascending=True)).reset_index()
        
        st.markdown('##### {}'.format(rating_votes_low['restaurant_name'][0]))
        st.markdown('##### {}/5.0'.format(rating_votes_low['aggregate_rating'][0]))

    with col3:
        st.markdown('### Restaurante Maior Valor Médio')
        df_aux1 = df1.loc[((df1['price_brl'] < 126968090.40121888) & (df1['price_brl'] > 0.0)), :]
        price_brl_high = (df_aux1.loc[:, ['restaurant_name', 'price_brl']].groupby('restaurant_name')).mean().sort_values(by='price_brl', ascending=False).reset_index()
        
        st.markdown('##### {}'.format(price_brl_high['restaurant_name'][0]))
        st.markdown('##### R${}'.format(round(price_brl_high['price_brl'][0],2)))
    
    with col4:
        st.markdown('### Restaurante Menor Valor Médio')
        df_aux1 = df1.loc[((df1['price_brl'] < 126968090.40121888) & (df1['price_brl'] > 0.0)), :]
        price_brl_low = (df_aux1.loc[:, ['restaurant_name', 'price_brl']].groupby('restaurant_name')).mean().sort_values(by='price_brl', ascending=True).reset_index()
        
        st.markdown('##### {}'.format(price_brl_low['restaurant_name'][0]))
        st.markdown('##### R${}'.format(round(price_brl_low['price_brl'][0],2)))

    st.markdown('-----------------')
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('### Top 10 Melhores Tipos de Culinária\n Por Nota Média ')
        cuisines_best_rating = df1.loc[:, ['cuisines', 'aggregate_rating']].groupby('cuisines').mean().sort_values(by='aggregate_rating', ascending=False).reset_index()
        
        fig = px.bar(data_frame=round(cuisines_best_rating.head(10),2), x='cuisines', y='aggregate_rating', text_auto=True, color='cuisines')
        fig.update_traces(textposition='outside', selector=dict(type='bar'))
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown('### Top 10 Piores Tipos de Culinária\n Por Nota Média ')
        cuisines_worst_rating = df1.loc[:, ['cuisines', 'aggregate_rating']].groupby('cuisines').mean().sort_values(by='aggregate_rating', ascending=True).reset_index()
        
        fig = px.bar(data_frame=round(cuisines_worst_rating.head(10),2), x='cuisines', y='aggregate_rating', text_auto=True, color='cuisines')
        fig.update_traces(textposition='outside', selector=dict(type='bar'))
        st.plotly_chart(fig, use_container_width=True)

with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('### Maior Valor Médio para 2 Pessoas\n Por Culinária ')
        df_aux1 = df1.loc[((df1['price_brl'] < 126968090.40121888) & (df1['price_brl'] > 0.0)), :]

        restaurants_cost = df_aux1.loc[:, ['cuisines', 'price_brl']].groupby('cuisines').mean().sort_values(by='price_brl', ascending=False).reset_index()
        st.table(restaurants_cost.head(10))
    
    with col2:
        st.markdown('### Tipos de Culinária\n Que mais Realizam Entregas ')
        df_aux1 = df1.loc[(df1['has_online_delivery'] == 1), :]
        cuisines_delivery = df_aux1.loc[:, ['cuisines', 'is_delivering_now']].groupby('cuisines').count().sort_values(by='is_delivering_now', ascending=False).reset_index()

        st.table(cuisines_delivery.head(10))
        





