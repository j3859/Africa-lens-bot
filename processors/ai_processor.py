import google.generativeai as genai
from config.settings import GEMINI_API_KEY
from utils.logger import log_info, log_error, log_success

genai.configure(api_key=GEMINI_API_KEY)

class AIProcessor:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")
    
    def generate_post(self, headline, summary, country, niche, output_language):
        source_text = headline
        if summary:
            source_text = f"{headline}. {summary}"
        
        if output_language == "french":
            prompt = self._get_french_prompt(source_text, country, niche)
        else:
            prompt = self._get_english_prompt(source_text, country, niche)
        
        try:
            response = self.model.generate_content(prompt)
            post_text = response.text.strip()
            
            # Clean up any markdown or quotes
            post_text = post_text.replace("`", "").strip()
            if post_text.startswith('"') and post_text.endswith('"'):
                post_text = post_text[1:-1]
            
            return post_text
        
        except Exception as e:
            log_error(f"Gemini API error: {e}")
            return None
    
    def _get_french_prompt(self, source_text, country, niche):
        return f'''Tu es un gestionnaire de page Facebook africaine avec 120 000 abonnés.
Crée un post Facebook engageant en FRANÇAIS basé sur cette actualité.

Actualité: {source_text}
Pays concerné: {country}
Catégorie: {niche}

Règles:
- Écris en français courant et accessible
- Commence par une accroche forte (première ligne très importante)
- 2-3 paragraphes courts maximum
- Ajoute 2-3 emojis pertinents (pas trop)
- Termine par une question pour encourager les commentaires
- Ajoute 2-3 hashtags pertinents à la fin
- Ne copie pas le texte source, reformule complètement
- Ton: informatif mais conversationnel
- Ne mets pas de guillemets autour du post

Génère uniquement le post, rien d'autre.'''

    def _get_english_prompt(self, source_text, country, niche):
        return f'''You are an African Facebook page manager with 120,000 followers.
Create an engaging Facebook post in ENGLISH based on this news.

News: {source_text}
Country: {country}
Category: {niche}

Rules:
- Write in clear, accessible English
- Start with a strong hook (first line is crucial)
- 2-3 short paragraphs maximum
- Add 2-3 relevant emojis (not too many)
- End with a question to encourage comments
- Add 2-3 relevant hashtags at the end
- Do not copy the source text, completely rewrite it
- Tone: informative but conversational
- Do not put quotes around the post

Generate only the post, nothing else.'''

ai_processor = AIProcessor()