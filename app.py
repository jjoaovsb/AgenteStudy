import streamlit as st
import os
import time
from dotenv import load_dotenv
from src.agent import StudyAgent
from src.scraper import extract_text_from_url, extract_text_from_pdf

# --- CONFIGURAÇÃO ---
st.set_page_config(
    page_title="AgentStudy", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

def setup_interface():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        :root { --primary: #4F46E5; --bg-gray: #F9FAFB; --border-color: #E5E7EB; }
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #111827; background-color: #FFFFFF; }
        
        header {visibility: visible !important; background: transparent !important;}
        #MainMenu, footer {visibility: hidden;}
        
        [data-testid="stSidebar"] { background-color: var(--bg-gray); border-right: 1px solid var(--border-color); }
        
        /* Botões Sidebar */
        div[data-testid="stSidebar"] .stButton button { border: none; background: transparent; text-align: left; color: #4B5563; }
        div[data-testid="stSidebar"] .stButton button:hover { background: #EEF2FF; color: var(--primary); }
        
        /* Nova Matéria */
        .new-chat-btn { background-color: #EEF2FF; color: #4F46E5; border: 1px solid #C7D2FE; font-weight: 700; border-radius: 8px; }

        /* Títulos */
        .scanner-title { font-size: 3rem; font-weight: 800; color: #111827; text-align: center; letter-spacing: -0.03em; margin-bottom: 10px; }
        .scanner-subtitle { text-align: center; color: #6B7280; font-size: 1.1rem; margin-bottom: 40px; }
        
        /* Inputs & Chat */
        .stTextInput input { border-radius: 8px; text-align: center; }
        .stChatMessage { background-color: white; border: 1px solid #F3F4F6; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
        
        /* Container de Estudo (Box com Sombra) */
        .study-box {
            background-color: #FDFDFD;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 20px;
            height: 70vh; /* Altura fixa com scroll */
            overflow-y: auto;
        }
    </style>
    """, unsafe_allow_html=True)

def extract_name_smart(roadmap_text):
    for line in roadmap_text.split('\n'):
        if line.strip().startswith('#'):
            return line.replace('#', '').strip()[:30]
    return "Nova Disciplina"

def main():
    setup_interface()
    load_dotenv()
    
    # --- INÍCIO DA ALTERAÇÃO ---
    try:
        # 1. Tenta pegar dos Segredos do Streamlit (Nuvem)
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        # 2. Se falhar (rodando local), pega do arquivo .env
        api_key = os.getenv("GOOGLE_API_KEY")
    # --- FIM DA ALTERAÇÃO ---

    if not api_key:
        st.error("⚠️ API Key ausente.")
        st.stop()

    if "sessions" not in st.session_state: st.session_state.sessions = {}

    if "sessions" not in st.session_state: st.session_state.sessions = {}
    if "current_session" not in st.session_state: st.session_state.current_session = None

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### ⚡ AgentStudy")
        if st.button("➕ Nova Matéria", use_container_width=True):
            st.session_state.current_session = None
            st.rerun()
        st.markdown("---")
        
        if not st.session_state.sessions:
            st.info("Nenhuma disciplina.")
        else:
            sorted_sessions = sorted(st.session_state.sessions.items(), key=lambda x: x[1].get('pinned', False), reverse=True)
            for s_id, data in sorted_sessions:
                c1, c2 = st.columns([0.85, 0.15])
                with c1:
                    icon = "📌" if data.get('pinned') else "📚"
                    b_type = "primary" if st.session_state.current_session == s_id else "secondary"
                    if st.button(f"{icon} {s_id}", key=f"nav_{s_id}", use_container_width=True, type=b_type):
                        st.session_state.current_session = s_id
                        st.rerun()
                with c2:
                    with st.popover("⋮"):
                        new_n = st.text_input("Renomear", value=s_id, key=f"ren_{s_id}")
                        if new_n != s_id:
                            st.session_state.sessions[new_n] = st.session_state.sessions.pop(s_id)
                            st.session_state.sessions[new_n]['name'] = new_n
                            if st.session_state.current_session == s_id: st.session_state.current_session = new_n
                            st.rerun()
                        if st.button("Fixar", key=f"pin_{s_id}"):
                            data['pinned'] = not data.get('pinned', False); st.rerun()
                        if st.button("Excluir", key=f"del_{s_id}"):
                            del st.session_state.sessions[s_id]
                            if st.session_state.current_session == s_id: st.session_state.current_session = None
                            st.rerun()

    # --- TELA 1: LANDING ---
    if st.session_state.current_session is None:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col_L, col_Main, col_R = st.columns([1, 3, 1])
        with col_Main:
            st.markdown('<div class="scanner-title">AgentStudy</div>', unsafe_allow_html=True)
            st.markdown('<div class="scanner-subtitle">Cole a URL da disciplina e deixe a IA buscar tudo para você</div>', unsafe_allow_html=True)
            
            tab_link, tab_pdf = st.tabs(["🔗 Link", "📂 PDF"])
            with tab_link:
                c_in, c_bt = st.columns([3.5, 1.5])
                with c_in: url = st.text_input("URL", placeholder="https://...", label_visibility="collapsed")
                with c_bt:
                    if st.button("🔍 Buscar"):
                        if url:
                            with st.spinner("Analisando..."):
                                try:
                                    raw = extract_text_from_url(url)
                                    agent = StudyAgent(api_key)
                                    roadmap = agent.create_study_roadmap(raw)
                                    name = extract_name_smart(roadmap)
                                    st.session_state.sessions[name] = {"name": name, "roadmap": roadmap, "agent": agent, "messages": [], "pinned": False}
                                    st.session_state.current_session = name
                                    st.rerun()
                                except Exception as e: st.error(f"Erro: {e}")
            with tab_pdf:
                up = st.file_uploader("PDF", type="pdf", label_visibility="collapsed")
                if st.button("📂 Processar"):
                    if up:
                        with st.spinner("Lendo..."):
                            try:
                                raw = extract_text_from_pdf(up)
                                agent = StudyAgent(api_key)
                                roadmap = agent.create_study_roadmap(raw)
                                name = extract_name_smart(roadmap)
                                st.session_state.sessions[name] = {"name": name, "roadmap": roadmap, "agent": agent, "messages": [], "pinned": False}
                                st.session_state.current_session = name
                                st.rerun()
                            except Exception as e: st.error(f"Erro: {e}")
            st.markdown("<br><p style='text-align:center; color:#9CA3AF;'>Suporta: Júpiter Web, SIGAA, Moodle e outros.</p>", unsafe_allow_html=True)

    # --- TELA 2: WORKSPACE (SPLIT VIEW) ---
    else:
        s_id = st.session_state.current_session
        data = st.session_state.sessions[s_id]
        
        # Header da Matéria
        c_title, c_dl = st.columns([5, 1.5])
        with c_title: st.markdown(f"## 🎓 {data['name']}")
        with c_dl:
            pdf = data['agent'].generate_pdf(data['roadmap'])
            st.download_button("📥 Baixar Resumo (PDF)", pdf, "Resumo.pdf", "application/pdf")

            # --- FEATURE: MAPA MENTAL ---
        with st.expander("🧠 Mapa Mental (Visualização)"):
            if data.get('mindmap'):
                st.graphviz_chart(data['mindmap'])
            else:
                if st.button("Gerar Mapa Mental Agora"):
                    with st.spinner("Desenhando estruturas..."):
                        try:
                            dot_code = data['agent'].generate_mindmap_code(data['roadmap'])
                            data['mindmap'] = dot_code
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao gerar mapa: {e}")

        # --- O NOVO LAYOUT DE ESTUDO (SPLIT) ---
        # Coluna Esquerda (1.3): Conteúdo de Estudo
        # Coluna Direita (1.0): Chat
        col_content, col_chat = st.columns([1.3, 1])
        
        with col_content:
            st.markdown("### 📖 Material de Estudo")
            # Área de conteúdo rolável
            with st.container(height=600):
                st.markdown(data['roadmap'])
        
        with col_chat:
            st.markdown("### 💬 Tutor Virtual")
            
            # Histórico do Chat
            # Container com altura fixa para rolar as mensagens
            chat_container = st.container(height=480)
            with chat_container:
                for msg in data['messages']:
                    with st.chat_message(msg["role"]):
                        if isinstance(msg["content"], bytes): st.image(msg["content"])
                        else: st.markdown(msg["content"])

            # Input e Clips (Abaixo do chat)
            c_clip, c_in = st.columns([0.15, 0.85])
            with c_clip:
                with st.popover("📎"):
                    extra = st.file_uploader("PDF", type="pdf", key="chat_up")
                    if extra and st.button("Enviar"):
                        txt = extract_text_from_pdf(extra)
                        data['roadmap'] += f"\n\n[ANEXO]: {txt}"
                        st.success("Adicionado!"); st.rerun()
            
            with c_in:
                prompt = st.chat_input("Pergunte sobre o conteúdo...", key="main_chat_input")

            # Lógica de Resposta
            if prompt:
                data['messages'].append({"role": "user", "content": prompt})
                st.rerun()

            if data['messages'] and data['messages'][-1]["role"] == "user":
                # Mostra o spinner DENTRO da coluna do chat
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("Processando..."):
                            agent = data['agent']
                            context = data['roadmap']
                            last = data['messages'][-1]["content"]
                            p_low = last.lower()
                            
                            # Roteamento
                            if any(x in p_low for x in ["imagem", "desenho"]):
                                img = agent.generate_didactic_image(last)
                                if img:
                                    st.image(img); data['messages'].append({"role": "assistant", "content": img})
                                else:
                                    resp = agent.generate_lesson(last, context)
                                    st.markdown(resp); data['messages'].append({"role": "assistant", "content": resp})
                            elif any(x in p_low for x in ["exercício", "questão"]):
                                resp = agent.generate_exercises(last, context)
                                lbl, fn = "📥 Baixar Exercícios", "Exercicios.pdf"
                                st.markdown(resp); data['messages'].append({"role": "assistant", "content": resp})
                                pdf = agent.generate_pdf(resp)
                                # Botão de download aparece no chat
                                st.download_button(lbl, pdf, fn, "application/pdf", key=f"d_{len(data['messages'])}")
                            elif any(x in p_low for x in ["aula", "expli"]):
                                resp = agent.generate_lesson(last, context)
                                lbl, fn = "📥 Baixar Aula", "Aula.pdf"
                                st.markdown(resp); data['messages'].append({"role": "assistant", "content": resp})
                                pdf = agent.generate_pdf(resp)
                                st.download_button(lbl, pdf, fn, "application/pdf", key=f"d_{len(data['messages'])}")
                            else:
                                resp = agent.answer_doubt(last, context)
                                lbl, fn = "📥 Baixar Resposta", "Resposta.pdf"
                                st.markdown(resp); data['messages'].append({"role": "assistant", "content": resp})
                                pdf = agent.generate_pdf(resp)
                                st.download_button(lbl, pdf, fn, "application/pdf", key=f"d_{len(data['messages'])}")

if __name__ == "__main__":
    main()