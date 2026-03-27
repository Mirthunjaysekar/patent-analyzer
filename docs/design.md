# Patent Analyzer - Design Document

## 1. System Architecture
Client-Server Architecture:
- Client: React.js frontend (patent-chatbot/)
- Server: Python Flask backend (backend/backend/)

## 2. Data Flow
1. User enters patent idea in React frontend
2. Frontend sends POST request to Flask backend
3. Backend calls Google Gemini API and gets AI summary
4. Backend searches Google Patents and fetches 5 related patents
5. Backend performs delta analysis between idea and each patent
6. Novelty features and patentability score are calculated
7. Results are returned to frontend and displayed

## 3. SCM Branching Strategy
- main: Production-ready stable code
- develop: Integration and testing branch
- feature/gemini-integration: Gemini AI summary feature
- feature/patent-search: Google Patents search feature
- feature/delta-analysis: Comparison and analysis feature
- feature/novelty-score: Patentability scoring feature

## 4. Configuration Items
- Source Code: /backend/backend/*.py
- Frontend: /patent-chatbot/src/*.js
- Docs: /docs/*.md
- Tests: /test/*.json
- Build: /build/build.sh