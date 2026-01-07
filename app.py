import streamlit as st
import whisper
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os
from moviepy.editor import VideoFileClip

# Groq Setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Pro MM AI Translator", page_icon="🎬")
st.title("🎬 High-Quality AI Video Translator")

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

uploaded_file = st.file_uploader("ဗီဒီယို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("စတင် ဘာသာပြန်ပါ"):
        with st.spinner('AI က အသံကို သေချာဖတ်ပြီး အချောသပ်နေပါတယ်...'):
            video_path = "temp_video.mp4"
            audio_path = "temp_audio.mp3"
            try:
                # ၁။ ဗီဒီယို သိမ်းပြီး အသံကို သီးသန့်ထုတ်ယူခြင်း
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.info("အဆင့် (၁): ဗီဒီယိုထဲက အသံကို ကြည်လင်အောင် ဖမ်းယူနေပါတယ်...")
                video = VideoFileClip(video_path)
                video.audio.write_audiofile(audio_path, logger=None)
                video.close()

                # ၂။ အသံကို စာသားပြောင်းခြင်း
                st.info("အဆင့် (၂): စကားလုံးများကို တိကျအောင် နားထောင်နေပါတယ်...")
                result = model.transcribe(audio_path, fp16=False)
                original_text = result['text'].strip()

                if not original_text:
                    st.error("ဗီဒီယိုထဲမှာ စကားပြောသံ လုံးဝ ရှာမတွေ့ပါဘူး။")
                else:
                    # ၃။ Groq နဲ့ အကောင်းဆုံး မြန်မာ Script ရေးခြင်း
                    st.info("အဆင့် (၃): စာသားကို ရုပ်ရှင်နောက်ခံစကားပြောဟန်ဖြင့် အချောသပ်နေပါတယ်...")
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a professional Burmese movie scriptwriter. Translate the text into very smooth, natural, and engaging spoken Burmese. Avoid bookish language. Make it sound like a real person talking in a video. Only output the translated Burmese text."},
                            {"role": "user", "content": f"Translate this perfectly: {original_text}"}
                        ]
                    )
                    mm_text = completion.choices[0].message.content
                    
                    # ၄။ မြန်မာ AI အသံထုတ်ခြင်း
                    st.info("အဆင့် (၄): သဘာဝကျသော မြန်မာအသံကို ဖန်တီးနေပါတယ်...")
                    output_audio = "final_output.mp3"
                    communicate = edge_tts.Communicate(mm_text, "my-MM-ZawZawNeural")
                    asyncio.run(communicate.save(output_audio))

                    st.success("ဘာသာပြန်ခြင်း အောင်မြင်စွာ ပြီးဆုံးပါပြီ!")
                    st.subheader("မြန်မာ Script")
                    st.write(mm_text)
                    st.audio(output_audio)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                # ဖိုင်အဟောင်းများ ရှင်းလင်းခြင်း
                if os.path.exists(video_path): os.remove(video_path)
                if os.path.exists(audio_path): os.remove(audio_path)
