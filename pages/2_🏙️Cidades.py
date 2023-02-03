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

# FILTRO DE PAÍS
rows_selected = df1['country'].isin(country_selection)
df1 = df1.loc[rows_selected, :]

st.sidebar.markdown("""---""")

# ================================================================
# ABA DE VISÃO CIDADES
# ================================================================        
with st.container():
    st.header('Top 10 Cidades com mais tipos de Culinária')
    city_cuisines = df1.loc[:, ['cuisines', 'city']].groupby('city').nunique().sort_values(by='cuisines', ascending=False).reset_index()

    fig = px.bar(data_frame=city_cuisines.head(10), x='city', y='cuisines', text_auto=True, color='city')
    fig.update_traces(textposition='outside', selector=dict(type='bar'))
    st.plotly_chart(fig, use_container_width=True)
        
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('### Top 10 Cidades com Restaurantes com Nota Média acima de 4')
        city_rating4 = df1.loc[(df1['aggregate_rating'] > 4), ['restaurant_id', 'city']].groupby('city').nunique().sort_values(by='restaurant_id', ascending=False).reset_index()

        fig = px.bar(data_frame=city_rating4.head(10), x='city', y='restaurant_id', text_auto=True, color='city')
        fig.update_traces(textposition='outside', selector=dict(type='bar'))
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown('### Top 10 Cidades com Restaurantes com Nota Média abaixo de 2.5')
        city_rating2 = df1.loc[(df1['aggregate_rating'] < 2.5), ['restaurant_id', 'city']].groupby('city').nunique().sort_values(by='restaurant_id', ascending=False).reset_index()

        fig = px.bar(data_frame=city_rating2, x='city', y='restaurant_id', text_auto=True, color='city')
        fig.update_traces(textposition='outside', selector=dict(type='bar'))
        st.plotly_chart(fig, use_container_width=True)
        
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.header('Top 10 Cidades com Maior Valor Médio\n Prato para 2 Pessoas')
        df_aux1 = df1.loc[((df1['price_brl'] < 126968090.40121888) & (df1['price_brl'] > 0.0)), :]

        city_cost = df_aux1.loc[:, ['city','country', 'price_brl']].groupby(['city', 'country']).mean().sort_values(by='price_brl', ascending=False).reset_index()
        st.table(city_cost.head(10))
        
    with col2:
        st.header('Top 10 Cidades com Menor Valor Médio\n Prato para 2 Pessoas')
        df_aux1 = df1.loc[((df1['price_brl'] < 126968090.40121888) & (df1['price_brl'] > 0.0)), :]
 
        city_cost = df_aux1.loc[:, ['city', 'country', 'price_brl']].groupby(['city', 'country']).mean().sort_values(by='price_brl', ascending=True).reset_index()
        st.table(city_cost.head(10))
