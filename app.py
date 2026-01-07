import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os

# Groq Setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Pro AI Video Translator", page_icon="🎙️")
st.title("🎙️ Professional AI Video Translator")
st.markdown("ဗီဒီယိုထဲက ဘာသာစကားကို Narrator တစ်ယောက်လို ချောမွေ့စွာ ပြန်ဆိုပေးပါသည်။")

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv', 'mp3'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က နောက်ခံစကားပြောသူတစ်ယောက်လို ဖန်တီးပေးနေပါတယ်...'):
            try:
                # ၁။ ဖိုင်ကို ယာယီသိမ်းခြင်း
                file_ext = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tfile:
                    tfile.write(uploaded_file.getbuffer())
                    temp_path = tfile.name

                # ၂။ Groq Cloud သုံးပြီး အသံကို စာသားပြောင်းခြင်း (Error ကင်းပြီး ပိုတိကျပါတယ်)
                st.info("အဆင့် (၁): အသံကို တိကျအောင် နားထောင်နေပါတယ်...")
                with open(temp_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=(temp_path, audio_file.read()),
                        model="whisper-large-v3",
                        response_format="verbose_json",
                    )
                
                original_text = transcription.text.strip()
                detected_lang = transcription.language

                if not original_text:
                    st.error("ဗီဒီယိုထဲမှာ အသံရှာမတွေ့ပါ။")
                else:
                    st.write(f"🔍 သိရှိရသော ဘာသာစကား: **{detected_lang.upper()}**")

                    # ၃။ Narrator Script ရေးခြင်း
                    st.info("အဆင့် (၂): နောက်ခံစကားပြောဟန်ဖြင့် အချောသပ်နေပါတယ်...")
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a professional Burmese documentary narrator. Translate the text into engaging, smooth, and natural spoken Burmese. Use expressive language that sounds like a human storyteller. Avoid formal or robotic book language. Output only the Burmese translation."
                            },
                            {"role": "user", "content": f"Translate this {detected_lang} text into a smooth Burmese narration: {original_text}"}
                        ]
                    )
                    mm_text = completion.choices[0].message.content
                    
                    # ၄။ မြန်မာ AI အသံထုတ်ခြင်း (ZawZaw က အချောဆုံးပါ)
                    st.info("အဆင့် (၃): သဘာဝကျသော မြန်မာအသံကို ဖန်တီးနေပါတယ်...")
                    output_audio = "narrator_voice.mp3"
                    communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                    asyncio.run(communicate.save(output_audio))

                    st.success("ဘာသာပြန်ခြင်း အောင်မြင်ပါတယ်!")
                    st.subheader("မြန်မာ Narrator Script")
                    st.text_area("", mm_text, height=250)
                    
                    st.subheader("မြန်မာ AI အသံ (Professional Voice)")
                    st.audio(output_audio)
                
                os.remove(temp_path)
            except Exception as e:
                st.error(f"Error အသေးစိတ်: {str(e)}")
