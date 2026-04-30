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

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import pytz

# --- FUNÇÃO DE APOIO PARA O GRUPO ---
def determinar_status_estilizado(nome_colega):
    # Simulação de status (No futuro, isso lerá a aba 'Logs' da planilha central)
    # Por enquanto, exibe a escala para orientação do time
    return "🕒 Agendado"

# --- TELA DO AGENTE ATUALIZADA ---
def tela_agente():
    agora_br = get_brasilia_time()
    st.markdown(f"### 🚀 Expert: {st.session_state.usuario_nome} | 🕒 {agora_br.strftime('%H:%M:%S')}")
    
    df_escala = carregar_dados(URL_ESCALA)
    p1, p2 = "00:00", "00:00"
    
    if not df_escala.empty:
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_row.empty:
            p1, p2 = user_row.iloc[0]['pausa_1'], user_row.iloc[0]['pausa_2']

    # --- MÉTRICAS DE ADERÊNCIA ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Minha Pausa 1", p1, delta=verificar_aderencia(p1), delta_color="inverse")
    with m2:
        st.metric("Minha Pausa 2", p2, delta=verificar_aderencia(p2), delta_color="inverse")
    with m3:
        st.metric("Cronômetro Atual", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    # --- LAYOUT PRINCIPAL ---
    col_status, col_time = st.columns([1.5, 1])

    with col_status:
        st.subheader("🕹️ Meu Controle")
        cor_alerta = "#ff4b4b" if "ATRASADO" in verificar_aderencia(p1) else "#00d1b2"
        
        st.markdown(f"""
            <div style='text-align:center; background-color:#1e1e1e; padding:30px; border-radius:15px; border:3px solid {cor_alerta};'>
                <p style='margin:0; font-size:20px; color:#bbb;'>STATUS ATUAL</p>
                <h2 style='margin:0; color:white;'>{st.session_state.status.upper()}</h2>
                <h1 style='color:{cor_alerta}; font-family:monospace; font-size:85px; margin:10px 0;'>{formatar_tempo(st.session_state.inicio_status)}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botões de Status (Mesma lógica anterior)
        if st.session_state.status == "Offline":
            if st.button("🏁 INICIAR TURNO", type="primary", use_container_width=True):
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                registrar_log("Início de Turno")
                st.rerun()
        elif st.session_state.status == "Disponível":
            c_b1, c_b2, c_b3 = st.columns(3)
            if c_b1.button("☕ Pausa 1", use_container_width=True):
                st.session_state.update({'status': "Em Pausa 1", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Pausa 1"); st.rerun()
            if c_b2.button("🚻 Banheiro", use_container_width=True):
                st.session_state.update({'status': "Banheiro", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Banheiro"); st.rerun()
            if c_b3.button("🏥 Médico/FB", use_container_width=True):
                st.session_state.update({'status': "Médico/Feedback", 'inicio_status': get_brasilia_time()})
                registrar_log("Início Médico/FB"); st.rerun()
        else:
            if st.button("🟢 RETORNEI (VOLTAR DISPONÍVEL)", type="primary", use_container_width=True):
                registrar_log(f"Retorno de {st.session_state.status}")
                st.session_state.update({'status': "Disponível", 'inicio_status': get_brasilia_time()})
                st.rerun()

    with col_time:
        st.subheader("👥 Autonomia de Time")
        st.caption("Veja quem divide a janela de pausa com você:")
        
        if not df_escala.empty:
            # Filtra colegas que têm a mesma Pausa 1 (Lanche)
            colegas = df_escala[df_escala['pausa_1'] == p1].copy()
            
            for _, row in colegas.iterrows():
                is_me = " (Eu)" if row['nome'].lower() == st.session_state.usuario_nome.lower() else ""
                # Estilização baseada em quem está com você
                bg_color = "#2e3136" if is_me == "" else "#0e6355"
                
                st.markdown(f"""
                    <div style='background-color:{bg_color}; padding:12px; border-radius:8px; margin-bottom:8px; border-left:5px solid #00d1b2;'>
                        <div style='display:flex; justify-content:between; align-items:center;'>
                            <b style='font-size:16px;'>{row['nome']}{is_me}</b>
                        </div>
                        <div style='display:flex; justify-content:space-between; font-size:13px; color:#aaa;'>
                            <span>Previsto: {row['pausa_1']}</span>
                            <span style='color:#00d1b2;'>Status: {determinar_status_estilizado(row['nome'])}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Escala não carregada.")

    # --- HISTÓRICO ---
    st.divider()
    with st.expander("📝 Meu Histórico de Registros (Hoje)", expanded=False):
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
