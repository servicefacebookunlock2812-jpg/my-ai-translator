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

st.set_page_config(page_title="Pro AI Translator", page_icon="🎙️")
st.title("🎙️ Professional AI Video Translator")

@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")

model = load_whisper()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က Narrator တစ်ယောက်လို ဖန်တီးပေးနေပါတယ်...'):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၁။ အသံကို စာသားပြောင်း (FFmpeg ရှိမှ အလုပ်လုပ်မှာပါ)
                st.info("အဆင့် (၁): အသံကို နားထောင်နေပါတယ်...")
                result = model.transcribe(video_path)
                original_text = result['text']
                detected_lang = result.get('language', 'unknown')
                
                # ၂။ Narrator ပုံစံ ချောမွေ့အောင် ဘာသာပြန်ခြင်း
                st.info("အဆင့် (၂): ဇာတ်ကြောင်းပြောဟန်ဖြင့် အချောသပ်နေပါတယ်...")
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional movie narrator. Translate the input into very smooth, natural Burmese speech. Use engaging spoken Burmese instead of book language. Make it sound like a storyteller. Only output the translation."
                        },
                        {"role": "user", "content": f"Translate this {detected_lang} to smooth Burmese: {original_text}"}
                    ]
                )
                mm_text = completion.choices[0].message.content
                
                # ၃။ မြန်မာအသံထုတ် (ZawZawNeural က ပိုချောပါတယ်)
                st.info("အဆင့် (၃): သဘာဝကျသော အသံကို ဖန်တီးနေပါတယ်...")
                output_audio = "narrator_voice.mp3"
                communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                asyncio.run(communicate.save(output_audio))

                st.success("ဘာသာပြန်ခြင်း ပြီးပါပြီ!")
                st.subheader("မြန်မာ Script (အချောသပ်ပြီး)")
                st.write(mm_text)
                st.audio(output_audio)
                
                os.remove(video_path)
            except Exception as e:
                st.error(f"Error: {str(e)}")
