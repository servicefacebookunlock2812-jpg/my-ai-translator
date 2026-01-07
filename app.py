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

st.set_page_config(page_title="Pro MM AI Translator", page_icon="🎬")
st.title("🎬 High-Quality AI Video Translator")

@st.cache_resource
def load_whisper():
    # RAM မစားအောင် အပေါ့စား model ကို သုံးထားပါတယ်
    return whisper.load_model("tiny")

model = load_whisper()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က ဗီဒီယိုကို စစ်ဆေးနေပါတယ်...'):
            try:
                # ၁။ ဗီဒီယိုကို ယာယီသိမ်းခြင်း
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၂။ အသံကို တိုက်ရိုက် စာသားပြောင်းခြင်း (အသံဖမ်းစနစ်ကို ပိုကောင်းအောင် ပြင်ထားတယ်)
                st.info("အဆင့် (၁): ဗီဒီယိုထဲက စကားလုံးတွေကို နားထောင်နေပါတယ်...")
                result = model.transcribe(video_path, task="transcribe")
                original_text = result['text'].strip()

                if not original_text:
                    st.warning("ဗီဒီယိုထဲမှာ စကားပြောသံ ရှာမတွေ့ပါဘူး။ အသံပါတဲ့ ဗီဒီယိုနဲ့ ပြန်စမ်းပေးပါဗျ။")
                else:
                    detected_lang = result.get('language', 'unknown')
                    st.write(f"🔍 သိရှိရသော ဘာသာစကား: **{detected_lang.upper()}**")

                    # ၃။ Groq နဲ့ အချောဆုံး မြန်မာ Script ရေးခြင်း
                    st.info("အဆင့် (၂): လူသားတစ်ယောက်လို ချောမွေ့အောင် ပြန်ဆိုနေပါတယ်...")
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a professional Burmese translator. Translate to natural, engaging, spoken Burmese script. Only provide the translation."},
                            {"role": "user", "content": f"Translate this: {original_text}"}
                        ]
                    )
                    mm_text = completion.choices[0].message.content
                    
                    # ၄။ မြန်မာအသံထုတ်ခြင်း
                    st.info("အဆင့် (၃): သဘာဝကျသော မြန်မာအသံကို ဖန်တီးနေပါတယ်...")
                    output_audio = "final_voice.mp3"
                    # ZawZaw အသံက ပိုချောပါတယ်
                    communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                    asyncio.run(communicate.save(output_audio))

                    st.success("ဘာသာပြန်ခြင်း ပြီးပါပြီ!")
                    st.subheader("မြန်မာ Script")
                    st.write(mm_text)
                    st.audio(output_audio)
                
                os.remove(video_path)
            except Exception as e:
                st.error(f"Error: {str(e)}")
