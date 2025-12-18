import requests
from bs4 import BeautifulSoup

def extract_text_from_url(url: str) -> str:
    """
    Acessa uma URL universitária e extrai todo o texto visível.
    Tenta limpar menus e rodapés para focar no conteúdo acadêmico.
    """
    try:
        # Headers para fingir que somos um navegador (evita bloqueio da USP/Federais)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parseia o HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts e estilos (limpeza)
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        # Pega o texto limpo
        text = soup.get_text(separator='\n')
        
        # Remove linhas vazias em excesso
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text[:20000] # Limita a 20k caracteres para não estourar o prompt inicial
        
    except Exception as e:
        return f"Erro ao ler site: {str(e)}"