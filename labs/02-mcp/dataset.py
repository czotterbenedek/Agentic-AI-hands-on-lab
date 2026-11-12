"""Bibliographic research dataset and Crossref API integration with offline fallback."""

import json
import urllib.request
import urllib.parse
from typing import Any, Dict, List, Optional


RESEARCH_DATASET: List[Dict[str, Any]] = [
    {
        "paper_id": "1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"],
        "year": 2017,
        "citations": 125000,
        "doi": "10.48550/arXiv.1706.03762",
        "abstract": "We propose the Transformer, a model architecture eschewing recurrence and relying entirely on an attention mechanism to draw global dependencies between input and output.",
        "topics": ["transformer", "attention", "nlp", "deep learning"],
        "bibtex": "@article{vaswani2017attention,\n  title={Attention is all you need},\n  author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, {\\L}ukasz and Polosukhin, Illia},\n  journal={Advances in neural information processing systems},\n  volume={30},\n  year={2017}\n}",
    },
    {
        "paper_id": "1810.04805",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        "year": 2018,
        "citations": 85000,
        "doi": "10.48550/arXiv.1810.04805",
        "abstract": "We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers, designed to pre-train deep bidirectional representations from unlabeled text.",
        "topics": ["bert", "nlp", "transformer", "pretraining"],
        "bibtex": "@article{devlin2018bert,\n  title={BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding},\n  author={Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina},\n  journal={arXiv preprint arXiv:1810.04805},\n  year={2018}\n}",
    },
    {
        "paper_id": "2106.09685",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "authors": ["Edward J. Hu", "Yelong Shen", "Phillip Wallis", "Zeyuan Allen-Zhu", "Yuanzhi Li", "Shean Wang", "Lu Wang", "Weizhu Chen"],
        "year": 2021,
        "citations": 18500,
        "doi": "10.48550/arXiv.2106.09685",
        "abstract": "We propose Low-Rank Adaptation (LoRA), which freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture.",
        "topics": ["lora", "fine-tuning", "parameter-efficient", "llm"],
        "bibtex": "@article{hu2021lora,\n  title={LoRA: Low-Rank Adaptation of Large Language Models},\n  author={Hu, Edward J and Shen, Yelong and Wallis, Phillip and Allen-Zhu, Zeyuan and Li, Yuanzhi and Wang, Shean and Wang, Lu and Chen, Weizhu},\n  journal={arXiv preprint arXiv:2106.09685},\n  year={2021}\n}",
    },
    {
        "paper_id": "2201.11903",
        "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "authors": ["Jason Wei", "Xuezhi Wang", "Dale Schuurmans", "Maarten Bosma", "Brian Ichter", "Fei Xia", "Ed Chi", "Quoc Le", "Denny Zhou"],
        "year": 2022,
        "citations": 12000,
        "doi": "10.48550/arXiv.2201.11903",
        "abstract": "We explore how generating a chain of thought—a series of intermediate reasoning steps—significantly improves the ability of large language models to perform complex reasoning.",
        "topics": ["reasoning", "prompting", "chain-of-thought", "llm"],
        "bibtex": "@article{wei2022chain,\n  title={Chain-of-thought prompting elicits reasoning in large language models},\n  author={Wei, Jason and Wang, Xuezhi and Schuurmans, Dale and Bosma, Maarten and Ichter, Brian and Xia, Fei and Chi, Ed and Le, Quoc and Zhou, Denny},\n  journal={Advances in Neural Information Processing Systems},\n  volume={35},\n  pages={24824--24837},\n  year={2022}\n}",
    },
    {
        "paper_id": "2210.03629",
        "title": "ReAct: Synergizing Reasoning and Acting in Language Models",
        "authors": ["Shunyu Yao", "Jeffrey Zhao", "Dian Yu", "Nan Du", "Izhak Shafran", "Karthik Narasimhan", "Yuan Cao"],
        "year": 2022,
        "citations": 7500,
        "doi": "10.48550/arXiv.2210.03629",
        "abstract": "We explore the use of LLMs to generate both reasoning traces and task-specific actions in an interleaved manner, enabling greater synergy between the two.",
        "topics": ["react", "agent", "reasoning", "tool calling"],
        "bibtex": "@article{yao2022react,\n  title={ReAct: Synergizing Reasoning and Acting in Language Models},\n  author={Yao, Shunyu and Zhao, Jeffrey and Yu, Dian and Du, Nan and Shafran, Izhak and Narasimhan, Karthik and Cao, Yuan},\n  journal={arXiv preprint arXiv:2210.03629},\n  year={2022}\n}",
    },
    {
        "paper_id": "2302.04761",
        "title": "Toolformer: Language Models Can Teach Themselves to Use Tools",
        "authors": ["Timo Schick", "Jane Dwivedi-Yu", "Roberto Dessi", "Roberta Raileanu", "Maria Lomeli", "Luke Zettlemoyer", "Nicola Cancedda", "Thomas Scialom"],
        "year": 2023,
        "citations": 6200,
        "doi": "10.48550/arXiv.2302.04761",
        "abstract": "Language models can teach themselves to use external tools via simple APIs, deciding which tool to call, when to call it, what arguments to pass, and how to incorporate results.",
        "topics": ["toolformer", "agent", "tool calling", "llm"],
        "bibtex": "@article{schick2023toolformer,\n  title={Toolformer: Language Models Can Teach Themselves to Use Tools},\n  author={Schick, Timo and Dwivedi-Yu, Jane and Dessi, Roberto and Raileanu, Roberta and Lomeli, Maria and Zettlemoyer, Luke and Cancedda, Nicola and Scialom, Thomas},\n  journal={arXiv preprint arXiv:2302.04761},\n  year={2023}\n}",
    },
]


def search_crossref_api(query: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
    """Attempt to query Crossref public API; gracefully returns None on network error or offline mode."""
    url = f"https://api.crossref.org/works?query={urllib.parse.quote(query)}&rows={limit}"
    headers = {"User-Agent": "BME-AgenticAI-Lab/1.0 (mailto:lab@university.edu)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("message", {}).get("items", [])
            results = []
            for item in items:
                title = item.get("title", ["Unknown Title"])[0]
                authors = [
                    f"{a.get('given', '')} {a.get('family', '')}".strip()
                    for a in item.get("author", [])
                ]
                year = (
                    item.get("published", {}).get("date-parts", [[None]])[0][0]
                    or item.get("created", {}).get("date-parts", [[None]])[0][0]
                    or 2023
                )
                results.append({
                    "paper_id": item.get("DOI", "unknown_doi"),
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "citations": item.get("is-referenced-by-count", 0),
                    "doi": item.get("DOI", ""),
                    "abstract": item.get("abstract", "No abstract available via Crossref API."),
                    "source": "crossref",
                })
            return results
    except Exception:
        # Graceful fallback to offline local dataset
        return None
