# Patent Analyzer - Requirements Document

## 1. Overview
A web-based AI-powered tool that analyzes patent ideas and determines 
their novelty and patentability using Google Gemini AI.

## 2. Functional Requirements
- FR01: User can input their patent idea as text
- FR02: System generates an AI summary using Google Gemini API
- FR03: System fetches 5 closely related patents from Google Patents
- FR04: System performs delta analysis between user idea and each patent
- FR05: System displays novelty features unique to the user idea
- FR06: System calculates and displays patentability percentage

## 3. Non-Functional Requirements
- NFR01: Response time should be under 30 seconds
- NFR02: API keys must be stored securely in .env files
- NFR03: System should work on all modern browsers

## 4. Tech Stack
- Frontend: React.js, TailwindCSS
- Backend: Python Flask
- AI Model: Google Gemini API
- Patent Source: Google Patents