import sys
import os
import json
import streamlit as st
from duckduckgo_search import DDGS


def query_historic_facts(sport, query_text):
    facts_list = [
        {"sport": "Cricket", "fact": "The first official cricket Test match was played in 1877 between Australia and England at the Melbourne Cricket Ground (MCG). Australia won by 45 runs."},
        {"sport": "Badminton", "fact": "The Thomas Cup, established in 1948, is the premier international men's team badminton championship. India won its historic first title in 2022 by defeating Indonesia 3-0."},
        {"sport": "Football", "fact": "The FIFA World Cup was first held in 1930. Uruguay hosted and won the tournament, defeating Argentina 4-2 in the final match in Montevideo."}
    ]
    matched_facts = [item["fact"] for item in facts_list if item["sport"].lower() == sport.lower()]
    return matched_facts


def get_live_news_context(sport_name):
    search_query = f"{sport_name} latest tournament results championship winners news 2026"
    retrieved_texts = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=3))
            for index, r in enumerate(results, start=1):
                title = r.get("title", "No Title")
                snippet = r.get("body", "No Content Available")
                retrieved_texts.append(f"Source ({index}): {title}\nContent: {snippet}")
    except Exception as e:
        return "No recent search engine updates available due to system connectivity constraints."
    return "\n\n".join(retrieved_texts)


def compile_quiz_data(sport, difficulty, api_key):
    import google.generativeai as genai
    
    db_matches = query_historic_facts(sport=sport, query_text=sport)
    db_context = "\n".join(db_matches) if db_matches else "No offline historic data recorded."
    
    web_context = get_live_news_context(sport)
    unified_context = f"=== HISTORICAL FACTS (Sourced from Local Vector Memory) ===\n{db_context}\n\n=== LIVE INTERNET NEWS ===\n{web_context}"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = (
        "You are an expert sports quiz creator. Your job is to write multiple-choice quizzes "
        "relying strictly on the provided Context. Avoid hallucinations. Do not use facts not "
        f"found in the Context details below.\n\nCONTEXT DETAILS: \n{unified_context}\n\n"
        f"Generate exactly 3 unique multiple-choice questions for the sport: {sport}.\n"
        f"Difficulty target: {difficulty}.\n\n"
        "Format each question exactly as follows so my program can parse it:\n"
        "Question: [Question text here]\n"
        "A) [Option A]\n"
        "B) [Option B]\n"
        "C) [Option C]\n"
        "D) [Option D]\n"
        "Correct Answer: [Single Letter, e.g., A]\n"
        "Explanation: [Detailed reasoning quoting from the context details]\n"
    )
    
    response = model.generate_content(prompt)
    return response.text, unified_context


st.set_page_config(page_title="Sports Quiz Agent", page_icon="🏆")
st.title("🏆 AI-Powered Sports Quiz Generator")
st.write("Engineered via dual-track RAG (Local Memory Store + DuckDuckGo Real-Time Search).")

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("🔒 GEMINI_API_KEY is missing! Add it under Streamlit Advanced Settings -> Secrets.")
else:
    st.sidebar.header("Quiz Settings")
    sport_choice = st.sidebar.selectbox("Select Sport", ["Cricket", "Football", "Badminton"])
    difficulty = st.sidebar.select_slider("Select Difficulty", options=["Easy", "Medium", "Hard"])

    if "quiz_output" not in st.session_state:
        st.session_state.quiz_output = None
        st.session_state.quiz_context = None

    if st.sidebar.button("Generate Fresh Quiz", use_container_width=True):
        with st.spinner("Analyzing historic vectors and scouring the web..."):
            try:
                quiz_text, context_used = compile_quiz_data(sport_choice, difficulty, api_key)
                st.session_state.quiz_output = quiz_text
                st.session_state.quiz_context = context_used
                st.success("Quiz generated successfully!")
            except Exception as e:
                st.error(f"Execution Error: {e}")

    if st.session_state.quiz_output:
        st.subheader(f"Current Quiz: {sport_choice} ({difficulty})")
        st.text_area("Generated Quiz Template Output", value=st.session_state.quiz_output, height=350)
        
        with st.expander("🔍 Inspect Ground Truth Data Context (RAG Audit Check)"):
            st.code(st.session_state.quiz_context, language="markdown")
