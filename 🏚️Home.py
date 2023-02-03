import streamlit as st
from PIL import Image

st.set_page_config(
    page_title=":knife_fork_plate: Home",
    page_icon="knife_fork_plate",
    layout='wide'
)

image = Image.open('img/logo_eat_out.png')
st.sidebar.image(image, use_column_width='auto')

st.header('Eat Out')
st.subheader('Sempre a escolha certa!')

tab1, tab2 = st.tabs(['Página Inicial', 'Atualizações'])
with tab1:
    with st.container():
        st.header('Como utilizar este Dashboard?')
        st.markdown('### Demonstração de uso')
        st.markdown("----------")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('##### - Visualize e interaja com os gráficos dispostos')
            st.image('img/gif_graph.gif')
           
        with col2:
            st.markdown('##### - Alterne as páginas e selecione os filtros')
            st.image('img/gif_graph2.gif')

st.markdown("----------")
        
with tab2:
    with st.container():
        st.header("Atualizações")
        st.markdown("### Versão 1.1")

        st.markdown("----------")
        # primeiro item das atualizações
        st.markdown("##### - Adicionadas informações nas localizações do mapa")
        image_path_1 = 'img/localizacao_info.png'
        image_1 = Image.open(image_path_1)
        st.image(image_1)

        st.markdown("----------")
        # segundo item das atualizações
        st.markdown("##### - Atualizados os rankings na seção de Culinárias")
        image_path_2 = 'img/ranking_culinaria.png'
        image_2 = Image.open(image_path_2)
        st.image(image_2)

        st.markdown("----------")
        # terceiro item das atualizações
        st.markdown("#####  - Criado o filtro de Preço")
        image_path_3 = 'img/filtro_preco.png'
        image_3 = Image.open(image_path_3)
        st.image(image_3)
          
with st.container():
    
    col1, col2 = st.columns(2)
            
    with col1:
        st.markdown('# Sugestões de Melhoria?\n ## Entre em contato abaixo!')
        
        contact_form = """
                          <form action="https://formsubmit.co/github.gabrielpastega@gmail.com" method="POST">
                          <input type="hidden" name="_captcha" value="false">
                          <input type="text" name="name" placeholder="Seu nome ou Empresa" required>
                          <input type="email" name="email" placeholder="Seu e-mail" required>
                          <textarea name="message" placeholder="Insira sua mensagem aqui"></textarea>
                          <button type="submit">Enviar</button>
                          </form>
                       """
        
        st.markdown(contact_form, unsafe_allow_html=True)
        
        def local_css(file_name):
            with open(file_name) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        local_css('style/style.css')    
                
    with col2:
        st.markdown('# Precisa de ajuda? \n ## Time de Data Science no Discord\n - @gabrielpastega')