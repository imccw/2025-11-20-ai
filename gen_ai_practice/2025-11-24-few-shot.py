import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

examples = [
    {"review": "Great quality for reasonable price. Excellent!", "sentiment": "Positive"},
    {"review": "The beans were stale and bitter. Disappointing.", "sentiment": "Negative"},
    {"review": "Standard medium roast coffee. Nothing special.", "sentiment": "Neutral"}
]

def create_analyzer():
    load_dotenv()
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=PromptTemplate(
            input_variables=["review", "sentiment"],
            template="Coffee Review: {review}\nSentiment: {sentiment}"
        ),
        prefix="""Analyze the coffee review sentiment.
Respond with ONLY ONE WORD: Positive, Negative, Mixed, or Neutral.\n\n""",
        suffix="Coffee Review: {input_text}\nSentiment:",
        input_variables=["input_text"]
    )

    return model, prompt

def analyze_review(model, prompt, review):
    return model.invoke(prompt.format(input_text=review)).content.strip()

def main():
    model, prompt = create_analyzer()
    print("Coffee Review Sentiment Analyzer (type 'quit' to exit)")

    while True:
        review = input("Enter coffee review: ").strip()

        if not review:
            continue
        if review.lower() == 'quit':
            break

        try:
            print(analyze_review(model, prompt, review))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
