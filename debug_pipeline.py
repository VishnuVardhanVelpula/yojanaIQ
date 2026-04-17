from rag import answer_query
import json

with open('data/ragas_testset.json') as f:
    test = json.load(f)

q = test[0]
result = answer_query(q['user_profile'], q['question'])

print("Total chunks:", len(result['retrieved_chunks']))
print("Sources:", result['retrieval_sources'])
print()
for i, c in enumerate(result['retrieved_chunks']):
    print(f"Chunk {i+1}: {c.get('id','?')} | source={c.get('source','?')} | rerank={c.get('rerank_score','not set')}")
