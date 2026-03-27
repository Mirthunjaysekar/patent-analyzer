# Patent Analyzer - Main Flask Application
import os, json, urllib.parse
from flask import Flask, request, jsonify
from serpapi import GoogleSearch
import google.generativeai as genai
from flask_cors import CORS
import re

# ----------------------------
# Setup
# ----------------------------
app = Flask(__name__)
CORS(app)

# Load API Keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not GEMINI_API_KEY or not SERPAPI_KEY:
    raise ValueError("❌ Missing API Keys: Please set GEMINI_API_KEY and SERPAPI_KEY in .env")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# ----------------------------
# ENHANCED: Junk Idea Detection Function
# ----------------------------
def is_patenable_idea(idea_text):
    """Use Gemini to determine if the idea is patentable or junk"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        CRITICAL: Analyze this idea and determine if it is potentially PATENTABLE or NON-PATENTABLE (JUNK).
        
        STRICT PATENTABILITY CRITERIA (must meet these to be patentable):
        - Must be a TECHNICAL INVENTION or INNOVATION
        - Must solve a TECHNICAL PROBLEM
        - Must have SPECIFIC TECHNICAL IMPLEMENTATION
        - Must be NOVEL and NON-OBVIOUS
        - Must have INDUSTRIAL APPLICATION
        
        DEFINITE NON-PATENTABLE (JUNK) IDEAS:
        - Personal letters, emails, correspondence (leave letters, resignation, etc.)
        - Poems, stories, songs, lyrics, creative writing
        - Artwork, paintings, drawings, artistic creations
        - Recipes, menus, food preparations
        - Business methods without technical innovation
        - Abstract ideas without technical implementation
        - Mathematical formulas alone
        - Natural phenomena, discoveries
        - Simple automation of manual tasks
        - Common everyday activities without technical innovation
        - Greetings, invitations, announcements
        - Diary entries, journals, personal thoughts
        - Shopping lists, to-do lists
        - Social media posts, blog content
        
        IDEA TO ANALYZE: "{idea_text}"
        
        Return ONLY a JSON object with this EXACT structure:
        {{
          "is_patenable": true/false,
          "confidence": "high/medium/low",
          "reason": "clear explanation of why it is or isn't patentable",
          "category": "technical_innovation/abstract_idea/personal_letter/artistic_work/business_method/natural_phenomenon/other_junk",
          "assessment": "patentable_technical_innovation" OR "non_patenable_junk_idea"
        }}
        
        Be STRICT and CONSERVATIVE. Only mark as patentable if it clearly meets technical innovation criteria.
        """
        
        response = model.generate_content(prompt, request_options={"timeout": 30})
        raw_text = response.text.strip() if response and response.text else "{}"
        
        clean_text = raw_text.replace('```json', '').replace('```', '').strip()
        
        try:
            analysis = json.loads(clean_text)
            # Ensure assessment field is set
            if "assessment" not in analysis:
                analysis["assessment"] = "patentable_technical_innovation" if analysis.get("is_patenable", False) else "non_patenable_junk_idea"
            return analysis
        except json.JSONDecodeError:
            print(f"❌ Junk detection JSON error. Raw: {raw_text}")
            return enhanced_fallback_patentability_check(idea_text)
            
    except Exception as e:
        print(f"❌ Error in patentability check: {e}")
        return enhanced_fallback_patentability_check(idea_text)

def enhanced_fallback_patentability_check(idea_text):
    """Enhanced fallback method using comprehensive keyword analysis"""
    # Extensive list of junk/non-patentable indicators
    junk_indicators = [
        # Personal correspondence
        'dear', 'sincerely', 'yours', 'regards', 'best regards', 'kind regards',
        'to whom it may concern', 'resignation', 'application', 'complaint',
        'greeting', 'invitation', 'congratulations', 'condolences',
        
        # Letters and documents
        'letter', 'email', 'memorandum', 'memo', 'notice', 'announcement',
        'circular', 'bulletin', 'newsletter',
        
        # Creative works
        'poem', 'poetry', 'story', 'tale', 'narrative', 'song', 'lyrics',
        'verse', 'rhyme', 'artwork', 'painting', 'drawing', 'sketch',
        'sculpture', 'photograph', 'composition',
        
        # Personal content
        'diary', 'journal', 'memoir', 'autobiography', 'biography',
        'blog', 'post', 'article', 'essay',
        
        # Food and recipes
        'recipe', 'cookbook', 'menu', 'ingredient', 'cooking', 'baking',
        'food', 'meal', 'dish', 'cuisine',
        
        # Simple lists and plans
        'shopping list', 'grocery list', 'to-do list', 'checklist',
        'itinerary', 'schedule', 'plan', 'agenda',
        
        # Common activities
        'exercise', 'workout', 'routine', 'habit', 'hobby', 'game',
        'entertainment', 'recreation', 'leisure',
        
        # Abstract concepts
        'love', 'happiness', 'friendship', 'relationship', 'emotion',
        'feeling', 'thought', 'idea', 'concept', 'theory',
        
        # Business terms without technical context
        'marketing', 'advertising', 'sales', 'promotion', 'brand',
        'customer', 'client', 'profit', 'revenue'
    ]
    
    # Technical/patentable indicators
    technical_indicators = [
        'system', 'method', 'device', 'apparatus', 'mechanism', 'algorithm',
        'processor', 'sensor', 'circuit', 'software', 'hardware', 'protocol',
        'engine', 'module', 'component', 'interface', 'network', 'database',
        'invention', 'innovation', 'technical', 'technology', 'engineering',
        'automation', 'robotic', 'electronic', 'digital', 'smart',
        'patent', 'invent', 'develop', 'create', 'build', 'design',
        'solution', 'problem', 'efficiency', 'performance', 'optimization'
    ]
    
    idea_lower = idea_text.lower()
    words = idea_lower.split()
    
    # Count matches
    junk_count = sum(1 for indicator in junk_indicators if indicator in idea_lower)
    tech_count = sum(1 for indicator in technical_indicators if indicator in idea_lower)
    
    # Enhanced heuristic analysis
    word_count = len(words)
    has_technical_context = tech_count > 0
    has_junk_context = junk_count > 0
    is_too_short = word_count < 8  # Very short ideas are likely junk
    
    print(f"🔍 Fallback analysis - Words: {word_count}, Tech: {tech_count}, Junk: {junk_count}")
    
    # Decision logic
    if is_too_short or (has_junk_context and not has_technical_context) or junk_count > tech_count:
        return {
            "is_patenable": False,
            "confidence": "high",
            "reason": f"Idea appears to be non-technical based on analysis. Contains {junk_count} non-patentable indicators vs {tech_count} technical indicators.",
            "category": "other_junk",
            "assessment": "non_patenable_junk_idea"
        }
    else:
        return {
            "is_patenable": True,
            "confidence": "medium", 
            "reason": f"Idea contains technical elements ({tech_count} technical indicators) worthy of patent analysis.",
            "category": "technical_innovation",
            "assessment": "patentable_technical_innovation"
        }

# ----------------------------
# Helper Functions
# ----------------------------
def generate_search_query(idea_text):
    """Use Gemini to generate optimized patent search queries"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        Based on this invention idea, generate 3 specific patent search queries that will find the most relevant existing patents.
        Focus on the core technical components and unique aspects.
        
        Idea: {idea_text}
        
        Return ONLY a JSON array of 3 search query strings. Example: ["query1", "query2", "query3"]
        """
        response = model.generate_content(prompt, request_options={"timeout": 30})
        raw_text = response.text.strip() if response and response.text else "[]"
        
        clean_text = raw_text.replace('```json', '').replace('```', '').strip()
        
        try:
            queries = json.loads(clean_text)
            if isinstance(queries, list) and len(queries) >= 3:
                return queries[:3]
        except:
            pass
        
        # Fallback queries
        return [
            f'"{idea_text}"',
            f"patent {idea_text}",
            f"invention {idea_text}"
        ]
    except Exception as e:
        print(f"Error generating search queries: {e}")
        return [idea_text]

def fetch_related_patents(idea_text):
    """Fetch closely related patents using optimized search queries"""
    try:
        # Generate optimized search queries
        search_queries = generate_search_query(idea_text)
        all_patents = []
        
        for query in search_queries:
            try:
                search = GoogleSearch({
                    "engine": "google_patents",
                    "q": query,
                    "hl": "en",
                    "api_key": SERPAPI_KEY
                })
                results = search.get_dict()
                
                items = results.get("organic_results") or results.get("patents") or []
                for item in items[:3]:  # Get top 3 from each query
                    title = item.get("title", "").strip()
                    snippet = item.get("snippet", "").strip()
                    
                    # Filter out low-quality results
                    if title and len(title) > 10 and snippet and len(snippet) > 20:
                        link = item.get("link")
                        if not link:
                            safe_title = urllib.parse.quote(title)
                            link = f"https://patents.google.com/?q={safe_title}"
                        
                        patent_data = {
                            "title": title,
                            "link": link,
                            "snippet": snippet,
                            "search_query": query
                        }
                        
                        # Avoid duplicates
                        if not any(p['title'] == title for p in all_patents):
                            all_patents.append(patent_data)
                
            except Exception as e:
                print(f"Error searching with query '{query}': {e}")
                continue
        
        # Sort by relevance (you could add more sophisticated ranking here)
        return all_patents[:5]  # Return top 5 most relevant
        
    except Exception as e:
        print(f"Error fetching patents: {e}")
        return []

def generate_ai_summary(idea_text):
    """Use Gemini to generate an AI-powered summary of the idea"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        Analyze this invention idea and provide a comprehensive technical summary in 3-4 sentences.
        Focus on the core technical components, unique mechanisms, and innovative aspects.
        
        Idea: {idea_text}
        """
        response = model.generate_content(prompt, request_options={"timeout": 30})
        return response.text.strip() if response and response.text else "No summary generated."
    except Exception as e:
        return f"⚠️ Gemini error: {e}"

def extract_technical_features_with_gemini(idea_text, summary_text, patent_contexts=None):
    """Use Gemini to extract comprehensive technical features with patent context"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        patent_context_str = ""
        if patent_contexts:
            patent_context_str = "\n\nRelevant Patent Context:\n" + "\n".join([f"- {ctx}" for ctx in patent_contexts[:3]])
        
        prompt = f"""
        Analyze this invention idea and extract 8-15 specific technical features, components, or innovative elements.
        Consider what would be important for patent comparison and novelty assessment.
        
        USER IDEA: {idea_text}
        TECHNICAL SUMMARY: {summary_text}
        {patent_context_str}
        
        Return ONLY a JSON array of feature strings. Focus on:
        - Technical mechanisms
        - System components
        - Unique processes
        - Innovative algorithms
        - Specific technical implementations
        
        Example: ["blockchain-based verification", "real-time data processing", "machine learning algorithm"]
        
        Return ONLY valid JSON array.
        """
        
        response = model.generate_content(prompt, request_options={"timeout": 30})
        raw_text = response.text.strip() if response and response.text else "[]"
        
        clean_text = raw_text.replace('```json', '').replace('```', '').strip()
        
        try:
            features = json.loads(clean_text)
            if isinstance(features, list) and features:
                cleaned_features = []
                for feature in features:
                    if isinstance(feature, str) and len(feature.strip()) > 3:
                        # Clean and normalize features
                        clean_feature = feature.strip().lower()
                        cleaned_features.append(clean_feature)
                return list(set(cleaned_features))[:15]  # Remove duplicates and limit
        except json.JSONDecodeError:
            print(f"JSON decode error. Raw: {raw_text}")
        
        return extract_features_fallback(idea_text + " " + summary_text)
        
    except Exception as e:
        print(f"Error extracting technical features: {e}")
        return extract_features_fallback(idea_text + " " + summary_text)

def extract_features_fallback(text):
    """Fallback feature extraction"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    features = []
    for word in words:
        if (word not in stop_words and 
            word not in features and 
            len(word) > 3):
            features.append(word)
    
    return features[:10]

def analyze_patent_features_with_gemini(patent_title, patent_snippet, user_features):
    """Use Gemini to analyze patent and check for user features"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""
        Analyze this patent and determine which of the user's technical features are present.
        
        PATENT TITLE: {patent_title}
        PATENT DESCRIPTION: {patent_snippet}
        
        USER FEATURES TO CHECK:
        {json.dumps(user_features, indent=2)}
        
        For each user feature, analyze if the patent contains that specific technical element.
        Consider synonyms, similar concepts, and equivalent technical implementations.
        
        Return ONLY a JSON object with:
        - "present_features": array of user features that ARE in this patent
        - "absent_features": array of user features that are NOT in this patent
        - "patent_features": array of key technical features found in the patent
        
        Example:
        {{
          "present_features": ["blockchain", "encryption"],
          "absent_features": ["ai algorithm", "real-time processing"],
          "patent_features": ["distributed ledger", "cryptographic security"]
        }}
        """
        
        response = model.generate_content(prompt, request_options={"timeout": 30})
        raw_text = response.text.strip() if response and response.text else "{}"
        
        clean_text = raw_text.replace('```json', '').replace('```', '').strip()
        
        try:
            analysis = json.loads(clean_text)
            return analysis
        except json.JSONDecodeError:
            print(f"Patent analysis JSON error. Raw: {raw_text}")
            return {
                "present_features": [],
                "absent_features": user_features,
                "patent_features": []
            }
            
    except Exception as e:
        print(f"Error analyzing patent features: {e}")
        return {
            "present_features": [],
            "absent_features": user_features,
            "patent_features": []
        }

# ----------------------------
# Enhanced Delta Logic Analysis
# ----------------------------
def perform_smart_delta_analysis(user_features, patents):
    """
    Perform intelligent delta analysis using Gemini for better accuracy
    """
    if not user_features:
        return {
            "error": "No features extracted from user idea",
            "table_markdown": "",
            "table_html": "",
            "novelty_percent": 0,
            "novel_features": []
        }
    
    if not patents:
        table_markdown = create_empty_patents_table(user_features)
        table_html = create_empty_patents_table_html(user_features)
        return {
            "table_markdown": table_markdown,
            "table_html": table_html,
            "novelty_percent": 100.0,
            "novel_features": user_features,
            "novel_count": len(user_features),
            "total_features": len(user_features)
        }
    
    print(f"🔍 Analyzing {len(patents)} patents against {len(user_features)} user features...")
    
    # Analyze each patent with Gemini
    patent_analyses = []
    all_present_features = set()
    
    for i, patent in enumerate(patents):
        print(f"  Analyzing patent {i+1}: {patent['title'][:50]}...")
        
        analysis = analyze_patent_features_with_gemini(
            patent['title'], 
            patent['snippet'], 
            user_features
        )
        
        patent_analyses.append({
            'title': patent['title'],
            'link': patent['link'],
            'present_features': set(analysis.get('present_features', [])),
            'absent_features': set(analysis.get('absent_features', [])),
            'patent_features': analysis.get('patent_features', [])
        })
        
        # Track features present in any patent
        all_present_features.update(analysis.get('present_features', []))
    
    # Calculate novelty
    novel_features = [feature for feature in user_features if feature not in all_present_features]
    novelty_percent = (len(novel_features) / len(user_features)) * 100 if user_features else 0
    
    # Create comparison tables with error handling
    try:
        table_markdown = create_smart_delta_table(user_features, patent_analyses)
    except Exception as e:
        print(f"❌ Error creating markdown table: {e}")
        table_markdown = create_fallback_table_markdown(user_features, patent_analyses)
    
    try:
        table_html = create_smart_delta_table_html(user_features, patent_analyses)
    except Exception as e:
        print(f"❌ Error creating HTML table: {e}")
        table_html = create_fallback_table_html(user_features, patent_analyses)
    
    # Create detailed comparisons
    detailed_comparisons = create_smart_detailed_comparisons(user_features, patent_analyses)
    
    return {
        "table_html": table_html,
        "table_markdown": table_markdown,
        "novelty_percent": round(novelty_percent, 2),
        "novel_features": novel_features,
        "novel_count": len(novel_features),
        "total_features": len(user_features),
        "detailed_comparisons": detailed_comparisons,
        "user_features": user_features,
        "patents_analyzed": len(patent_analyses),
        "analysis_method": "gemini_enhanced"
    }

def create_smart_delta_table(user_features, patent_analyses):
    """Create markdown table using Gemini analysis results"""
    if not patent_analyses:
        return "No patents available for comparison"
    
    # Header
    header = "| Feature / Keyword |"
    separator = "|------------------|"
    
    for patent in patent_analyses:
        short_title = patent['title'][:20] + '...' if len(patent['title']) > 20 else patent['title']
        header += f" {short_title} |"
        separator += "-----------------|"
    
    header += " Novel? |"
    separator += "--------|"
    
    table = header + "\n" + separator + "\n"
    
    # Rows
    for feature in user_features:
        row = f"| {feature} |"
        
        feature_in_any_patent = False
        for patent in patent_analyses:
            if feature in patent['present_features']:
                row += " ✅ Present |"
                feature_in_any_patent = True
            else:
                row += " ❌ Absent |"
        
        if feature_in_any_patent:
            row += " ❌ Common |"
        else:
            row += " ✅ Novel |"
        
        table += row + "\n"
    
    return table

def create_smart_delta_table_html(user_features, patent_analyses):
    """Create HTML table using Gemini analysis results"""
    if not patent_analyses:
        return "<p>No patents available for comparison</p>"
    
    html = '<div class="delta-table-container">'
    html += '<table class="delta-table">'
    
    # Header row
    html += '<thead><tr>'
    html += '<th>Feature / Keyword</th>'
    for patent in patent_analyses:
        short_title = patent['title'][:25] + '...' if len(patent['title']) > 25 else patent['title']
        html += f'<th>{short_title}</th>'
    html += '<th>Novel?</th>'
    html += '</tr></thead>'
    
    # Data rows
    html += '<tbody>'
    for feature in user_features:
        html += '<tr>'
        html += f'<td class="feature-name">{feature}</td>'
        
        feature_in_any_patent = False
        for patent in patent_analyses:
            if feature in patent['present_features']:
                html += '<td class="present">✅ Present</td>'
                feature_in_any_patent = True
            else:
                html += '<td class="absent">❌ Absent</td>'
        
        if feature_in_any_patent:
            html += '<td class="common">❌ Common</td>'
        else:
            html += '<td class="novel">✅ Novel</td>'
        
        html += '</tr>'
    
    html += '</tbody></table></div>'
    return html

def create_fallback_table_markdown(user_features, patent_analyses):
    """Fallback markdown table creation with error handling"""
    try:
        if not patent_analyses:
            return create_empty_patents_table(user_features)
        
        table_lines = []
        # Header
        header = "| Feature |"
        for patent in patent_analyses:
            short_title = patent['title'][:15] + '...' if len(patent['title']) > 15 else patent['title']
            header += f" {short_title} |"
        header += " Novel? |"
        table_lines.append(header)
        
        # Separator
        separator = "|--------|"
        for _ in patent_analyses:
            separator += "---------|"
        separator += "--------|"
        table_lines.append(separator)
        
        # Rows
        for feature in user_features:
            row = f"| {feature} |"
            feature_in_any = False
            for patent in patent_analyses:
                if feature in patent.get('present_features', set()):
                    row += " ✅ |"
                    feature_in_any = True
                else:
                    row += " ❌ |"
            
            row += " ✅ |" if not feature_in_any else " ❌ |"
            table_lines.append(row)
        
        return "\n".join(table_lines)
    except Exception as e:
        return f"Error generating table: {str(e)}"

def create_fallback_table_html(user_features, patent_analyses):
    """Fallback HTML table creation with error handling"""
    try:
        if not patent_analyses:
            return create_empty_patents_table_html(user_features)
        
        html = '<div class="delta-table-container"><table class="delta-table"><thead><tr><th>Feature</th>'
        for patent in patent_analyses:
            short_title = patent['title'][:15] + '...' if len(patent['title']) > 15 else patent['title']
            html += f'<th>{short_title}</th>'
        html += '<th>Novel?</th></tr></thead><tbody>'
        
        for feature in user_features:
            html += f'<tr><td>{feature}</td>'
            feature_in_any = False
            for patent in patent_analyses:
                if feature in patent.get('present_features', set()):
                    html += '<td class="present">✅</td>'
                    feature_in_any = True
                else:
                    html += '<td class="absent">❌</td>'
            
            if feature_in_any:
                html += '<td class="common">❌</td>'
            else:
                html += '<td class="novel">✅</td>'
            html += '</tr>'
        
        html += '</tbody></table></div>'
        return html
    except Exception as e:
        return f'<p>Error generating table: {str(e)}</p>'

def create_smart_detailed_comparisons(user_features, patent_analyses):
    """Create detailed comparisons using Gemini analysis"""
    comparisons = []
    
    for patent in patent_analyses:
        user_features_set = set(user_features)
        present_features = patent['present_features']
        absent_features = user_features_set - present_features
        
        comparisons.append({
            'patent_title': patent['title'],
            'patent_link': patent['link'],
            'user_unique_features': list(absent_features),
            'patent_unique_features': patent['patent_features'],
            'common_features': list(present_features),
            'novelty_percent': round((len(absent_features) / len(user_features)) * 100, 2) if user_features else 0
        })
    
    return comparisons

def create_empty_patents_table(user_features):
    """Create markdown table when no patents are available"""
    table = "| Feature / Keyword | Patent Status | Novel? |\n"
    table += "|------------------|---------------|--------|\n"
    
    for feature in user_features:
        table += f"| {feature} | ❌ No Patents | ✅ Novel |\n"
    
    return table

def create_empty_patents_table_html(user_features):
    """Create HTML table when no patents are available"""
    html = '<div class="delta-table-container"><table class="delta-table">'
    html += '<thead><tr><th>Feature / Keyword</th><th>Patent Status</th><th>Novel?</th></tr></thead>'
    html += '<tbody>'
    
    for feature in user_features:
        html += f'<tr><td>{feature}</td><td>❌ No Patents</td><td class="novel">✅ Novel</td></tr>'
    
    html += '</tbody></table></div>'
    return html

# ----------------------------
# NEW: Novelty-Based Patentability Assessment
# ----------------------------
def assess_patentability_based_on_novelty(delta_analysis, patentability_check):
    """Assess patentability based on novelty percentage and other factors"""
    novelty_percent = delta_analysis.get("novelty_percent", 0)
    novel_count = delta_analysis.get("novel_count", 0)
    total_features = delta_analysis.get("total_features", 0)
    
    # Patentability thresholds
    HIGH_NOVELTY_THRESHOLD = 70    # 70%+ novelty = High patent potential
    MEDIUM_NOVELTY_THRESHOLD = 40  # 40-69% novelty = Medium patent potential
    LOW_NOVELTY_THRESHOLD = 20     # 20-39% novelty = Low patent potential
    # Below 20% = Very low patent potential
    
    # Base assessment on novelty percentage
    if novelty_percent >= HIGH_NOVELTY_THRESHOLD:
        patentability_score = "high"
        assessment = "high_patent_potential"
        recommendation = "Strong candidate for patent filing - high novelty detected"
        color = "green"
    elif novelty_percent >= MEDIUM_NOVELTY_THRESHOLD:
        patentability_score = "medium"
        assessment = "moderate_patent_potential"
        recommendation = "Moderate patent potential - consider prior art analysis"
        color = "orange"
    elif novelty_percent >= LOW_NOVELTY_THRESHOLD:
        patentability_score = "low"
        assessment = "low_patent_potential"
        recommendation = "Low patent potential - significant prior art overlap"
        color = "red"
    else:
        patentability_score = "very_low"
        assessment = "very_low_patent_potential"
        recommendation = "Very low patent potential - high similarity to existing patents"
        color = "dark_red"
    
    # Consider other factors
    confidence = patentability_check.get("confidence", "medium")
    category = patentability_check.get("category", "technical_innovation")
    
    # Adjust based on initial patentability check confidence
    if confidence == "low" and patentability_score in ["high", "medium"]:
        patentability_score = "medium" if patentability_score == "high" else "low"
        recommendation += " (Note: Initial technical assessment had low confidence)"
    
    return {
        "patentability_score": patentability_score,
        "assessment": assessment,
        "novelty_percentage": novelty_percent,
        "novel_features_count": novel_count,
        "total_features_count": total_features,
        "recommendation": recommendation,
        "color": color,
        "thresholds": {
            "high": HIGH_NOVELTY_THRESHOLD,
            "medium": MEDIUM_NOVELTY_THRESHOLD,
            "low": LOW_NOVELTY_THRESHOLD
        },
        "factors_considered": ["novelty_percentage", "feature_count", "initial_assessment"]
    }

# ----------------------------
# ENHANCED Flask Route with Novelty-Based Assessment
# ----------------------------
@app.route("/chat", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        idea_text = data.get("idea") or data.get("message") or ""
        idea_text = idea_text.strip()

        if not idea_text:
            return jsonify({"error": "No idea provided"}), 400

        print(f"🔍 Analyzing idea: {idea_text}")

        # Step 0 - Check if idea is patentable
        patentability_check = is_patenable_idea(idea_text)
        print(f"✅ Patentability check: {patentability_check}")
        
        if not patentability_check.get("is_patenable", True):
            return jsonify({
                "error": "non_patenable_idea",
                "message": "🚫 This idea cannot be patented - it does not meet patent eligibility criteria",
                "details": {
                    "reason": patentability_check.get("reason", "Idea lacks technical innovation or is too abstract"),
                    "category": patentability_check.get("category", "unknown"),
                    "confidence": patentability_check.get("confidence", "medium"),
                    "assessment": patentability_check.get("assessment", "non_patenable_junk_idea")
                },
                "suggestion": "Please provide a technical invention with specific implementations, mechanisms, or innovative solutions to a technical problem. Patentable ideas typically involve new devices, systems, methods, or compositions with practical applications.",
                "status": "rejected",
                "patentability": "not_patenable"
            }), 400

        # If idea is patentable, proceed with full analysis
        print("✅ Idea is patentable - proceeding with full analysis...")

        # Step 1: AI Summary
        summary = generate_ai_summary(idea_text)
        print("✅ Summary generated")

        # Step 2: Related Patents (with optimized search)
        patents = fetch_related_patents(idea_text)
        print(f"✅ Found {len(patents)} closely related patents")

        # Step 3: Extract User Features with patent context
        patent_contexts = [f"{p['title']}: {p['snippet'][:100]}..." for p in patents]
        user_features = extract_technical_features_with_gemini(idea_text, summary, patent_contexts)
        print(f"✅ Extracted {len(user_features)} user features: {user_features}")

        # Step 4: Perform Smart Delta Analysis with Gemini
        delta_results = perform_smart_delta_analysis(user_features, patents)
        print("✅ Smart delta analysis completed")

        # NEW: Step 5 - Assess patentability based on novelty
        novelty_assessment = assess_patentability_based_on_novelty(delta_results, patentability_check)
        print(f"✅ Novelty-based assessment: {novelty_assessment['patentability_score']}")

        # Prepare response for PATENTABLE ideas
        response_data = {
            "status": "success",
            "patentability": "potentially_patenable",
            "summary": summary,
            "related_patents": patents,
            "patentability_check": patentability_check,
            "novelty_assessment": novelty_assessment,  # NEW: Add novelty assessment
            "delta_analysis": {
                "main_table": delta_results["table_markdown"],
                "main_table_html": delta_results["table_html"],
                "novelty_percent": delta_results["novelty_percent"],
                "novel_features": delta_results["novel_features"],
                "novel_count": delta_results["novel_count"],
                "total_features": delta_results["total_features"],
                "user_features": delta_results["user_features"],
                "patents_analyzed": delta_results["patents_analyzed"],
                "detailed_comparisons": delta_results["detailed_comparisons"],
                "analysis_method": delta_results.get("analysis_method", "standard")
            }
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"❌ Error in analyze endpoint: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "Smart Patent Delta Analysis API",
        "timestamp": "2024-01-01 00:00:00",
        "features": ["junk_idea_detection", "patent_search", "delta_analysis", "novelty_scoring", "novelty_based_assessment"]
    })

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    print("🚀 Starting Smart Patent Analysis Server...")
    print("✅ Gemini API Configured")
    print("✅ SerpAPI Configured")
    print("✅ Smart Delta Logic Engine Ready")
    print("✅ ENHANCED Junk Idea Detection System Ready")
    print("✅ Novelty-Based Patentability Assessment Ready")
    print("🔍 System will now REJECT: Leave letters, poems, recipes, abstract ideas, etc.")
    print("📊 Novelty Thresholds: High (≥70%) | Medium (≥40%) | Low (≥20%) | Very Low (<20%)")
