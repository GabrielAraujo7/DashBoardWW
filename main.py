import pandas as pd
import unicodedata
import streamlit as st
import plotly.express as px

# ============================================================
# CONFIGURAÇÃO INICIAL DO DASHBOARD
# ============================================================

st.set_page_config(
    page_title="Dashboard SUS",
    layout="wide"
)

st.title("Dashboard de Atendimentos SUS")


# ============================================================
# FUNÇÃO DE PADRONIZAÇÃO DE TEXTO
# Remove espaços, acentos e padroniza tudo em maiúsculo
# ============================================================

def limpar_texto(texto):
    texto = str(texto).upper().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ASCII", "ignore").decode("utf-8")
    return texto


# ============================================================
# ETAPA 1 — LEITURA DAS BASES
# Base 1: Atendimentos SUS
# Base 2: População dos municípios IBGE
# ============================================================

df_dados = pd.read_csv("DADOS.txt")

df_mun = pd.read_excel(
    "estimativa_dou_2021.xls",
    sheet_name="Municípios",
    skiprows=1
)



# ============================================================
# ETAPA 2 — TRATAMENTO DA BASE DO IBGE
# Renomeia colunas e padroniza município
# ============================================================

df_mun.columns = [
    "uf",
    "cod_uf",
    "cod_municipio",
    "nome_municipio",
    "populacao"
]

df_mun = df_mun[df_mun["uf"] == "CE"]

df_mun["municipio"] = df_mun["nome_municipio"].apply(limpar_texto)


# ============================================================
# ETAPA 3 — TRATAMENTO DA BASE DE ATENDIMENTOS
# Padroniza município e corrige divergência de nomenclatura
# ============================================================

df_dados["municipio"] = df_dados["MUNICÍPIO"].apply(limpar_texto)

df_dados["municipio"] = df_dados["municipio"].replace({
    "ITAPAGE": "ITAPAJE"
})


# ============================================================
# ETAPA 4 — TRATAMENTO DA POPULAÇÃO
# Remove pontos e observações como (1), (2), etc.
# ============================================================

df_mun["populacao"] = (
    df_mun["populacao"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(r"\(\d+\)", "", regex=True)
)

df_mun["populacao"] = pd.to_numeric(
    df_mun["populacao"],
    errors="coerce"
)


# ============================================================
# ETAPA 5 — SELEÇÃO DAS COLUNAS NECESSÁRIAS DO IBGE
# ============================================================

df_mun = df_mun[
    ["uf", "municipio", "populacao"]
]


# ============================================================
# ETAPA 6 — CRIAÇÃO DA TABELA DE ATENDIMENTOS
# Conta quantos registros existem por município
# ============================================================

atendimentos = (
    df_dados
    .groupby("municipio")
    .size()
    .reset_index(name="total_atendimentos")
)


# ============================================================
# ETAPA 7 — JUNÇÃO DAS BASES
# Junta atendimentos com população dos municípios
# ============================================================

df_final = atendimentos.merge(
    df_mun,
    on="municipio",
    how="left"
)


# ============================================================
# ETAPA 8 — CRIAÇÃO DAS MÉTRICAS
# atendimentos_100k = atendimentos por 100 mil habitantes
# incoerente = municípios com mais atendimentos que habitantes
# ============================================================

df_final["atendimentos_100k"] = (
    df_final["total_atendimentos"] / df_final["populacao"]
) * 100000

df_final["incoerente"] = (
    df_final["total_atendimentos"] > df_final["populacao"]
)


# ============================================================
# ETAPA 9 — CRIAÇÃO DA REGIÃO
# Como sua base está majoritariamente no CE, Nordeste será dominante
# ============================================================

mapa_regiao = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",

    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",

    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",

    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",

    "PR": "Sul", "RS": "Sul", "SC": "Sul"
}

df_final["regiao"] = df_final["uf"].map(mapa_regiao)


# ============================================================
# ETAPA 10 — EXPORTAÇÃO DA BASE TRATADA
# Essa base pode ser usada no Qlik, Power BI ou Excel
# ============================================================

df_final.to_csv(
    "base_final_bi.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# KPIs PRINCIPAIS
# ============================================================

st.subheader("Indicadores Gerais")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total de Atendimentos",
    int(df_filtrado["total_atendimentos"].sum())
)

col2.metric(
    "Municípios",
    df_filtrado["municipio"].nunique()
)

col3.metric(
    "Média por Município",
    round(df_filtrado["total_atendimentos"].mean(), 2)
)

col4.metric(
    "Municípios Incoerentes",
    int(df_filtrado["incoerente"].sum())
)


# ============================================================
# GRÁFICO 1 — TOP 10 MUNICÍPIOS POR VOLUME ABSOLUTO
# ============================================================

st.subheader("Volume de Atendimentos por Município")

top_volume = (
    df_filtrado
    .sort_values(by="total_atendimentos", ascending=False)
    .head(10)
)

fig_top_volume = px.bar(
    top_volume,
    x="municipio",
    y="total_atendimentos",
    title="Top 10 Municípios por Total de Atendimentos",
    labels={
        "municipio": "Município",
        "total_atendimentos": "Total de Atendimentos"
    }
)

st.plotly_chart(fig_top_volume, use_container_width=True)


# ============================================================
# GRÁFICO 2 — MAIOR VOLUME PROPORCIONAL
# ============================================================

st.subheader("Ranking Proporcional de Atendimentos")

top_proporcional = (
    df_filtrado
    .sort_values(by="atendimentos_100k", ascending=False)
    .head(10)
)

fig_top_prop = px.bar(
    top_proporcional,
    x="municipio",
    y="atendimentos_100k",
    title="Top 10 Municípios com Maior Atendimento por 100 mil Habitantes",
    labels={
        "municipio": "Município",
        "atendimentos_100k": "Atendimentos por 100 mil habitantes"
    }
)

st.plotly_chart(fig_top_prop, use_container_width=True)


# ============================================================
# GRÁFICO 3 — MENOR VOLUME PROPORCIONAL
# ============================================================

menor_proporcional = (
    df_filtrado
    .sort_values(by="atendimentos_100k", ascending=True)
    .head(10)
)

fig_menor_prop = px.bar(
    menor_proporcional,
    x="municipio",
    y="atendimentos_100k",
    title="Top 10 Municípios com Menor Atendimento por 100 mil Habitantes",
    labels={
        "municipio": "Município",
        "atendimentos_100k": "Atendimentos por 100 mil habitantes"
    }
)

st.plotly_chart(fig_menor_prop, use_container_width=True)


# ============================================================
# GRÁFICO 4 — POPULAÇÃO X ATENDIMENTOS
# Ajuda a comparar volume absoluto com tamanho populacional
# ============================================================

st.subheader("Relação entre População e Atendimentos")

fig_scatter = px.scatter(
    df_filtrado,
    x="populacao",
    y="total_atendimentos",
    hover_name="municipio",
    size="atendimentos_100k",
    title="População x Total de Atendimentos",
    labels={
        "populacao": "População",
        "total_atendimentos": "Total de Atendimentos",
        "atendimentos_100k": "Atendimentos por 100 mil"
    }
)

st.plotly_chart(fig_scatter, use_container_width=True)



# ============================================================
# TABELA — MUNICÍPIOS COM POSSÍVEL INCOERÊNCIA
# ============================================================

st.subheader("Validação de Coerência")

incoerentes = df_filtrado[df_filtrado["incoerente"] == True]

if incoerentes.empty:
    st.success("Não foram encontrados municípios com mais atendimentos que habitantes.")
else:
    st.warning("Foram encontrados municípios com mais atendimentos que habitantes.")
    st.dataframe(incoerentes)


# ============================================================
# TABELA FINAL — BASE ENRIQUECIDA
# ============================================================

st.subheader("Base Final Enriquecida")

st.dataframe(df_filtrado)