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

st.set_page_config(page_title="Premium MM AI Translator", page_icon="🎬")
st.title("🎬 Premium AI Video Translator")

@st.cache_resource
def load_whisper():
    # ပိုတိကျအောင် 'base' model ကို သုံးပါမယ်
    return whisper.load_model("base")

model = load_whisper()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('အကောင်းဆုံးဖြစ်အောင် ဖန်တီးပေးနေပါတယ်...'):
            try:
                # ၁။ ဗီဒီယို သိမ်းဆည်းခြင်း
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၂။ အသံဖမ်းယူခြင်း (Whisper)
                st.info("အဆင့် (၁): ဗီဒီယိုထဲက စကားလုံးတွေကို နားထောင်နေပါတယ်...")
                result = model.transcribe(video_path, fp16=False) # Error ကာကွယ်ဖို့ fp16=False ထည့်ထားတယ်
                original_text = result['text'].strip()

                if not original_text:
                    st.error("ဗီဒီယိုထဲမှာ စကားပြောသံ ရှာမတွေ့ပါဘူး။ တခြားဗီဒီယိုနဲ့ ပြန်စမ်းကြည့်ပေးပါဗျ။")
                else:
                    detected_lang = result.get('language', 'unknown')
                    st.write(f"🔍 သိရှိရသော ဘာသာစကား: **{detected_lang.upper()}**")

                    # ၃။ Groq Llama 3.3 နဲ့ ချောမွေ့အောင် ဘာသာပြန်ခြင်း
                    st.info("အဆင့် (၂): လူသားတစ်ယောက်လို ပီပီသသ အချောသပ်ပေးနေပါတယ်...")
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a professional Burmese storyteller. Translate the text into polished, natural-sounding Burmese narration. Avoid formal book language; use engaging spoken Burmese. Only provide the translation."
                            },
                            {"role": "user", "content": f"Translate this to smooth Burmese: {original_text}"}
                        ]
                    )
                    mm_text = completion.choices[0].message.content
                    
                    # ၄။ မြန်မာအသံထုတ်ခြင်း (Edge TTS)
                    st.info("အဆင့် (၃): သဘာဝကျသော မြန်မာ AI အသံကို ဖန်တီးနေပါတယ်...")
                    output_audio = "voice_final.mp3"
                    communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                    asyncio.run(communicate.save(output_audio))

                    st.success("ဘာသာပြန်ခြင်း အောင်မြင်ပါတယ်!")
                    st.subheader("မြန်မာ Script")
                    st.write(mm_text)
                    st.audio(output_audio)
                    
                    with open(output_audio, "rb") as f:
                        st.download_button("အသံဖိုင် သိမ်းရန်", f, file_name="ai_translated.mp3")
                
                os.remove(video_path)
            except Exception as e:
                st.error(f"Error: {str(e)}")
