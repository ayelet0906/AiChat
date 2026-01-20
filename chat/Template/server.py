"""
אפליקציה לצ'אט עם GPT בתחום מוגבל - גרסת שרת Flask
מאפשרת שיחה עם מודל AI בתחום ספציפי בלבד עם ממשק HTML
"""

import os
import secrets
import dotenv
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # מפתח סודי לניהול סשנים

# טען משתני סביבה
dotenv.load_dotenv()

# הגדרת התחום הספציפי לצ'אט
DOMAIN = "עזרה בתכנות Python"  # ניתן לשנות לכל תחום אחר

# הגדרת הוראות המערכת שמגבילות את המודל לתחום ספציפי
SYSTEM_PROMPT = f"""אתה עוזר AI שמתמחה אך ורק ב{DOMAIN}.
אל תענה על שאלות שלא קשורות ל{DOMAIN}.
אם מישהו שואל שאלה שאינה קשורה, הסבר בנימוס שאתה יכול לעזור רק בנושאים הקשורים ל{DOMAIN}."""

# משתנה סביבה ל-Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("אזהרה: לא נמצא GOOGLE_API_KEY!")
    print("אנא הגדר את משתנה הסביבה GOOGLE_API_KEY בקובץ .env")
else:
    genai.configure(api_key=GOOGLE_API_KEY)


@app.route('/')
def home():
    """עמוד הבית - ממשק הצ'אט"""
    # אתחול היסטוריית שיחה חדשה לסשן
    if 'conversation_history' not in session:
        session['conversation_history'] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    return render_template('index.html', domain=DOMAIN)


@app.route('/chat', methods=['POST'])
def chat():
    """נקודת קצה לשליחת הודעות לצ'אט"""
    if not GOOGLE_API_KEY:
        return jsonify({'error': 'שרת לא מוגדר כראוי - חסר מפתח Google AI'}), 500

    # קבלת ההודעה מהמשתמש
    data = request.json
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': 'הודעה ריקה'}), 400

    # קבלת היסטוריית השיחה מהסשן
    conversation_history = session.get('conversation_history', [
        {"role": "system", "content": SYSTEM_PROMPT}
    ])

    # הוספת הודעת המשתמש
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    try:
        # בניית פרומפט
        prompt = f"{SYSTEM_PROMPT}\n\nמשתמש: {user_message}\nעוזר:"
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        assistant_message = response.text.strip() if hasattr(response, 'text') else str(response)

        # הוספת תשובת ה-AI להיסטוריה
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # שמירת ההיסטוריה בסשן
        session['conversation_history'] = conversation_history

        return jsonify({
            'response': assistant_message
        })

    except Exception as e:
        return jsonify({
            'error': f'שגיאה בתקשורת עם Google AI: {str(e)}'
        }), 500


@app.route('/clear', methods=['POST'])
def clear_history():
    """ניקוי היסטוריית השיחה"""
    session['conversation_history'] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    return jsonify({'message': 'היסטוריית השיחה נוקתה'})


if __name__ == "__main__":
    print("=" * 60)
    print(f"שרת צ'אט AI - תחום: {DOMAIN}")
    print("=" * 60)
    print("מודל: Gemini-Pro (Google AI Studio)")
    print("פתח את הדפדפן והיכנס ל: http://localhost:5000")
    print("-" * 60)
    app.run(debug=True, port=5000)
