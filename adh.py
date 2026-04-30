import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURAÇÃO DA CONEXÃO DIRETA ---
# Substituímos o segredo pelo link público para facilitar seu acesso agora
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"

# --- INICIALIZAÇÃO DO ESTADO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.perfil = None
    st.session_state.usuario_nome = ""
    st.session_state.status = "Disponível"
    st.session_state.inicio_status = datetime.now()

# --- FUNÇÃO PARA CARREGAR USUÁRIOS DA PLANILHA ---
def carregar_usuarios():
    try:
        # Lê a planilha convertendo para CSV via URL pública
        df = pd.read_csv(SHEET_URL)
        # Limpa nomes de colunas (remove espaços)
        df.columns = df.columns.str.strip().str.lower()
        return df.set_index('email').to_dict('index')
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return {}

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide")

# --- TELA DE LOGIN ---
def tela_login():
    st.markdown("<h1 style='text-align: center;'>🔐 Login WFM</h1>", unsafe_allow_html=True)
    
    usuarios_db = carregar_usuarios()
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("form_login"):
            email = st.text_input("E-mail corporativo").strip().lower()
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if email in usuarios_db and str(usuarios_db[email]['senha']) == str(senha):
                    st.session_state.autenticado = True
                    st.session_state.perfil = usuarios_db[email]['perfil']
                    st.session_state.usuario_nome = usuarios_db[email]['nome']
                    st.rerun()
                else:
                    st.error("Usuário não encontrado ou senha incorreta.")
        
        st.info("💡 Os acessos são gerenciados pela planilha de escala.")

# --- TELAS DE PERFIL ---
def tela_agente():
    st.title(f"🚀 Painel do Expert: {st.session_state.usuario_nome}")
    # ... (restante do código de cronômetro e botões que enviamos antes)
    st.write("Visão do Agente Ativa")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

def tela_admin():
    st.title("🛡️ Painel de Supervisão")
    st.write("Bem-vindo, Supervisor. Aqui você verá a esteira de todos.")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

# --- FLUXO PRINCIPAL ---
if not st.session_state.autenticado:
    tela_login()
else:
    if st.session_state.perfil == "Admin":
        tela_admin()
    else:
        tela_agente()
