import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import indei_branding as indei

# Configuração da página
st.set_page_config(page_title="INDEI — Geral", page_icon="🌍", layout="wide")
indei.inject_indei_theme()
indei.sidebar_branding("Geral")

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

        # 4. Limpeza e conversão robusta (BR: milhar com ponto, decimal com vírgula; ex.: R$ 18.329,13)
        for col in todas_numericas:
            if col in df.columns:
                df[col] = indei.parse_brazilian_number_series(df[col])
                
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
st.title("INDEI")
st.markdown("Um índice de prosperidade sistêmica dos territórios brasileiros.")


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
    color_continuous_scale=indei.SEQUENTIAL_SCALE,
    labels={map_col_selecionada: map_metrica_label},
)
fig_mapa.update_geos(fitbounds="geojson", visible=False)
indei.style_plotly(fig_mapa)
indei.style_choropleth_coloraxis(fig_mapa)
indei.style_choropleth_map_canvas(fig_mapa)
fig_mapa.update_layout(height=700, margin={"r": 0, "t": 0, "l": 0, "b": 0})
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
    
    fig_bar = px.bar(
        top10,
        x=group_cols,
        y=metrica_col,
        color=group_cols,
        text_auto=".2f",
        title=f"Destaques: Top 10 {nivel_geo} - {metrica_rank_label}",
        color_discrete_sequence=indei.COLORWAY,
    )
    fig_bar.update_xaxes(categoryorder="total descending")
    indei.style_plotly(fig_bar)
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- SEÇÃO 3: EXPLORADOR DE INDICADORES ---
st.header("3. Detalhamento de Indicadores")
st.markdown("Analise a anatomia da medição através dos 63 indicadores e 20 subgrupos.")

with st.expander("Ver tabela completa de indicadores (código, nome e fonte)", expanded=False):
    indicadores_meta = [
        {"Código": "EC 1.1", "Indicador": "Quantidade de Empresas / 1.000 habitantes", "Fonte": "Mapa de Empresas + população IBGE"},
        {"Código": "EC 1.2", "Indicador": "Quantidade de Micro e Pequenas Empresas / 1.000 habitantes", "Fonte": "Mapa de Empresas + população IBGE"},
        {"Código": "EC 1.3", "Indicador": "Quantidade de MEIs / 1.000 habitantes", "Fonte": "Receita Fazenda Simples Nacional"},
        {"Código": "EC 2.1", "Indicador": "Taxa de Equilíbrio Setorial (Equidade/Diversidade de Pielou dos CNAES)", "Fonte": "Receita Fazenda Simples Nacional"},
        {"Código": "EC 2.2", "Indicador": "Quantidade de OSCs / 1.000 habitantes", "Fonte": "Receita Fazenda Simples Nacional"},
        {"Código": "EC 3.1", "Indicador": "Número de ICTs/100.000 empresas", "Fonte": "Mapa das ICTs (MCTI/CNPq)"},
        {"Código": "EC 3.2", "Indicador": "Número de Empresas com Base tecnológica / 1.000 habitantes", "Fonte": "Mapa de Empresas (Governo Federal)"},
        {"Código": "EC 4.1", "Indicador": "Arrecadação MEI Receita Federal / 1000 MEIs", "Fonte": "Receita Federal"},
        {"Código": "EC 4.2", "Indicador": "Despesas Públicas Correntes Liquidadas", "Fonte": "SICONFI"},
        {"Código": "EC 5.1", "Indicador": "Crescimento na Quantidade de Empresas Ativas", "Fonte": "Mapa de Empresas (Ministério do Desenvolvimento, Indústria, Comércio e Serviços - MDIC)"},
        {"Código": "EC 5.2", "Indicador": "Criação de empregos", "Fonte": "Novo CAGED"},
        {"Código": "EC 6.1", "Indicador": "Crescimento da Qtde de Empresas com base tecnológica", "Fonte": "Mapa de Empresas (Governo Federal)"},
        {"Código": "EC 6.2", "Indicador": "Quantidade de Empresas com CNAEs \"Sociais\"/Total de empresas", "Fonte": "Mapa de Empresas (Governo Federal)"},
        {"Código": "EC 7.1", "Indicador": "Índice ODS 8 - Trabalho decente e crescimento econômico", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "EC 7.2", "Indicador": "Índice ODS 9 - Indústria Inovação e Infraestrutura", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "EC 8.1", "Indicador": "PIB Per cápita", "Fonte": "IBGE"},
        {"Código": "EC 8.2", "Indicador": "Índice ODS 10 - Redução das Desigualdades", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "SOC 1.1", "Indicador": "(%) Taxa de participação unidades locais do setor cultural em relação ao total cadastro empresas", "Fonte": "IBGE SIIC - Sistema de Informações e Indicadores Culturais"},
        {"Código": "SOC 1.2", "Indicador": "(%) Taxa de pessoal assalariado no setor de cultura", "Fonte": "IBGE SIIC - Sistema de Informações e Indicadores Culturais"},
        {"Código": "SOC 1.3", "Indicador": "Número de IES/habitantes", "Fonte": "Ministério da Educação (MEC)"},
        {"Código": "SOC 2.1", "Indicador": "(Ensino Superior) Quantidade de docentes em exercício / hab", "Fonte": "INEP - Censo da Educação Superior"},
        {"Código": "SOC 2.2", "Indicador": "Taxa de concluintes / ingressantes universitários", "Fonte": "INEP - Censo da Educação Superior"},
        {"Código": "SOC 2.3", "Indicador": "Índice de Desenvolvimento da Educação Básica - IDEB", "Fonte": "INEP"},
        {"Código": "SOC 2.4", "Indicador": "Índice ODS 4 Educação de Qualidade", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "SOC 2.5", "Indicador": "Pessoas de 18 anos ou mais com ensino médio ou superior completo", "Fonte": "SIDRA"},
        {"Código": "SOC 3.1", "Indicador": "(Ensino Superior) Quantidade de docentes em exercício - Mulheres em relação ao total Docentes em exercício", "Fonte": "INEP - Censo da Educação Superior"},
        {"Código": "SOC 3.2", "Indicador": "(Ensino Superior) Quantidade de docentes em exercício - Preto, Pardo, Indígena em relação ao total Docentes em exercício", "Fonte": "INEP - Censo da Educação Superior"},
        {"Código": "SOC 3.3", "Indicador": "(Ensino Superior) Quantidade de docentes em exercício - Pessoas Com Deficiência em relação ao total Docentes em exercício", "Fonte": "INEP - Censo da Educação Superior"},
        {"Código": "SOC 3.4", "Indicador": "Taxa de mulheres na câmara municipal", "Fonte": "Senado Legislativo"},
        {"Código": "SOC 4.1", "Indicador": "(%) de gasto Política Nacional Aldir Blanc de Fomento à Cultura", "Fonte": "Painel de Dados Ministério da Cultura"},
        {"Código": "SOC 4.2", "Indicador": "Despesas empenhadas em Saúde por hab", "Fonte": "SICONFI"},
        {"Código": "SOC 4.3", "Indicador": "Despesas com Educação", "Fonte": "Sistema de Informações sobre Orçamentos Públicos em Educação (SIOPE) / Fundo Nacional de Desenvolvimento da Educação (FNDE)"},
        {"Código": "SOC 5.1", "Indicador": "Taxa de comparecimento eleições", "Fonte": "TSE"},
        {"Código": "SOC 5.2", "Indicador": "Público em sessões de cinema por 100 mil hab (Municipal: primeiro semestre 2025)", "Fonte": "ANCINE"},
        {"Código": "SOC 5.3", "Indicador": "Agentes Econômicos Regulares Registrados na Ancine", "Fonte": "ANCINE"},
        {"Código": "SOC 6.1", "Indicador": "Contagem de serviços socioassistenciais", "Fonte": "MUNIC"},
        {"Código": "SOC 6.2", "Indicador": "Contagem Serviços socioassistenciais para grupos específicos", "Fonte": "MUNIC"},
        {"Código": "SOC 6.3", "Indicador": "Contagem Ações desenvolvidas Segurança Alimentar", "Fonte": "MUNIC"},
        {"Código": "SOC 6.4", "Indicador": "Contagem Conselhos Municipais para Direitos Humanos", "Fonte": "MUNIC"},
        {"Código": "SOC 6.5", "Indicador": "Contagem de Políticas ou programas na área de direitos humanos", "Fonte": "MUNIC"},
        {"Código": "SOC 7.1", "Indicador": "Quantidade de Unidades Básicas de Saúde por hab", "Fonte": "Ministério da Saúde"},
        {"Código": "SOC 7.2", "Indicador": "Indivíduos com IMC adequado (eutrófico)", "Fonte": "SISVAN"},
        {"Código": "SOC 7.3", "Indicador": "Equipes de saúde por hab", "Fonte": "DATASUS"},
        {"Código": "MED 1.1", "Indicador": "Porcentagem de Estabelecimentos Agropecuários (%)", "Fonte": "IBGE – Censo Agropecuário"},
        {"Código": "MED 1.2", "Indicador": "Área plantada ou destinada à colheita (Hectares)", "Fonte": "IBGE – PAM - Produção Agrícola Municipal"},
        {"Código": "MED 1.3", "Indicador": "Área Florestal", "Fonte": "MapBiomas"},
        {"Código": "MED 1.4", "Indicador": "Taxa de população rural", "Fonte": "IBGE – População por municípios"},
        {"Código": "MED 2.1", "Indicador": "Produtores Orgânicos/100 mil hab", "Fonte": "MAPA - Cadastros Nacional de Produtores Orgânicos (CNPO)"},
        {"Código": "MED 2.2", "Indicador": "Empresas com CNAE Ambiental / 10 mil empresas", "Fonte": "Mapa de Empresas"},
        {"Código": "MED 2.3", "Indicador": "Estabelecimentos agropecuários com uso de agricultura/pecuária orgânica (%)", "Fonte": "Censo Agropecuário"},
        {"Código": "MED 3.1", "Indicador": "% de pessoas que percorrem a maior parte do trajeto para o trabalho a pé", "Fonte": "Censo Demográfico 2022"},
        {"Código": "MED 3.2", "Indicador": "% de pessoas que percorrem a maior parte do trajeto para o trabalho de transporte público", "Fonte": "Censo Demográfico 2022"},
        {"Código": "MED 3.3", "Indicador": "(Inverso da) Duração média do deslocamento para o trabalho", "Fonte": "Censo Demográfico 2022"},
        {"Código": "MED 4.1", "Indicador": "Índice ODS 12 Consumo e produção responsáveis", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "MED 4.2", "Indicador": "Índice ODS 13 Ação contra a mudança global do clima", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "MED 4.3", "Indicador": "Taxa de habitantes por Volume de Esgoto coletado por dia", "Fonte": "IBGE – Pesquisa Nacional de Saneamento Básico"},
        {"Código": "MED 4.4", "Indicador": "% de domicílios com coleta de lixo", "Fonte": "IBGE – Censo Demográfico 2022"},
        {"Código": "MED 5.1", "Indicador": "Árvores viárias por habitante", "Fonte": "IBGE / Prefeituras – Inventários Florestais Urbanos"},
        {"Código": "MED 5.2", "Indicador": "Índice ODS 6 Água potável e saneamento", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "MED 5.3", "Indicador": "Índice ODS 7 Energia acessível e limpa", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "MED 5.4", "Indicador": "Índice ODS 14 Vida na Água", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
        {"Código": "MED 5.5", "Indicador": "Índice ODS 15 Vida Terrestre", "Fonte": "Índice de Desenvolvimento Sustentável das Cidades"},
    ]
    st.dataframe(pd.DataFrame(indicadores_meta), use_container_width=True, hide_index=True, height=460)

tab_barras, tab_radar = st.tabs(["Gráfico de Barras", "Gráfico de Radar"])

with tab_barras:
    with st.expander("Configurar Análise de Subgrupo", expanded=True):
        col_ind1, col_ind2, col_ind3, col_ind4 = st.columns(4)
        with col_ind1:
            eixo_sel = st.selectbox("Eixo", ["Econômico", "Sociocultural", "Ambiental"], key="bar_eixo")
        with col_ind2:
            subgrupos = {
                "Econômico": ["EC1", "EC2", "EC3", "EC4", "EC5", "EC6", "EC7", "EC8"],
                "Sociocultural": ["SOC1", "SOC2", "SOC3", "SOC4", "SOC5", "SOC6", "SOC7"],
                "Ambiental": ["MED1", "MED2", "MED3", "MED4", "MED5"],
            }[eixo_sel]
            sub_sel = st.selectbox("Subgrupo", subgrupos, key="bar_subgrupo")
        with col_ind3:
            nivel_ind = st.selectbox("Nível de Agrupamento", ["Municipal", "Estadual", "Regional"], key="bar_nivel")
        with col_ind4:
            if nivel_ind == "Municipal":
                territorio = st.multiselect(
                    "Selecionar Municípios",
                    df_raw["Ecossistema"].unique(),
                    default=df_raw["Ecossistema"].unique()[:5],
                    key="bar_territorio_mun",
                )
            elif nivel_ind == "Estadual":
                territorio = st.multiselect(
                    "Selecionar Estados",
                    df_raw["Estado"].unique(),
                    default=df_raw["Estado"].unique()[:5],
                    key="bar_territorio_uf",
                )
            else:
                territorio = st.multiselect(
                    "Selecionar Regiões",
                    df_raw["Região"].unique(),
                    default=df_raw["Região"].unique(),
                    key="bar_territorio_reg",
                )

    cols_indicadores = [c for c in df_raw.columns if c.startswith(f"{sub_sel}.")]
with st.expander("Ver tabela de subgrupos (código, nome e descritivo)", expanded=False):
    descritivos_subgrupos = {
        "EC1": "Densidade econômico-empresarial: mede a vitalidade da atividade econômica local, pela concentração de empresas (de MEI a grandes) e presença de atividades de maior valor agregado, como inovação e pesquisa.",
        "EC2": "Diversidade econômico-empresarial: avalia a heterogeneidade da economia, a presença de negócios de impacto e empresas inovadoras, incluindo diversidade de gênero em lideranças, como proxy de resiliência e equidade.",
        "EC3": "Conectividade empresarial: observa a infraestrutura que cola o ecossistema (coworkings, incubadoras, polos tech, associações), indicando capacidade de articulação e troca entre atores econômicos.",
        "EC4": "Fluidez financeira: mede o sistema circulatório do capital, considerando disponibilidade de recursos públicos e privados, fomento a áreas estratégicas e capacidade de consumo das famílias.",
        "EC5": "Geração de riqueza: foca no saldo líquido de criação de empresas e empregos, como sinal de resiliência e dinamismo real do ambiente de negócios.",
        "EC6": "Geração de economia de impacto: identifica o quanto o crescimento econômico se orienta por propósito, olhando para economia social e solidária, sobrevivência de empresas e adesão a práticas de responsabilidade socioambiental.",
        "EC7": "Mercado de trabalho: aplica uma lente de equidade sobre o emprego, avaliando inserção de grupos historicamente vulneráveis (jovens, mulheres, PCDs, imigrantes) e oferta de trabalho decente.",
        "EC8": "Distribuição de riqueza: verifica se a riqueza gerada melhora o padrão de vida, combinando PIB per capita, desigualdade (Gini) e custo de vida local para responder a quem serve a prosperidade.",
        "SOC1": "Densidade e infraestrutura cultural: mensura a espinha dorsal do setor cultural (empregos, salários, museus, equipamentos, uso de leis de incentivo) como base de identidade e coesão social.",
        "SOC2": "Densidade de talento: avalia a qualidade do capital humano por meio de trajetória educacional, escolaridade básica, ensino superior e qualificação docente.",
        "SOC3": "Diversidade e conectividade cultural: mede inclusão, acesso à informação e abertura do sistema, via acesso digital (internet, telefonia) articulado a dimensões de igualdade e diversidade.",
        "SOC4": "Fluidez de gasto: quantifica o fluxo de recursos para a cultura, olhando execução orçamentária, captação via leis de incentivo e capacidade institucional de executar projetos culturais.",
        "SOC5": "Atividade / passividade cultural: observa engajamento cívico e participação na vida comunitária (presença em eventos culturais, participação eleitoral), distinguindo população mais ativa ou mais passiva.",
        "SOC6": "Qualidade / Alegria de vida: captura o bem-estar de forma holística: segurança, justiça social, saneamento, longevidade e acesso à fruição cultural cotidiana.",
        "SOC7": "Vida saudável: diagnostica a saúde da população, combinando determinantes sociais (ausência de fome), comportamentos (alimentação, exercício) e estrutura de saúde (densidade de médicos).",
        "MED1": "Densidade economia rural: traça o panorama de ocupação do solo e importância do modo de vida rural, observando extensão das atividades agroflorestais e distribuição rural/urbana da população.",
        "MED2": "Economia ambiental: mede a força da economia verde, via agricultura orgânica, cadeias de reciclagem e adesão a sistemas de gestão ambiental e de pegada de carbono.",
        "MED3": "Mobilidade ecológica / conectividade rural: avalia padrões de deslocamento (transporte sustentável vs. motorizado individual) e vitalidade de associações de produtores e ONGs ambientais.",
        "MED4": "Consumo responsável: monitora a transição energética e a pegada ecológica, analisando investimentos ambientais da indústria, evolução da matriz energética, novos modelos econômicos e uso de recursos.",
        "MED5": "Qualidade do ambiente rural e urbano: faz o diagnóstico direto da saúde dos ecossistemas e da habitabilidade, com indicadores de qualidade do ar, proteção da biodiversidade e acesso a água, saneamento e energia limpa.",
    }
    nomes_subgrupos = {
        "EC1": "Densidade econômico-empresarial",
        "EC2": "Diversidade econômico-empresarial",
        "EC3": "Conectividade empresarial",
        "EC4": "Fluidez financeira",
        "EC5": "Geração de riqueza",
        "EC6": "Geração de economia de impacto",
        "EC7": "Mercado de trabalho",
        "EC8": "Distribuição de riqueza",
        "SOC1": "Densidade e infraestrutura cultural",
        "SOC2": "Densidade de talento",
        "SOC3": "Diversidade e conectividade cultural",
        "SOC4": "Fluidez de gasto",
        "SOC5": "Atividade / passividade cultural",
        "SOC6": "Qualidade / Alegria de vida",
        "SOC7": "Vida saudável",
        "MED1": "Densidade economia rural",
        "MED2": "Economia ambiental",
        "MED3": "Mobilidade ecológica / conectividade rural",
        "MED4": "Consumo responsável",
        "MED5": "Qualidade do ambiente rural e urbano",
    }
    ordem_subgrupos = [
        "EC1", "EC2", "EC3", "EC4", "EC5", "EC6", "EC7", "EC8",
        "SOC1", "SOC2", "SOC3", "SOC4", "SOC5", "SOC6", "SOC7",
        "MED1", "MED2", "MED3", "MED4", "MED5",
    ]
    subgrupos_meta = [
        {
            "Código do subgrupo": codigo,
            "Nome do subgrupo": nomes_subgrupos[codigo],
            "Descritivo do subgrupo": descritivos_subgrupos[codigo],
        }
        for codigo in ordem_subgrupos
    ]
    st.dataframe(pd.DataFrame(subgrupos_meta), use_container_width=True, hide_index=True, height=460)

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
        df_ind_final = df_raw[df_raw["Ecossistema"].isin(territorio)]
        label_col = "Ecossistema"
    elif nivel_ind == "Estadual":
        df_ind_final = df_raw[df_raw["Estado"].isin(territorio)].groupby("Estado")[cols_indicadores].mean().reset_index()
        label_col = "Estado"
    else:
        df_ind_final = df_raw[df_raw["Região"].isin(territorio)].groupby("Região")[cols_indicadores].mean().reset_index()
        label_col = "Região"

    if not df_ind_final.empty and cols_indicadores:
        df_long = df_ind_final.melt(id_vars=[label_col], value_vars=cols_indicadores, var_name="Indicador", value_name="Nota")
        fig_ind = px.bar(
            df_long,
            x="Indicador",
            y="Nota",
            color=label_col,
            barmode="group",
            title=f"Desempenho Detalhado - {sub_sel}",
            text_auto=".2f",
            color_discrete_sequence=indei.COLORWAY,
        )
        indei.style_plotly(fig_ind)
        st.plotly_chart(fig_ind, use_container_width=True)

with tab_radar:
    st.markdown("Compare territórios com visualização em radar por eixos, subgrupos ou indicadores.")

    eixo_to_subgrupos = {
        "Econômico": ["EC1", "EC2", "EC3", "EC4", "EC5", "EC6", "EC7", "EC8"],
        "Sociocultural": ["SOC1", "SOC2", "SOC3", "SOC4", "SOC5", "SOC6", "SOC7"],
        "Ambiental": ["MED1", "MED2", "MED3", "MED4", "MED5"],
    }

    c_r1, c_r2 = st.columns(2)
    with c_r1:
        radar_tipo = st.selectbox(
            "Tipo de Radar",
            [
                "3 pontas (Eixos Gerais)",
                "X pontas (Média dos Subgrupos)",
                "X pontas (Indicadores do Subgrupo)",
            ],
            key="radar_tipo",
        )
    with c_r2:
        radar_nivel = st.selectbox(
            "Nível de Agrupamento",
            ["Geral Brasil", "Regional", "Estadual", "Municipal"],
            key="radar_nivel",
        )

    if radar_nivel == "Regional":
        opcoes = sorted(df_raw["Região"].dropna().unique())
        selecionados = st.multiselect("Selecionar Regiões", opcoes, default=opcoes, key="radar_sel_reg")
        radar_df = df_raw[df_raw["Região"].isin(selecionados)].groupby("Região", as_index=False).mean(numeric_only=True)
        radar_label = "Região"
    elif radar_nivel == "Estadual":
        opcoes = sorted(df_raw["Estado"].dropna().unique())
        selecionados = st.multiselect("Selecionar Estados", opcoes, default=opcoes[:5], key="radar_sel_uf")
        radar_df = df_raw[df_raw["Estado"].isin(selecionados)].groupby("Estado", as_index=False).mean(numeric_only=True)
        radar_label = "Estado"
    elif radar_nivel == "Municipal":
        opcoes = sorted(df_raw["Ecossistema"].dropna().unique())
        selecionados = st.multiselect("Selecionar Municípios", opcoes, default=opcoes[:5], key="radar_sel_mun")
        radar_df = df_raw[df_raw["Ecossistema"].isin(selecionados)].copy()
        radar_label = "Ecossistema"
    else:
        radar_df = df_raw.select_dtypes(include="number").mean(numeric_only=True).to_frame().T
        radar_df[["Rótulo"]] = "Brasil"
        radar_label = "Rótulo"

    if radar_tipo == "3 pontas (Eixos Gerais)":
        radar_cols = ["Eixo Econômico", "Eixo Sociocultural", "Eixo Ambiental"]
        radar_title = "Radar dos 3 Eixos Gerais"
    elif radar_tipo == "X pontas (Média dos Subgrupos)":
        eixo_sub = st.selectbox("Selecionar conjunto de subgrupos", list(eixo_to_subgrupos.keys()), key="radar_subgrupo_eixo")
        subgrupos_sel = eixo_to_subgrupos[eixo_sub]
        radar_cols = []
        for sg in subgrupos_sel:
            sg_cols = [c for c in df_raw.columns if c.startswith(f"{sg}.")]
            if sg_cols:
                radar_df[sg] = radar_df[sg_cols].mean(axis=1, skipna=True)
                radar_cols.append(sg)
        radar_title = f"Radar de Médias dos Subgrupos - Eixo {eixo_sub}"
    else:
        eixo_sub = st.selectbox("Selecionar eixo para escolher subgrupo", list(eixo_to_subgrupos.keys()), key="radar_ind_eixo")
        subgrupo_ind = st.selectbox("Selecionar subgrupo", eixo_to_subgrupos[eixo_sub], key="radar_ind_subgrupo")
        radar_cols = [c for c in df_raw.columns if c.startswith(f"{subgrupo_ind}.")]
        radar_title = f"Radar de Indicadores - {subgrupo_ind}"

    radar_cols_valid = [c for c in radar_cols if c in radar_df.columns]
    radar_cols_valid = [c for c in radar_cols_valid if radar_df[c].notna().any()]

    if radar_df.empty or not radar_cols_valid:
        st.info("Sem dados suficientes para montar o radar com os filtros atuais.")
    else:
        fig_radar = go.Figure()
        for i, (_, row) in enumerate(radar_df.iterrows()):
            nome = str(row[radar_label]) if radar_label in radar_df.columns else f"Série {i+1}"
            valores = [row[col] for col in radar_cols_valid]
            valores.append(valores[0])
            theta = radar_cols_valid + [radar_cols_valid[0]]
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=valores,
                    theta=theta,
                    fill="toself",
                    name=nome,
                    opacity=0.55,
                )
            )

        indei.style_plotly(fig_radar)
        fig_radar.update_layout(
            title=radar_title,
            polar=dict(radialaxis=dict(visible=True)),
            height=650,
            showlegend=True,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

st.divider()