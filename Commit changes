import streamlit as st
import whisper
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import os

# Gemini API Key Setup
API_KEY = "AIzaSyAycw9hVYcrpTOJoHpT4Kserqci826Rq2A"
genai.configure(api_key=API_KEY)
llm_model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="MM AI Video Translator", page_icon="🇲🇲")
st.title("🇲🇲 Myanmar Video AI Translator")

@st.cache_resource
def load_model():
    return whisper.load_model("base")

stt_model = load_model()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI အလုပ်လုပ်နေသည်...'):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                tfile.write(uploaded_file.read())
                video_path = tfile.name

            # ၁။ စာသားပြောင်းခြင်း
            result = stt_model.transcribe(video_path)
            
            # ၂။ Gemini နဲ့ မြန်မာလို ပြန်ရေးခြင်း
            prompt = f"Translate and rewrite this transcript into natural, polished Burmese: {result['text']}"
            mm_text = llm_model.generate_content(prompt).text
            
            # ၃။ မြန်မာအသံထုတ်ခြင်း
            audio_file = "output.mp3"
            asyncio.run(edge_tts.Communicate(mm_text, "my-MM-ThihaNeural").save(audio_file))

            st.subheader("မြန်မာ Script")
            st.text_area("", mm_text, height=200)
            st.audio(audio_file)
            
            with open(audio_file, "rb") as f:
                st.download_button("အသံဖိုင်ဒေါင်းရန်", f, file_name="ai_voice.mp3")
            
            os.remove(video_path)
