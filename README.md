# 📚 BizMind AI — Business Knowledge RAG Chatbot

An AI-powered Retrieval-Augmented Generation (RAG) chatbot that allows users to ask questions about a Business Knowledge Manual and receive document-grounded answers with source and page citations.

## 🚀 Live Demo

## 📌 Project Overview

**BizMind AI** is a document-based AI assistant built using Google Gemini and Streamlit.

The chatbot uses **Retrieval-Augmented Generation (RAG)** to retrieve relevant information from a business knowledge document before generating an answer.

This helps the chatbot provide answers based on the organization's knowledge base rather than relying only on general model knowledge.

---

## ✨ Key Features

- 🤖 AI-powered business knowledge assistant
- 🔎 Retrieval-Augmented Generation (RAG)
- 📄 PDF document-based question answering
- 📑 Source and page citations
- 💬 Conversational follow-up questions
- 🛡️ Document-grounded responses
- 🎨 Professional Streamlit interface
- 🔐 Secure API key management using environment variables
- 💡 Suggested questions for users

---

## 🏗️ System Architecture

```text
                 Business Knowledge Manual
                           │
                           ▼
                      File Search
                           │
                           ▼
                    Retrieve Relevant
                       Information
                           │
                           ▼
                    Generate Answer
                           │
                           ▼
                  Source + Page Citation
                           │
                           ▼
                    Streamlit UI
                           │
                           ▼
                         User
