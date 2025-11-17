import streamlit as st
from streamlit_folium import folium_static
import folium
import pandas as pd
import json
import os 
import plotly.express as px 

st.set_page_config(layout="wide")
st.title("Distribuição de Casos de Dengue no Município do Rio de Janeiro")

map_captions = {
    2020: "Análise de 2020: Houve um pico de casos no verão.",
    2021: "Análise de 2021: Casos controlados durante a pandemia de COVID.",
    2022: "Análise de 2022: Leve aumento na zona oeste.",
    2023: "Análise de 2023: Grande aumento de casos em diversos bairros.",
    2024: "Análise de 2024: Surto de dengue no Município.",
    2025: "Análise de 2025: Dados parciais até o momento."
}

anos_disponiveis = sorted(map_captions.keys())


def criar_mapa(year: int):
    tabela_path = f"MAPAS/Dengue{year}.xlsx"
    geojson_path = f"MAPAS/Bairros{year}.geojson"

    tabela = pd.read_excel(tabela_path)
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    mapadengue = folium.Map([-22.92425, -43.32733], tiles="cartodbpositron", zoom_start=10)

    for feature in geojson_data['features']:
        nome_bairro = feature['properties']['nome']
        total = tabela.loc[tabela['nome'].astype(str).str.strip() == str(nome_bairro).strip(), 'Total']
        if not total.empty:
            feature['properties']['Total'] = int(total.iloc[0]) 
        else:
            feature['properties']['Total'] = 0

    folium.Choropleth(
        geo_data=geojson_data,
        data=tabela,
        columns=["nome", "Total"],
        key_on="feature.properties.nome",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        nan_fill_color="#f5f5c0",
        legend_name=f"Casos de Dengue no Município do Rio de Janeiro em {year}"
    ).add_to(mapadengue)
    
    highlight = folium.features.GeoJson(
        data=geojson_data,
        name='Hover nos Bairros',
        style_function=lambda x: {"fillColor": "white", "color": "black", "fillOpacity": 0.001, "weight": 0.001},
        highlight_function=lambda x: {"fillColor": "darkyellow", "color": "black", "fillOpacity": 0.5, "weight": 1}
    )
    folium.features.GeoJsonTooltip(
        fields=['nome', 'Total'],
        aliases=['Bairro: ', 'Casos de Dengue: '],
        localize=True,
        style=("background-color: yellow; color: black; font-weight: bold;")
    ).add_to(highlight)
    highlight.add_to(mapadengue)
   
    return mapadengue

@st.cache_data
def plotar_grafico_mensal_consolidado(year: int):
    mensal_path = "MAPAS/anomes.xlsx" 

    mensal_df = pd.read_excel(mensal_path)
    
    colunas_desejadas = ['Ano','Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez','Total']
    
    df_row = mensal_df[mensal_df['Ano'].astype(str).str.strip() == str(year)]
    
    if not df_row.empty:
        
        
        serie_data = df_row.iloc[0][colunas_desejadas[1:]].astype(float)
        
        labels = colunas_desejadas[1:]

        
        plot_data = pd.DataFrame({
            'Mês/Período': labels,
            'Casos': serie_data.values 
        })

        st.subheader(f"Casos mensais e Total Anual ({year})")
        
        fig = px.bar(plot_data, 
                     x='Mês/Período', 
                     y='Casos', 
                     title=f'Distribuição Mensal de Casos em {year}')
        
        st.plotly_chart(fig, use_container_width=True) 



@st.cache_data
def plotar_grafico_bairros(year: int):
    data_file = f"MAPAS/Dengue{year}.xlsx"
    
    df = pd.read_excel(data_file)
    if 'nome' in df.columns and 'Total' in df.columns:
        st.subheader(f"Gráfico de Barras — Casos por Bairro em {year}")
        
        chart_df = df[['nome', 'Total']].copy()
        chart_df = chart_df.sort_values(by='Total', ascending=False).head(20)

        fig = px.bar(chart_df, x='Total', y='nome', orientation='h',
                     title=f'Top 20 Bairros com Mais Casos de Dengue em {year}',
                     labels={'nome': ''})
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)



year_to_func = {year: lambda y=year: criar_mapa(y) for year in anos_disponiveis}

selected_year = st.sidebar.selectbox("Escolha o ano:", anos_disponiveis)

if selected_year:
    st.header(f"Visualizando: Mapa da Dengue {selected_year}")

    col_left, col_map, col_right = st.columns([1, 3, 1])

    with col_map:
        map_object = year_to_func[selected_year]()
        folium_static(map_object, width=750, height=500)

    caption = map_captions.get(selected_year)
    if caption:
        st.markdown(f"**Descrição do Mapa:** {caption}")
        st.markdown("---") 

    plotar_grafico_bairros(selected_year)
    st.markdown("---") 

    plotar_grafico_mensal_consolidado(selected_year)

st.markdown("---") 

st.caption("Fonte dos Dados: Secretaria Municipal de Saúde do Rio de Janeiro")

st.markdown("""
<p style='text-align: center; opacity: 0.7; font-size: small;'>
    Mapas e gráficos gerados a partir dos dados retirados do site https://saude.prefeitura.rio/dengue-dados-epidemiologicos.
    <br>
    Os dados do ano de 2025 são parciais e sujeitos a alterações.
</p>
""", unsafe_allow_html=True)
