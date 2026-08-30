from ai.assessment import assess_answer
from core.knowledge_model import Concept


question = "What does the % operator do in Python?"

answer = "It divides two numbers."

result = assess_answer(
    subject="Python",
    question=question,
    answer=answer
)

print("\nAI ASSESSMENT")
print(result)

concept = Concept(result["concept"])

concept.update(
    score=result["score"],
    mistake=result["misconception"],
    mistake_type=result["mistake_type"]
)

print("\nUPDATED KNOWLEDGE MODEL")
print(concept.to_dict())