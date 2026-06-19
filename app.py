import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Conferente de Lances", page_icon="📊", layout="wide")

# Inicializa a variável de controle para o botão "Nova Conferência"
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

def resetar_app():
    """Função para limpar o arquivo enviado e iniciar nova conferência."""
    st.session_state["file_uploader_key"] += 1

# --- CABEÇALHO COM LOGO ---
# Verifica se a imagem existe no repositório para evitar erros de inicialização
if os.path.exists("logo_drogafonte (1).png"):
    st.image("logo_drogafonte (1).png", width=250)
else:
    st.info("💡 Dica: Suba o arquivo 'logo_drogafonte (1).png' no seu GitHub para exibir a logo aqui.")

st.title("📊 Conferente de Lances de Pregão")
st.write("Identifique automaticamente lances com descontos excessivos ou valores acima do Valor Inicial.")

# Botão de Nova Conferência no topo
col_titulo, col_botao = st.columns([4, 1])
with col_botao:
    st.button("🔄 Nova Conferência", on_click=resetar_app, use_container_width=True)

# Widget de upload
uploaded_file = st.file_uploader(
    "Selecione o relatório (.xls, .xlsx ou .csv)", 
    type=["csv", "xls", "xlsx"], 
    key=str(st.session_state["file_uploader_key"])
)

if uploaded_file is not None:
    try:
        # --- 1. IDENTIFICAÇÃO DO CABEÇALHO ---
        if uploaded_file.name.endswith('.csv'):
            df_cabecalho = pd.read_csv(uploaded_file, nrows=5, header=None, encoding='utf-8')
        else:
            df_cabecalho = pd.read_excel(uploaded_file, nrows=5, header=None)
        
        info_pregao = str(df_cabecalho.iloc[3, 0]) if len(df_cabecalho) > 3 else "Informação do pregão não encontrada"
        info_emissao = str(df_cabecalho.iloc[4, 0]) if len(df_cabecalho) > 4 else "Informação de emissão não encontrada"
        
        st.info(f"**Identificação do Relatório:**\n\n📌 {info_pregao}\n\n⏱️ {info_emissao}")
        
        uploaded_file.seek(0)
        
        # --- 2. PROCESSAMENTO DOS DADOS ---
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=6)
        else:
            df = pd.read_excel(uploaded_file, skiprows=6)
            
        df.columns = df.columns.str.strip()
        
        lances_acima = []
        descontos_excessivos = []
        todos_alertas = []
        
        coluna_desc = '--------------------------------- D i s c r i m i n a ç ã o ---------------------------------'
        
        for index, row in df.iterrows():
            try:
                vlr_unit = float(row['Vlr. Unit.'])
                lance = float(row['Lance'])
                item = row['Item']
                
                descricao = str(row[coluna_desc])[:80].replace('\n', ' ') + "..." if coluna_desc in row else "Sem descrição"
                
                # Regra 1: Lance MAIOR que o Valor Inicial
                if lance > vlr_unit:
                    dados_alerta = {
                        "Item": item,
                        "Tipo de Alerta": "LANCE ACIMA DO VALOR",
                        "Descrição": descricao,
                        "Valor Inicial (R$)": round(vlr_unit, 4),
                        "Lance (R$)": round(lance, 4),
                        "Diferença / Desconto": f"R$ {(lance - vlr_unit):.4f} a mais"
                    }
                    lances_acima.append(dados_alerta)
                    todos_alertas.append(dados_alerta)
                    continue
                    
                # Regra 2: Desconto de MAIS DE 40%
                limite_minimo = vlr_unit * 0.60
                
                if lance < limite_minimo:
                    desconto_perc = ((vlr_unit - lance) / vlr_unit) * 100
                    dados_alerta = {
                        "Item": item,
                        "Tipo de Alerta": "DESCONTO > 40%",
                        "Descrição": descricao,
                        "Valor Inicial (R$)": round(vlr_unit, 4),
                        "Lance (R$)": round(lance, 4),
                        "Diferença / Desconto": f"{desconto_perc:.1f}% de desconto"
                    }
                    descontos_excessivos.append(dados_alerta)
                    todos_alertas.append(dados_alerta)
                    
            except (ValueError, TypeError):
                continue
            except KeyError as e:
                st.error(f"Erro: Coluna {e} não encontrada. O arquivo não está no padrão esperado.")
                st.stop()
                
        # --- 3. EXIBIÇÃO E DOWNLOAD ---
        st.divider()
        st.subheader("Resultados da Conferência")
        
        col1, col2 = st.columns(2)
        col1.metric("Lances ACIMA do Valor Inicial", len(lances_acima))
        col2.metric("Lances com Desconto > 40%", len(descontos_excessivos))
        
        if todos_alertas:
            df_export = pd.DataFrame(todos_alertas)
            csv_export = df_export.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
            
            st.download_button(
                label="📥 Baixar Relatório de Alertas (Excel/CSV)",
                data=csv_export,
                file_name="alertas_conferencia.csv",
                mime="text/csv",
                type="primary"
            )
            st.write("")
        
        if lances_acima:
            st.error("🚨 Itens com Lance MAIOR que o Valor Inicial:")
            st.dataframe(pd.DataFrame(lances_acima).drop(columns=["Tipo de Alerta"]), use_container_width=True)
            
        if descontos_excessivos:
            st.warning("⚠️ Itens com Desconto EXCESSIVO (Maior que 40% em relação ao Valor Inicial):")
            st.dataframe(pd.DataFrame(descontos_excessivos).drop(columns=["Tipo de Alerta"]), use_container_width=True)
            
        if not todos_alertas:
            st.success("✅ Tudo certo! Nenhum alerta de valor ou desconto encontrado neste arquivo.")
            st.balloons()
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao tentar processar o arquivo: {e}")
