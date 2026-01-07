import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os

# Groq Setup (Latest Model)
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Pro Narrator AI", page_icon="🎙️")
st.title("🎙️ Professional Narrator AI Translator")

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က ဇာတ်ကြောင်းပြောသူတစ်ယောက်လို ဖန်တီးပေးနေပါတယ်...'):
            try:
                # ၁။ ဖိုင်ကို ယာယီသိမ်းခြင်း
                file_ext = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tfile:
                    tfile.write(uploaded_file.getbuffer())
                    temp_path = tfile.name

                # ၂။ အသံဖမ်းခြင်း (Whisper-v3 ကို သုံးထားလို့ Error ကင်းပါတယ်)
                st.info("အဆင့် (၁): အသံကို တိကျအောင် နားထောင်နေပါတယ်...")
                with open(temp_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=(temp_path, audio_file.read()),
                        model="whisper-large-v3",
                        response_format="text",
                    )
                original_text = transcription.strip()

                if not original_text:
                    st.error("အသံဖမ်းယူ၍ မရပါ။")
                else:
                    # ၃။ ချောမွေ့သော Narrator Script ရေးခြင်း
                    st.info("အဆင့် (၂): ဇာတ်ကြောင်းပြောဟန်ဖြင့် အချောသပ်နေပါတယ်...")
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a professional movie narrator. Translate to natural, engaging, and smooth spoken Burmese speech. Do not use book language. Output only the translation."},
                            {"role": "user", "content": f"Translate this into a smooth narrator script: {original_text}"}
                        ]
                    )
                    mm_text = completion.choices[0].message.content
                    
                    # ၄။ မြန်မာအသံထုတ် (ZawZaw အသံက အပီပြင်ဆုံးပါ)
                    st.info("အဆင့် (၃): သဘာဝကျသော အသံကို ဖန်တီးနေပါတယ်...")
                    output_audio = "final_narrator.mp3"
                    communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                    asyncio.run(communicate.save(output_audio))

                    st.success("ဘာသာပြန်ခြင်း အောင်မြင်ပါတယ်!")
                    st.subheader("မြန်မာ Narrator Script")
                    st.write(mm_text)
                    st.audio(output_audio)
                
                os.remove(temp_path)
            except Exception as e:
                st.error(f"Error: {str(e)}")
