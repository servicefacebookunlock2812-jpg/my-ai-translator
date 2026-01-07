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

st.set_page_config(page_title="Premium AI Video Translator", page_icon="🎬")
st.title("🎬 Premium AI Video Translator")
st.markdown("ပိုမိုချောမွေ့သော မြန်မာဘာသာပြန်နှင့် AI အသံစနစ်ကို အသုံးပြုထားပါသည်။")

@st.cache_resource
def load_whisper():
    # နည်းနည်းပိုကောင်းအောင် 'base' model ကို ပြန်သုံးပေးထားပါတယ်
    return whisper.load_model("base")

model = load_whisper()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က အကောင်းဆုံးဖြစ်အောင် ဖန်တီးပေးနေပါတယ်...'):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                # ၁။ အသံကို စာသားပြောင်း
                st.info("အဆင့် (၁): စကားလုံးများကို တိကျအောင် နားထောင်နေပါတယ်...")
                result = model.transcribe(video_path)
                original_text = result['text']
                detected_lang = result.get('language', 'unknown')

                # ၂။ Groq Llama 3.3 နဲ့ ချောမွေ့အောင် ဘာသာပြန်ခြင်း
                st.info("အဆင့် (၂): လူသားတစ်ယောက်လို ပီပီသသ အချောသပ်ပေးနေပါတယ်...")
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional Burmese screenplayer and narrator. Translate the content into polished, human-like Burmese. Use natural spoken Burmese instead of formal bookish language. Make it sound engaging and smooth for a video narration. Only provide the final Burmese text."
                        },
                        {"role": "user", "content": f"Translate this {detected_lang} content to smooth Burmese: {original_text}"}
                    ]
                )
                mm_text = completion.choices[0].message.content
                
                # ၃။ ပိုမိုကောင်းမွန်သော မြန်မာအသံထုတ်ခြင်း
                st.info("အဆင့် (၃): သဘာဝကျသော မြန်မာ AI အသံကို ဖန်တီးနေပါတယ်...")
                output_audio = "polished_voice.mp3"
                # ZawZawNeural က ပိုပြီး သဘာဝကျပါတယ်
                communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                asyncio.run(communicate.save(output_audio))

                st.success("ဘာသာပြန်ခြင်း ပြီးပါပြီ!")
                
                st.subheader("မြန်မာ Script (အချောသပ်ပြီး)")
                st.write(mm_text)
                
                st.subheader("နားထောင်ရန် (Premium Voice)")
                st.audio(output_audio)
                
                with open(output_audio, "rb") as f:
                    st.download_button("အသံဖိုင်ကို သိမ်းဆည်းရန်", f, file_name="ai_translated_voice.mp3")
                
                os.remove(video_path)
            except Exception as e:
                st.error(f"Error: {str(e)}")
