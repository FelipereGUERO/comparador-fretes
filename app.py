import streamlit as st
import pandas as pd

st.title("Protótipo Customizado - Comparador de Fretes")

# Upload múltiplo de arquivos Excel/CSV
uploaded_files = st.file_uploader(
    "Faça upload das planilhas das transportadoras (Excel ou CSV)", 
    accept_multiple_files=True, 
    type=['xlsx', 'xls', 'csv']
)

header_line = st.number_input("Linha do cabeçalho na planilha (base 1)", min_value=1, value=11)

peso_kg = st.number_input("Peso da carga (kg)", min_value=0.1, value=50.0)

ufs = []
cidades = []
dfs_transportadoras = {}

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file, header=header_line-1)
            else:
                df = pd.read_csv(uploaded_file, header=header_line-1)
            dfs_transportadoras[uploaded_file.name] = df
            ufs.extend(df['UF'].dropna().unique())
        except Exception as e:
            st.error(f"Erro ao ler {uploaded_file.name}: {e}")

    ufs = sorted(set(ufs))
    uf_selected = st.selectbox("Selecione a UF", ufs)

    cidades = []
    for df in dfs_transportadoras.values():
        if 'UF' in df.columns and 'CIDADE' in df.columns:
            cidades.extend(df[df['UF'] == uf_selected]['CIDADE'].dropna().unique())
    cidades = sorted(set(cidades))
    cidade_selected = st.selectbox("Selecione a Cidade", cidades)

    def calcular_custo_total(linha, peso_kg):
        faixas = [10, 20, 30, 50, 70, 100]
        colunas = [
            'Até 10 Kg (R$/CTe)',
            'Até 20 Kg (R$/CTe)',
            'Até 30 Kg (R$/CTe)',
            'Até 50 Kg (R$/CTe)',
            'Até 70 Kg (R$/CTe)',
            'Até 100 Kg (R$/CTe)'
        ]
        
        preco_base = None
        for faixa, col in zip(faixas, colunas):
            if peso_kg <= faixa:
                preco_base = linha[col]
                break
        
        if preco_base is None:
            excedente = peso_kg - 100
            preco_base = linha['Até 100 Kg (R$/CTe)'] + excedente * linha['Excedente por KG (R$)']
        
        frete_valor = preco_base * (linha['Frete Valor (%) - ADValorem'] / 100)
        gris_percent = linha['GRIS (%)'] / 100
        minimo_gris = linha['Mínimo de GRIS (R$)']
        gris = max(preco_base * gris_percent, minimo_gris)
        pedagio = (peso_kg / 100) * linha['Fração do pedágio']
        
        custo_total = preco_base + frete_valor + gris + pedagio
        return round(custo_total, 2)

    if st.button("Calcular Melhor Frete"):
        resultados = []
        for nome, df in dfs_transportadoras.items():
            linha = df[(df['UF'] == uf_selected) & (df['CIDADE'] == cidade_selected)]
            if linha.empty:
                st.warning(f"Destino não encontrado em {nome}")
                continue
            linha = linha.iloc[0]
            try:
                custo = calcular_custo_total(linha, peso_kg)
                resultados.append({'Transportadora': nome, 'Custo Total (R$)': custo})
            except Exception as e:
                st.error(f"Erro ao calcular custo para {nome}: {e}")
        if resultados:
            df_resultados = pd.DataFrame(resultados).sort_values('Custo Total (R$)')
            st.dataframe(df_resultados)
            melhor = df_resultados.iloc[0]
            st.success(f"Melhor opção: {melhor['Transportadora']} com custo R$ {melhor['Custo Total (R$)']}")
        else:
            st.error("Nenhum resultado disponível para os parâmetros informados.")
else:
    st.info("Faça upload das planilhas para começar.")