import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAÇÃO DE INTERFACE ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# URLs das Planilhas
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 2. INICIALIZAÇÃO DO ESTADO (SESSION STATE) ---
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

# --- 3. FUNÇÕES DE SUPORTE ---
def carregar_dados(url):
    try:
        # Cache buster para dados sempre frescos
        df = pd.read_csv(url + f"&cache={time.time()}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except:
        return pd.DataFrame()

def registrar_log(tipo_evento):
    """Armazena o evento no histórico da sessão do usuário"""
    hora_atual = datetime.now().strftime("%H:%M:%S")
    st.session_state.historico_pausas.append({
        "Evento": tipo_evento,
        "Horário": hora_atual
    })

def formatar_tempo(inicio):
    diff = datetime.now() - inicio
    m, s = divmod(int(diff.total_seconds()), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

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
                        st.session_state.update({
                            'autenticado': True,
                            'perfil': user_match.iloc[0]['perfil'],
                            'usuario_nome': user_match.iloc[0]['nome'],
                            'hora_login': datetime.now().strftime("%H:%M:%S")
                        })
                        registrar_log("Login no Sistema")
                        st.rerun()
                st.error("E-mail ou senha incorretos.")

# --- 5. TELA DO AGENTE (INDIVIDUAL + GRUPO) ---
def tela_agente():
    st.markdown(f"### Expert: {st.session_state.usuario_nome} | 🟢 Login: {st.session_state.hora_login}")
    
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2 = "00:00", "00:00"
    
    if not df_escala.empty:
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_row.empty:
            p1, p2 = user_row.iloc[0]['pausa_1'], user_row.iloc[0]['pausa_2']

    # Métricas de Cabeçalho
    c1, c2, c3 = st.columns(3)
    c1.metric("Pausa 1 (Lanche)", p1)
    c2.metric("Pausa 2 (Descanso)", p2)
    c3.metric("Tempo em Atividade", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    col_principal, col_grupo = st.columns([2, 1])

    with col_principal:
        # Painel do Cronômetro
        st.markdown(f"<div style='text-align:center; background-color:#1e1e1e; padding:25px; border-radius:15px; border:1px solid #333;'>", unsafe_allow_html=True)
        st.write(f"STATUS ATUAL: **{st.session_state.status.upper()}**")
        st.markdown(f"<h1 style='color:#00d1b2; font-family:monospace; font-size:90px; margin:0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Botões de Status
        st.markdown("<br>", unsafe_allow_html=True)
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
            if st.button("🟢 FINALIZAR PAUSA E VOLTAR DISPONÍVEL", type="primary", use_container_width=True):
                registrar_log(f"Fim de {st.session_state.status}")
                st.session_state.update({'status': "Disponível", 'inicio_status': datetime.now()}); st.rerun()

    with col_grupo:
        st.markdown("### 👥 Status do Grupo")
        if not df_escala.empty:
            colegas = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'] != st.session_state.usuario_nome)]
            if not colegas.empty:
                for _, row in colegas.iterrows():
                    st.markdown(f"<div style='background:#262730; padding:10px; border-radius:5px; margin-bottom:5px; border-left:3px solid #00d1b2;'><b>{row['nome']}</b><br><small>Pausa Prevista: {row['pausa_1']}</small></div>", unsafe_allow_html=True)
            else:
                st.caption("Sem colegas mapeados para este horário.")

    st.divider()
    
    # Seção de Histórico
    st.subheader("📝 Meu Histórico de Registros")
    if st.session_state.historico_pausas:
        st.table(pd.DataFrame(st.session_state.historico_pausas))
    else:
        st.info("Nenhum registro até o momento.")

# --- 6. TELA ADMIN (MANTIDA E SIMPLES) ---
def tela_admin():
    st.title("🛡️ Painel de Supervisão WFM")
    
    # Métricas Globais Fictícias (para você trabalhar depois)
    m1, m2, m3 = st.columns(3)
    m1.metric("Experts Online", "24")
    m2.metric("Em Pausa agora", "5")
    m3.metric("Aderência Global", "92%")
    
    st.divider()
    
    # Visualização da Escala Geral
    st.subheader("📋 Gestão de Escalas")
    df_escala = carregar_dados(URL_ESCALA)
    if not df_escala.empty:
        st.dataframe(df_escala, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("📊 Logs de Atividade")
    st.info("Aqui serão exibidos os logs de login e pausas de todos os usuários em tempo real.")

# --- 7. NAVEGAÇÃO E REFRESH ---
if not st.session_state.autenticado:
    tela_login()
else:
    # Barra Lateral
    with st.sidebar:
        st.title("Configurações")
        st.write(f"Usuário: **{st.session_state.usuario_nome}**")
        st.write(f"Perfil: {st.session_state.perfil}")
        if st.button("🚪 Sair do Turno", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
    
    # Direcionamento por perfil
    if st.session_state.perfil == "Admin":
        tela_admin()
    else:
        tela_agente()

    # Loop de atualização do cronômetro (1 segundo)
    time.sleep(1)
    st.rerun()
