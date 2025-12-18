from google import genai
from google.genai import types
from fpdf import FPDF
import io
import re
 



class StudyAgent:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        if not api_key:
            raise ValueError("API Key é obrigatória.")
        
        clean_key = api_key.strip().replace('"', '').replace("'", "")
        self.client = genai.Client(api_key=clean_key)
        self.model_name = model

    def _call(self, contents, temperature=0.2) -> str:
        """Motor genérico que aceita Texto ou Multimodal (PDF/Imagem)"""
        try:
            res = self.client.models.generate_content(
                model=self.model_name,
                contents=contents, # Agora aceita lista de partes (texto + arquivo)
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=8192
                )
            )
            text = res.text
            
            # Filtro de limpeza (Remove saudações iniciais se houver)
            if "# " in text:
                return text[text.find("# "):] 
            return text
            
        except Exception as e:
            return f"Erro: {e}"

    # --- MOTOR DE IMAGEM ---
    def generate_didactic_image(self, prompt_user: str) -> bytes:
        try:
            image_prompt = f"Detailed academic diagram or infographic about: {prompt_user}. Textbook style, white background, high resolution, scientific accuracy."
            response = self.client.models.generate_image(
                model='imagen-3.0-generate-001',
                prompt=image_prompt,
                config=types.GenerateImageConfig(number_of_images=1, aspect_ratio="16:9")
            )
            img_pil = response.generated_images[0].image
            buf = io.BytesIO()
            img_pil.save(buf, format="PNG")
            return buf.getvalue()
        except Exception:
            return None



# --- NOVO: GERADOR DE MAPA MENTAL (NOTEBOOKLM STYLE) ---
    def generate_mindmap_code(self, context_data: str) -> str:
        """Gera código Graphviz DOT estilizad para parecer o NotebookLM."""
        prompt = f"""
        ATUE COMO UM ESPECIALISTA EM VISUALIZAÇÃO DE DADOS.
        
        CONTEXTO:
        {context_data[:20000]}
        
        TAREFA:
        Crie um código GRAPHVIZ (DOT) que represente um MAPA MENTAL deste conteúdo.
        
        ESTILO VISUAL OBRIGATÓRIO (NotebookLM Style):
        1. Layout: Da esquerda para a direita (rankdir=LR).
        2. Nós: Formato 'box' mas com estilo 'rounded,filled'.
        3. Cores: Fundo dos nós #F3F4F6 (Cinza muito claro), Borda #E5E7EB.
        4. Fonte: Arial ou Helvetica.
        5. Conexões: Curvas (splines=ortho ou curved).
        
        REGRAS DE OUTPUT:
        - Retorne APENAS o código DOT dentro de um bloco ```dot ... ```.
        - O nó central deve ser o Nome da Disciplina (Cor um pouco mais escura, ex: #E0E7FF).
        - Ramifique para os Módulos principais.
        - Ramifique dos Módulos para os Tópicos chave.
        - Mantenha os textos curtos nos nós.
        """
        
        # Chamada direta para evitar os filtros de texto do _call
        try:
            res = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            )
            # Limpa o markdown do código
            code = res.text.replace('```dot', '').replace('```', '').strip()
            return code
        except Exception as e:
            return f"Error: {e}"

            
    # --- PROMPTS "DEEP ACADEMIC" ---
    
    def create_study_roadmap(self, url_text: str) -> str:
        prompt = f"""
       FUNÇÃO: Você é uma Inteligência Artificial avançada especializada em estruturação de conhecimento acadêmico.        
        DADOS DA MATÉRIA:
        {url_text}
        
        ---
        TAREFA:
        Crie um PLANO DE ENSINO SUPERIOR COMPLETO E DETALHADO.
        Não faça listas simples. Descreva a jornada acadêmica com profundidade.
        
        ESTRUTURA OBRIGATÓRIA:
        
        # [Nome da Disciplina] - Plano de Ensino
        
        ## 🎯 Ementa e Objetivos Acadêmicos
        (Descreva detalhadamente as competências técnicas e teóricas que serão desenvolvidas. Nível de ementa oficial.)
        
        ## 📚 Bibliografia Fundamental e Complementar
        (Liste os livros com comentários sobre por que cada um é importante. Ex: "Use o livro X para a teoria de Y...")
        
        ## 🗓️ Cronograma Semestral (Deep Dive)
        Divida o curso em Módulos ou Unidades. Para cada unidade, detalhe:
        - Tópicos Principais
        - Tópicos Avançados
        - Leitura Obrigatória (Capítulos específicos)
        
        ## 💡 Metodologia de Estudo Avançada
        (Como um pesquisador estuda isso? Análise de artigos? Dedução de fórmulas? Estudos de caso?)
        
        SEM EMOJIS. TEXTO DENSO E PROFISSIONAL.
        """
        return self._call(prompt)

    def generate_lesson(self, topic: str, context_data: str) -> str:
        prompt = f"""
        ATUE COMO UM PROFESSOR TITULAR SÊNIOR (PhD).
        DADOS DA MATÉRIA:.
        O aluno pediu uma aula sobre: "{topic}".
        
        CONTEXTO: {context_data}
        
        DIRETRIZ DE EXTENSÃO E PROFUNDIDADE:
        - ESQUEÇA RESUMOS. O aluno quer um MATERIAL COMPLETO, nível capítulo de livro.
        - SEJA EXTENSO. Cubra todas as nuances, exceções, histórico e teoria.
        - MATEMÁTICA: Não jogue a fórmula. Deduza. Explique cada variável. Mostre o "porquê".
        - PROGRAMAÇÃO: Explique a arquitetura, complexidade (Big O), e dê código robusto.
        - BIOLÓGICAS: Descreva processos moleculares/fisiológicos passo a passo.
        
        ESTRUTURA DA AULA MAGNA:
        
        ## {topic}
        
        ### 1. Introdução e Contextualização Histórica
        (Origem do conceito, quem descobriu, qual problema resolve)
        
        ### 2. Fundamentação Teórica Sólida
        (O "núcleo duro" da matéria. Definições formais, axiomas, princípios fundamentais. Texto longo e explicativo.)
        
        ### 3. Desenvolvimento Técnico Detalhado
        (Aqui entra o conteúdo pesado. Fórmulas, mecanismos, algoritmos. Explique como se estivesse escrevendo a "Bíblia" do assunto.)
        
        ### 4. Análise Crítica e Aplicações Avançadas
        (Limitações da teoria, casos de uso na indústria moderna, debates acadêmicos atuais.)
        
        ### 5. Estudo de Caso Resolvido (Nível Expert)
        (Um problema complexo resolvido do início ao fim com comentários em cada etapa.)
        
        SEM EMOJIS. LINGUAGEM ACADÊMICA FORMAL.
        """
        return self._call(prompt)

    def generate_exercises(self, topic: str, context_data: str) -> str:
        prompt = f"""
        ATUE COMO UMA BANCA DE PÓS-GRADUAÇÃO.        
        DADOS DA MATÉRIA:.
        
        TÓPICO: {topic}
        CONTEXTO: {context_data}
        
        Gere uma LISTA DE EXERCÍCIOS INTENSIVA.
        Não faça perguntas de "O que é?". Faça perguntas de "Analise", "Calcule", "Projete", "Critique".
        
        ESTRUTURA:
        ## Lista de Treinamento Avançado: {topic}
        
        1. **Questão Analítica (Dissertativa):** (Exige conectar múltiplos conceitos)
        2. **Problema Prático Complexo:** (Cálculo ou Código que exige várias etapas)
        3. **Estudo de Caso:** (Situação real que exige solução técnica)
        4. **O "Boss Final":** (Uma questão nível prova de final de curso ou concurso de alto nível)
        
        ---
        ### Gabarito e Resolução Comentada
        (Para cada questão, escreva quase uma mini-aula explicando a solução. Mostre o raciocínio, não apenas o resultado.)
        
        SEM EMOJIS.
        """
        return self._call(prompt)

    def answer_doubt(self, question: str, context_data: str) -> str:
        prompt = f"""
        Contexto: {context_data}
        Pergunta: "{question}"
        
        DIRETRIZ:
        - Responda como se estivesse orientando uma tese.
        - Não seja superficial. Dê a resposta completa, com contexto, exceções e referências teóricas.
        - Se for código, dê o código otimizado e explique linha a linha.
        - Não se despeda fique sempre dispoível para ajudar.
        - Não fale em nenhuma hipótese que você é um reitor ou alguma autoridade acadêmica você é uma inteligência artificial.


        - Sem emojis.
        """
        return self._call(prompt)

    # --- GERADOR DE PDF FINAL (FIX: Sem Interrogações e Sem Quebra) ---
    def generate_pdf(self, content: str) -> bytes:
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 10)
                self.set_text_color(100, 100, 100)
                self.cell(0, 10, 'AgentStudy - Material Oficial', 0, 1, 'R')
                self.set_draw_color(220, 220, 220)
                self.line(10, 20, 200, 20)
                self.ln(10)
            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

        pdf = PDF()
        pdf.set_margins(20, 20, 20)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # 1. REMOVE "PÁGINA X" PERDIDA NO MEIO DO TEXTO
        clean_content = re.sub(r'(Página \d+|Page \d+)', '', content, flags=re.IGNORECASE)
        
        # 2. LIMPEZA DE FORMATACAO MARKDOWN
        clean_content = clean_content \
            .replace('**', '') \
            .replace('__', '') \
            .replace('`', '') \
            .replace('##', '') 
            
        # 3. SANITIZAÇÃO DE CARACTERES
        replacements = {
            '–': '-', '—': '-', '“': '"', '”': '"', '’': "'", '‘': "'", '…': '...', '•': '-'
        }
        for char, repl in replacements.items():
            clean_content = clean_content.replace(char, repl)
        
        # MUDANÇA: 'ignore' remove o emoji (evita '?')
        safe_content = clean_content.encode('latin-1', 'ignore').decode('latin-1')

        w_eff = pdf.epw 
        
        # Divide em parágrafos duplos
        paragraphs = safe_content.split('\n\n')
        
        for p in paragraphs:
            p = p.strip()
            if not p: continue
            
            # Remove quebras de linha DENTRO do parágrafo
            fluent_p = p.replace('\n', ' ')
            
            # Títulos
            if p.startswith('#'):
                clean_title = p.replace('#', '').strip()
                pdf.set_font("Arial", 'B', 14)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(4)
                pdf.multi_cell(w_eff, 7, clean_title.upper())
                pdf.ln(2)
            
            # Listas
            elif p.startswith('- ') or p.startswith('* '):
                pdf.set_font("Arial", '', 11)
                pdf.set_text_color(30, 30, 30)
                items = p.split('\n') 
                for item in items:
                    clean_item = item.replace('- ', '').replace('* ', '').strip()
                    if clean_item:
                        pdf.set_x(25)
                        pdf.multi_cell(w_eff - 5, 6, f"- {clean_item}")
                pdf.ln(2)
                
            # Texto Normal
            else:
                pdf.set_font("Arial", '', 11)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(w_eff, 6, fluent_p)
                pdf.ln(3)

        return bytes(pdf.output(dest='S'))