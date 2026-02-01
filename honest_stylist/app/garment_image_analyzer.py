# Garment image analyzer
# Extracts color and suggests silhouette from uploaded cloth image

import cv2
import numpy as np
from sklearn.cluster import KMeans
from typing import Dict, Tuple

class GarmentImageAnalyzer:
    """Analyze uploaded garment image to extract attributes"""
    
    def analyze_garment_image(self, image_path: str) -> Dict:
        """
        Extract garment attributes from image.
        
        Returns:
        {
            "color_hex": "#A9788D",
            "color_family": "cool",  # warm, cool, neutral
            "brightness": "medium",   # low, medium, high
            "suggestions": {
                "silhouette": ["fitted", "oversized", "straight"],
                "shoulder_emphasis": ["low", "medium", "high"],
                "visual_weight": ["light", "medium", "heavy"]
            },
            "confidence": 0.75
        }
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Extract dominant color
            color_info = self._extract_dominant_color(image)
            
            # Estimate brightness
            brightness = self._estimate_brightness(color_info["lab_l"])
            
            # Determine color family
            color_family = self._determine_color_family(
                color_info["lab_a"],
                color_info["lab_b"]
            )
            
            # Map to color seasons
            color_seasons = self.map_color_to_season(color_family, brightness)
            
            return {
                "color_hex": color_info["hex"],
                "color_family": color_family,
                "brightness": brightness,
                "color_season": color_seasons,
                "suggestions": {
                    "silhouette": ["fitted", "oversized", "straight"],
                    "shoulder_emphasis": ["low", "medium", "high"],
                    "visual_weight": ["light", "medium", "heavy"]
                },
                "confidence": 0.75,
                "lab_l": color_info["lab_l"],
                "lab_a": color_info["lab_a"],
                "lab_b": color_info["lab_b"]
            }
        except Exception as e:
            print(f"Warning: Garment image analysis failed: {e}")
            # Fallback
            return {
                "color_hex": "#808080",
                "color_family": "neutral",
                "brightness": "medium",
                "color_season": ["Light Spring", "Cool Winter", "Soft Autumn", "Deep Winter"],
                "suggestions": {
                    "silhouette": ["fitted", "oversized", "straight"],
                    "shoulder_emphasis": ["low", "medium", "high"],
                    "visual_weight": ["light", "medium", "heavy"]
                },
                "confidence": 0.0,
                "lab_l": 128,
                "lab_a": 0,
                "lab_b": 0
            }
    
    def _extract_dominant_color(self, image) -> Dict:
        """Extract dominant color using k-means clustering"""
        try:
            # Reshape pixels
            pixels = image.reshape(-1, 3)
            
            # Remove black/white pixels (likely background or folds)
            # Keep only pixels that are reasonably colored
            mask = np.all(
                (pixels > 30) & (pixels < 225),
                axis=1
            )
            filtered_pixels = pixels[mask]
            
            if len(filtered_pixels) < 10:
                # Not enough pixels, use all
                filtered_pixels = pixels
            
            # K-means clustering
            kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
            kmeans.fit(filtered_pixels)
            
            # Get dominant color (most frequent cluster)
            labels, counts = np.unique(kmeans.labels_, return_counts=True)
            dominant_idx = labels[np.argmax(counts)]
            dominant_color_bgr = kmeans.cluster_centers_[dominant_idx]
            
            # Convert BGR to RGB
            dominant_color_rgb = dominant_color_bgr[::-1]
            
            # Convert to LAB for analysis
            dominant_color_bgr_uint8 = np.uint8([[dominant_color_bgr]])
            dominant_color_lab = cv2.cvtColor(
                dominant_color_bgr_uint8,
                cv2.COLOR_BGR2LAB
            )[0][0]
            
            # Convert RGB to HEX
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(dominant_color_rgb[0]),
                int(dominant_color_rgb[1]),
                int(dominant_color_rgb[2])
            ).upper()
            
            return {
                "hex": hex_color,
                "lab_l": int(dominant_color_lab[0]),
                "lab_a": int(dominant_color_lab[1]),
                "lab_b": int(dominant_color_lab[2]),
                "rgb": tuple(int(x) for x in dominant_color_rgb)
            }
        except Exception as e:
            print(f"Error extracting color: {e}")
            return {
                "hex": "#808080",
                "lab_l": 128,
                "lab_a": 0,
                "lab_b": 0,
                "rgb": (128, 128, 128)
            }
    
    def _determine_color_family(self, lab_a: int, lab_b: int) -> str:
        """
        Determine if color is warm, cool, or neutral.
        
        In LAB color space:
        - a > 0 = red/warm
        - a < 0 = green/cool
        - b > 0 = yellow/warm
        - b < 0 = blue/cool
        """
        undertone_score = lab_a + lab_b
        
        if undertone_score > 10:
            return "warm"
        elif undertone_score < -10:
            return "cool"
        else:
            return "neutral"
    
    def _estimate_brightness(self, lab_l: int) -> str:
        """
        Estimate brightness from LAB L value.
        L ranges from 0 (black) to 100 (white).
        """
        if lab_l > 70:
            return "high"
        elif lab_l > 40:
            return "medium"
        else:
            return "low"
    
    def map_color_to_season(self, color_family: str, brightness: str) -> list:
        """
        Map color family + brightness to possible seasons.
        Returns list of seasons this color could work with.
        """
        mapping = {
            ("warm", "high"): ["Light Spring", "Soft Autumn"],
            ("warm", "medium"): ["Soft Autumn", "Deep Winter"],
            ("warm", "low"): ["Deep Winter"],
            ("cool", "high"): ["Light Spring", "Cool Winter"],
            ("cool", "medium"): ["Cool Winter"],
            ("cool", "low"): ["Deep Winter", "Cool Winter"],
            ("neutral", "high"): ["Light Spring"],
            ("neutral", "medium"): ["Cool Winter", "Light Spring"],
            ("neutral", "low"): ["Deep Winter"],
        }
        
        key = (color_family, brightness)
        return mapping.get(key, ["Light Spring", "Cool Winter", "Soft Autumn", "Deep Winter"])
