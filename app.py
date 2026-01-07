import streamlit as st
import whisper
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os
import re
from pydub import AudioSegment
from pydub.silence import split_on_silence

# Groq Setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Universal AI Translator", page_icon="🌐")
st.title("🌐 Universal AI Video Translator")
st.markdown("**Video ထဲက လူတွေပြောတဲ့စကားကို တိုက်ရိုက် မြန်မာလို ပြန်ပေးမယ်**")

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

def extract_audio_from_video(video_path, audio_path="temp_audio.wav"):
    """Video ကနေ audio ထုတ်ယူခြင်း"""
    try:
        video = AudioSegment.from_file(video_path)
        video.export(audio_path, format="wav")
        return audio_path
    except Exception as e:
        st.error(f"Audio ထုတ်ယူရာတွင် error: {str(e)}")
        return None

def clean_translated_text(text):
    """မြန်မာစာသားကို သန့်ရှင်းပေးခြင်း"""
    # စာကြောင်းတွေကို သပ်သပ်ရပ်ရပ် ဖြစ်အောင်
    text = re.sub(r'([။?!])', r'\1\n', text)
    # အပိုစာလုံးများဖယ်ရှား
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

uploaded_file = st.file_uploader("ဗီဒီယို ဖိုင်ကို တင်ပေးပါ", type=['mp4', 'mov', 'avi', 'mkv', 'mp3', 'wav'])

if uploaded_file is not None:
    if st.button("🎤 Video ထဲက စကားသံကို မြန်မာလို ပြန်ပေးမယ်"):
        with st.spinner('Video ထဲက စကားသံတွေကို နားထောင်ပြီး မြန်မာလို ပြန်နေပါတယ်...'):
            try:
                # Temporary file သိမ်းခြင်း
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name

                st.info("📹 Video ဖိုင်ကို ဖွင့်နေပါတယ်...")
                
                # ၁။ Video ကနေ audio ထုတ်ယူ
                audio_path = extract_audio_from_video(video_path)
                if not audio_path:
                    st.error("Audio ထုတ်ယူ၍မရပါ")
                    return
                
                st.info("👂 Video ထဲက စကားသံတွေကို နားထောင်နေပါတယ်...")
                
                # ၂။ Whisper နဲ့ တိုက်ရိုက် transcription
                result = model.transcribe(
                    audio_path,
                    language=None,  # Auto detect language
                    task="transcribe",
                    verbose=True
                )
                
                original_text = result['text']
                detected_lang = result.get('language', 'unknown').upper()
                
                st.success(f"✅ ဘာသာစကားတွေ့ရှိပြီ: **{detected_lang}**")
                
                with st.expander("🔍 မူရင်းစကားသံများ (Original Audio Text)"):
                    st.write(original_text)
                
                # ၃။ မြန်မာလို တိုက်ရိုက် ဘာသာပြန်
                st.info("🌐 မြန်မာလို ဘာသာပြန်နေပါတယ်...")
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": """မင်းက professional ဘာသာပြန်ဆရာဖြစ်တယ်။ 
                        Video ထဲက လူတွေပြောနေတဲ့ စကားသံကို မြန်မာလိုပြန်ပေးရမယ်။
                        
                        **သတိထားရမယ့်အချက်များ:**
                        1. **တိုက်ရိုက်ပြန်ရမယ်** - လူတွေပြောသလိုပဲ ပြန်ရမယ်
                        2. **နေရာဒေသကိုက်ညီအောင်** - မြန်မာပြည်မှာ သုံးနေကျစကားလုံးတွေသုံးရမယ်
                        3. **သဘာဝကျအောင်** - စာရေးသလိုမဟုတ်ဘဲ စကားပြောသလိုပြန်ရမယ်
                        4. **အသံထွက်လွယ်အောင်** - TTS နဲ့ပြောတဲ့အခါ အဆင်ပြေအောင်
                        
                        **ဥပမာ:**
                        - "Hello, how are you?" → "ဟေ့လို၊ နေကောင်းလား?"
                        - "I need to go to the market" → "ဈေးကိုသွားဖို့လိုတယ်"
                        - "This is very important" → "ဒါက အရမ်းအရေးကြီးတယ်"
                        
                        ဘာသာပြန်ချက်တစ်ခုတည်းကိုပဲပေးပါ။"""},
                        
                        {"role": "user", "content": f"""ဒီ {detected_lang} စကားသံကို မြန်မာလို တိုက်ရိုက်ပြန်ပေးပါ။ 
                        လူတွေပြောနေတဲ့ စကားသံအတိုင်း သဘာဝကျကျပြန်ပေးပါ။
                        
                        စကားသံ: "{original_text}"
                        
                        မြန်မာလို ဘာသာပြန်ချက်:"""}
                    ],
                    temperature=0.8,  # နည်းနည်းပိုဖန်တီးနိုင်အောင်
                    max_tokens=2000
                )
                
                mm_text = completion.choices[0].message.content
                mm_text = clean_translated_text(mm_text)
                
                st.success("✅ ဘာသာပြန်ပြီးပါပြီ!")
                
                # ၄။ မြန်မာအသံထုတ်ခြင်း (TTS)
                st.info("🗣️ မြန်မာအသံထွက်နေပါတယ်...")
                
                output_audio = "burmese_translation.mp3"
                
                # Voice setting ကို ပိုသဘာဝကျအောင်လုပ်ခြင်း
                communicate = edge_tts.Communicate(
                    text=mm_text,
                    voice="my-MM-ThihaNeural",
                    rate="+8%",      # နည်းနည်းမြန်အောင်
                    pitch="+1Hz",    # သဘာဝကျအောင်
                    volume="+0%"     # အသံအတိုင်း
                )
                
                asyncio.run(communicate.save(output_audio))
                
                # ၅။ ရလဒ်များပြသခြင်း
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🇲🇲 မြန်မာစာသား")
                    st.text_area("ဘာသာပြန်ထားသော စာသား", mm_text, height=250, label_visibility="collapsed")
                
                with col2:
                    st.subheader("🔊 မြန်မာအသံ")
                    st.audio(output_audio, format="audio/mp3")
                    
                    # Download button
                    with open(output_audio, "rb") as f:
                        st.download_button(
                            label="📥 အသံဖိုင်ဒေါင်းလုဒ်",
                            data=f,
                            file_name="video_dialogue_burmese.mp3",
                            mime="audio/mp3"
                        )
                
                # ၆။ Cleanup
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                if os.path.exists(output_audio):
                    os.remove(output_audio)
                    
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ အမှားတစ်ခုဖြစ်နေပါတယ်: {str(e)}")
                st.info("ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ထပ်စမ်းကြည့်ပါ။")

st.markdown("---")
st.markdown("""
### 📋 သိထားသင့်သည်များ:
1. **Video ထဲက လူစကားသံကိုပဲ ဘာသာပြန်ပေးမည်**
2. **အသံရှင်းလျှင် ပိုကောင်းပါသည်**
3. **တစ်ကြိမ်တည်း 5 မိနစ်အောက် video ကိုသာ အကြံပြုပါသည်**
4. **ဘာသာစကားအားလုံးကို မြန်မာလိုပြန်ပေးမည်**
""")
