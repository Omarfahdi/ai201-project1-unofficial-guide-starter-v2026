"""Checks criterion 4 over every chunk in the index."""
import chromadb
client = chromadb.PersistentClient(path="chroma_db")
for col in client.list_collections():
    name = col if isinstance(col, str) else col.name
    docs = client.get_collection(name).get(include=["documents", "metadatas"])
    texts, metas = docs["documents"], docs["metadatas"]
    lens = [len(t) for t in texts]
    bad_len = [(m, l) for m, l in zip(metas, lens) if not 200 <= l <= 1200]
    bad_head = [m for m, t in zip(metas, texts) if " — " not in t.splitlines()[0]]
    print(f"{name}: {len(texts)} chunks, min {min(lens)}, max {max(lens)}")
    print(f"  outside 200-1200: {len(bad_len)}", bad_len[:10])
    print(f"  first line missing 'Guide — Section': {len(bad_head)}", bad_head[:10])
