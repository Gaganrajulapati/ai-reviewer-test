import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_code(filename, diff, full_content):
    """
    Sends the code to the AI.
    Advanced Feature: We send the FULL file content for context,
    but ask it to focus its review on the specific DIFF.
    """
    
    system_prompt = """
    You are a Senior Principal Engineer at a FAANG company.
    Your job is to review Pull Requests.
    
    You have two inputs:
    1. The FULL FILE content (for context).
    2. The GIT DIFF (the specific changes).
    
    Rules:
    1. Only flag CRITICAL issues (Security, Performance, Major Logic Bugs).
    2. Ignore formatting/style (PEP8, etc.).
    3. If the code is good, return an empty list.
    4. You MUST return a valid JSON object with a key "reviews".
    
    Output Format:
    {
        "reviews": [
            {
                "line": <line_number_in_diff>,
                "issue": "<concise_description>",
                "fix": "<suggested_code_snippet>",
                "severity": "high/medium"
            }
        ]
    }
    """

    user_message = f"""
    FILENAME: {filename}
    
    === FULL FILE CONTEXT ===
    {full_content}
    
    === GIT DIFF (CHANGES) ===
    {diff}
    
    Review the changes in the DIFF using the context from the FULL FILE.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use gpt-4o for better results if budget allows
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}  # This ensures we get pure JSON
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}