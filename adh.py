import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. CONFIGURAÇÃO DE DESIGN (UI/UX) ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# CSS Customizado para deixar o painel com cara de App profissional
st.markdown("""
    <style>
    /* Estilização dos Cards */
    .stMetric {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #333;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    /* Título do Cronômetro */
    .timer-text {
        font-family: 'Courier New', Courier, monospace;
        color: #00d1b2;
        text-shadow: 0px 0px 10px #00d1b2;
    }
    /* Estilização da Tabela de Colegas */
    .colega-card {
        background-color: #262730;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        border-left: 4px solid #fdfd96;
    }
    /* Botões Grandes */
    .stButton>button {
        height: 3em;
        border-radius: 10px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURAÇÃO DE DADOS ---
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

if 'autenticado' not in st.session_state:
    st.session_state.update({'autenticado': False, 'perfil': None, 'usuario_nome': "", 'status': "Disponível", 'inicio_status': datetime.now()})

def carregar_dados(url):
    try:
        df = pd.read_csv(url + f"&cache={time.time()}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except: return pd.DataFrame()

def formatar_tempo(inicio):
    diff = datetime.now() - inicio
    m, s = divmod(int(diff.total_seconds()), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# --- 3. TELAS ---

def tela_login():
    st.markdown("<h1 style='text-align: center; color: white;'>🚀 ConvertaX <span style='color: #00d1b2;'>WFM</span></h1>", unsafe_allow_html=True)
    df_users = carregar_dados(URL_ACESSOS)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login"):
            email = st.text_input("E-mail Corporativo").strip().lower()
            senha = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR PAINEL", use_container_width=True):
                user_match = df_users[df_users['email'].str.lower() == email] if not df_users.empty else pd.DataFrame()
                if not user_match.empty and str(user_match.iloc[0]['senha']) == senha:
                    st.session_state.update({'autenticado': True, 'perfil': user_match.iloc[0]['perfil'], 'usuario_nome': user_match.iloc[0]['nome']})
                    st.rerun()
                else: st.error("Acesso negado. Verifique e-mail e senha.")

def tela_agente():
    # Header Principal
    c_logo, c_nome = st.columns([0.1, 0.9])
    with c_nome:
        st.title(f"Bem-vindo, {st.session_state.usuario_nome}")
    
    # Busca Escala
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2, meu_grupo = "--:--", "--:--", ""
    if not df_escala.empty:
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_row.empty:
            p1, p2, meu_grupo = user_row.iloc[0]['pausa_1'], user_row.iloc[0]['pausa_2'], user_row.iloc[0]['pausa_1']

    # --- LINHA 1: METRICAS ---
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Lanche (P1)", p1)
    with m2: st.metric("Descanso (P2)", p2)
    with m3: st.metric("Sessão Atual", formatar_tempo(st.session_state.inicio_status))

    st.markdown("<br>", unsafe_allow_html=True)

    # --- LINHA 2: FOCO OPERACIONAL ---
    col_main, col_side = st.columns([2, 1])

    with col_main:
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center; font-size: 1.2rem; color: #888;'>STATUS: <b>{st.session_state.status.upper()}</b></p>", unsafe_allow_html=True)
            st.markdown(f"<h1 class='timer-text' style='text-align: center; font-size: 120px; margin-top: -20px;'>{formatar_tempo(st.session_state.inicio_status)}</h1>", unsafe_allow_html=True)
            
            c_btn1, c_btn2, c_btn3 = st.columns([1,2,1])
            with c_btn2:
                if st.session_state.status != "Em Pausa":
                    if st.button("☕ INICIAR PAUSA", type="primary", use_container_width=True):
                        st.session_state.status = "Em Pausa"; st.session_state.inicio_status = datetime.now(); st.rerun()
                else:
                    if st.button("🟢 VOLTAR AO TRABALHO", use_container_width=True):
                        st.session_state.status = "Disponível"; st.session_state.inicio_status = datetime.now(); st.rerun()

    with col_side:
        st.markdown("### 👥 Meu Grupo")
        if not df_escala.empty:
            colegas = df_escala[(df_escala['pausa_1'] == meu_grupo) & (df_escala['nome'].str.lower() != st.session_state.usuario_nome.lower())]
            if not colegas.empty:
                for _, row in colegas.iterrows():
                    st.markdown(f"<div class='colega-card'>👤 <b>{row['nome']}</b><br><small>Pausas: {row['pausa_1']} | {row['pausa_2']}</small></div>", unsafe_allow_html=True)
            else: st.caption("Nenhum colega no mesmo horário.")

    # Mural de Avisos
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📢 Mural de Avisos da Supervisão", expanded=True):
        st.warning("⚠️ **Lentidão detectada:** Backoffice CASSINO/VERA. Não abrir chamados duplicados.")

def tela_admin():
    st.title("🛡️ Painel de Gestão WFM")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Experts Online", "18")
    m2.metric("Em Pausa", "4")
    m3.metric("Aderência Dia", "94%")
    m4.metric("NPS Acumulado", "9.1")

    st.divider()
    
    col_tab, col_inc = st.columns([2, 1])
    with col_tab:
        st.subheader("📊 Escala Geral")
        df_escala = carregar_dados(URL_ESCALA)
        st.dataframe(df_escala, use_container_width=True, hide_index=True)
    
    with col_inc:
        st.subheader("🚩 Incidentes Ativos")
        st.error("**[CRÍTICO]** Lentidão Sistema de Pagamentos\n\n*Início: 10:20*")
        st.info("**[INFO]** Atualização de script de atendimento disponível no Drive.")

# --- 4. EXECUÇÃO ---
if not st.session_state.autenticado:
    tela_login()
else:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.title("Menu")
        st.write(f"Usuário: **{st.session_state.usuario_nome}**")
        st.write(f"Perfil: {st.session_state.perfil}")
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            st.session_state.autenticado = False; st.rerun()
    
    if st.session_state.perfil == "Admin": tela_admin()
    else: tela_agente()
    
    time.sleep(1)
    st.rerun()
