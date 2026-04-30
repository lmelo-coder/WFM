import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz # Certifique-se de que está no seu requirements.txt

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

# --- 2. TRATAMENTO DE HORÁRIO BRASÍLIA ---
def get_brasilia_time():
    # Retorna o datetime atual de Brasília
    return datetime.now(pytz.timezone('America/Sao_Paulo')).replace(tzinfo=None)

# --- 3. INICIALIZAÇÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.update({
        'autenticado': False,
        'perfil': None,
        'usuario_nome': "",
        'status': "Offline",
        'inicio_status': None,
        'hora_login': None,
        'historico_pausas': []
    })

# --- 4. FUNÇÕES ---
def carregar_dados(url):
    try:
        df = pd.read_csv(f"{url}&cache={int(time.time())}")
        df.columns = df.columns.str.strip().str.lower()
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    except: return pd.DataFrame()

def formatar_tempo(inicio):
    if inicio is None: return "00:00:00"
    diff = get_brasilia_time() - inicio
    total_segundos = int(diff.total_seconds())
    horas, resto = divmod(total_segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def registrar_log(tipo_evento):
    hora_atual = get_brasilia_time().strftime("%H:%M:%S")
    st.session_state.historico_pausas.append({
        "Evento": tipo_evento,
        "Horário": hora_atual
    })

def verificar_aderencia(horario_planejado):
    """Retorna True se estiver atrasado para a pausa"""
    try:
        agora = get_brasilia_time()
        hp = datetime.strptime(horario_planejado, "%H:%M").replace(
            year=agora.year, month=agora.month, day=agora.day
        )
        # Se passou do horário e ele ainda está disponível ou offline
        if agora > hp and st.session_state.status in ["Disponível", "Offline"]:
            atraso = int((agora - hp).total_seconds() / 60)
            return f"⚠️ ATRASADO ({atraso} min)"
        return "✅ EM DIA"
    except: return ""

# URLs
URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

# --- 5. TELAS ---
def tela_login():
    st.markdown("<h1 style='text-align: center;'>🚀 ConvertaX WFM</h1>", unsafe_allow_html=True)
    df_users = carregar_dados(URL_ACESSOS)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("E-mail Corporativo").strip().lower()
            senha = st.text_input("Senha", type="password").strip()
            if st.form_submit_button("ACESSAR PORTAL", use_container_width=True):
                if not df_users.empty:
                    user_match = df_users[df_users['email'].str.lower() == email]
                    if not user_match.empty and str(user_match.iloc[0]['senha']) == senha:
                        st.session_state.update({
                            'autenticado': True,
                            'perfil': user_match.iloc[0]['perfil'],
                            'usuario_nome': user_match.iloc[0]['nome'],
                            'hora_login': get_brasilia_time().strftime("%H:%M:%S")
                        })
                        registrar_log("Acesso ao Portal")
                        st.rerun()
                st.error("Credenciais inválidas.")

def tela_agente():
    # Cabeçalho com horário de Brasília
    st.markdown(f"### Expert: {st.session_state.usuario_nome} | 🟢 Login: {st.session_state.hora_login} | 🕒 Agora: {get_brasilia_time().strftime('%H:%M:%S')}")
    
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2 = "00:00", "00:00"
    if not df_escala.empty:
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_row.empty:
            p1, p2 = user_row.iloc[0]['pausa_1'], user_row.iloc[0]['pausa_2']

    # --- INDICADORES DE ADERÊNCIA (Onde o agente vê que está atrasado) ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Pausa 1", p1, delta=verificar_aderencia(p1), delta_color="inverse")
    with m2:
        st.metric("Pausa 2", p2, delta=verificar_aderencia(p2), delta_color="inverse")
    with m3:
        st.metric("Cronômetro Ativo", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    col_main, col_side = st.columns([2, 1])
    with col_main:
        # Cronômetro visual
        cor_cronometro = "#ff4b4b" if "ATRASADO" in verificar_aderencia(p1) or "ATRASADO" in verificar_aderencia(p2) else "#00d1b2"
        
        st.markdown(f"""
            <div style='text-align:center; background-color:#1e1e1e; padding:20px; border-radius:15px; border:2px solid {cor_cronometro};'>
                <p style='margin:0; font-size:18px;'>STATUS ATUAL: <b>{st.session_state.status.upper()}</b></p>
                <h1 style='color:{cor_cronometro}; font-family:monospace; font-size:80px; margin:0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.status == "Offline":
            if st.button("🏁 FICAR DISPONÍVEL (COMEÇAR TURNO)", type="primary", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                registrar_log("Início de Turno")
                st.rerun()

        elif st.session_state.status == "Disponível":
            cols = st.columns(3)
            if cols[0].button("☕ Pausa Escala", use_container_width=True):
                st.session_state.update({'status': "Em Pausa Escala", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Pausa Escala")
                st.rerun()
            if cols[1].button("🚻 Banheiro", use_container_width=True):
                st.session_state.update({'status': "Banheiro", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Banheiro")
                st.rerun()
            if cols[2].button("🏥 Médico/FB", use_container_width=True):
                st.session_state.update({'status': "Médico/Feedback", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Médico/Feedback")
                st.rerun()
        else:
            if st.button("🟢 RETORNEI PARA DISPONÍVEL", type="primary", use_container_width=True):
                registrar_log(f"Retorno de: {st.session_state.status}")
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                st.rerun()

    with col_side:
        st.markdown("### 👥 Colegas (Mesmo Turno)")
        if not df_escala.empty:
            colegas = df_escala[(df_escala['pausa_1'] == p1) & (df_escala['nome'] != st.session_state.usuario_nome)]
            for _, row in colegas.iterrows():
                st.info(f"👤 {row['nome']}")

    st.divider()
    st.subheader("📝 Registro de Atividades")
    if st.session_state.historico_pausas:
        st.dataframe(pd.DataFrame(st.session_state.historico_pausas), use_container_width=True)

# --- 6. ADMIN / NAVEGAÇÃO ---
if not st.session_state.autenticado:
    tela_login()
else:
    if st.session_state.perfil == "Admin":
        st.title("🛡️ Painel Admin")
        st.dataframe(carregar_dados(URL_ESCALA), use_container_width=True)
    else:
        tela_agente()
    
    time.sleep(1)
    st.rerun()
