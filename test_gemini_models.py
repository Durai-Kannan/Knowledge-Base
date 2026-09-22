import os
import time

from google import genai


API_KEY = os.getenv("GEMINI_API_KEY", "")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=API_KEY
)


models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]


prompt = (
    "Answer in one short sentence: "
    "Who is the CEO of Apple?"
)


print()
print("=" * 75)
print("GEMINI MODEL AVAILABILITY TEST")
print("=" * 75)


results = []


for model_name in models_to_test:

    print()
    print(f"Testing: {model_name}")
    print("-" * 75)

    start_time = time.time()

    try:

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        elapsed = time.time() - start_time

        answer = getattr(
            response,
            "text",
            None
        )

        if answer:

            print("STATUS : SUCCESS")
            print(f"TIME   : {elapsed:.2f}s")
            print(f"ANSWER : {answer.strip()}")

            results.append({
                "model": model_name,
                "status": "SUCCESS",
                "time": elapsed,
            })

        else:

            print("STATUS : EMPTY RESPONSE")

            results.append({
                "model": model_name,
                "status": "EMPTY",
                "time": elapsed,
            })

    except Exception as e:

        elapsed = time.time() - start_time

        error = str(e)

        if "404" in error:
            status = "404 - NOT AVAILABLE"

        elif "429" in error:
            status = "429 - QUOTA EXCEEDED"

        elif "503" in error:
            status = "503 - TEMPORARILY UNAVAILABLE"

        elif "403" in error:
            status = "403 - PERMISSION ERROR"

        elif "401" in error:
            status = "401 - AUTHENTICATION ERROR"

        else:
            status = "ERROR"

        print(f"STATUS : {status}")
        print(f"TIME   : {elapsed:.2f}s")
        print(f"ERROR  : {error[:300]}")

        results.append({
            "model": model_name,
            "status": status,
            "time": elapsed,
        })

    # Avoid hammering the API
    time.sleep(2)


print()
print("=" * 75)
print("SUMMARY")
print("=" * 75)

for result in results:

    print(
        f"{result['model']:35} "
        f"{result['status']:30} "
        f"{result['time']:.2f}s"
    )