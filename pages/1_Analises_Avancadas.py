import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="Análises Avançadas", page_icon="📈", layout="wide")
st.title("Análises Avançadas e Estatísticas")
st.markdown("Explore a biometria do ecossistema de impacto através de estatísticas descritivas e correlações multidimensionais.")

st.sidebar.title("Análises Avançadas")

# 1. Carregamento e Limpeza de Dados
@st.cache_data
def load_data():
    try:
        url = st.secrets["csv_url"]
        df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8', decimal=',', thousands='.')
        df.columns = df.columns.str.strip()

        # Lista de colunas base para conversão
        cols_base = ['Valor final INDEI', 'Eixo Econômico', 'Eixo sociocultural', 'Eixo ambiental', 
                     'PIB per capita', 'IDH', 'População estimada']
        
        # Identifica automaticamente colunas de indicadores e médias
        cols_indicadores = [c for c in df.columns if "." in c or "Média" in c]
        todas_numericas = list(set(cols_base + cols_indicadores))

        for col in todas_numericas:
            if col in df.columns:
                # Limpeza robusta: remove R$, espaços e ajusta separadores
                df[col] = df[col].astype(str).str.replace(r'[R\$\s\.]', '', regex=True).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

df_raw = load_data()

# Filtrando colunas numéricas válidas para os seletores
colunas_stats = df_raw.select_dtypes(include=['float64', 'int64']).columns.tolist()
colunas_stats = [c for c in colunas_stats if c not in ['Código IBGE']]

# --- SEÇÃO 1: ESTATÍSTICAS DESCRITIVAS ---
st.header("1. Estatísticas Descritivas")
with st.expander("Ver métricas detalhadas", expanded=True):
    # Filtros de Localidade para Estatística
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        reg_est = st.multiselect("Filtrar por Região:", options=df_raw['Região'].unique(), default=df_raw['Região'].unique(), key="est_reg")
    with col_f2:
        # Filtra estados com base nas regiões selecionadas
        estados_disponiveis = df_raw[df_raw['Região'].isin(reg_est)]['Estado'].unique()
        uf_est = st.multiselect("Filtrar por Estado:", options=estados_disponiveis, default=estados_disponiveis, key="est_uf")
    with col_f3:
        # Filtra municípios com base nos estados selecionados
        mun_disponiveis = df_raw[df_raw['Estado'].isin(uf_est)]['Ecossistema'].unique()
        mun_est = st.multiselect("Filtrar por Município:", options=mun_disponiveis, default=mun_disponiveis, key="est_mun")

    # Seleção da Variável (mantenha abaixo dos filtros de localidade)
    metrica_descritiva = st.selectbox("Selecione a variável para análise:", options=colunas_stats, index=colunas_stats.index('Valor final INDEI'))
    
    if metrica_descritiva:
        data = df_raw[metrica_descritiva].dropna()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Média geral Brasil", f"{data.mean():.3f}")
        c2.metric("Mediana  geral Brasil", f"{data.median():.3f}")
        c3.metric("Desvio Padrão  geral Brasil", f"{data.std():.3f}")
        c4.metric("Amostra (n) geral Brasil", len(data))
    
    # Aplicação dos filtros no dataframe para o cálculo
df_est_filtrado = df_raw[
    (df_raw['Região'].isin(reg_est)) & 
    (df_raw['Estado'].isin(uf_est)) & 
    (df_raw['Ecossistema'].isin(mun_est))
]

if not df_est_filtrado.empty and metrica_descritiva:
    data = df_est_filtrado[metrica_descritiva].dropna()
    
    if len(data) > 0:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Média", f"{data.mean():.3f}")
        c2.metric("Mediana", f"{data.median():.3f}")
        c3.metric("Desvio Padrão", f"{data.std():.3f}")
        c4.metric("Amostra (n)", len(data))
    else:
        st.warning("Não há dados numéricos para os filtros selecionados.")
else:
    st.error("Nenhum território selecionado. Ajuste os filtros acima.")

st.divider()

if len(data) > 0:
    # --- NOVO: Boxplot de Distribuição Multidimensional ---
    st.markdown("#### Distribuição Visual (Boxplot Avançado)")

    col_box1, col_box2 = st.columns(2)
    with col_box1:
        # 1. Seleção múltipla de indicadores
        indicadores_box = st.multiselect(
            "Selecione os indicadores para o Boxplot:", 
            options=colunas_stats, 
            default=[metrica_descritiva] # Puxa a métrica das estatísticas como padrão
        )
    with col_box2:
        # 2. Seleção da Perspectiva (Eixos)
        perspectiva_box = st.radio(
            "Perspectiva de Análise:",
            options=[
                "Por Nível Geográfico (Distribuição do indicador nos territórios)",
                "Por Indicadores (Distribuição das notas dentro do território)"
            ]
        )
        
        # 3. Nível Geográfico para o eixo/cor
        nivel_agrupamento = st.selectbox(
            "Agrupar categorias por:", 
            ["Região", "Estado", "Ecossistema (Município)"]
        )
        
    if len(indicadores_box) > 0 and len(df_est_filtrado) > 0:
        # O segredo está no 'melt': ele transforma as colunas de indicadores em linhas
        # para que o Plotly consiga agrupar perfeitamente
        df_melted = df_est_filtrado.melt(
            id_vars=['Ecossistema', 'Estado', 'Região'],
            value_vars=indicadores_box,
            var_name='Indicador',
            value_name='Nota'
        )
        
        col_agrupamento = {"Região": "Região", "Estado": "Estado", "Ecossistema (Município)": "Ecossistema"}[nivel_agrupamento]
        
        if "Geográfico" in perspectiva_box:
            # Cenário A: Eixo X = Geografia / Cor = Indicador
            fig_box = px.box(
                df_melted, 
                x=col_agrupamento, 
                y='Nota', 
                color='Indicador',
                points="all", # Mostra os pontos (cidades) ao lado da caixa
                hover_name='Ecossistema',
                title="Distribuição Geográfica dos Indicadores"
            )
        else:
            # Cenário B: Eixo X = Indicadores / Cor = Geografia
            fig_box = px.box(
                df_melted, 
                x='Indicador', 
                y='Nota', 
                color=col_agrupamento,
                points="all",
                hover_name='Ecossistema',
                title="Perfil do Território através dos Indicadores Selecionados"
            )
            
        fig_box.update_layout(height=500)
        st.plotly_chart(fig_box, use_container_width=True)
        
        st.caption("""
            **Dica Analítica:** O agrupamento 'Por Nível Geográfico' é ideal para ver gargalos estruturais de uma região. 
            O agrupamento 'Por Indicadores' é ideal para mapear os pontos fortes e fracos de um território específico.
        """)
    else:
        st.info("Selecione ao menos um indicador e garanta que os filtros de localidade possuam dados.")

st.divider()

# --- SEÇÃO 2: HEATMAP E EXPLICAÇÃO TÉCNICA ---
st.header("2. Matriz de Correlação (Heatmap)")

# Guia de interpretação conforme a metodologia INDEI
st.info("""
**Guia de Interpretação Estatística:**
* **Pearson:** Mede a relação linear entre duas variáveis. É ideal para identificar se uma variável cresce proporcionalmente à outra.
* **Spearman:** Baseia-se em postos (rankings). É mais robusto para dados com 'outliers' ou relações que crescem juntas mas não necessariamente de forma linear.
* **Valores de Referência (Módulo):**
    * **0,70 a 1,00:** Correlação Forte.
    * **0,40 a 0,70:** Correlação Moderada (O IDH tem correlação de 0,50 com o INDEI).
    * **0,00 a 0,40:** Correlação Fraca/Baixa (O PIB per capita tem correlação de 0,37 com o INDEI ).
""")

col_h1, col_h2 = st.columns([1, 3])
with col_h1:
    metodo = st.radio("Método:", ["Pearson", "Spearman"])
    default_vars = [c for c in ['Valor final INDEI', 'Eixo Econômico', 'Eixo sociocultural', 'Eixo ambiental', 'IDH', 'PIB per capita'] if c in colunas_stats]
    vars_h = st.multiselect("Variáveis:", options=colunas_stats, default=default_vars)

with col_h2:
    if len(vars_h) > 1:
        corr_matrix = df_raw[vars_h].corr(method=metodo.lower())
        fig_h = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        st.plotly_chart(fig_h, use_container_width=True)

st.divider()

# --- SEÇÃO 3: RELAÇÃO BIVARIADA DINÂMICA (2D) ---
st.header("3. Relação Bivariada (2D Scatter Plot)")
with st.expander("Configurar Eixos do Gráfico", expanded=True):
    col_2d1, col_2d2, col_2d3 = st.columns(3)
    with col_2d1:
        eixo_x_2d = st.selectbox("Eixo X:", options=colunas_stats, index=colunas_stats.index('Eixo Econômico'))
    with col_2d2:
        eixo_y_2d = st.selectbox("Eixo Y:", options=colunas_stats, index=colunas_stats.index('Eixo sociocultural'))
    with col_2d3:
        cor_2d = st.selectbox("Colorir por:", ["Região", "Estado", "Quartil Geral", "Quartil Econômico", "Quartil Sociocultural", "Quartil Ambiental"])

fig_2d = px.scatter(
    df_raw, x=eixo_x_2d, y=eixo_y_2d, color=cor_2d,
    hover_name='Ecossistema', size='População estimada',
    trendline="ols", title=f"Análise: {eixo_x_2d} vs {eixo_y_2d}"
)
st.plotly_chart(fig_2d, use_container_width=True)

st.divider()

# --- SEÇÃO 4: GRÁFICO 3D DINÂMICO ---
st.header("4. Visualização Multidimensional (3D)")
col_3d1, col_3d2, col_3d3 = st.columns(3)
with col_3d1:
    x_3d = st.selectbox("Eixo X (3D):", options=colunas_stats, index=colunas_stats.index('Eixo Econômico'), key="x3")
with col_3d2:
    y_3d = st.selectbox("Eixo Y (3D):", options=colunas_stats, index=colunas_stats.index('Eixo sociocultural'), key="y3")
with col_3d3:
    z_3d = st.selectbox("Eixo Z (3D):", options=colunas_stats, index=colunas_stats.index('Eixo ambiental'), key="z3")

fig_3d = px.scatter_3d(
    df_raw, x=x_3d, y=y_3d, z=z_3d, color='Região',
    hover_name='Ecossistema', opacity=0.7, height=800
)
fig_3d.update_traces(marker=dict(size=4))
st.plotly_chart(fig_3d, use_container_width=True)

# --- SEÇÃO 5: BASE DE DADOS COMPLETA ---
st.header("5. Base de Dados Original")
st.markdown(f"Consulta integral aos dados dos 319 municípios e 63 indicadores avaliados.")

with st.expander("Visualizar Tabela Completa"):
    # Botão para download dos dados que estão sendo visualizados
    csv = df_raw.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar base completa em CSV",
        data=csv,
        file_name='base_completa_indei.csv',
        mime='text/csv',
    )
    
    # Exibição da tabela
    st.dataframe(df_raw, use_container_width=True)