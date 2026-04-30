import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÃO DE INTERFACE (Sempre o primeiro comando) ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# --- 2. INICIALIZAÇÃO DO ESTADO DE SESSÃO (Evita o AttributeError) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'perfil' not in st.session_state:
    st.session_state.perfil = None
if 'usuario_nome' not in st.session_state:
    st.session_state.usuario_nome = ""
if 'status' not in st.session_state:
    st.session_state.status = "Disponível"
if 'inicio_status' not in st.session_state:
    st.session_state.inicio_status = datetime.now()
if 'hora_login' not in st.session_state:
    st.session_state.hora_login = None
if 'historico_pausas' not in st.session_state:
    st.session_state.historico_pausas = []

# --- 3. FUNÇÕES DE SUPORTE (Definidas antes do uso para evitar NameError) ---
def carregar_dados(url):
    try:
        # Força o refresh da planilha com timestamp
        df = pd.read_csv(f"{url}&cache={int(time.time())}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except:
        return pd.DataFrame()

def formatar_tempo(inicio):
    if inicio is None: return "00:00:00"
    diff = datetime.now() - inicio
    total_segundos = int(diff.total_seconds())
    horas, resto = divmod(total_segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def registrar_log(tipo_evento):
    hora_atual = datetime.now().strftime("%H:%M:%S")
    st.session_state.historico_pausas.append({
        "Evento": tipo_evento,
        "Horário": hora_atual
    })

# URLs das Planilhas
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

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
                st.error("Dados incorretos ou erro de conexão com a planilha.")

# --- 5. TELA DO AGENTE ---
def tela_agente():
    st.markdown(f"### Expert: {st.session_state.usuario_nome} | 🟢 Login: {st.session_state.hora_login}")
    
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2 = "00:00", "00:00"
    
    if not df_escala.empty:
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_row.empty:
            p1, p2 = user_row.iloc[0]['pausa_1'], user_row.iloc[0]['pausa_2']

    # Métricas principais
    m1, m2, m3 = st.columns(3)
    m1.metric("Pausa 1", p1)
    m2.metric("Pausa 2", p2)
    m3.metric("Tempo em Status", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    # Layout de Status e Grupo
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.markdown(f"<div style='text-align:center; background-color:#1e1e1e; padding:20px; border-radius:15px; border:1px solid #333;'>", unsafe_allow_html=True)
        st.write(f"STATUS ATUAL: **{st.session_state.status.upper()}**")
        st.markdown(f"<h1 style='color:#00d1b2; font-family:monospace; font-size:80px; margin:0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns(3)
        if st.session_state.status == "Disponível":
            if cols[0].button("☕ Iniciar Pausa", use_container_width=True, type="primary"):
                registrar_log("Início Pausa Escala")
                st.session_state.update({'status': "Pausa Escala", 'inicio_status': datetime.now()})
                st.rerun()
            if cols[1].button("🚻 Banheiro", use_container_width=True):
                registrar_log("Início Banheiro")
                st.session_state.update({'status': "Banheiro", 'inicio_status': datetime.now()})
                st.rerun()
            if cols[2].button("🏥 Médico/FB", use_container_width=True):
                registrar_log("Início Médico/Feedback")
                st.session_state.update({'status': "Médico/Feedback", 'inicio_status': datetime.now()})
                st.rerun()
        else:
            if st.button("🟢 FINALIZAR E VOLTAR DISPONÍVEL", type="primary", use_container_width=True):
                registrar_log(f"Fim de {st.session_state.status}")
                st.session_state.update({'status': "Disponível", 'inicio_status': datetime.now()})
                st.rerun()

    with col_side:
        st.markdown("### 👥 Colegas (Mesmo Turno)")
        if not df_escala.empty:
            # Mostra quem tem o mesmo horário de Pausa 1
            colegas = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'] != st.session_state.usuario_nome)]
            if not colegas.empty:
                for _, row in colegas.iterrows():
                    st.info(f"👤 {row['nome']}")
            else:
                st.caption("Nenhum colega neste horário.")

    # Histórico de Registros
    st.divider()
    st.subheader("📝 Meu Histórico de Pausas")
    if st.session_state.historico_pausas:
        st.table(pd.DataFrame(st.session_state.historico_pausas))
    else:
        st.info("Nenhum registro ainda.")

# --- 6. TELA ADMIN (ESTRUTURA SIMPLES) ---
def tela_admin():
    st.title("🛡️ Painel Admin")
    st.write(f"Bem-vindo, {st.session_state.usuario_nome}")
    df_escala = carregar_dados(URL_ESCALA)
    st.subheader("Escala Completa da Operação")
    st.dataframe(df_escala, use_container_width=True, hide_index=True)

# --- 7. LÓGICA DE NAVEGAÇÃO PRINCIPAL ---
if not st.session_state.autenticado:
    tela_login()
else:
    # Sidebar de Navegação
    with st.sidebar:
        st.title("WFM Menu")
        st.write(f"Usuário: **{st.session_state.usuario_nome}**")
        if st.button("🚪 Sair / Logoff"):
            st.session_state.autenticado = False
            st.rerun()
    
    # Direciona conforme o perfil
    if st.session_state.perfil == "Admin":
        tela_admin()
    else:
        tela_agente()

    # Controle de Refresh (Sempre no final)
    time.sleep(1)
    st.rerun()
