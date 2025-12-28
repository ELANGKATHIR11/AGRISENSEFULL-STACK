"""
RAG Engine for AgriSense - LangChain-based Farmer Assistant
===========================================================

This module implements a Retrieval-Augmented Generation (RAG) system that:
1. Ingests agricultural knowledge from PDFs and existing QA pairs
2. Uses ChromaDB for efficient semantic search
3. Leverages local LLMs (via Ollama or LlamaCpp) for answer generation

Why RAG?
--------
- Reduces hallucinations by grounding answers in actual documentation
- Allows updating knowledge base without retraining the LLM
- Combines semantic search with generative capabilities
- Cost-effective (runs locally, no API costs)

Architecture:
-------------
1. Document Ingestion: PDFs + JSON → Text Chunks → Embeddings → ChromaDB
2. Query Processing: User Question → Embedding → Similarity Search → Top-K Docs
3. Answer Generation: Context + Question → LLM → Structured Answer

Author: AgriSense Team
Date: December 2025
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Core dependencies
try:
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.llms import Ollama
    from langchain_community.vectorstores import Chroma
    
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LangChain not available: {e}")
    LANGCHAIN_AVAILABLE = False

# Configure logger
logger = logging.getLogger(__name__)


class FarmerAssistant:
    """
    RAG-based chatbot for agricultural advice using LangChain + ChromaDB.
    
    This class manages the entire RAG pipeline:
    - Knowledge base ingestion (PDFs, JSON)
    - Vector store management (ChromaDB)
    - Query processing with semantic retrieval
    - Answer generation using local LLM
    
    Features:
    ---------
    - Multi-source knowledge: Combines PDFs and structured QA pairs
    - Semantic search: Uses sentence-transformers for embeddings
    - Local LLM: Ollama (mistral/llama2) or LlamaCpp for privacy
    - Persistent storage: ChromaDB persists embeddings to disk
    - Graceful fallback: Returns rule-based answers if AI unavailable
    
    Example:
    --------
    ```python
    assistant = FarmerAssistant(
        chroma_persist_dir="./chroma_db",
        model_name="mistral"
    )
    
    # One-time knowledge ingestion
    assistant.ingest_knowledge_base(
        pdf_dir="./crop_guides",
        json_path="./chatbot_qa_pairs.json"
    )
    
    # Query the assistant
    answer = assistant.ask("How do I treat tomato blight?")
    print(answer["answer"])
    ```
    """
    
    def __init__(
        self,
        chroma_persist_dir: str = "./chroma_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model: str = "mistral",
        llm_backend: str = "ollama",
        device: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 4,
    ):
        """
        Initialize the RAG-based Farmer Assistant.
        
        Parameters:
        -----------
        chroma_persist_dir : str
            Directory to persist ChromaDB vector store (enables caching)
        embedding_model : str
            HuggingFace model for text embeddings (default: all-MiniLM-L6-v2)
            Why: Lightweight, fast, good quality embeddings
        llm_model : str
            LLM model name (ollama: mistral/llama2, llamacpp: path to .gguf)
        llm_backend : str
            "ollama" (recommended) or "llamacpp"
        device : Optional[str]
            "cuda", "cpu", or None (auto-detect)
            Why: Allows forcing CPU mode on systems without GPU
        chunk_size : int
            Maximum characters per text chunk
            Why: Balance between context and retrieval precision
        chunk_overlap : int
            Character overlap between chunks
            Why: Prevents splitting important information
        top_k : int
            Number of relevant documents to retrieve
            Why: More context improves answer quality, but increases latency
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain dependencies not installed. "
                "Install with: pip install -r requirements-ai.txt"
            )
        
        self.chroma_persist_dir = Path(chroma_persist_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        
        # Auto-detect device if not specified
        if device is None:
            device = os.getenv("AGRISENSE_AI_DEVICE", "cuda" if self._is_cuda_available() else "cpu")
        self.device = device
        
        logger.info(f"Initializing FarmerAssistant with device={self.device}")
        
        # Initialize embeddings
        # Why HuggingFaceEmbeddings: Free, local, no API costs
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={"device": self.device},
                encode_kwargs={"normalize_embeddings": True},  # Why: Improves cosine similarity
            )
            logger.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            raise
        
        # Initialize vector store (lazy loading - will be populated during ingestion)
        self.vectorstore: Optional[Chroma] = None
        
        # Initialize LLM
        try:
            if llm_backend == "ollama":
                # Why Ollama: Easiest setup, automatic model management, good performance
                self.llm = Ollama(
                    model=llm_model,
                    temperature=0.1,  # Why: Lower temp = more factual, less creative
                    num_ctx=4096,     # Context window size
                    top_k=40,         # For sampling diversity
                    top_p=0.9,        # Nucleus sampling
                )
                logger.info(f"Initialized Ollama with model: {llm_model}")
            elif llm_backend == "llamacpp":
                # Why LlamaCpp: Direct GGUF support, no separate service needed
                from langchain_community.llms import LlamaCpp
                self.llm = LlamaCpp(
                    model_path=llm_model,
                    temperature=0.1,
                    max_tokens=512,
                    top_p=0.9,
                    n_ctx=4096,
                    n_gpu_layers=-1 if self.device == "cuda" else 0,  # Why: GPU acceleration
                )
                logger.info(f"Initialized LlamaCpp with model: {llm_model}")
            else:
                raise ValueError(f"Unknown LLM backend: {llm_backend}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            logger.warning("LLM unavailable - will fall back to retrieval-only mode")
            self.llm = None
        
        # Text splitter for chunking documents
        # Why RecursiveCharacterTextSplitter: Respects sentence boundaries
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],  # Priority order
        )
    
    def _is_cuda_available(self) -> bool:
        """Check if CUDA is available for GPU acceleration."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def ingest_knowledge_base(
        self,
        pdf_dir: Optional[str] = None,
        json_path: Optional[str] = None,
        force_rebuild: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingest agricultural knowledge from PDFs and JSON QA pairs into ChromaDB.
        
        This method:
        1. Loads and chunks PDF documents
        2. Converts JSON QA pairs to documents
        3. Generates embeddings for all text
        4. Stores in ChromaDB (persistent)
        
        Why separate ingestion:
        - Knowledge base is static (doesn't change frequently)
        - Embeddings are expensive to compute
        - One-time operation saves latency on queries
        
        Parameters:
        -----------
        pdf_dir : Optional[str]
            Directory containing crop guide PDFs
        json_path : Optional[str]
            Path to existing chatbot_qa_pairs.json
        force_rebuild : bool
            If True, rebuild even if ChromaDB exists
            
        Returns:
        --------
        Dict with ingestion statistics (docs processed, chunks created, etc.)
        """
        # Check if ChromaDB already exists and we're not forcing rebuild
        if self.chroma_persist_dir.exists() and not force_rebuild:
            logger.info("ChromaDB already exists - loading existing vectorstore")
            try:
                self.vectorstore = Chroma(
                    persist_directory=str(self.chroma_persist_dir),
                    embedding_function=self.embeddings,
                )
                collection_count = self.vectorstore._collection.count()
                logger.info(f"Loaded vectorstore with {collection_count} documents")
                return {
                    "status": "loaded_existing",
                    "documents_in_store": collection_count,
                    "message": "Using existing knowledge base. Use force_rebuild=True to regenerate.",
                }
            except Exception as e:
                logger.warning(f"Failed to load existing ChromaDB: {e}. Rebuilding...")
        
        documents = []
        stats = {"pdfs_loaded": 0, "json_pairs_loaded": 0, "total_chunks": 0}
        
        # Load PDFs
        if pdf_dir and Path(pdf_dir).exists():
            logger.info(f"Loading PDFs from {pdf_dir}")
            try:
                # Why DirectoryLoader: Batch loads all PDFs recursively
                pdf_loader = DirectoryLoader(
                    pdf_dir,
                    glob="**/*.pdf",
                    loader_cls=PyPDFLoader,
                    show_progress=True,
                )
                pdf_docs = pdf_loader.load()
                
                # Why chunking: Large PDFs need to be split for better retrieval
                pdf_chunks = self.text_splitter.split_documents(pdf_docs)
                documents.extend(pdf_chunks)
                
                stats["pdfs_loaded"] = len(pdf_docs)
                stats["pdf_chunks"] = len(pdf_chunks)
                logger.info(f"Loaded {len(pdf_docs)} PDFs, created {len(pdf_chunks)} chunks")
            except Exception as e:
                logger.error(f"Error loading PDFs: {e}")
        
        # Load JSON QA pairs
        if json_path and Path(json_path).exists():
            logger.info(f"Loading QA pairs from {json_path}")
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    qa_data = json.load(f)
                
                # Convert QA pairs to documents
                # Why: Treat each QA pair as a mini-document for retrieval
                from langchain.schema import Document
                
                questions = qa_data.get("questions", [])
                answers = qa_data.get("answers", [])
                
                for i, (q, a) in enumerate(zip(questions, answers)):
                    # Combine Q&A for better semantic matching
                    content = f"Question: {q}\n\nAnswer: {a}"
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "qa_pairs",
                            "question": q,
                            "index": i,
                        }
                    )
                    documents.append(doc)
                
                stats["json_pairs_loaded"] = len(questions)
                logger.info(f"Loaded {len(questions)} QA pairs")
            except Exception as e:
                logger.error(f"Error loading JSON QA pairs: {e}")
        
        if not documents:
            raise ValueError("No documents loaded! Provide valid pdf_dir or json_path")
        
        stats["total_chunks"] = len(documents)
        logger.info(f"Total documents to ingest: {len(documents)}")
        
        # Create ChromaDB vectorstore
        # Why Chroma: Lightweight, fast, persistent, no server needed
        try:
            # Clear existing if force_rebuild
            if force_rebuild and self.chroma_persist_dir.exists():
                import shutil
                shutil.rmtree(self.chroma_persist_dir)
                logger.info("Cleared existing ChromaDB")
            
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(self.chroma_persist_dir),
            )
            
            # Persist to disk
            # Why: Avoids recomputing embeddings on every restart
            self.vectorstore.persist()
            logger.info(f"Successfully persisted vectorstore to {self.chroma_persist_dir}")
            
            stats["status"] = "success"
            return stats
            
        except Exception as e:
            logger.error(f"Failed to create vectorstore: {e}")
            raise
    
    def ask(
        self,
        query: str,
        return_sources: bool = False,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Ask the farmer assistant a question using RAG.
        
        Process:
        1. Embed the query
        2. Retrieve top-K similar documents from ChromaDB
        3. Format context + question as prompt
        4. Generate answer using LLM
        5. Return answer with optional source citations
        
        Why this approach:
        - Retrieval: Finds relevant context from knowledge base
        - Augmentation: Adds retrieved context to prompt
        - Generation: LLM synthesizes final answer
        
        Parameters:
        -----------
        query : str
            Farmer's question (e.g., "How to treat tomato blight?")
        return_sources : bool
            If True, include source documents in response
        max_retries : int
            Number of retries if LLM fails
            
        Returns:
        --------
        Dict containing:
        - answer: Generated response
        - sources: List of source documents (if return_sources=True)
        - confidence: Similarity score of best match
        - retrieval_mode: "rag" or "retrieval_only" (if LLM unavailable)
        """
        if not self.vectorstore:
            raise RuntimeError(
                "Knowledge base not initialized! Call ingest_knowledge_base() first."
            )
        
        logger.info(f"Processing query: {query}")
        
        # Retrieve relevant documents
        # Why similarity_search_with_score: Need confidence scores
        try:
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                query,
                k=self.top_k,
            )
            
            if not docs_with_scores:
                return {
                    "answer": "I couldn't find relevant information in my knowledge base. Please try rephrasing your question.",
                    "confidence": 0.0,
                    "retrieval_mode": "no_results",
                }
            
            # Extract documents and scores
            docs = [doc for doc, _ in docs_with_scores]
            scores = [score for _, score in docs_with_scores]
            best_score = min(scores)  # Why min: Lower score = better match in ChromaDB
            
            logger.info(f"Retrieved {len(docs)} documents, best score: {best_score:.4f}")
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {
                "answer": f"Error during retrieval: {str(e)}",
                "confidence": 0.0,
                "retrieval_mode": "error",
            }
        
        # If LLM is available, use RAG
        if self.llm:
            try:
                # Create custom prompt
                # Why custom prompt: Control answer format and tone
                prompt_template = """You are an expert agricultural advisor helping farmers. 
Use the following pieces of context to answer the question at the end. 
If you don't know the answer based on the context, say so - don't make up information.
Provide practical, actionable advice.

Context:
{context}

Question: {question}

Helpful Answer:"""
                
                PROMPT = PromptTemplate(
                    template=prompt_template,
                    input_variables=["context", "question"],
                )
                
                # Create retrieval QA chain
                # Why chain: Encapsulates retrieval + generation pipeline
                qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",  # Why "stuff": Simple, passes all docs to LLM
                    retriever=self.vectorstore.as_retriever(search_kwargs={"k": self.top_k}),
                    return_source_documents=return_sources,
                    chain_type_kwargs={"prompt": PROMPT},
                )
                
                # Generate answer with retries
                for attempt in range(max_retries):
                    try:
                        result = qa_chain({"query": query})
                        
                        response = {
                            "answer": result["result"],
                            "confidence": 1.0 - (best_score / 2.0),  # Normalize to 0-1
                            "retrieval_mode": "rag",
                        }
                        
                        if return_sources:
                            response["sources"] = [
                                {
                                    "content": doc.page_content[:200],  # Preview
                                    "metadata": doc.metadata,
                                }
                                for doc in result.get("source_documents", [])
                            ]
                        
                        logger.info("Successfully generated RAG answer")
                        return response
                        
                    except Exception as e:
                        logger.warning(f"LLM generation attempt {attempt + 1} failed: {e}")
                        if attempt == max_retries - 1:
                            logger.error("All LLM attempts failed, falling back to retrieval-only")
                            break
            
            except Exception as e:
                logger.error(f"RAG pipeline error: {e}")
        
        # Fallback: Return best matching document (retrieval-only mode)
        # Why fallback: System remains functional even if LLM unavailable
        logger.info("Using retrieval-only fallback")
        best_doc = docs[0]
        
        response = {
            "answer": best_doc.page_content,
            "confidence": 1.0 - (best_score / 2.0),
            "retrieval_mode": "retrieval_only",
            "note": "LLM unavailable - showing best matching content",
        }
        
        if return_sources:
            response["sources"] = [
                {
                    "content": doc.page_content[:200],
                    "metadata": doc.metadata,
                }
                for doc in docs
            ]
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
        --------
        Dict with vectorstore stats, model info, etc.
        """
        stats = {
            "device": self.device,
            "llm_available": self.llm is not None,
            "vectorstore_initialized": self.vectorstore is not None,
        }
        
        if self.vectorstore:
            try:
                stats["documents_count"] = self.vectorstore._collection.count()
            except Exception:
                stats["documents_count"] = "unknown"
        
        return stats


# Singleton instance for dependency injection
_farmer_assistant_instance: Optional[FarmerAssistant] = None


def get_farmer_assistant() -> FarmerAssistant:
    """
    Get or create singleton FarmerAssistant instance.
    
    Why singleton:
    - Embeddings and vector store are expensive to initialize
    - Share across all API requests
    - Reduces memory footprint
    
    Usage in FastAPI:
    -----------------
    ```python
    @app.post("/ai/chat")
    async def chat(
        query: str,
        assistant: FarmerAssistant = Depends(get_farmer_assistant)
    ):
        return assistant.ask(query)
    ```
    """
    global _farmer_assistant_instance
    
    if _farmer_assistant_instance is None:
        # Get configuration from environment
        chroma_dir = os.getenv("AGRISENSE_CHROMA_DIR", "./chroma_db")
        llm_model = os.getenv("AGRISENSE_LLM_MODEL", "mistral")
        llm_backend = os.getenv("AGRISENSE_LLM_BACKEND", "ollama")
        
        logger.info("Initializing FarmerAssistant singleton")
        _farmer_assistant_instance = FarmerAssistant(
            chroma_persist_dir=chroma_dir,
            llm_model=llm_model,
            llm_backend=llm_backend,
        )
    
    return _farmer_assistant_instance
