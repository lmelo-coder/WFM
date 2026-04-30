import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÃO DE INTERFACE ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 2. FUNÇÕES DE APOIO (Definidas antes de tudo para evitar NameError) ---
def formatar_tempo(inicio):
    if inicio is None: return "00:00:00"
    diff = datetime.now() - inicio
    m, s = divmod(int(diff.total_seconds()), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def carregar_dados(url):
    try:
        df = pd.read_csv(url + f"&cache={time.time()}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except:
        return pd.DataFrame()

def registrar_log(tipo_evento):
    hora_atual = datetime.now().strftime("%H:%M:%S")
    if 'historico_pausas' in st.session_state:
        st.session_state.historico_pausas.append({"Evento": tipo_evento, "Horário": hora_atual})

# --- 3. INICIALIZAÇÃO DO ESTADO ---
if 'autenticado' not in st.session_state:
    st.session_state.update({
        'autenticado': False,
        'perfil': None,
        'usuario_nome': "",
        'status': "Disponível",
        'inicio_status': datetime.now(),
        'hora_login': None,
        'historico_pausas': []
    })

# --- 4. TELA DE LOGIN ---
def tela_login():
    st.markdown("<h1 style='text-align: center;'>🚀 ConvertaX WFM</h1>", unsafe_allow_html=True)
    df_users = carregar_dados(URL_ACESSOS)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("E-mail Corporativo").strip().lower()
            senha = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR NO TURNO", use_container_width=True):
                if not df_users.empty:
                    user_match = df_users[df_users['email'].str.lower() == email]
                    if not user_match.empty and str(user_match.iloc[0]['senha']) == senha:
                        st.session_state.autenticado = True
                        st.session_state.perfil = user_match.iloc[0]['perfil']
                        st.session_state.usuario_nome = user_match.iloc[0]['nome']
                        st.session_state.hora_login = datetime.now().strftime("%H:%M:%S")
                        registrar_log("Login no Sistema")
                        st.rerun()
                st.error("Dados incorretos ou erro de conexão.")

# --- 5. TELA DO AGENTE ---
def tela_agente():
    st.markdown(f"### Expert: {st.session_state.usuario_nome} | 🟢 Login: {st.session_state.hora_login}")
    
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2 = "00:00", "00:00"
    
    if not df_escala.empty:
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_row.empty:
            p1, p2 = user_row.iloc[0]['pausa_1'], user_row.iloc[0]['pausa_2']

    c1, c2, c3 = st.columns(3)
    c1.metric("Pausa 1", p1)
    c2.metric("Pausa 2", p2)
    # Correção do erro da imagem: garantindo que a função e a variável existem
    c3.metric("Tempo em Status", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    col_main, col_side = st.columns([2, 1])
    with col_main:
        st.markdown(f"<div style='text-align:center; background-color:#1e1e1e; padding:20px; border-radius:15px; border:1px solid #333;'>", unsafe_allow_html=True)
        st.write(f"STATUS ATUAL: **{st.session_state.status.upper()}**")
        st.markdown(f"<h1 style='color:#00d1b2; font-family:monospace; font-size:80px; margin:0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        cols = st.columns(3)
        if st.session_state.status == "Disponível":
            if cols[0].button("☕ Iniciar Pausa", use_container_width=True, type="primary"):
                registrar_log("Início Pausa Escala")
                st.session_state.update({'status': "Pausa Escala", 'inicio_status': datetime.now()}); st.rerun()
            if cols[1].button("🚻 Banheiro", use_container_width=True):
                registrar_log("Início Banheiro")
                st.session_state.update({'status': "Banheiro", 'inicio_status': datetime.now()}); st.rerun()
            if cols[2].button("🏥 Médico/FB", use_container_width=True):
                registrar_log("Início Médico/Feedback")
                st.session_state.update({'status': "Médico/Feedback", 'inicio_status': datetime.now()}); st.rerun()
        else:
            if st.button("🟢 VOLTAR DISPONÍVEL", type="primary", use_container_width=True):
                registrar_log(f"Fim de {st.session_state.status}")
                st.session_state.update({'status': "Disponível", 'inicio_status': datetime.now()}); st.rerun()

    with col_side:
        st.markdown("### 👥 Colegas (Mesmo Turno)")
        if not df_escala.empty:
            colegas = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'] != st.session_state.usuario_nome)]
            for _, row in colegas.iterrows():
                st.info(f"👤 {row['nome']}")

    st.divider()
    st.subheader("📝 Meu Histórico de Pausas")
    if st.session_state.historico_pausas:
        st.table(pd.DataFrame(st.session_state.historico_pausas))

# --- 6. TELA ADMIN ---
def tela_admin():
    st.title("🛡️ Painel Admin")
    df_escala = carregar_dados(URL_ESCALA)
    st.dataframe(df_escala, use_container_width=True)

# --- 7. NAVEGAÇÃO ---
if not st.session_state.autenticado:
    tela_login()
else:
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()
    
    if st.session_state.perfil == "Admin":
        tela_admin()
    else:
        tela_agente()

    time.sleep(1)
    st.rerun()
