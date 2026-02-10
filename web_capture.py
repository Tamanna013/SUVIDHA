# webcam_capture.py
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import os
import time
from translations import t

class SimpleWebcam:
    def __init__(self):
        self.photo_quality_threshold = 0.7  # Minimum quality score
        self.min_face_size = (200, 200)  # Minimum face size
    
    def capture_photo_interface(self, current_lang='en'):
        """Enhanced photo capture interface with multilingual support"""
        st.subheader(t('capture_photo', current_lang))
        
        # Method selection
        capture_method = st.radio(
            "Select Capture Method",
            [t('upload_photo', current_lang), t('take_photo', current_lang)],
            horizontal=True
        )
        
        if capture_method == t('upload_photo', current_lang):
            return self.upload_photo(current_lang)
        else:
            return self.capture_with_webcam(current_lang)
    
    def upload_photo(self, current_lang='en'):
        """Upload photo with verification"""
        uploaded_file = st.file_uploader(
            t('upload_photo', current_lang),
            type=['jpg', 'jpeg', 'png', 'bmp'],
            help="Upload a clear photo of your face for verification"
        )
        
        if uploaded_file:
            try:
                # Read image
                image = Image.open(uploaded_file)
                
                # Display image
                st.image(image, caption=t('upload_photo', current_lang), use_column_width=True)
                
                # Verify photo quality
                verification_result = self.verify_photo_quality(image)
                
                if verification_result['valid']:
                    # Save to session
                    st.session_state['user_photo'] = uploaded_file.getvalue()
                    st.session_state['photo_metadata'] = {
                        'filename': uploaded_file.name,
                        'size': len(uploaded_file.getvalue()),
                        'type': uploaded_file.type,
                        'upload_time': time.time()
                    }
                    
                    if st.button(t('use_photo', current_lang), key="use_uploaded"):
                        st.success(t('photo_verification', current_lang))
                        return image
                else:
                    st.warning(f"Photo quality issues: {verification_result['message']}")
                    st.info("Please upload a clear photo with your face visible")
                    
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")
        
        return None
    
    def capture_with_webcam(self, current_lang='en'):
        """Capture photo using webcam simulation"""
        st.info("For actual webcam capture, install 'streamlit-webrtc' package")
        
        # Simulated webcam capture
        col1, col2 = st.columns(2)
        
        with col1:
            # Simulated camera preview
            placeholder = st.empty()
            with placeholder.container():
                # Create a simulated camera view
                sim_image = self.generate_simulated_image()
                st.image(sim_image, caption="Camera Preview", use_column_width=True)
        
        with col2:
            st.write("**Instructions:**")
            st.write("1. Position your face in the frame")
            st.write("2. Ensure good lighting")
            st.write("3. Look directly at the camera")
            st.write("4. Keep a neutral expression")
            st.write("5. Click 'Capture Photo'")
        
        # Capture button
        if st.button(f"📸 {t('take_photo', current_lang)}", type="primary", key="capture_button"):
            # Simulate photo capture
            captured_image = self.generate_simulated_image(add_face=True)
            
            # Verify photo
            verification_result = self.verify_photo_quality(captured_image)
            
            if verification_result['valid']:
                # Display captured photo
                placeholder.image(captured_image, caption=t('photo_captured', current_lang), use_column_width=True)
                
                # Save to session
                img_bytes = io.BytesIO()
                captured_image.save(img_bytes, format='PNG')
                st.session_state['user_photo'] = img_bytes.getvalue()
                st.session_state['photo_metadata'] = {
                    'filename': f"captured_{int(time.time())}.png",
                    'size': len(img_bytes.getvalue()),
                    'type': 'image/png',
                    'capture_time': time.time()
                }
                
                st.success(f"✅ {t('photo_captured', current_lang)}")
                
                if st.button(t('use_photo', current_lang), key="use_captured"):
                    return captured_image
            else:
                st.error(f"Photo quality issues: {verification_result['message']}")
                st.info("Please try again with better lighting and positioning")
        
        return None
    
    def generate_simulated_image(self, add_face=False):
        """Generate a simulated image for demo purposes"""
        # Create a blank image
        img = Image.new('RGB', (640, 480), color='lightblue')
        
        if add_face:
            # Add a simple face for simulation
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # Face oval
            draw.ellipse([(220, 120), (420, 320)], fill='beige', outline='black', width=2)
            
            # Eyes
            draw.ellipse([(280, 180), (320, 220)], fill='white', outline='black', width=1)
            draw.ellipse([(320, 180), (360, 220)], fill='white', outline='black', width=1)
            draw.ellipse([(300, 190), (310, 200)], fill='black')  # Left pupil
            draw.ellipse([(340, 190), (350, 200)], fill='black')  # Right pupil
            
            # Nose
            draw.line([(320, 220), (320, 260)], fill='black', width=2)
            
            # Mouth
            draw.arc([(280, 260), (360, 300)], 0, 180, fill='red', width=3)
        
        return img
    
    def verify_photo_quality(self, image):
        """Verify photo quality for face recognition"""
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Basic quality checks
            checks = []
            
            # 1. Check image dimensions
            height, width = img_array.shape[:2]
            if height >= 300 and width >= 300:
                checks.append(("Dimensions", True, f"{width}x{height}"))
            else:
                checks.append(("Dimensions", False, "Image too small"))
            
            # 2. Check brightness/contrast
            if len(img_array.shape) == 3:  # Color image
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:  # Already grayscale
                gray = img_array
            
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            if 30 <= brightness <= 220:
                checks.append(("Brightness", True, f"{brightness:.1f}"))
            else:
                checks.append(("Brightness", False, "Too dark/bright"))
            
            if contrast >= 30:
                checks.append(("Contrast", True, f"{contrast:.1f}"))
            else:
                checks.append(("Contrast", False, "Low contrast"))
            
            # 3. Check for blur (using Laplacian variance)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur_score >= 100:
                checks.append(("Sharpness", True, f"{blur_score:.1f}"))
            else:
                checks.append(("Sharpness", False, "Image is blurry"))
            
            # Summary
            passed = sum(1 for _, passed, _ in checks if passed)
            total = len(checks)
            
            if passed == total:
                return {
                    'valid': True,
                    'score': passed/total,
                    'checks': checks,
                    'message': "Photo quality is good"
                }
            else:
                failed = [name for name, passed, _ in checks if not passed]
                return {
                    'valid': False,
                    'score': passed/total,
                    'checks': checks,
                    'message': f"Issues with: {', '.join(failed)}"
                }
                
        except Exception as e:
            return {
                'valid': False,
                'score': 0,
                'checks': [],
                'message': f"Verification error: {str(e)}"
            }
    
    def save_photo_to_database(self, user_id, photo_data, purpose="verification"):
        """Save photo to database for future reference"""
        # In production, you would:
        # 1. Save photo to secure storage
        # 2. Store metadata in database
        # 3. Encrypt sensitive data
        # 4. Set expiration if needed
        
        # For demo, just store in session
        if 'user_photos' not in st.session_state:
            st.session_state.user_photos = {}
        
        photo_id = f"photo_{int(time.time())}"
        st.session_state.user_photos[photo_id] = {
            'user_id': user_id,
            'purpose': purpose,
            'timestamp': time.time(),
            'metadata': st.session_state.get('photo_metadata', {})
        }
        
        return photo_id
    
    def compare_with_aadhaar_photo(self, captured_photo, aadhaar_photo_path):
        """Compare captured photo with Aadhaar photo"""
        # This is a simplified version
        # In production, use proper face recognition
        
        try:
            # Load Aadhaar photo
            if os.path.exists(aadhaar_photo_path):
                aadhaar_img = Image.open(aadhaar_photo_path)
                
                # Simple comparison (in production, use face recognition)
                # For demo, just return a simulated match
                
                # Simulate processing
                import random
                match_score = random.uniform(0.7, 0.95)  # Simulated match score
                
                return {
                    'match': match_score > 0.8,
                    'score': match_score,
                    'message': f"Photo match score: {match_score:.2%}"
                }
            else:
                return {
                    'match': False,
                    'score': 0,
                    'message': "Aadhaar photo not found"
                }
                
        except Exception as e:
            return {
                'match': False,
                'score': 0,
                'message': f"Comparison error: {str(e)}"
            }