import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os

# Groq Setup (ဘရိုရဲ့ Key နဲ့ Model အသစ်ကို သေချာထည့်ထားပါတယ်)
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Pro Narrator AI", page_icon="🎙️")
st.title("🎙️ Professional Narrator AI Translator")
st.markdown("ဗီဒီယိုထဲက ဘာသာစကားကို လူသားတစ်ယောက်လို ချောမွေ့စွာ ပြန်ဆိုပေးပါသည်။")

uploaded_file = st.file_uploader("ဗီဒီယို (သို့) အသံဖိုင် တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv', 'mp3', 'wav'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က ဇာတ်ကြောင်းပြောသူတစ်ယောက်လို ဖန်တီးပေးနေပါတယ်...'):
            try:
                # ၁။ ဖိုင်ကို ယာယီသိမ်းခြင်း (FFmpeg Error ကင်းစေရန် Cloud စနစ်သုံးပါမည်)
                file_ext = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tfile:
                    tfile.write(uploaded_file.getbuffer())
                    temp_path = tfile.name

                # ၂။ Groq Cloud Whisper သုံးပြီး အသံကို စာသားပြောင်းခြင်း
                # (ဒီနည်းက အသံမရတဲ့ Error ကို ကျိန်းသေဖြေရှင်းပေးပါတယ်)
                st.info("အဆင့် (၁): စကားလုံးများကို တိကျအောင် နားထောင်နေပါတယ်...")
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

                    # ၃။ Narrator Script ရေးခြင်း (ပိုမိုချောမွေ့သော Prompt သုံးထားသည်)
                    st.info("အဆင့် (၂): ဇာတ်ကြောင်းပြောဟန်ဖြင့် အချောသပ်နေပါတယ်...")
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a top-tier Burmese documentary narrator. Translate the input into natural, engaging, and professional spoken Burmese narration. Use flowy, human-like language. Avoid formal book Burmese. Output ONLY the Burmese translation."
                            },
                            {"role": "user", "content": f"Translate this {detected_lang} into a smooth Burmese narrator script: {original_text}"}
                        ]
                    )
                    mm_text = completion.choices[0].message.content
                    
                    # ၄။ မြန်မာ AI အသံထုတ်ခြင်း (ZawZawNeural က အချောမွေ့ဆုံးပါ)
                    st.info("အဆင့် (၃): သဘာဝကျသော မြန်မာအသံကို ဖန်တီးနေပါတယ်...")
                    output_audio = "final_narrator.mp3"
                    communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                    asyncio.run(communicate.save(output_audio))

                    st.success("ဘာသာပြန်ခြင်း အောင်မြင်ပါတယ်!")
                    st.subheader("မြန်မာ Narrator Script")
                    st.text_area("", mm_text, height=250)
                    
                    st.subheader("နားထောင်ရန် (ZawZaw Voice)")
                    st.audio(output_audio)
                
                os.remove(temp_path)
            except Exception as e:
                st.error(f"Error ဖြစ်သွားပါတယ်: {str(e)}")
