import os
from openai import OpenAI

class AITools:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")
                self.client = None

    def _call_openai(self, system_prompt, user_prompt):
        if not self.client:
            return "AI features are currently unavailable because the OpenAI API key is missing or invalid."

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return "Sorry, I encountered an error while processing your request."

    def solve_doubt(self, question):
        system_prompt = "You are a friendly and helpful tutor. Explain this concept in very simple words for a school student. If it's a math question, give a step-by-step solution."
        return self._call_openai(system_prompt, question)

    def study_chatbot(self, message):
        system_prompt = "You are a friendly AI tutor for ASWATHAMA CLASSES. You help students with concept doubts, exam preparation, and study tips."
        return self._call_openai(system_prompt, message)

    def analyze_attendance(self, attendance_data_str):
        system_prompt = "You are an AI assistant helping a teacher. Analyze attendance data and provide insights. State which students are irregular, calculate attendance percentage if possible, and suggest actions."
        return self._call_openai(system_prompt, f"Here is the recent attendance data:\n{attendance_data_str}")

    def summarize_video(self, topic):
        system_prompt = "You are an AI study assistant. Generate summary notes for revision based on the video topic provided. Include a summary and key points."
        return self._call_openai(system_prompt, f"Video topic: {topic}")

    def generate_quiz(self, subject, topic):
        system_prompt = "You are an AI teacher. Generate 5 MCQ questions with answers for the given subject and topic. Format clearly."
        return self._call_openai(system_prompt, f"Subject: {subject}\nTopic: {topic}")

    def generate_announcement(self, prompt):
        system_prompt = "You are an AI assistant for a coaching class. Write a professional coaching class announcement based on the prompt."
        return self._call_openai(system_prompt, prompt)

ai = AITools()
