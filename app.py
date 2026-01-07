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

# Model နာမည်ကို အလုပ်လုပ်ဖို့ အသေချာဆုံးပုံစံနဲ့ ပြင်ထားပါတယ်
llm_model = genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="Universal AI Video Translator", page_icon="🌍")
st.title("🌍 Universal AI Video Translator")

@st.cache_resource
def load_model():
    return whisper.load_model("base")

stt_model = load_model()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က ဘာသာစကားကို ခွဲခြားပြီး ဘာသာပြန်နေပါတယ်...'):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၁။ ဘာသာစကားကို အလိုအလျောက် သိရှိခြင်း
                st.info("အဆင့် (၁): ဗီဒီယိုထဲက ဘာသာစကားကို စစ်ဆေးပြီး စာသားပြောင်းနေပါတယ်...")
                result = stt_model.transcribe(video_path)
                original_text = result['text']
                detected_lang = result.get('language', 'unknown')
                
                st.write(f"🔍 သိရှိရသော ဘာသာစကား: **{detected_lang.upper()}**")

                # ၂။ Gemini နဲ့ မြန်မာလို ပြန်ဆိုခြင်း
                st.info("အဆင့် (၂): မြန်မာလို ပီပီသသ ပြန်ဆိုနေပါတယ်...")
                prompt = f"The text is in {detected_lang}. Translate to natural, professional Burmese: {original_text}"
                response = llm_model.generate_content(prompt)
                mm_text = response.text
                
                # ၃။ မြန်မာ AI အသံထုတ်ခြင်း
                st.info("အဆင့် (၃): မြန်မာ AI အသံဖိုင် ဖန်တီးနေပါတယ်...")
                output_audio = "final_voice.mp3"
                communicate = edge_tts.Communicate(mm_text, "my-MM-ThihaNeural")
                asyncio.run(communicate.save(output_audio))

                st.success("ဘာသာပြန်ခြင်း အောင်မြင်ပါတယ်!")
                st.subheader("မြန်မာ Script (စာသား)")
                st.text_area("", mm_text, height=250)
                st.audio(output_audio)
                
                with open(output_audio, "rb") as f:
                    st.download_button("မြန်မာအသံဖိုင်ကို ဒေါင်းလုဒ်ယူရန်", f, file_name="translated_voice.mp3")
                
                os.remove(video_path)
                
            except Exception as e:
                st.error(f"Error အသေးစိတ်: {str(e)}")
