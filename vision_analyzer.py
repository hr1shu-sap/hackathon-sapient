import cv2
import numpy as np
from typing import Dict
from sklearn.cluster import KMeans
import colorsys
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks import python


class VisionAnalyzer:
    """
    Vision Analyzer for Honest Stylist.
    Focuses on:
    - Color science (stable)
    - Body balance signals (contextual, honest)
    """

    # --------------------------------------------------
    # INIT
    # --------------------------------------------------

    def __init__(self):

        # Face / Eye Detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

        # MediaPipe Tasks – Selfie Segmentation
        try:
            base_options = python.BaseOptions(
                model_asset_path="selfie_segmenter.tflite"
            )

            options = vision.ImageSegmenterOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                output_category_mask=True
            )

            self.segmenter = vision.ImageSegmenter.create_from_options(options)
            self.body_enabled = True

        except Exception as e:
            print("⚠️ Image Segmenter not loaded:", e)
            self.body_enabled = False

    # --------------------------------------------------
    # MAIN ENTRY
    # --------------------------------------------------

    def analyze_photo(self, image_path: str) -> Dict:

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Image not found")

        img_norm = self._normalize_lighting(img)

        face, face_found = self._detect_face(img_norm)

        skin = self._extract_skin(face)
        hair = self._extract_hair(img_norm)
        eyes = self._extract_eye_color(face)

        body_profile = self._analyze_body_balance(img_norm)

        # ---- Color theory ----
        temp = self._classify_temperature(skin["rgb"])
        depth = self._classify_depth(skin["rgb"])
        chroma = self._blend_chroma(skin["rgb"], eyes["rgb"])
        contrast = self._classify_contrast(skin["rgb"], hair["rgb"])

        season = self._map_season(temp, depth, chroma, contrast)

        confidence = self._compute_confidence(
            face_found, skin, hair, eyes, body_profile
        )

        return {
            "skin_hex": skin["hex"],
            "hair_hex": hair["hex"],
            "eye_hex": eyes["hex"],
            "season": season,
            "temperature": temp,
            "contrast": contrast,
            "body_profile": body_profile,
            "confidence": confidence
        }

    # --------------------------------------------------
    # BODY BALANCE (SEGMENTATION-BASED)
    # --------------------------------------------------

    def _analyze_body_balance(self, img) -> Dict:
        """
        Extracts silhouette balance signals instead of forcing body shape.
        """

        if not self.body_enabled:
            return self._empty_body_profile()

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        )

        result = self.segmenter.segment(mp_image)
        if result.category_mask is None:
            return self._empty_body_profile()

        mask = result.category_mask.numpy_view()
        if mask.ndim == 3:
            mask = mask[:, :, 0]

        mask = (mask > 0).astype(np.uint8)
        h, w = mask.shape

        # Not enough visible body
        if np.sum(mask) < 0.15 * h * w:
            return self._empty_body_profile(conf=0.3)

        def width_at(ratio):
            y = int(h * ratio)
            xs = np.where(mask[y] > 0)[0]
            return xs[-1] - xs[0] if len(xs) > 0 else 0

        shoulder_w = width_at(0.25)
        waist_w = width_at(0.50)
        hip_w = width_at(0.70)

        if min(shoulder_w, waist_w, hip_w) == 0:
            return self._empty_body_profile(conf=0.4)

        shoulder_r = shoulder_w / h
        waist_r = waist_w / h
        hip_r = hip_w / h

        sh_diff = shoulder_r - hip_r
        waist_def = 1 - (waist_r / max(shoulder_r, hip_r))

        signals = {
            "shoulder_dominant": sh_diff > 0.10,
            "hip_dominant": sh_diff < -0.10,
            "defined_waist": waist_def > 0.25
        }

        # Only assign shape if VERY clear
        if signals["defined_waist"] and signals["hip_dominant"]:
            shape = "Pear"
        elif signals["defined_waist"] and signals["shoulder_dominant"]:
            shape = "Inverted Triangle"
        elif signals["defined_waist"] and abs(sh_diff) < 0.08:
            shape = "Hourglass"
        else:
            shape = "Rectangle"

        return {
            "shape": shape,
            "signals": signals,
            "ratios": {
                "shoulder": round(shoulder_r, 2),
                "waist": round(waist_r, 2),
                "hip": round(hip_r, 2)
            },
            "confidence": 0.85
        }

    def _empty_body_profile(self, conf=0.0):
        return {
            "shape": "Rectangle",
            "signals": {
                "shoulder_dominant": False,
                "hip_dominant": False,
                "defined_waist": False
            },
            "ratios": {},
            "confidence": conf
        }

    # --------------------------------------------------
    # IMAGE PREP
    # --------------------------------------------------

    def _normalize_lighting(self, img):
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.equalizeHist(l)
        return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    def _detect_face(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            h, w, _ = img.shape
            return img[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8)], False
        x, y, w, h = faces[0]
        return img[y:y+h, x:x+w], True

    # --------------------------------------------------
    # COLOR EXTRACTION
    # --------------------------------------------------

    def _dominant(self, roi):
        if roi.size == 0:
            return {"rgb": [128, 128, 128], "hex": "#808080"}
        pixels = roi.reshape(-1, 3)
        kmeans = KMeans(n_clusters=3, n_init=5)
        labels = kmeans.fit_predict(pixels)
        dom = kmeans.cluster_centers_[np.argmax(np.bincount(labels))]
        rgb = dom[::-1].astype(int)
        return {"rgb": rgb, "hex": "#{:02X}{:02X}{:02X}".format(*rgb)}

    def _extract_skin(self, face):
        h, w, _ = face.shape
        roi = face[int(h*0.4):int(h*0.7), int(w*0.3):int(w*0.7)]
        return self._dominant(roi)

    def _extract_hair(self, img):
        h, w, _ = img.shape
        roi = img[int(h*0.02):int(h*0.18), int(w*0.25):int(w*0.75)]
        return self._dominant(roi)

    def _extract_eye_color(self, face):
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(gray, 1.2, 4)
        for (ex, ey, ew, eh) in eyes:
            if ew < 15 or eh < 15:
                continue
            eye = face[ey:ey+eh, ex:ex+ew]
            h, w, _ = eye.shape
            iris = eye[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
            return self._dominant(iris)
        return {"rgb": [120, 120, 120], "hex": "#777777"}

    # --------------------------------------------------
    # COLOR THEORY
    # --------------------------------------------------

    def _classify_temperature(self, rgb):
        R, G, B = rgb
        Cb = 128 - 0.168736*R - 0.331264*G + 0.5*B
        Cr = 128 + 0.5*R - 0.418688*G - 0.081312*B
        return "warm" if Cr > Cb else "cool"

    def _classify_depth(self, rgb):
        L = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
        if L > 170:
            return "light"
        if L < 100:
            return "dark"
        return "medium"

    def _blend_chroma(self, skin, eye):
        def sat(rgb):
            r, g, b = [x/255 for x in rgb]
            return colorsys.rgb_to_hsv(r, g, b)[1]
        s = sat(skin)*0.6 + sat(eye)*0.4
        if s > 0.55:
            return "bright"
        if s < 0.30:
            return "muted"
        return "medium"

    def _classify_contrast(self, skin, hair):
        lum = lambda rgb: 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
        d = abs(lum(skin) - lum(hair))
        if d > 80:
            return "high"
        if d > 40:
            return "medium"
        return "low"

    def _map_season(self, temp, depth, chroma, contrast):
        if temp == "warm":
            if chroma == "bright" and contrast == "high":
                return "Bright Spring"
            if depth == "light":
                return "Light Spring"
            if depth == "dark":
                return "Deep Autumn"
            if chroma == "muted":
                return "Soft Autumn"
            return "True Spring"
        if temp == "cool":
            if chroma == "bright" and contrast == "high":
                return "Bright Winter"
            if depth == "dark":
                return "Deep Winter"
            if chroma == "muted":
                return "Soft Summer"
            if depth == "light":
                return "Light Summer"
            return "True Summer"
        return "Soft Autumn"

    def _compute_confidence(self, face_found, skin, hair, eyes, body):
        c = 1.0
        if not face_found:
            c -= 0.3
        if eyes["hex"] == "#777777":
            c -= 0.2
        if hair["hex"] == "#808080":
            c -= 0.2
        if body["confidence"] < 0.5:
            c -= 0.2
        return max(0.0, c)
