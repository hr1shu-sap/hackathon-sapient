# Vision analysis module
# Uses simple image processing for face and body analysis
# Extracts skin tone, body shape, and contrast

import cv2
import numpy as np
from typing import Tuple, Dict
from sklearn.cluster import KMeans

class VisionAnalyzer:
    """Analyze user photo for styling attributes"""
    
    def __init__(self):
        # Simplified for MVP - no expensive detectors
        pass
        
    def analyze_photo(self, image_path: str) -> Dict:
        """
        Main analysis function.
        
        Returns:
        {
            "skin_hex": "D4A5A5",
            "skin_undertone": "warm",
            "contrast_level": "high",
            "body_shape": "Inverted Triangle",
            "skin_season": "Soft Autumn",
            "confidence": 0.85
        }
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Step 1: Detect face and extract skin tone
        skin_analysis = self._extract_skin_tone(image)
        
        # Step 2: Detect body and compute shape
        body_analysis = self._analyze_body_shape(image)
        
        # Step 3: Determine contrast level
        contrast = self._calculate_contrast(image, skin_analysis)
        
        # Step 4: Map to color season
        skin_season = self._map_to_color_season(
            skin_analysis["undertone"],
            contrast
        )
        
        return {
            "skin_hex": skin_analysis["hex"],
            "skin_undertone": skin_analysis["undertone"],
            "contrast_level": contrast,
            "body_shape": body_analysis["shape"],
            "skin_season": skin_season,
            "confidence": 0.85  # TODO: compute real confidence
        }
    
    def _extract_skin_tone(self, image) -> Dict:
        """
        Use simple color sampling to extract skin tone.
        Falls back gracefully if detection fails.
        """
        try:
            # For MVP, sample from middle of image (where face usually is)
            h, w, _ = image.shape
            center_y = int(h * 0.4)
            center_x = int(w * 0.5)
            
            # Sample a square region around center
            sample_size = 50
            roi = image[
                max(0, center_y-sample_size):min(h, center_y+sample_size),
                max(0, center_x-sample_size):min(w, center_x+sample_size)
            ]
            
            if roi.size == 0:
                return {
                    "hex": "C8956F",
                    "undertone": "neutral",
                    "lab_l": 50,
                    "lab_a": 5,
                    "lab_b": 10
                }
            
            # Reshape for k-means
            pixels = roi.reshape(-1, 3)
            
            # Find 3 dominant colors
            kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
            kmeans.fit(pixels)
            
            # Use the most common cluster (should be skin)
            dominant_color_bgr = kmeans.cluster_centers_[0]
            dominant_color_rgb = dominant_color_bgr[::-1]
            
            # Convert to LAB for undertone analysis
            dominant_color_bgr_uint8 = np.uint8([[dominant_color_bgr]])
            dominant_color_lab = cv2.cvtColor(dominant_color_bgr_uint8, cv2.COLOR_BGR2LAB)[0][0]
            
            # Convert RGB to HEX
            hex_color = "{:02x}{:02x}{:02x}".format(
                int(dominant_color_rgb[0]),
                int(dominant_color_rgb[1]),
                int(dominant_color_rgb[2])
            ).upper()
            
            # Determine undertone from LAB a and b values
            undertone_score = dominant_color_lab[1] + dominant_color_lab[2]
            
            if undertone_score > 5:
                undertone = "warm"
            elif undertone_score < -5:
                undertone = "cool"
            else:
                undertone = "neutral"
            
            return {
                "hex": hex_color,
                "undertone": undertone,
                "lab_l": int(dominant_color_lab[0]),
                "lab_a": int(dominant_color_lab[1]),
                "lab_b": int(dominant_color_lab[2])
            }
        except Exception as e:
            print(f"Warning: Skin tone extraction failed: {e}")
            return {
                "hex": "C8956F",
                "undertone": "neutral",
                "lab_l": 50,
                "lab_a": 5,
                "lab_b": 10
            }
    
    def _analyze_body_shape(self, image) -> Dict:
        """
        Estimate body shape based on image aspect ratio.
        Fallback for when pose detection isn't available.
        """
        try:
            h, w, _ = image.shape
            aspect_ratio = w / h if h > 0 else 1.0
            
            # Simple heuristic
            if aspect_ratio > 0.7:
                shape = "Inverted Triangle"  # Wide photo = broad shoulders
            elif aspect_ratio < 0.4:
                shape = "Pear"  # Tall photo = narrow shoulders
            else:
                shape = "Rectangle"
            
            return {"shape": shape, "ratio": aspect_ratio}
        except Exception as e:
            print(f"Warning: Body shape detection failed: {e}")
            return {"shape": "Rectangle", "ratio": 1.0}
    
    def _calculate_contrast(self, image, skin_analysis: Dict) -> str:
        """
        Calculate contrast between skin and overall image.
        High contrast = lots of color/tone variation in face area.
        """
        # Simplified: use LAB L value (lightness)
        # Low L = dark, High L = light
        # Contrast is about color variation, not just lightness
        
        lab_l = skin_analysis.get("lab_l", 50)
        
        # If very light or very dark, high contrast with typical clothing
        if lab_l > 65 or lab_l < 35:
            contrast = "high"
        elif 45 <= lab_l <= 55:
            contrast = "low"
        else:
            contrast = "medium"
        
        return contrast
    
    def _map_to_color_season(self, undertone: str, contrast: str) -> str:
        """
        Map undertone + contrast to color season.
        This is simplistic but explainable.
        """
        if undertone == "cool" and contrast == "high":
            return "Cool Winter"
        elif undertone == "cool" and contrast == "low":
            return "Light Spring"
        elif undertone == "warm" and contrast == "high":
            return "Deep Winter"  # Deep autumns have warmth + contrast
        elif undertone == "warm" and contrast == "low":
            return "Soft Autumn"
        else:
            # neutral
            return "Light Spring"
