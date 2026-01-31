import cv2
import numpy as np
from typing import Dict
from sklearn.cluster import KMeans
import colorsys
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks import python


class VisionAnalyzer:

    def __init__(self):

        # -----------------------------
        # Face/Eye Detection
        # -----------------------------
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

        # -----------------------------
        # MediaPipe Pose (Tasks API)
        # -----------------------------
        try:
            base_options = python.BaseOptions(
                model_asset_path="pose_landmarker.task"
            )

            options = vision.PoseLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE
            )

            self.pose_landmarker = vision.PoseLandmarker.create_from_options(options)
            self.pose_enabled = True

        except Exception as e:
            print("⚠️ Pose model not loaded:", e)
            self.pose_enabled = False

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

        body = self._analyze_body_shape(img_norm)

        temp = self._classify_temperature(skin["rgb"])
        depth = self._classify_depth(skin["rgb"])
        chroma = self._blend_chroma(skin["rgb"], eyes["rgb"])
        contrast = self._classify_contrast(skin["rgb"], hair["rgb"])

        season = self._map_season(temp, depth, chroma, contrast)

        confidence = self._compute_confidence(
            face_found, skin, hair, eyes, body
        )

        return {
            "skin_hex": skin["hex"],
            "hair_hex": hair["hex"],
            "eye_hex": eyes["hex"],
            "body_shape": body["shape"],
            "body_ratios": body["ratios"],
            "season": season,
            "temperature": temp,
            "contrast": contrast,
            "confidence": confidence
        }

    # --------------------------------------------------
    # BODY SHAPE (MediaPipe Tasks)
    # --------------------------------------------------

    def _analyze_body_shape(self, img) -> Dict:

        if not self.pose_enabled:
            return {"shape": "Rectangle", "ratios": {}, "confidence": 0.0}

        # MediaPipe prefers a square IMAGE_DIMENSIONS when using NORM_RECT.
        # Crop to a centered square to avoid the "Using NORM_RECT without IMAGE_DIMENSIONS" warning
        h_img, w_img = img.shape[:2]
        min_dim = min(h_img, w_img)
        y0 = (h_img - min_dim) // 2
        x0 = (w_img - min_dim) // 2
        square = img[y0:y0 + min_dim, x0:x0 + min_dim]

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(square, cv2.COLOR_BGR2RGB)
        )

        result = self.pose_landmarker.detect(mp_image)

        if not result.pose_landmarks:
            return {"shape": "Rectangle", "ratios": {}, "confidence": 0.0}

        lm = result.pose_landmarks[0]

        def body_width(p1, p2):
            return np.sqrt(
                (lm[p1].x - lm[p2].x) ** 2 +
                (lm[p1].y - lm[p2].y) ** 2
            )

        s_w = body_width(11, 12)  # shoulders
        h_w = body_width(23, 24)  # hips

        if h_w == 0:
            return {"shape": "Rectangle", "ratios": {}, "confidence": 0.0}

        s_to_h = s_w / h_w

        # Human-calibrated thresholds
        if s_to_h >= 1.18:
            shape = "Inverted Triangle"
        elif s_to_h <= 0.88:
            shape = "Pear"
        else:
            shape = "Rectangle"

        # Confidence estimation
        confidence = 0.9
        arm_y_diff = abs(lm[11].y - lm[13].y)
        if arm_y_diff > 0.15:
            confidence -= 0.3

        return {
            "shape": shape,
            "ratios": {
                "shoulder_hip": round(s_to_h, 2)
            },
            "confidence": max(0.4, confidence)
        }


    # --------------------------------------------------
    # LIGHT NORMALIZATION
    # --------------------------------------------------

    def _normalize_lighting(self, img):
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l,a,b = cv2.split(lab)
        l = cv2.equalizeHist(l)
        lab = cv2.merge((l,a,b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # --------------------------------------------------
    # FACE
    # --------------------------------------------------

    def _detect_face(self, img):

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray,1.3,5)

        if len(faces)==0:
            h,w,_=img.shape
            return img[int(h*0.2):int(h*0.8),
                       int(w*0.2):int(w*0.8)], False

        x,y,w,h = faces[0]
        return img[y:y+h,x:x+w], True

    # --------------------------------------------------
    # DOMINANT COLOR
    # --------------------------------------------------

    def _dominant(self, roi):

        if roi.size==0:
            return {"rgb":[128,128,128],"hex":"#808080"}

        pixels = roi.reshape(-1,3)

        kmeans = KMeans(n_clusters=3,n_init=5)
        labels = kmeans.fit_predict(pixels)

        _,counts = np.unique(labels,return_counts=True)
        dom = kmeans.cluster_centers_[np.argmax(counts)]

        rgb = dom[::-1].astype(int)
        hexv = "#{:02X}{:02X}{:02X}".format(*rgb)

        return {"rgb":rgb,"hex":hexv}

    # --------------------------------------------------
    # SKIN / HAIR / EYES
    # --------------------------------------------------

    def _extract_skin(self, face):
        h,w,_=face.shape
        roi = face[int(h*0.4):int(h*0.7),
                   int(w*0.3):int(w*0.7)]
        return self._dominant(roi)

    def _extract_hair(self, img):
        h,w,_=img.shape
        roi = img[int(h*0.02):int(h*0.18),
                  int(w*0.25):int(w*0.75)]
        return self._dominant(roi)

    def _extract_eye_color(self, face):

        gray = cv2.cvtColor(face,cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(gray,1.2,4)

        for (ex,ey,ew,eh) in eyes:
            if ew<15 or eh<15: continue
            eye = face[ey:ey+eh,ex:ex+ew]
            h,w,_=eye.shape
            iris = eye[int(h*0.25):int(h*0.75),
                       int(w*0.25):int(w*0.75)]
            return self._dominant(iris)

        return {"rgb":[120,120,120],"hex":"#777777"}

    # --------------------------------------------------
    # CLASSIFIERS
    # --------------------------------------------------

    def _classify_temperature(self,rgb):
        R,G,B=rgb
        Cb = 128 - 0.168736*R - 0.331264*G + 0.5*B
        Cr = 128 + 0.5*R - 0.418688*G - 0.081312*B
        return "warm" if Cr>Cb else "cool"

    def _classify_depth(self,rgb):
        R,G,B=rgb
        L = 0.299*R+0.587*G+0.114*B
        if L>170:return"light"
        if L<100:return"dark"
        return"medium"

    def _blend_chroma(self,skin,eye):

        def sat(rgb):
            r,g,b=[x/255 for x in rgb]
            _,s,_=colorsys.rgb_to_hsv(r,g,b)
            return s

        s=(sat(skin)*0.6)+(sat(eye)*0.4)

        if s>0.55:return"bright"
        if s<0.30:return"muted"
        return"medium"

    def _classify_contrast(self,skin,hair):

        def lum(rgb):
            R,G,B=rgb
            return 0.299*R+0.587*G+0.114*B

        d=abs(lum(skin)-lum(hair))

        if d>80:return"high"
        if d>40:return"medium"
        return"low"

    # --------------------------------------------------

    def _map_season(self,temp,depth,chroma,contrast):

        if temp=="warm":
            if chroma=="bright" and contrast=="high":return"Bright Spring"
            if depth=="light":return"Light Spring"
            if depth=="dark":return"Deep Autumn"
            if chroma=="muted":return"Soft Autumn"
            return"True Spring"

        if temp=="cool":
            if chroma=="bright" and contrast=="high":return"Bright Winter"
            if depth=="dark":return"Deep Winter"
            if chroma=="muted":return"Soft Summer"
            if depth=="light":return"Light Summer"
            return"True Summer"

        return"Soft Autumn"

    # --------------------------------------------------

    def _compute_confidence(self,face_found,skin,hair,eyes,body):

        c=1.0
        if not face_found:c-=0.3
        if eyes["hex"]=="#777777":c-=0.2
        if hair["hex"]=="#808080":c-=0.2
        if body["confidence"]<0.5:c-=0.2

        return max(0.0,c)
