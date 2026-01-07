import streamlit as st
import whisper
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os

# Groq Setup (ဘရိုရဲ့ Key ကို ထည့်ပေးထားပါတယ်)
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Universal AI Translator", page_icon="🌐")
st.title("🌐 Universal AI Video Translator")
st.markdown("ဗီဒီယိုထဲက ဘယ်ဘာသာစကားကိုမဆို AI က အလိုအလျောက် သိရှိပြီး မြန်မာလို အသံထွက်ပေးပါမယ်။")

@st.cache_resource
def load_whisper():
    # RAM မစားဘဲ မြန်မြန်ဆန်ဆန် အလုပ်လုပ်ဖို့ tiny model ကို သုံးထားပါတယ်
    return whisper.load_model("tiny")

model = load_whisper()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('Groq AI က အမြန်နှုန်းနဲ့ အလုပ်လုပ်နေပါတယ်...'):
            try:
                # ၁။ ဗီဒီယိုကို ခေတ္တသိမ်းခြင်း
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၂။ အသံကို စာသားပြောင်းခြင်း
                st.info("အဆင့် (၁): ဘာသာစကားကို စစ်ဆေးပြီး စာသားပြောင်းနေပါတယ်...")
                result = model.transcribe(video_path)
                original_text = result['text']
                detected_lang = result.get('language', 'unknown')
                
                st.write(f"🔍 သိရှိရသော ဘာသာစကား: **{detected_lang.upper()}**")

                # ၃။ Groq Llama 3 နဲ့ မြန်မာလို ပြန်ဆိုခြင်း
                st.info("အဆင့် (၂): မြန်မာလို ပီပီသသ ပြန်ဆိုနေပါတယ်...")
                completion = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": "You are a professional Burmese translator. Translate the text into natural, professional Burmese. Only provide the translation text without any notes."},
                        {"role": "user", "content": f"Translate this {detected_lang} text to natural Burmese: {original_text}"}
                    ]
                )
                mm_text = completion.choices[0].message.content
                
                # ၄။ မြန်မာ AI အသံထုတ်ခြင်း
                st.info("အဆင့် (၃): မြန်မာ AI အသံဖိုင် ဖန်တီးနေပါတယ်...")
                output_audio = "final_voice.mp3"
                communicate = edge_tts.Communicate(mm_text, "my-MM-ThihaNeural")
                asyncio.run(communicate.save(output_audio))

                st.success("ဘာသာပြန်ခြင်း အောင်မြင်ပါတယ်!")
                st.subheader("မြန်မာ Script (စာသား)")
                st.write(mm_text)
                
                st.subheader("မြန်မာ AI အသံ")
                st.audio(output_audio)
                
                with open(output_audio, "rb") as f:
                    st.download_button("အသံဖိုင်ကို ဒေါင်းလုဒ်ယူရန်", f, file_name="ai_translated_voice.mp3")
                
                os.remove(video_path)
                
            except Exception as e:
                st.error(f"Error ဖြစ်သွားပါတယ်: {str(e)}")
