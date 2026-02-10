# voice_assistant.py
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
from translations import t

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.supported_languages = {
            'en': 'English',
            'hi': 'Hindi',
            'mr': 'Marathi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'bn': 'Bengali'
        }
        
        # Voice commands in multiple languages
        self.voice_commands = {
            'en': [
                "Submit electricity bill complaint",
                "Check my service request status",
                "Find nearest municipal office",
                "Pay water bill",
                "Register new complaint",
                "Emergency help",
                "Track my application",
                "Upload documents",
                "Contact support",
                "Check payment status"
            ],
            'hi': [
                "बिजली बिल शिकायत दर्ज करें",
                "मेरी सेवा अनुरोध स्थिति जांचें",
                "निकटतम नगर निगम कार्यालय ढूंढें",
                "पानी बिल भुगतान करें",
                "नई शिकायत पंजीकृत करें",
                "आपातकालीन सहायता",
                "मेरे आवेदन की स्थिति ट्रैक करें",
                "दस्तावेज़ अपलोड करें",
                "समर्थन से संपर्क करें",
                "भुगतान स्थिति जांचें"
            ],
            'mr': [
                "वीज बिल तक्रार सबमिट करा",
                "माझी सेवा विनंती स्थिती तपासा",
                "जवळचे नगरपालिका कार्यालय शोधा",
                "पाणी बिल भरा",
                "नवीन तक्रार नोंदवा",
                "आणीबाणी मदत",
                "माझ्या अर्जाची स्थिती ट्रॅक करा",
                "कागदपत्रे अपलोड करा",
                "समर्थनाशी संपर्क साधा",
                "पेमेंट स्थिती तपासा"
            ],
            'ta': [
                "மின்சார பில் புகார் சமர்ப்பிக்கவும்",
                "எனது சேவை கோரிக்கை நிலையை சரிபார்க்கவும்",
                "அருகிலுள்ள நகராட்சி அலுவலகத்தைக் கண்டறியவும்",
                "நீர் கட்டணம் செலுத்தவும்",
                "புதிய புகார் பதிவு செய்யவும்",
                "அவசர உதவி",
                "எனது விண்ணப்ப நிலையைக் கண்காணிக்கவும்",
                "ஆவணங்களைப் பதிவேற்றவும்",
                "ஆதரவைத் தொடர்பு கொள்ளவும்",
                "கட்டண நிலையை சரிபார்க்கவும்"
            ]
        }
        
        # Voice responses in multiple languages
        self.voice_responses = {
            'en': {
                'electricity': "I can help with electricity services. Would you like to submit a complaint, pay a bill, or request a new connection?",
                'water': "For water department services, I can help with complaints, bill payments, or new connections.",
                'gas': "Gas department services include safety inspections, leak complaints, and new connections.",
                'waste': "Waste management services: garbage collection complaints, sanitation issues, or recycling information.",
                'status': "To check your service request status, please provide your request ID or Aadhaar number.",
                'payment': "I can help you pay bills. Which department bill would you like to pay?",
                'emergency': "For emergencies: Police - 100, Fire - 101, Ambulance - 102, Electricity - 1912, Gas leak - 1906",
                'default': "I can help you with electricity, water, gas, and waste management services. What do you need?",
                'greeting': "Welcome to SUVIDHA voice assistant. I can help you with electricity, water, gas, and waste management services."
            },
            'hi': {
                'electricity': "मैं बिजली सेवाओं में मदद कर सकता हूं। क्या आप शिकायत दर्ज करना, बिल भरना या नया कनेक्शन चाहते हैं?",
                'water': "पानी विभाग की सेवाओं के लिए, मैं शिकायतें, बिल भुगतान या नए कनेक्शन में मदद कर सकता हूं।",
                'gas': "गैस विभाग सेवाओं में सुरक्षा निरीक्षण, रिसाव शिकायतें और नए कनेक्शन शामिल हैं।",
                'waste': "कचरा प्रबंधन सेवाएं: कचरा संग्रह शिकायतें, सफाई मुद्दे, या पुनर्चक्रण जानकारी।",
                'status': "अपनी सेवा अनुरोध स्थिति जांचने के लिए, कृपया अपना अनुरोध आईडी या आधार नंबर प्रदान करें।",
                'payment': "मैं आपको बिल भुगतान में मदद कर सकता हूं। आप किस विभाग का बिल भरना चाहते हैं?",
                'emergency': "आपातकाल के लिए: पुलिस - 100, आग - 101, एम्बुलेंस - 102, बिजली - 1912, गैस रिसाव - 1906",
                'default': "मैं आपकी बिजली, पानी, गैस और कचरा प्रबंधन सेवाओं में मदद कर सकता हूं। आपको क्या चाहिए?",
                'greeting': "सुविधा वॉयस असिस्टेंट में आपका स्वागत है। मैं आपकी बिजली, पानी, गैस और कचरा प्रबंधन सेवाओं में मदद कर सकता हूं।"
            },
            'mr': {
                'electricity': "मी वीज सेवांमध्ये मदत करू शकतो. तुम्हाला तक्रार सबमिट करायची आहे, बिल भरायचे आहे की नवीन कनेक्शन हवे आहे?",
                'water': "पाणी विभाग सेवांसाठी, मी तक्रारी, बिल भरपाई किंवा नवीन कनेक्शनमध्ये मदत करू शकतो.",
                'gas': "गॅस विभाग सेवांमध्ये सुरक्षा तपासणी, गळती तक्रारी आणि नवीन कनेक्शन समाविष्ट आहेत.",
                'waste': "कचरा व्यवस्थापन सेवा: कचरा संकलन तक्रारी, स्वच्छता समस्या किंवा पुनर्वापर माहिती.",
                'status': "तुमची सेवा विनंती स्थिती तपासण्यासाठी, कृपया तुमची विनंती आयडी किंवा आधार क्रमांक प्रदान करा.",
                'payment': "मी तुम्हाला बिले भरण्यात मदत करू शकतो. तुम्हाला कोणत्या विभागाचे बिल भरायचे आहे?",
                'emergency': "आणीबाणीसाठी: पोलिस - 100, आग - 101, एंब्युलन्स - 102, वीज - 1912, गॅस गळती - 1906",
                'default': "मी तुम्हाला वीज, पाणी, गॅस आणि कचरा व्यवस्थापन सेवांमध्ये मदत करू शकतो. तुम्हाला काय हवे आहे?",
                'greeting': "सुविधा व्हॉइस असिस्टंट मध्ये आपले स्वागत आहे. मी वीज, पाणी, गॅस आणि कचरा व्यवस्थापन सेवांमध्ये आपली मदत करू शकतो."
            },
            'ta': {
                'electricity': "மின்சார சேவைகளில் நான் உதவ முடியும். நீங்கள் புகாரை சமர்ப்பிக்கவா, கட்டணம் செலுத்தவா அல்லது புதிய இணைப்பு கோரவா விரும்புகிறீர்கள்?",
                'water': "நீர் துறை சேவைகளுக்கு, நான் புகார்கள், கட்டண செலுத்துதல் அல்லது புதிய இணைப்புகளில் உதவ முடியும்.",
                'gas': "எரிவாயு துறை சேவைகளில் பாதுகாப்பு ஆய்வுகள், கசிவு புகார்கள் மற்றும் புதிய இணைப்புகள் அடங்கும்.",
                'waste': "குப்பை மேலாண்மை சேவைகள்: குப்பை சேகரிப்பு புகார்கள், சுகாதார பிரச்சினைகள் அல்லது மறுசுழற்சி தகவல்.",
                'status': "உங்கள் சேவை கோரிக்கை நிலையை சரிபார்க்க, உங்கள் கோரிக்கை ஐடி அல்லது ஆதார் எண்ணை வழங்கவும்.",
                'payment': "கட்டணங்களை செலுத்த நான் உங்களுக்கு உதவ முடியும். எந்த துறை கட்டணத்தை செலுத்த விரும்புகிறீர்கள்?",
                'emergency': "அவசர நிலைகளுக்கு: காவல் - 100, தீ - 101, ஆம்புலன்ஸ் - 102, மின்சாரம் - 1912, எரிவாயு கசிவு - 1906",
                'default': "மின்சாரம், நீர், எரிவாயு மற்றும் குப்பை மேலாண்மை சேவைகளில் நான் உங்களுக்கு உதவ முடியும். உங்களுக்கு என்ன தேவை?",
                'greeting': "சுயிதா குரல் உதவியாளருக்கு வரவேற்கிறோம். மின்சாரம், நீர், எரிவாயு மற்றும் குப்பை மேலாண்மை சேவைகளில் நான் உங்களுக்கு உதவ முடியும்."
            }
        }
    
    def voice_interface(self, current_lang='en'):
        """Main voice interface with multilingual support"""
        st.markdown(f"### 🗣️ {t('voice_assistant_title', current_lang)}")
        
        # Language selection for voice
        selected_lang = st.selectbox(
            t('speak_language', current_lang),
            list(self.supported_languages.values()),
            index=list(self.supported_languages.values()).index(
                self.supported_languages.get(current_lang, 'English')
            )
        )
        
        lang_code = [k for k, v in self.supported_languages.items() 
                    if v == selected_lang][0]
        
        # Voice commands in selected language
        st.write(f"**{t('try_saying', current_lang)}**")
        commands = self.voice_commands.get(lang_code, self.voice_commands['en'])
        
        for cmd in commands:
            st.write(f"• '{cmd}'")
        
        # Voice input
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"🎤 {t('start_listening', current_lang)}", 
                        use_container_width=True, key="voice_start"):
                self.listen_and_process(lang_code, current_lang)
        
        with col2:
            if st.button(f"🔊 {t('speak_help', current_lang)}", 
                        use_container_width=True, key="voice_help"):
                self.speak_welcome_message(lang_code)
        
        # Voice output
        if st.session_state.get('voice_response'):
            st.info(f"**{t('voice_assistant_title', current_lang)}:** {st.session_state['voice_response']}")
            
            # Text-to-speech
            if st.button(f"🔊 {t('hear_response', current_lang)}", 
                        key="voice_hear"):
                self.text_to_speech(
                    st.session_state['voice_response'], 
                    lang_code
                )
    
    def listen_and_process(self, lang_code='en', current_lang='en'):
        """Listen to voice and process command"""
        try:
            with sr.Microphone() as source:
                st.info(t('listening', current_lang))
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5)
                
                # Recognize speech
                text = self.recognizer.recognize_google(audio, language=lang_code)
                st.success(f"You said: {text}")
                
                # Process command
                response = self.process_voice_command(text, lang_code)
                st.session_state['voice_response'] = response
                
        except sr.WaitTimeoutError:
            st.error(t('speech_detected', current_lang))
        except sr.UnknownValueError:
            st.error(t('speech_not_understood', current_lang))
        except sr.RequestError:
            st.error(t('speech_service_unavailable', current_lang))
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def process_voice_command(self, text, lang_code='en'):
        """Process voice command and return response in appropriate language"""
        text_lower = text.lower()
        responses = self.voice_responses.get(lang_code, self.voice_responses['en'])
        
        # Check for keywords in the spoken language
        keywords = {
            'electricity': ['electricity', 'power', 'bill', 'current', 'light'],
            'water': ['water', 'pipeline', 'supply', 'tap', 'drinking'],
            'gas': ['gas', 'cylinder', 'leak', 'cooking', 'lpg'],
            'waste': ['garbage', 'waste', 'clean', 'trash', 'dustbin'],
            'status': ['status', 'track', 'update', 'progress', 'check'],
            'payment': ['pay', 'payment', 'bill', 'due', 'amount'],
            'emergency': ['emergency', 'urgent', 'help', 'accident', 'danger']
        }
        
        # For Hindi
        if lang_code == 'hi':
            keywords = {
                'electricity': ['बिजली', 'पावर', 'बिल', 'करंट', 'लाइट'],
                'water': ['पानी', 'पाइपलाइन', 'सप्लाई', 'नल', 'पीने'],
                'gas': ['गैस', 'सिलेंडर', 'रिसाव', 'खाना', 'एलपीजी'],
                'waste': ['कचरा', 'वेस्ट', 'साफ', 'कूड़ा', 'डस्टबिन'],
                'status': ['स्थिति', 'ट्रैक', 'अपडेट', 'प्रगति', 'जांच'],
                'payment': ['भुगतान', 'पेमेंट', 'बिल', 'नियत', 'राशि'],
                'emergency': ['आपातकाल', 'जरूरी', 'मदद', 'दुर्घटना', 'खतरा']
            }
        
        # For Marathi
        elif lang_code == 'mr':
            keywords = {
                'electricity': ['वीज', 'पॉवर', 'बिल', 'करंट', 'लाइट'],
                'water': ['पाणी', 'पाईपलाइन', 'सप्लाई', 'नळ', 'पिण्याचे'],
                'gas': ['गॅस', 'सिलेंडर', 'गळती', 'स्वयंपाक', 'एलपीजी'],
                'waste': ['कचरा', 'वेस्ट', 'स्वच्छ', 'कचरा', 'डस्टबिन'],
                'status': ['स्थिती', 'ट्रॅक', 'अपडेट', 'प्रगती', 'तपासणी'],
                'payment': ['पेमेंट', 'भरपाई', 'बिल', 'नियत', 'रक्कम'],
                'emergency': ['आणीबाणी', 'गरजेचे', 'मदत', 'अपघात', 'धोका']
            }
        
        # For Tamil
        elif lang_code == 'ta':
            keywords = {
                'electricity': ['மின்சாரம்', 'பவர்', 'பில்', 'கரண்ட்', 'லைட்'],
                'water': ['நீர்', 'குழாய்', 'விநியோகம்', 'குழாய்', 'குடிநீர்'],
                'gas': ['எரிவாயு', 'சிலிண்டர்', 'கசிவு', 'சமையல்', 'எல்பீஜி'],
                'waste': ['குப்பை', 'கழிவு', 'சுத்தம்', 'குப்பை', 'டஸ்ட்பின்'],
                'status': ['நிலை', 'ட்ராக்', 'புதுப்பிப்பு', 'முன்னேற்றம்', 'சரிபார்க்க'],
                'payment': ['பணம்', 'கட்டணம்', 'பில்', 'காலக்கெடு', 'தொகை'],
                'emergency': ['அவசர', 'அவசரம்', 'உதவி', 'விபத்து', 'அபாயம்']
            }
        
        # Check for each category
        for category, words in keywords.items():
            for word in words:
                if word in text_lower:
                    return responses.get(category, responses['default'])
        
        return responses['default']
    
    def text_to_speech(self, text, lang_code='en'):
        """Convert text to speech"""
        try:
            # Create temporary file for audio
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                tts.save(fp.name)
                # Play audio in Streamlit
                audio_file = open(fp.name, 'rb')
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format='audio/mp3')
                
            # Cleanup
            os.unlink(fp.name)
            
        except Exception as e:
            st.error(f"Text-to-speech failed: {e}")
    
    def speak_welcome_message(self, lang_code='en'):
        """Speak welcome message in selected language"""
        responses = self.voice_responses.get(lang_code, self.voice_responses['en'])
        self.text_to_speech(responses.get('greeting', responses['default']), lang_code)
    
    def execute_voice_command(self, command, lang_code='en'):
        """Execute voice command and perform action"""
        # This function would integrate with the main application
        # to perform actual actions based on voice commands
        
        command_lower = command.lower()
        
        # Map commands to actions
        actions = {
            'submit electricity': lambda: self.navigate_to('new_request'),
            'check status': lambda: self.navigate_to('track_status'),
            'pay bill': lambda: self.navigate_to('payments'),
            'emergency': lambda: self.navigate_to('emergency'),
            'upload document': lambda: self.navigate_to('documents')
        }
        
        for key, action in actions.items():
            if key in command_lower:
                action()
                return f"Navigating to {key}..."
        
        return "I understand. How can I help you further?"
    
    def navigate_to(self, page):
        """Navigate to specific page"""
        st.session_state.page = page
        st.rerun()