import streamlit as st
import whisper
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import os

# Gemini API Key Setup
# ဘရိုရဲ့ API Key ကို ဒီမှာ ထည့်ထားပါတယ်
API_KEY = "AIzaSyAycw9hVYcrpTOJoHpT4Kserqci826Rq2A"
genai.configure(api_key=API_KEY)

# Model Name ကို နောက်ဆုံးထွက် version ဖြစ်တဲ့ 'gemini-1.5-flash-latest' လို့ ပြင်ထားပါတယ်
llm_model = genai.GenerativeModel('gemini-1.5-flash-latest')

st.set_page_config(page_title="MM AI Video Translator", page_icon="🇲🇲")
st.title("🇲🇲 Myanmar Video AI Translator")

# Whisper Model ကို ပေါ့ပေါ့ပါးပါး ဖြစ်အောင် base သုံးထားပါတယ်
@st.cache_resource
def load_model():
    return whisper.load_model("base")

stt_model = load_model()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ (MP4, MOV, AVI)", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က ကြိုးစားပမ်းစား အလုပ်လုပ်နေပါတယ်... ခဏစောင့်ပေးပါဗျာ'):
            try:
                # ၁။ ဗီဒီယိုကို ခေတ္တသိမ်းဆည်းခြင်း
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၂။ အသံမှ စာသားပြောင်းခြင်း (Transcription)
                st.info("အဆင့် (၁): ဗီဒီယိုထဲက အင်္ဂလိပ်စကားတွေကို နားထောင်နေပါတယ်...")
                result = stt_model.transcribe(video_path)
                en_text = result['text']
                
                # ၃။ Gemini ဖြင့် မြန်မာလို အချောသပ်ရေးခြင်း (Translation)
                st.info("အဆင့် (၂): မြန်မာလို ပီပီသသ ပြန်ရေးပေးနေပါတယ်...")
                prompt = f"Please translate and rewrite the following English transcript into natural, polished, and human-like Burmese language. Make it sound like a professional narrator. Transcript: {en_text}"
                response = llm_model.generate_content(prompt)
                mm_text = response.text
                
                # ၄။ မြန်မာ AI အသံထုတ်ခြင်း (Text-to-Speech)
                st.info("အဆင့် (၃): မြန်မာ AI အသံဖိုင် ဖန်တီးနေပါတယ်...")
                output_audio = "final_voice.mp3"
                communicate = edge_tts.Communicate(mm_text, "my-MM-ThihaNeural")
                asyncio.run(communicate.save(output_audio))

                # ရလဒ်များကို ပြသခြင်း
                st.success("ဘာသာပြန်ခြင်း အောင်မြင်စွာ ပြီးဆုံးပါပြီ!")
                
                st.subheader("မြန်မာ Script (စာသား)")
                st.text_area("", mm_text, height=250)
                
                st.subheader("မြန်မာ AI အသံ")
                st.audio(output_audio)
                
                # ဒေါင်းလုဒ် ခလုတ်
                with open(output_audio, "rb") as f:
                    st.download_button("မြန်မာအသံဖိုင်ကို ဒေါင်းလုဒ်ယူရန်", f, file_name="myanmar_ai_voice.mp3")
                
                # ဖိုင်အဟောင်းကို ဖြတ်ခြင်း
                os.remove(video_path)
                
            except Exception as e:
                st.error(f"Error ဖြစ်သွားပါတယ်: {str(e)}")
