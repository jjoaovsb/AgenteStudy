import requests
from bs4 import BeautifulSoup
import pypdf
import io
import urllib3
from urllib.parse import urljoin

# Desabilita avisos de segurança (SSL) para sites universitários antigos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_text_from_url(url: str) -> str:
    """
    Scraper Universal com Detector de Login.
    """
    try:
        # Headers de Navegador (Chrome)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        
        # Timeout curto para falhar rápido se o site estiver morto
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        # Se der erro 403/401 (Proibido), avisamos o usuário
        if response.status_code in [401, 403]:
             raise ValueError("🔒 Acesso Negado. Este site exige login. Por favor, salve a página como PDF (Ctrl+P) e use a aba 'Via Arquivo'.")
        
        response.raise_for_status()
        
        # Rota PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            return _extract_from_bytes_pdf(response.content)
            
        # Rota HTML
        if response.encoding is None or response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding
            
        return _extract_from_html(response.text, url)
            
    except requests.exceptions.SSLError:
        # Tenta de novo sem verificar SSL (comum em federais)
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            return _extract_from_html(response.text, url)
        except:
            raise ValueError("🔒 Erro de Segurança no site. Salve como PDF e use a aba 'Via Arquivo'.")
            
    except Exception as e:
        # Repassa o erro limpo para o frontend
        if "403" in str(e) or "401" in str(e):
            raise ValueError("🔒 Site protegido por senha. Salve como PDF e use a aba 'Via Arquivo'.")
        raise e

def _extract_from_html(html_content, base_url) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # --- DETECTOR DE TELA DE LOGIN ---
    # Se o site for só um formulário de senha, avisamos o usuário
    text_lower = soup.get_text().lower()
    login_keywords = ['digite sua senha', 'esqueci minha senha', 'acesso ao sistema', 'login', 'usuário e senha', 'sigaa - sistema integrado']
    
    # Se tiver pouquíssimo texto e palavras de login, é bloqueado
    if len(text_lower) < 1000 and any(k in text_lower for k in login_keywords):
         raise ValueError("🔒 Este link leva para uma tela de Login. \n\n💡 SOLUÇÃO: Entre no site, aperte Ctrl+P > 'Salvar como PDF' e suba na aba 'Via Arquivo'.")

    # --- FAXINA ---
    junk_tags = ["script", "style", "nav", "footer", "iframe", "noscript", "svg", "button", "input", "select", "meta", "link", "aside"]
    for tag in soup(junk_tags):
        tag.decompose()

    for div in soup.find_all("div", class_=lambda x: x and any(y in x.lower() for y in ['cookie', 'popup', 'advert', 'banner', 'sidebar'])):
        div.decompose()

    # Captura LINKS
    for a in soup.find_all('a', href=True):
        link = a['href']
        text = a.get_text(strip=True)
        if link and text and len(text) > 3:
            full_link = urljoin(base_url, link)
            a.string = f"{text} [LINK: {full_link}]"

    # Extração
    content = soup.find('main') or soup.find('article') or soup.find('div', id=lambda x: x and 'content' in x.lower()) or soup.body
    if not content: content = soup

    raw_text = content.get_text(separator='\n')
    
    clean_lines = []
    for line in raw_text.splitlines():
        line = line.strip()
        if line: clean_lines.append(line)
            
    final_text = '\n'.join(clean_lines)
    
    if len(final_text) < 200:
         raise ValueError("O site é protegido. Salve a página como PDF (Ctrl+P) e use a opção 'Via Arquivo'.")

    return final_text[:50000]

def _extract_from_bytes_pdf(pdf_bytes) -> str:
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)[:60000]
    except Exception as e:
        return f"Erro PDF Web: {e}"

def extract_text_from_pdf(uploaded_file) -> str:
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)[:60000]
    except Exception as e:
        return f"Erro PDF Upload: {e}"