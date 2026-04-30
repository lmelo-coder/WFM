import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# URLs das Planilhas (Verifique se os nomes das abas estão corretos)
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 2. INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.perfil = None
    st.session_state.usuario_nome = ""
    st.session_state.status = "Disponível"
    st.session_state.inicio_status = datetime.now()

# --- 3. FUNÇÕES DE APOIO ---
def carregar_dados(url):
    try:
        # Cache buster para evitar dados velhos
        df = pd.read_csv(url + f"&cache={time.time()}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except:
        return pd.DataFrame()

def formatar_tempo(inicio):
    diff = datetime.now() - inicio
    m, s = divmod(int(diff.total_seconds()), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def calcular_atraso_aderencia(horario_planejado):
    try:
        agora = datetime.now()
        hp = datetime.strptime(horario_planejado, "%H:%M").replace(
            year=agora.year, month=agora.month, day=agora.day
        )
        atraso = (agora - hp).total_seconds() / 60
        if atraso > 0 and st.session_state.status == "Disponível":
            return f"⚠️ {int(atraso)} min atrasado"
        return "✅ OK"
    except: return "---"

# --- 4. TELA DE LOGIN ---
def tela_login():
    st.markdown("<h1 style='text-align: center;'>🚀 ConvertaX WFM</h1>", unsafe_allow_html=True)
    df_users = carregar_dados(URL_ACESSOS)
    
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login_form"):
            u_email = st.text_input("E-mail Corporativo").strip().lower()
            u_senha = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ENTRAR", use_container_width=True):
                if not df_users.empty:
                    user_match = df_users[df_users['email'].str.lower() == u_email]
                    if not user_match.empty and str(user_match.iloc[0]['senha']) == u_senha:
                        st.session_state.autenticado = True
                        st.session_state.perfil = user_match.iloc[0]['perfil']
                        st.session_state.usuario_nome = user_match.iloc[0]['nome']
                        st.rerun()
                st.error("Credenciais inválidas ou erro de conexão.")

# --- 5. TELA DO AGENTE ---
def tela_agente():
    st.markdown(f"### 🚀 Expert: {st.session_state.usuario_nome}")
    
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2, in_t = "00:00", "00:00", "00:00"
    
    if not df_escala.empty:
        user_data = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_data.empty:
            p1, p2, in_t = user_data.iloc[0]['pausa_1'], user_data.iloc[0]['pausa_2'], user_data.iloc[0]['inicio_turno']

    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Pausa 1", p1, delta=calcular_atraso_aderencia(p1), delta_color="inverse")
    c2.metric("Pausa 2", p2, delta=calcular_atraso_aderencia(p2), delta_color="inverse")
    c3.metric("Tempo em Status", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    # Cronômetro e Ações
    col_tempo, col_btn = st.columns([1.5, 1])
    with col_tempo:
        st.markdown(f"<div style='background-color:#1e1e1e; padding:20px; border-radius:10px; border:1px solid #333; text-align:center;'>", unsafe_allow_html=True)
        st.write(f"STATUS ATUAL: **{st.session_state.status.upper()}**")
        st.markdown(f"<h1 style='color:#00d1b2; font-family:monospace; font-size:80px; margin:0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_btn:
        st.write("### Alterar Status")
        if st.session_state.status == "Disponível":
            if st.button("☕ INICIAR PAUSA", type="primary", use_container_width=True):
                st.session_state.status = "Pausa Escala"; st.session_state.inicio_status = datetime.now(); st.rerun()
            if st.button("🚻 BANHEIRO / PARTICULAR", use_container_width=True):
                st.session_state.status = "Pausa Particular"; st.session_state.inicio_status = datetime.now(); st.rerun()
            if st.button("🏥 MÉDICO / FEEDBACK", use_container_width=True):
                st.session_state.status = "Médico / Feedback"; st.session_state.inicio_status = datetime.now(); st.rerun()
        else:
            if st.button("🟢 VOLTAR DISPONÍVEL", type="primary", use_container_width=True):
                st.session_state.status = "Disponível"; st.session_state.inicio_status = datetime.now(); st.rerun()

    # Notificação 3 min
    agora = datetime.now().strftime("%H:%M")
    try:
        aviso = (datetime.strptime(p1, "%H:%M") - timedelta(minutes=3)).strftime("%H:%M")
        if agora == aviso: st.toast("🚨 Sua pausa começa em 3 minutos!", icon="⏰")
    except: pass

# --- 6. TELA ADMIN ---
def tela_admin():
    st.title("🛡️ Painel Admin")
    df_escala = carregar_dados(URL_ESCALA)
    st.subheader("Escala Completa")
    st.dataframe(df_escala, use_container_width=True, hide_index=True)

# --- 7. LÓGICA DE NAVEGAÇÃO FINAL ---
if not st.session_state.autenticado:
    tela_login()
else:
    # Sidebar
    st.sidebar.title("Menu")
    st.sidebar.write(f"Usuário: {st.session_state.usuario_nome}")
    if st.sidebar.button("Logoff"):
        st.session_state.autenticado = False
        st.rerun()
    
    # Roteamento de perfil
    if st.session_state.perfil == "Admin":
        tela_admin()
    else:
        tela_agente()

    # Auto-refresh
    time.sleep(1)
    st.rerun()
