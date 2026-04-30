import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. INICIALIZAÇÃO DO ESTADO (EVITA O ERRO ATTRIBUTERROR) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.perfil = None
    st.session_state.usuario_nome = ""
    st.session_state.status = "Disponível"
    st.session_state.inicio_status = datetime.now()

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", initial_sidebar_state="expanded")

# CSS para Estilização
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .cronometro { font-size: 60px; font-weight: bold; text-align: center; color: #00d1b2; padding: 10px; }
    .card-esteira { background-color: #1e1e1e; border-radius: 10px; padding: 15px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES DE APOIO ---
def calcular_tempo(inicio):
    if not inicio: return "00:00"
    diff = datetime.now() - inicio
    minutos, segundos = divmod(diff.seconds, 60)
    return f"{minutos:02d}:{segundos:02d}"

# Banco de dados temporário (Será substituído pelo Google Sheets)
usuarios_db = {
    "admin@convertax.com.br": {"nome": "Supervisor WFM", "perfil": "Admin", "senha": "admin"},
    "agente@convertax.com.br": {"nome": "Expert ConvertaX", "perfil": "Agente", "senha": "123"}
}

# --- 4. TELAS DO SISTEMA ---

def tela_login():
    st.markdown("<h1 style='text-align: center;'>🔐 Login WFM ConvertaX</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("form_login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if email in usuarios_db and usuarios_db[email]['senha'] == senha:
                    st.session_state.autenticado = True
                    st.session_state.perfil = usuarios_db[email]['perfil']
                    st.session_state.usuario_nome = usuarios_db[email]['nome']
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

def exibir_esteira():
    st.subheader("📋 Esteira de Operação (Tempo Real)")
    # Simulação de dados (Isso virá do Sheets para todos verem a mesma coisa)
    dados = [
        {"Agente": st.session_state.usuario_nome, "Status": st.session_state.status, "Início": st.session_state.inicio_status, "Pausa": "21:30"},
        {"Agente": "Lucas Ryann", "Status": "Em Atendimento", "Início": datetime.now() - timedelta(minutes=15), "Pausa": "21:00"},
        {"Agente": "Francielle", "Status": "Disponível", "Início": datetime.now() - timedelta(minutes=5), "Pausa": "21:00"}
    ]
    df = pd.DataFrame(dados)
    df['Tempo'] = df['Início'].apply(calcular_tempo)
    
    # Exibição estilizada
    st.dataframe(df[['Agente', 'Status', 'Tempo', 'Pausa']], use_container_width=True, hide_index=True)

def tela_agente():
    st.title(f"🚀 Painel do Expert")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Seu Status", st.session_state.status)
        c2.metric("Tempo no Status", calcular_tempo(st.session_state.inicio_status))
        c3.metric("Próxima Pausa", "21:30")

    col_btn1, col_btn2 = st.columns(2)
    if st.session_state.status != "Em Pausa":
        if col_btn1.button("☕ INICIAR MINHA PAUSA", use_container_width=True, type="primary"):
            st.session_state.status = "Em Pausa"
            st.session_state.inicio_status = datetime.now()
            st.rerun()
    else:
        if col_btn1.button("🟢 VOLTAR AO ATENDIMENTO", use_container_width=True):
            st.session_state.status = "Em Atendimento"
            st.session_state.inicio_status = datetime.now()
            st.rerun()

    st.divider()
    exibir_esteira()

def tela_admin():
    st.title("🛡️ Dashboard de Supervisão")
    st.write("Visão macro da operação e aderência.")
    
    exibir_esteira()
    
    st.divider()
    st.subheader("🚨 Último Incidente Registrado")
    st.error("Lentidão Backoffice (Brands CASSINO/VERA) - 23:41")

# --- 5. LÓGICA DE NAVEGAÇÃO ---

if not st.session_state.autenticado:
    tela_login()
else:
    # Botão de Logout
