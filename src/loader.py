import os
import json
from docx import Document
from pypdf import PdfReader


class GlamourBotLoader:
    """
    GlamourBot Data Loader - No LangChain Required!

    Files:
        File 1: FAQ Questions Dataset.docx
        File 2: faqs.json
        File 3: Glamourbot.dataset.pdf
        File 4: MasterKB.json
        File 5: metadata.json
        File 6: Questions Dataset.docx
    """

    def load_docx(self, path: str, source_name: str = "") -> list[dict]:
        if not os.path.exists(path):
            print(f"[WARNING] File nahi mili: {path}")
            return []

        doc = Document(path)
        docs = []
        chunk = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                chunk.append(text)
            if len(chunk) >= 5:
                docs.append({
                    "content": "\n".join(chunk),
                    "metadata": {"source": source_name, "type": "docx"}
                })
                chunk = []

        if chunk:
            docs.append({
                "content": "\n".join(chunk),
                "metadata": {"source": source_name, "type": "docx"}
            })

        print(f"  [DOCX] {os.path.basename(path)} -> {len(docs)} chunks")
        return docs

    def load_pdf(self, path: str, source_name: str = "") -> list[dict]:
        if not os.path.exists(path):
            print(f"[WARNING] File nahi mili: {path}")
            return []

        reader = PdfReader(path)
        docs = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                docs.append({
                    "content": text.strip(),
                    "metadata": {"source": source_name, "type": "pdf", "page": i + 1}
                })

        print(f"  [PDF] {os.path.basename(path)} -> {len(docs)} pages")
        return docs

    def load_json(self, path: str, source_name: str = "") -> list[dict]:
        if not os.path.exists(path):
            print(f"[WARNING] File nahi mili: {path}")
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        docs = []
        for item in data:
            content = f"Q: {item.get('question', '')}\nA: {item.get('answer_content', '')}"

            keywords = item.get("recommended_keywords", [])
            if keywords:
                content += f"\nRecommended: {', '.join(keywords)}"

            tags = item.get("tags") or item.get("metadata", {}).get("tags", [])

            docs.append({
                "content": content,
                "metadata": {
                    "id":       item.get("id", ""),
                    "category": item.get("category", ""),
                    "tags":     ", ".join(tags),
                    "source":   source_name,
                    "type":     "json"
                }
            })

        print(f"  [JSON] {os.path.basename(path)} -> {len(docs)} entries")
        return docs

    def load_all(self, data_dir: str) -> list[dict]:
        print(f"\nLoading data from: {data_dir}\n")
        all_docs = []

        all_docs += self.load_docx(f"{data_dir}/FAQ Questions Dataset.docx", "faq_questions")
        all_docs += self.load_docx(f"{data_dir}/Questions Dataset.docx",     "qa_questions")
        all_docs += self.load_pdf(f"{data_dir}/Glamourbot.dataset.pdf",      "glamourbot_dataset")
        all_docs += self.load_json(f"{data_dir}/faqs.json",                  "faqs")
        all_docs += self.load_json(f"{data_dir}/MasterKB.json",              "MasterKB")
        all_docs += self.load_json(f"{data_dir}/metadata.json",              "metadata")

        print(f"\n[DONE] Total documents loaded: {len(all_docs)}")
        return all_docs


# Test
if __name__ == "__main__":
    loader = GlamourBotLoader()
    docs = loader.load_all(r"C:\Users\user\Desktop\GlamourBot\data")

    print("\n--- Sample ---")
    for i, doc in enumerate(docs[:3]):
        print(f"\n[{i+1}] Source: {doc['metadata']['source']}")
        print(f"Content: {doc['content'][:200]}...")