import streamlit as st
import whisper
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os

# Groq Setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Universal AI Translator", page_icon="🌐")
st.title("🌐 Universal AI Video Translator")

@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")

model = load_whisper()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က အဆင့်မြင့် Model သစ်ဖြင့် ဘာသာပြန်နေပါတယ်...'):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၁။ အသံကို စာသားပြောင်း
                result = model.transcribe(video_path)
                original_text = result['text']
                detected_lang = result.get('language', 'unknown')
                
                st.write(f"🔍 သိရှိရသော ဘာသာစကား: **{detected_lang.upper()}**")

                # ၂။ Groq Llama 3.3 နဲ့ မြန်မာလို ပြန်ဆို (Model နာမည်အသစ် ပြင်ထားပါတယ်)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a professional Burmese translator. Translate the text into natural Burmese. Only provide the translation."},
                        {"role": "user", "content": f"Translate this {detected_lang} text to natural Burmese: {original_text}"}
                    ]
                )
                mm_text = completion.choices[0].message.content
                
                # ၃။ မြန်မာ AI အသံထုတ်
                output_audio = "final_voice.mp3"
                communicate = edge_tts.Communicate(mm_text, "my-MM-ThihaNeural")
                asyncio.run(communicate.save(output_audio))

                st.success("ဘာသာပြန်ခြင်း ပြီးပါပြီ!")
                st.subheader("မြန်မာ Script")
                st.write(mm_text)
                st.audio(output_audio)
                
                os.remove(video_path)
            except Exception as e:
                st.error(f"Error ဖြစ်သွားပါတယ်: {str(e)}")
