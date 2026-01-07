import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os

# Groq Setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Ultra AI Translator", page_icon="🎬")
st.title("🎬 Ultra Fast AI Video Translator")

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv', 'mp3', 'wav'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('Cloud AI က အသံကို ဖမ်းယူ ဘာသာပြန်နေပါတယ်...'):
            try:
                # ၁။ ဖိုင်ကို ယာယီသိမ်းခြင်း
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
                    tfile.write(uploaded_file.getbuffer())
                    file_path = tfile.name

                # ၂။ Groq Cloud Whisper သုံးပြီး အသံကို စာသားပြောင်းခြင်း (ဒါက FFmpeg မလိုပါဘူး)
                st.info("အဆင့် (၁): စကားလုံးများကို တိကျအောင် နားထောင်နေပါတယ်...")
                with open(file_path, "rb") as file:
                    transcription = client.audio.transcriptions.create(
                        file=(file_path, file.read()),
                        model="distil-whisper-large-v3-en", # အလွန်မြန်သော model
                        response_format="text",
                    )
                original_text = transcription.strip()

                if not original_text:
                    st.error("အသံ ရှာမတွေ့ပါဘူး။")
                else:
                    # ၃။ Groq Llama 3.3 နဲ့ ချောမွေ့အောင် ဘာသာပြန်ခြင်း
                    st.info("အဆင့် (၂): လူသားတစ်ယောက်လို ပီပီသသ အချောသပ်ပေးနေပါတယ်...")
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a professional Burmese storyteller. Translate the text into natural, smooth, spoken Burmese. Only provide the translation."},
                            {"role": "user", "content": f"Translate this: {original_text}"}
                        ]
                    )
                    mm_text = completion.choices[0].message.content
                    
                    # ၄။ မြန်မာ AI အသံထုတ်ခြင်း
                    st.info("အဆင့် (၃): သဘာဝကျသော မြန်မာအသံကို ဖန်တီးနေပါတယ်...")
                    output_audio = "final_voice.mp3"
                    communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                    asyncio.run(communicate.save(output_audio))

                    st.success("ဘာသာပြန်ခြင်း အောင်မြင်ပါတယ်!")
                    st.subheader("မြန်မာ Script")
                    st.write(mm_text)
                    st.audio(output_audio)
                
                os.remove(file_path)
            except Exception as e:
                st.error(f"Error: {str(e)}")
