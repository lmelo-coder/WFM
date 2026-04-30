import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURAÇÃO E DADOS ---
st.set_page_config(page_title="WFM ConvertaX", layout="wide", page_icon="🚀")

URL_ACESSOS = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Acessos"
URL_ESCALA = "https://docs.google.com/spreadsheets/d/1JD2KDxSAkezSeoF1Bi5h5w8BitIzip7IuR0g19fdouU/gviz/tq?tqx=out:csv&sheet=Escala"

if 'autenticado' not in st.session_state:
    st.session_state.update({'autenticado': False, 'perfil': None, 'usuario_nome': "", 'status': "Disponível", 'inicio_status': datetime.now()})

def carregar_dados(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return pd.DataFrame()

def formatar_tempo(inicio):
    diff = datetime.now() - inicio
    m, s = divmod(int(diff.total_seconds()), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# --- TELA DE LOGIN ---
def tela_login():
    st.markdown("<h2 style='text-align: center;'>Portal WFM ConvertaX</h2>", unsafe_allow_html=True)
    df_users = carregar_dados(URL_ACESSOS)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login"):
            email = st.text_input("E-mail Corporativo").strip().lower()
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if not df_users.empty and email in df_users['email'].values:
                    user_data = df_users[df_users['email'] == email].iloc[0]
                    if str(user_data['senha']) == str(senha):
                        st.session_state.update({'autenticado': True, 'perfil': user_data['perfil'], 'usuario_nome': user_data['nome']})
                        st.rerun()
                st.error("Erro no login.")

# --- 🟢 VISÃO DO AGENTE (CRONÔMETRO + ESCALA INDIVIDUAL) ---
# --- 🟢 VISÃO DO AGENTE (CRONÔMETRO + ESCALA + COLEGAS) ---
def tela_agente():
    st.title(f"🚀 Painel do Expert: {st.session_state.usuario_nome}")
    
    # 1. CARREGA DADOS DA PLANILHA
    df_escala = carregar_dados(URL_ESCALA)
    
    p1, p2, meu_grupo = "--:--", "--:--", None
    
    if not df_escala.empty:
        # Busca dados do usuário logado
        user_row = df_escala[df_escala['nome'].str.lower() == st.session_state.usuario_nome.lower()]
        if not user_row.empty:
            p1 = user_row.iloc[0]['pausa_1']
            p2 = user_row.iloc[0]['pausa_2']
            # Vamos supor que você tenha uma coluna 'grupo' ou use o horário da Pausa 1 como referência
            meu_grupo = user_row.iloc[0]['pausa_1'] 

    # 2. MÉTRICAS INDIVIDUAIS
    c1, c2, c3 = st.columns(3)
    c1.metric("Sua Pausa 1", p1)
    c2.metric("Sua Pausa 2", p2)
    c3.metric("Tempo em Status", formatar_tempo(st.session_state.inicio_status))

    st.divider()

    # 3. ÁREA DE FOCO (CRONÔMETRO)
    col_esq, col_dir = st.columns([1.5, 1])
    
    with col_esq:
        st.markdown(f"<p style='text-align: center; margin-bottom: -20px;'>Status: <b>{st.session_state.status}</b></p>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; color: #00d1b2; font-size: 90px; font-family: monospace;'>{formatar_tempo(st.session_state.inicio_status)}</h1>", unsafe_allow_html=True)
        
        if st.session_state.status != "Em Pausa":
            if st.button("☕ INICIAR PAUSA", type="primary", use_container_width=True):
                st.session_state.status = "Em Pausa"; st.session_state.inicio_status = datetime.now(); st.rerun()
        else:
            if st.button("🟢 RETORNAR", use_container_width=True):
                st.session_state.status = "Disponível"; st.session_state.inicio_status = datetime.now(); st.rerun()

    with col_dir:
        # 4. VISÃO DOS COLEGAS (QUEM SAI JUNTO COMIGO?)
        st.write("### 👥 Colegas de Turno/Pausa")
        if not df_escala.empty and meu_grupo:
            # Filtra colegas que têm a mesma Pausa 1 que o usuário, excluindo ele mesmo
            colegas = df_escala[(df_escala['pausa_1'] == meu_grupo) & (df_escala['nome'].str.lower() != st.session_state.usuario_nome.lower())]
            
            if not colegas.empty:
                # Criamos uma visualização simples de cartões ou tabela
                for _, row in colegas.iterrows():
                    # No futuro, o status virá da aba de Status Real
                    st.markdown(f"""
                        <div style='background-color: #262730; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 3px solid #fdfd96;'>
                            <b>{row['nome']}</b> | Pausas: {row['pausa_1']} - {row['pausa_2']}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("Nenhum colega mapeado para este horário.")
        else:
            st.info("Escala não disponível para consulta de grupo.")

    st.divider()
    # Incidente aparece para o agente também para ele ficar ciente
    st.warning("⚠️ **Nota da Supervisão:** Fique atento aos incidentes no topo da página.")

# --- 🛡️ VISÃO DO ADMIN (CONTROLE GERAL + INCIDENTES) ---
def tela_admin():
    st.title("🛡️ Painel Admin - Gestão ConvertaX")
    
    # 1. KPIs DE OPERAÇÃO
    m1, m2, m3 = st.columns(3)
    m1.metric("Experts Online", "15") # Exemplo estático
    m2.metric("Quebra de Aderência", "2", delta="Atenção", delta_color="inverse")
    m3.metric("NPS Médio", "9.2")

    st.divider()

    # 2. ESTEIRA DE OPERAÇÃO COMPLETA
    st.subheader("📋 Visão de Escala do Time")
    df_escala = carregar_dados(URL_ESCALA)
    if not df_escala.empty:
        # Aqui o Admin vê a lista de TODO MUNDO
        st.dataframe(df_escala, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # 3. MURAL DE INCIDENTES (O que você formatou antes)
    st.error("🚨 **INCIDENTE ATIVO:** Lentidão Backoffice Brands CASSINO/VERA - Identificado às 23:41")
    st.info("💡 **Ação:** Orientar time a realizar limpeza de cache e aguardar normalização.")

# --- LÓGICA DE NAVEGAÇÃO ---
if not st.session_state.autenticado:
    tela_login()
else:
    st.sidebar.subheader(f"Logado: {st.session_state.usuario_nome}")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False; st.rerun()
    
    if st.session_state.perfil == "Admin":
        tela_admin()
    else:
        tela_agente()
    
    time.sleep(1)
    st.rerun()
