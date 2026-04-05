import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Geral", page_icon="🌍", layout="wide")
st.sidebar.markdown("# Geral")

# 1. Carregamento dos Dados
@st.cache_data
def load_data():
    try:
        url = st.secrets["csv_url"]
        # Carrega os dados tratando o padrão brasileiro
        df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8', decimal=',', thousands='.')
        
        # 1. Limpa espaços extras nos nomes das colunas
        df.columns = df.columns.str.strip()
        
        # 2. Padroniza apenas os nomes das colunas específicas que variam no CSV 
        # (evitamos usar .title() em tudo para não quebrar siglas como IDH e UF)
        renames = {
            'Valor final INDEI': 'Valor Geral INDEI',
            'Eixo sociocultural': 'Eixo Sociocultural',
            'Eixo ambiental': 'Eixo Ambiental'
        }
        df.rename(columns=renames, inplace=True)
        
        # 3. Lista de colunas numéricas conhecidas
        cols_base = ['Valor Geral INDEI', 'Eixo Econômico', 'Eixo Sociocultural', 'Eixo Ambiental', 
                     'PIB per capita', 'IDH', 'População estimada']
        
        # Adiciona os indicadores individuais dinamicamente (ex: EC1.1, SOC2.1)
        cols_indicadores = [c for c in df.columns if "." in c or "Média" in c]
        todas_numericas = list(set(cols_base + cols_indicadores))

        # 4. Limpeza e conversão robusta
        for col in todas_numericas:
            if col in df.columns:
                # Remove R$ e espaços. (Não removemos o ponto para não agrupar os números)
                df[col] = df[col].astype(str).str.replace(r'[R\$\s]', '', regex=True)
                # Garante que a vírgula vire ponto para o Python entender como decimal
                df[col] = df[col].str.replace(',', '.')
                # Converte para numérico
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 5. AJUSTE DE ESCALA 0 a 10 (exclusivo para as notas do INDEI)
                # Se os dados vieram como 434 em vez de 4.34, forçamos a divisão por 100.
                # Ignoramos PIB, População e IDH para não alterar seus valores originais.
                if col not in ['PIB per capita', 'População estimada', 'IDH']:
                    if df[col].max() > 10:
                        df[col] = df[col] / 100
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

df_raw = load_data()

# Título Principal
st.title("Índice de Ecossistemas de Impacto (INDEI)")
st.markdown("Uma análise sistêmica sobre a prosperidade e regeneração dos territórios brasileiros.")

# --- SEÇÃO 1: PANORAMA GEOGRÁFICO ---
st.header("1. Panorama Geográfico")
st.markdown("Visualize a distribuição da prosperidade pelos estados brasileiros através de diferentes dimensões.")

with st.expander("Selecionar Métrica do Mapa", expanded=True):
    # Dicionário alinhado exatamente com os nomes padronizados no load_data
    map_metrica_opcoes = {
        "Valor geral INDEI": "Valor Geral INDEI",
        "Valor Eixo Econômico": "Eixo Econômico",
        "Valor eixo sociocultural": "Eixo Sociocultural",
        "Valor eixo ambiental": "Eixo Ambiental"
    }
    map_metrica_label = st.selectbox(
        "Escolha a métrica para visualizar no mapa:", 
        options=list(map_metrica_opcoes.keys()), 
        key="map_met_sel"
    )
    map_col_selecionada = map_metrica_opcoes[map_metrica_label]

# Agrupa por estado para exibir no mapa de calor
df_mapa_plot = df_raw.groupby(['Estado', 'Sigla UF'])[map_col_selecionada].mean().reset_index()

fig_mapa = px.choropleth(
    df_mapa_plot, 
    geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
    locations="Sigla UF", 
    featureidkey="properties.sigla", 
    color=map_col_selecionada,
    hover_name="Estado", 
    color_continuous_scale="Viridis",
    labels={map_col_selecionada: map_metrica_label}
)
fig_mapa.update_geos(fitbounds="geojson", visible=False)
fig_mapa.update_layout(height=700, margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_mapa, use_container_width=True)

st.divider()

# --- SEÇÃO 2: RANKINGS DE IMPACTO ---
st.header("2. Rankings de Impacto")
with st.expander("Filtros do Ranking", expanded=True):
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        reg_rank = st.multiselect("Regiões", df_raw['Região'].unique(), default=df_raw['Região'].unique(), key="rank_reg")
    with col_r2:
        uf_rank = st.multiselect("Estados", df_raw[df_raw['Região'].isin(reg_rank)]['Estado'].unique(), 
                                 default=df_raw[df_raw['Região'].isin(reg_rank)]['Estado'].unique(), key="rank_uf")
    with col_r3:
        nivel_geo = st.selectbox("Nível Geográfico", ["Municípios", "Estados", "Regiões"], key="rank_nivel")
    with col_r4:
        metrica_rank_label = st.selectbox("Métrica", ["Geral", "Econômico", "Sociocultural", "Ambiental"], key="rank_met")

df_rank_filtered = df_raw[(df_raw['Região'].isin(reg_rank)) & (df_raw['Estado'].isin(uf_rank))]

# Dicionário de métricas do ranking alinhado com as colunas reais
metrica_col = {
    "Geral": "Valor Geral INDEI", 
    "Econômico": "Eixo Econômico", 
    "Sociocultural": "Eixo Sociocultural", 
    "Ambiental": "Eixo Ambiental"
}[metrica_rank_label]

if not df_rank_filtered.empty:
    group_cols = {"Municípios": "Ecossistema", "Estados": "Estado", "Regiões": "Região"}[nivel_geo]
    df_ranking_grouped = df_rank_filtered.groupby(group_cols)[metrica_col].mean().reset_index()
    top10 = df_ranking_grouped.nlargest(10, metrica_col)
    
    fig_bar = px.bar(top10, x=group_cols, y=metrica_col, color=group_cols, text_auto='.2f', 
                     title=f"Destaques: Top 10 {nivel_geo} - {metrica_rank_label}")
    fig_bar.update_xaxes(categoryorder='total descending')
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- SEÇÃO 3: EXPLORADOR DE INDICADORES ---
st.header("3. Detalhamento de Indicadores")
st.markdown("Analise a anatomia da medição através dos 63 indicadores e 20 subgrupos.")

with st.expander("Configurar Análise de Subgrupo", expanded=True):
    col_ind1, col_ind2, col_ind3, col_ind4 = st.columns(4)
    with col_ind1:
        eixo_sel = st.selectbox("Eixo", ["Econômico", "Sociocultural", "Ambiental"])
    with col_ind2:
        subgrupos = {
            "Econômico": ["EC1", "EC2", "EC3", "EC4", "EC5", "EC6", "EC7", "EC8"],
            "Sociocultural": ["SOC1", "SOC2", "SOC3", "SOC4", "SOC5", "SOC6", "SOC7"],
            "Ambiental": ["MED1", "MED2", "MED3", "MED4", "MED5"]
        }[eixo_sel]
        sub_sel = st.selectbox("Subgrupo", subgrupos)
    with col_ind3:
        nivel_ind = st.selectbox("Nível de Agrupamento", ["Municipal", "Estadual", "Regional"])
    with col_ind4:
        if nivel_ind == "Municipal":
            territorio = st.multiselect("Selecionar Municípios", df_raw['Ecossistema'].unique(), default=df_raw['Ecossistema'].unique()[:5])
        elif nivel_ind == "Estadual":
            territorio = st.multiselect("Selecionar Estados", df_raw['Estado'].unique(), default=df_raw['Estado'].unique()[:5])
        else:
            territorio = st.multiselect("Selecionar Regiões", df_raw['Região'].unique(), default=df_raw['Região'].unique())

# Identifica colunas do subgrupo selecionado (ex: EC1.1, EC1.2...)
cols_indicadores = [c for c in df_raw.columns if c.startswith(f"{sub_sel}.")]

if nivel_ind == "Municipal":
    df_ind_final = df_raw[df_raw['Ecossistema'].isin(territorio)]
    label_col = "Ecossistema"
elif nivel_ind == "Estadual":
    df_ind_final = df_raw[df_raw['Estado'].isin(territorio)].groupby("Estado")[cols_indicadores].mean().reset_index()
    label_col = "Estado"
else:
    df_ind_final = df_raw[df_raw['Região'].isin(territorio)].groupby("Região")[cols_indicadores].mean().reset_index()
    label_col = "Região"

if not df_ind_final.empty and cols_indicadores:
    df_long = df_ind_final.melt(id_vars=[label_col], value_vars=cols_indicadores, var_name="Indicador", value_name="Nota")
    fig_ind = px.bar(df_long, x="Indicador", y="Nota", color=label_col, barmode="group", 
                     title=f"Desempenho Detalhado - {sub_sel}", text_auto='.2f')
    st.plotly_chart(fig_ind, use_container_width=True)

st.divider()