import streamlit as st
import whisper
from groq import Groq
import edge_tts
import asyncio
import tempfile
import os

# Groq Setup - မင်း API key ကို environment variable က ယူမယ်
import os
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="AI Video/အသံဘာသာပြန်", page_icon="🌐")

st.title("🌐 AI စက်ဘာသာပြန်")
st.markdown("**ဗီဒီယို/အသံဖိုင်ထဲက စကားသံများကို မြန်မာလို ပြန်ဆိုပေးမည်**")

# Simple loading function
@st.cache_resource
def load_model():
    try:
        # Use tiny model for faster loading
        model = whisper.load_model("tiny")
        return model
    except Exception as e:
        st.error(f"Model ဖွင့်ရာတွင် အမှား: {str(e)}")
        return None

model = load_model()

# File uploader
uploaded_file = st.file_uploader("ဖိုင်တင်ရန်", type=['mp4', 'mp3', 'wav', 'm4a'])

if uploaded_file is not None:
    st.success(f"ဖိုင်တင်ပြီး: {uploaded_file.name}")
    
    # Show file info
    file_size = uploaded_file.size / (1024*1024)  # MB
    st.info(f"ဖိုင်အရွယ်အစား: {file_size:.2f} MB")
    
    if st.button("🚀 ဘာသာပြန်စမယ်"):
        with st.spinner('စကားသံများကို ဖော်ထုတ်နေပါသည်...'):
            try:
                # 1. Save uploaded file to temp
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    input_path = tmp_file.name
                
                # 2. Transcribe with Whisper
                if model:
                    result = model.transcribe(input_path)
                    original_text = result.get('text', '')
                    detected_lang = result.get('language', 'unknown')
                    
                    if original_text:
                        st.success(f"✅ စကားသံဖော်ထုတ်ပြီး | ဘာသာစကား: {detected_lang}")
                        
                        # Show original text
                        with st.expander("📝 မူရင်းစကားများ"):
                            st.write(original_text[:1000] + "..." if len(original_text) > 1000 else original_text)
                        
                        # 3. Translate with Groq
                        with st.spinner('မြန်မာလို ဘာသာပြန်နေပါသည်...'):
                            try:
                                completion = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": "မင်းက professional ဘာသာပြန်ဆရာဖြစ်ပြီး ဗီဒီယိုထဲက စကားသံများကို မြန်မာလို သဘာဝကျကျ ပြန်ပေးရမယ်။ ရုပ်ရှင်ထဲမှာ ပြောသလို ပြန်ပေးပါ။"
                                        },
                                        {
                                            "role": "user",
                                            "content": f"ဒီစကားကို မြန်မာလို သဘာဝကျကျ ပြန်ပေးပါ: {original_text}"
                                        }
                                    ],
                                    temperature=0.7,
                                    max_tokens=2000
                                )
                                
                                translated_text = completion.choices[0].message.content
                                
                                st.success("✅ ဘာသာပြန်ပြီးပါပြီ")
                                
                                # Show translated text
                                st.subheader("🇲🇲 မြန်မာပြန်")
                                st.text_area("ဘာသာပြန်ထားသော စာသား", 
                                           translated_text[:1500] + "..." if len(translated_text) > 1500 else translated_text,
                                           height=200)
                                
                                # 4. Generate Burmese TTS
                                with st.spinner('မြန်မာအသံထုတ်နေပါသည်...'):
                                    try:
                                        output_file = "burmese_output.mp3"
                                        communicate = edge_tts.Communicate(
                                            text=translated_text[:2000],  # Limit text length
                                            voice="my-MM-ThihaNeural",
                                            rate="+5%"
                                        )
                                        asyncio.run(communicate.save(output_file))
                                        
                                        # Show audio player
                                        st.subheader("🔊 မြန်မာအသံ")
                                        st.audio(output_file)
                                        
                                        # Download button
                                        with open(output_file, "rb") as f:
                                            st.download_button(
                                                label="📥 အသံဖိုင်ဒေါင်းလုဒ်",
                                                data=f,
                                                file_name="burmese_translation.mp3",
                                                mime="audio/mp3"
                                            )
                                        
                                        # Cleanup
                                        os.remove(output_file)
                                        
                                    except Exception as tts_error:
                                        st.warning(f"အသံထုတ်ရာတွင် အခက်အခဲ: {str(tts_error)}")
                                        st.info("စာသားကိုတော့ ရပါပြီ။ အသံထုတ်ဖို့ နောက်မှ ထပ်ကြိုးစားကြည့်ပါ။")
                                
                            except Exception as translate_error:
                                st.error(f"ဘာသာပြန်ရာတွင် အမှား: {str(translate_error)}")
                    
                    else:
                        st.warning("စကားသံ မတွေ့ပါ။ ဖိုင်ထဲမှာ စကားပြောသံပါသလား စစ်ဆေးပါ။")
                
                # Cleanup temp file
                if os.path.exists(input_path):
                    os.remove(input_path)
                    
            except Exception as e:
                st.error(f"အမှားတစ်ခုဖြစ်နေပါသည်: {str(e)}")
                st.info("ကျေးဇူးပြု၍ နောက်တစ်ကြိမ် ထပ်စမ်းကြည့်ပါ။")

# Add instructions
st.markdown("---")
st.markdown("""
### 📋 အသုံးပြုနည်း:
1. **ဗီဒီယို (MP4) သို့မဟုတ် အသံဖိုင် (MP3, WAV) တင်ပါ**
2. **"ဘာသာပြန်စမယ်" ခလုတ်ကို နှိပ်ပါ**
3. **စကားသံဖော်ထုတ်ခြင်း၊ ဘာသာပြန်ခြင်း၊ အသံထုတ်ခြင်း အဆင့်ဆင့်ကို စောင့်ပါ**
4. **မြန်မာစာသားနှင့် အသံဖိုင်ကို ရယူပါ**

### ⚠️ သိထားသင့်သည်များ:
- **Whisper model ကို တပ်ဆင်ရန် ၂-၃ မိနစ်ကြာနိုင်ပါသည်**
- **ပထမဆုံးအကြိမ် run တိုင်း model download လုပ်ရနိုင်သည်**
- **ဖိုင်အရွယ်အစား 50MB အောက်သာ အကြံပြုပါသည်**
- **အင်တာနက် ကောင်းမွန်စွာ ချိတ်ဆက်ထားပါ**
""")

# Fix for Streamlit Cloud deployment
st.markdown("---")
st.markdown("*Streamlit Cloud တွင် deploy လုပ်ရန် အောက်ပါအတိုင်း ပြင်ဆင်ပါ*")
st.code("""
# မင်း၏ Streamlit Cloud deployment settings:
1. requirements.txt ကို အထက်ပါအတိုင်း သေချာရေးပါ
2. packages.txt ဖိုင်ကို ဖန်တီးပြီး ffmpeg ထည့်ပါ
3. Secrets တွင် GROQ_API_KEY ထည့်ပါ (optional)
4. Deploy လုပ်ပါ
""")
