# 🚀 How to Run JEC Buddy

Follow these steps to start your project. All components (NLP, Backend, and Frontend) are now verified and working.

## 1. Start MongoDB
Ensure MongoDB is running on your machine.
- **Connection String**: `mongodb://127.0.0.1:27017/jec_buddy`
- *Note: The backend will crash if MongoDB is not started.*

## 2. Start the Backend
Open a new terminal and run:
```powershell
cd backend
npm install
npm run dev
```
**Verification**: You should see:
- `🚀 JEC Buddy backend running on http://127.0.0.1:5000`
- `✅ MongoDB connected: 127.0.0.1`

## 3. Start the Frontend
Open another new terminal and run:
```powershell
cd Frontend
npm install
npm run dev
```
**Verification**: You should see:
- `VITE v8.0.x ready`
- `➜  Local:   http://localhost:5173/`

## 4. Test the Chatbot
1. Open your browser to **http://localhost:5173/**.
2. Type a message like "What is the admission process?".
3. The chatbot should respond using the AI model I fixed.

---

### Key Information
- **NLP Logic**: Located in `nlp/chatbot_improved.py` (Fixed and verified).
- **Intents Data**: `nlp/college_intents.json`.
- **Environment**: Backend and Frontend have `.env` files for configuration.
