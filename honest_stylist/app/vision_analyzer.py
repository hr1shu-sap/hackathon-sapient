import cv2
import numpy as np
import colorsys
from typing import Dict
from sklearn.cluster import KMeans

class VisionAnalyzer:
    """
    Vision Analyzer
    - Robust skin / hair / eye color extraction
    - 12-season color analysis with confidence scores
    - Body balance signals (not brittle body types)
    """

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    # --------------------------------------------------
    # MAIN ENTRY
    # --------------------------------------------------

    def analyze_photo(self, image_path: str) -> Dict:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Image not found")

        img = self._normalize_lighting(img)
        face, face_found = self._detect_face(img)

        skin = self._extract_skin(face)
        hair = self._extract_hair(img)
        eyes = self._extract_eye_color(face)

        # ---- Color science ----
        temperature = self._classify_temperature(skin["rgb"])
        depth = self._classify_depth(skin["rgb"])
        chroma = self._blend_chroma(skin["rgb"], eyes["rgb"], depth)
        contrast = self._classify_contrast(skin["rgb"], hair["rgb"])

        season, season_confidence = self._score_seasons(
            temperature, depth, chroma, contrast
        )

        body_balance = self._estimate_body_balance(img)

        confidence = self._compute_confidence(
            face_found, skin, hair, eyes, season_confidence
        )

        return {
            "skin_hex": skin["hex"],
            "hair_hex": hair["hex"],
            "eye_hex": eyes["hex"],
            "season": season,
            "season_confidence": season_confidence,
            "temperature": temperature,
            "depth": depth,
            "chroma": chroma,
            "contrast": contrast,
            "body_balance": body_balance,
            "confidence": confidence,
        }

    # --------------------------------------------------
    # LIGHT NORMALIZATION
    # --------------------------------------------------

    def _normalize_lighting(self, img):
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.equalizeHist(l)
        lab = cv2.merge((l, a, b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # --------------------------------------------------
    # FACE DETECTION
    # --------------------------------------------------

    def _detect_face(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            h, w, _ = img.shape
            return img[int(h * 0.25):int(h * 0.75),
                       int(w * 0.25):int(w * 0.75)], False

        x, y, w, h = faces[0]
        return img[y:y + h, x:x + w], True

    # --------------------------------------------------
    # COLOR EXTRACTION
    # --------------------------------------------------

    def _dominant(self, roi):
        if roi.size == 0:
            return {"rgb": [128, 128, 128], "hex": "#808080"}

        pixels = roi.reshape(-1, 3)
        kmeans = KMeans(n_clusters=3, n_init=5)
        labels = kmeans.fit_predict(pixels)

        _, counts = np.unique(labels, return_counts=True)
        dom = kmeans.cluster_centers_[np.argmax(counts)]

        rgb = dom[::-1].astype(int)
        hexv = "#{:02X}{:02X}{:02X}".format(*rgb)

        return {"rgb": rgb, "hex": hexv}

    def _extract_skin(self, face):
        h, w, _ = face.shape
        roi = face[int(h * 0.4):int(h * 0.7),
                   int(w * 0.3):int(w * 0.7)]
        return self._dominant(roi)

    def _extract_hair(self, img):
        h, w, _ = img.shape
        roi = img[int(h * 0.02):int(h * 0.18),
                  int(w * 0.25):int(w * 0.75)]
        return self._dominant(roi)

    def _extract_eye_color(self, face):
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(gray, 1.2, 4)

        for (ex, ey, ew, eh) in eyes:
            if ew < 15 or eh < 15:
                continue
            eye = face[ey:ey + eh, ex:ex + ew]
            h, w, _ = eye.shape
            iris = eye[int(h * 0.25):int(h * 0.75),
                       int(w * 0.25):int(w * 0.75)]
            return self._dominant(iris)

        return {"rgb": [120, 120, 120], "hex": "#777777"}

    # --------------------------------------------------
    # COLOR CLASSIFIERS
    # --------------------------------------------------

    def _classify_temperature(self, rgb):
        R, G, B = rgb

        Cb = 128 - 0.168736 * R - 0.331264 * G + 0.5 * B
        Cr = 128 + 0.5 * R - 0.418688 * G - 0.081312 * B
        ycbcr_temp = "warm" if Cr > Cb else "cool"

        r, g, b = [x / 255 for x in rgb]
        _, s, v = colorsys.rgb_to_hsv(r, g, b)

        # Deep-skin correction
        if v < 0.45 and s > 0.35:
            return "cool"

        return ycbcr_temp

    def _classify_depth(self, rgb):
        R, G, B = rgb
        L = 0.299 * R + 0.587 * G + 0.114 * B
        if L > 170:
            return "light"
        if L < 100:
            return "dark"
        return "medium"

    def _blend_chroma(self, skin_rgb, eye_rgb, depth):
        def sat(rgb):
            r, g, b = [x / 255 for x in rgb]
            _, s, _ = colorsys.rgb_to_hsv(r, g, b)
            return s

        skin_s = sat(skin_rgb)
        eye_s = sat(eye_rgb)

        if depth == "dark":
            s = skin_s
        else:
            s = (skin_s * 0.7) + (eye_s * 0.3)

        if s > 0.55:
            return "bright"
        if s < 0.30:
            return "muted"
        return "medium"

    def _classify_contrast(self, skin, hair):
        def lum(rgb):
            R, G, B = rgb
            return 0.299 * R + 0.587 * G + 0.114 * B

        d = abs(lum(skin) - lum(hair))
        if d > 80:
            return "high"
        if d > 40:
            return "medium"
        return "low"

    # --------------------------------------------------
    # SEASON SCORING (PATCHED & BALANCED)
    # --------------------------------------------------

    def _score_seasons(self, temp, depth, chroma, contrast):
        scores = {
            "Deep Winter": 0, "Cool Winter": 0, "Bright Winter": 0,
            "Soft Summer": 0, "True Summer": 0, "Light Summer": 0,
            "Deep Autumn": 0, "True Autumn": 0, "Soft Autumn": 0,
            "Bright Spring": 0, "True Spring": 0, "Light Spring": 0,
        }

        # Temperature
        if temp == "cool":
            scores["Cool Winter"] += 2
            scores["True Summer"] += 2
            scores["Soft Summer"] += 2
            scores["Light Summer"] += 1
        else:
            scores["True Autumn"] += 2
            scores["Soft Autumn"] += 2
            scores["True Spring"] += 2
            scores["Light Spring"] += 1

        # Depth
        if depth == "dark":
            scores["Deep Winter"] += 2
            scores["Deep Autumn"] += 2
        elif depth == "light":
            scores["Light Summer"] += 2
            scores["Light Spring"] += 2
        else:
            scores["True Summer"] += 1
            scores["True Autumn"] += 1

        # Chroma
        if chroma == "muted":
            scores["Soft Summer"] += 3
            scores["Soft Autumn"] += 3
            scores["Bright Winter"] -= 2
            scores["Deep Winter"] -= 1
        elif chroma == "bright":
            scores["Bright Winter"] += 3
            scores["Bright Spring"] += 3
            scores["Soft Summer"] -= 1
            scores["True Summer"] -= 1

        # Contrast
        if contrast == "high":
            scores["Bright Winter"] += 2
            scores["Deep Winter"] += 2
        elif contrast == "low":
            scores["Soft Summer"] += 2
            scores["Soft Autumn"] += 2
            scores["Deep Winter"] -= 2
            scores["Bright Winter"] -= 2

        best = max(scores, key=scores.get)

        total = sum(max(v, 0) for v in scores.values()) or 1
        confidence = {
            k: round(max(v, 0) / total, 3)
            for k, v in scores.items()
            if v > 0
        }

        return best, confidence

    # --------------------------------------------------
    # BODY BALANCE (SAFE HEURISTIC)
    # --------------------------------------------------

    def _estimate_body_balance(self, img):
        h, w, _ = img.shape
        upper = img[int(h * 0.25):int(h * 0.4), :]
        lower = img[int(h * 0.55):int(h * 0.75), :]

        upper_w = np.mean(np.sum(upper > 0, axis=1))
        lower_w = np.mean(np.sum(lower > 0, axis=1))

        signals = {
            "shoulder_dominant": upper_w > lower_w * 1.1,
            "hip_dominant": lower_w > upper_w * 1.1,
            "defined_waist": abs(upper_w - lower_w) > 0.15 * w,
        }

        return {"signals": signals, "confidence": 0.6}

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    def _compute_confidence(self, face_found, skin, hair, eyes, season_conf):
        c = 1.0
        if not face_found:
            c -= 0.2
        if eyes["hex"] == "#777777":
            c -= 0.1
        if hair["hex"] == "#808080":
            c -= 0.1
        if max(season_conf.values()) < 0.25:
            c -= 0.2
        return round(max(0.0, c), 2)