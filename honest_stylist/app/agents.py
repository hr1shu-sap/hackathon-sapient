import json

class PhotoAnalysisAgent:
    def analyze(self, photo_path):
        # Placeholder: integrate with your VisionAnalyzer
        from vision_analyzer import VisionAnalyzer
        vision = VisionAnalyzer()
        return vision.analyze_photo(photo_path)

class GarmentSelectionAgent:
    def __init__(self, catalog_path):
        with open(catalog_path, 'r', encoding='utf-8') as f:
            self.garments = json.load(f)

    def recommend(self, user_profile):
        # Example: filter by season
        season = user_profile.get('season')
        return [g for g in self.garments if season in g.get('color_season', [])]

    def get_options(self):
        return [(g['sku'], g['name']) for g in self.garments]

    def get_garment(self, sku):
        for g in self.garments:
            if g['sku'] == sku:
                return g
        return None

class VerdictAgent:
    def score(self, user_profile, garment):
        from rule_engine import StylingAnalyzer
        analyzer = StylingAnalyzer()
        return analyzer.analyze(user_profile, garment)

class PivotAgent:
    def suggest(self, verdict, user_profile, garment, reasons, score):
        # Placeholder: integrate with GeminiExplainer if API key is set
        import os
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            from gemini_explainer import GeminiExplainer
            explainer = GeminiExplainer(api_key)
            return explainer.explain_verdict(
                verdict=verdict,
                user_profile=user_profile,
                garment=garment,
                rule_reasons=reasons,
                score=score
            )
        return None