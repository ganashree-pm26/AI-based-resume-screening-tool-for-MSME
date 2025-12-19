import streamlit as st
import json
from jd_pdf_parser import parse_job_description_pdf
from google_finder import find_candidates_for_jd
from resume_parser import parse_resume_file
from matching import compute_match_for_resume
from linkedin_finder import find_linkedin_candidates
from github_analyzer import analyze_github_profile


# Page config with custom theme
st.set_page_config(
    page_title="AI Hiring Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a1a;
        text-align: center;
        padding: 0.8rem 0 0.3rem 0;
        margin-bottom: 0.3rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .section-header {
        background: #2c3e50;
        color: white;
        padding: 0.75rem 1.2rem;
        border-radius: 5px;
        margin: 1.2rem 0 0.8rem 0;
        font-size: 1.2rem;
        font-weight: 600;
    }
    .info-card {
        background: #f8f9fa;
        padding: 1.2rem;
        border-radius: 5px;
        border-left: 3px solid #2c3e50;
        margin: 0.8rem 0;
    }
    .candidate-card {
        background: #ffffff;
        padding: 1.2rem;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin: 0.8rem 0;
        border-left: 3px solid #3498db;
    }
    .score-badge {
        background: #2c3e50;
        color: white;
        padding: 0.4rem 0.9rem;
        border-radius: 4px;
        font-weight: 600;
        display: inline-block;
        margin: 0.3rem 0;
        font-size: 0.95rem;
    }
    .skill-tag {
        background: #e8f4f8;
        color: #0d47a1;
        padding: 0.25rem 0.7rem;
        border-radius: 3px;
        display: inline-block;
        margin: 0.15rem;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .missing-skill-tag {
        background: #fce4ec;
        color: #c62828;
        padding: 0.25rem 0.7rem;
        border-radius: 3px;
        display: inline-block;
        margin: 0.15rem;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .stButton button {
        background: #2980b9;
        color: white;
        font-weight: 600;
        border: none;
    }
    .stButton button:hover {
        background: #3498db;
        border-color: #3498db;
    }
    .stDownloadButton button {
        background: #27ae60;
        color: white;
        font-weight: 600;
        border: none;
    }
    .stDownloadButton button:hover {
        background: #2ecc71;
        border-color: #2ecc71;
    }
    </style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">AI Hiring Platform</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Automated JD + Resume + LinkedIn + GitHub Analysis</p>', unsafe_allow_html=True)


# ============================================================
# 1. JOB DESCRIPTION ANALYZER
# ============================================================
st.markdown('<div class="section-header">Job Description Analyzer</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_jd = st.file_uploader("Upload Job Description", type=["pdf", "docx"], help="Upload a PDF or DOCX file containing the job description")

with col2:
    st.markdown("*Supported Formats*")
    st.markdown("PDF Documents | Word Documents (.docx)")

if uploaded_jd:
    ext = uploaded_jd.name.split(".")[-1]
    jd_path = f"uploaded_jd.{ext}"

    with open(jd_path, "wb") as f:
        f.write(uploaded_jd.getbuffer())

    with st.spinner("Analyzing job description..."):
        jd = parse_job_description_pdf(jd_path)
    
    st.success("JD parsed successfully")

    # Display JD details in organized columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("*Required Skills*")
        for skill in jd["skills"]:
            st.markdown(f'<span class="skill-tag">{skill}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("*Key Responsibilities*")
        for r in jd["responsibilities"]:
            st.markdown(f"• {r}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("*Position Details*")
        st.markdown(f"*Seniority Level:* {jd['seniority_level']}")
        st.markdown(f"*Domain:* {jd['domain']}")
        st.markdown(f"*Location:* {jd['location']}")
        st.markdown('</div>', unsafe_allow_html=True)


    # ============================================================
    # 2. GOOGLE PUBLIC RESUME FINDER
    # ============================================================
    st.markdown('<div class="section-header">Google Resume Finder</div>', unsafe_allow_html=True)
    st.markdown("Automatically discover and analyze public resumes matching your job requirements")

    col1, col2 = st.columns([1, 1])
    with col1:
        max_dl = st.slider("Maximum resumes to download", 1, 20, 5, help="Number of resumes to fetch and analyze")
    with col2:
        show_text = st.checkbox("Show full resume text", False, help="Display complete resume content in results")

    if st.button("Search Public Resumes", use_container_width=True):
        with st.spinner("Searching Google, downloading resumes, analyzing candidates..."):

            def parse_and_score(path, jd_obj, source_url=None):
                res = parse_resume_file(path)
                res["path"] = path
                return compute_match_for_resume(res, jd_obj, source_url)

            results = find_candidates_for_jd(jd, parse_and_score, max_downloads=max_dl)

        if not results:
            st.error("No public resumes found. Try adjusting your search criteria.")
        else:
            st.success(f"Found {len(results)} matching candidates")

            for i, r in enumerate(results, start=1):
                st.markdown(f'<div class="candidate-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"{r['candidate_name']}")
                with col2:
                    st.markdown(f'<div class="score-badge">Match Score: {r["final_score"]:.1%}</div>', unsafe_allow_html=True)
                
                st.markdown(f"[View Source]({r['source_url']})")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("*Matched Skills*")
                    for skill in r["matched_skills"]:
                        st.markdown(f'<span class="skill-tag">{skill}</span>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("*Missing Skills*")
                    for skill in r["missing_skills"]:
                        st.markdown(f'<span class="missing-skill-tag">{skill}</span>', unsafe_allow_html=True)

                if show_text:
                    with st.expander("View Full Resume"):
                        st.text(r["cleaned_text"])

                st.markdown('</div>', unsafe_allow_html=True)

            st.download_button(
                "Download Results as JSON",
                json.dumps(results, indent=2),
                "google_resume_results.json",
                use_container_width=True
            )


    # ============================================================
    # 3. LINKEDIN PROFILE FINDER
    # ============================================================
    st.markdown('<div class="section-header">LinkedIn Candidate Finder</div>', unsafe_allow_html=True)
    st.markdown("Discover relevant candidates via Google search")

    if st.button("Search LinkedIn Candidates", use_container_width=True):
        with st.spinner("Searching for LinkedIn profiles..."):
            linkedin_results = find_linkedin_candidates(jd)

        if not linkedin_results:
            st.error("No LinkedIn candidates found")
        else:
            st.success(f"Found {len(linkedin_results)} LinkedIn candidates")

            for i, c in enumerate(linkedin_results, start=1):
                st.markdown(f'<div class="candidate-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"{c['name']}")
                    st.markdown(f"{c['headline']}")
                with col2:
                    st.markdown(f'<div class="score-badge">Match: {c["match_score"]}%</div>', unsafe_allow_html=True)
                
                st.markdown(f"[View LinkedIn Profile]({c['url']})")
                
                st.markdown("*Skills*")
                for skill in c["skills"]:
                    st.markdown(f'<span class="skill-tag">{skill}</span>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("*Matched Skills*")
                    for skill in c["matched_skills"]:
                        st.markdown(f'<span class="skill-tag">{skill}</span>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("*Missing Skills*")
                    for skill in c["missing_skills"]:
                        st.markdown(f'<span class="missing-skill-tag">{skill}</span>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

            st.download_button(
                "Download LinkedIn Results JSON",
                json.dumps(linkedin_results, indent=2),
                "linkedin_results.json",
                use_container_width=True
            )


    # ============================================================
    # 4. GITHUB PROFILE ANALYZER
    # ============================================================
    st.markdown('<div class="section-header">GitHub Profile Analyzer</div>', unsafe_allow_html=True)
    st.markdown("Analyze a candidate's technical skills through their GitHub contributions")

    col1, col2 = st.columns([2, 1])
    with col1:
        github_user = st.text_input("Enter GitHub Username", placeholder="e.g., torvalds", help="GitHub username without @")

    if st.button("Analyze GitHub Profile", use_container_width=True):
        with st.spinner("Analyzing GitHub activity, repositories, and contributions..."):
            try:
                score, repos = analyze_github_profile(github_user)
                
                st.markdown(f'<div class="score-badge" style="font-size: 1.3rem;">Overall GitHub Score: {score}/100</div>', unsafe_allow_html=True)

                for r in repos:
                    st.markdown(f'<div class="candidate-card">', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"{r['repo']}")
                    with col2:
                        st.markdown(f'<div class="score-badge">Score: {r["score"]}</div>', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Stars", r['meta']['stars'])
                    with col2:
                        st.metric("Forks", r['meta']['forks'])
                    with col3:
                        st.metric("README", f"{len(r['meta']['readme'])} chars")
                    
                    st.markdown("*Languages*")
                    for lang in r['meta']['languages']:
                        st.markdown(f'<span class="skill-tag">{lang}</span>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

                st.download_button(
                    "Download GitHub Analysis JSON",
                    json.dumps({"username": github_user, "score": score, "repos": repos}, indent=2),
                    "github_analysis.json",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error analyzing GitHub profile: {str(e)}")


# Footer
st.markdown('<p style="text-align: center; color: #999; padding: 1rem 0; font-size: 0.85rem; border-top: 1px solid #eee; margin-top: 1.5rem;">AI-Powered Recruitment Platform</p>', unsafe_allow_html=True)
