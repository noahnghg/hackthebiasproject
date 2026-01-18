from sentence_transformers import SentenceTransformer, CrossEncoder, util
import torch
import spacy
import numpy as np
import matplotlib.pyplot as plt
import pdfplumber
from typing import Union, BinaryIO
import re
import warnings

warnings.filterwarnings("ignore")

# ============================================================================
# ANONYMIZER
# ============================================================================
class Anonymizer:
    def __init__(self, model: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(model)
        except OSError:
            print(f"Model '{model}' not found. Please run: python -m spacy download {model}")
            self.nlp = spacy.blank("en")
        
        if 'sentencizer' not in self.nlp.pipe_names:
            self.nlp.add_pipe('sentencizer')

    def anonymize_text(self, text: str) -> str:
        """
        Anonymizes PII from the text including Names, Emails, and Phone numbers.
        """
        if not text:
            return ""

        doc = self.nlp(text)
        redaction_ranges = []

        # Identify PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                redaction_ranges.append((ent.start_char, ent.end_char, "[NAME REDACTED]"))

        # Regex for Emails
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        for match in email_pattern.finditer(text):
            redaction_ranges.append((match.start(), match.end(), "[EMAIL REDACTED]"))

        # Regex for Phone Numbers
        phone_pattern = re.compile(r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b')
        for match in phone_pattern.finditer(text):
            redaction_ranges.append((match.start(), match.end(), "[PHONE REDACTED]"))

        redaction_ranges.sort(key=lambda x: x[0], reverse=True)

        final_text_chars = list(text)
        for start, end, replacement in redaction_ranges:
            final_text_chars[start:end] = list(replacement)

        return "".join(final_text_chars)


# ============================================================================
# PARSER
# ============================================================================
def extract_text_from_pdf(pdf_file: Union[str, BinaryIO]) -> str:
    """
    Extracts text from a given PDF file path or file-like object.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
    
    return text.strip()


# ============================================================================
# TRADITIONAL KEYWORD MATCHER (Standard ATS)
# ============================================================================
class KeywordMatcher:
    """
    Traditional ATS that uses simple keyword matching.
    This is how most basic ATS systems work - they just look for exact keywords.
    """
    def __init__(self):
        pass
    
    def extract_keywords(self, text: str) -> set:
        """Extract individual words (keywords) from text."""
        # Convert to lowercase and split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                     'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those'}
        keywords = set(word for word in words if word not in stop_words and len(word) > 2)
        return keywords
    
    def calculate_keyword_match_score(self, job_description: str, resume_text: str) -> float:
        """
        Calculate match score based on keyword overlap.
        This is a simple ratio: how many JD keywords appear in the resume.
        """
        jd_keywords = self.extract_keywords(job_description)
        resume_keywords = self.extract_keywords(resume_text)
        
        if not jd_keywords:
            return 0.0
        
        # Count how many JD keywords are found in resume
        matching_keywords = jd_keywords.intersection(resume_keywords)
        
        # Score is the percentage of JD keywords found in resume
        score = len(matching_keywords) / len(jd_keywords)
        
        return score


# ============================================================================
# SEMANTIC MATCHER (Our Fair ATS)
# ============================================================================
class SemanticMatcher:
    """
    Advanced semantic matching that understands context and similarity.
    Uses NLP to find similar words/phrases, not just exact keyword matches.
    """
    def __init__(self, bi_encoder_name: str = 'all-MiniLM-L6-v2', cross_encoder_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2', spacy_model: str = "en_core_web_sm"):
        self.bi_encoder = SentenceTransformer(bi_encoder_name)
        self.cross_encoder = CrossEncoder(cross_encoder_name)
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            print(f"Spacy model '{spacy_model}' not found. Loading blank 'en' model.")
            self.nlp = spacy.blank("en")
        
        if 'sentencizer' not in self.nlp.pipe_names:
            self.nlp.add_pipe('sentencizer')

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Computes semantic similarity using embeddings.
        This understands that "JavaScript" and "JS" are similar, or "developed" and "built".
        """
        if not text1 or not text2:
            return 0.0
        embeddings = self.bi_encoder.encode([text1, text2], convert_to_tensor=True)
        cosine_scores = util.cos_sim(embeddings[0], embeddings[1])
        return float(cosine_scores[0][0])

    def calculate_semantic_score(self, job_description: str, resume_text: str) -> float:
        """
        Calculate semantic similarity between entire documents.
        This finds similar meanings, not just exact word matches.
        """
        return self.compute_similarity(job_description, resume_text)


# ============================================================================
# BIASED ATS COMPARISON SYSTEM
# ============================================================================
class ATSComparison:
    def __init__(self, rejection_threshold: float = 0.4):
        """
        Initialize the ATS comparison system.
        
        Args:
            rejection_threshold: Score below which a resume is rejected (default 0.4)
        """
        self.anonymizer = Anonymizer()
        self.keyword_matcher = KeywordMatcher()
        self.semantic_matcher = SemanticMatcher()
        self.rejection_threshold = rejection_threshold
        
    def process_with_traditional_ats(self, resume_text: str, job_description: str) -> dict:
        """
        Traditional ATS: Simple keyword matching with NO bias removal.
        This is what most basic ATS systems do - just look for exact keywords.
        Names, demographics, etc. can influence decisions.
        """
        # No anonymization - names and personal info visible
        score = self.keyword_matcher.calculate_keyword_match_score(job_description, resume_text)
        accepted = score >= self.rejection_threshold
        
        return {
            "score": score,
            "accepted": accepted,
            "method": "Keyword Matching"
        }
    
    def process_with_fair_ats(self, resume_text: str, job_description: str) -> dict:
        """
        Our Fair ATS: Uses anonymization + semantic matching.
        - Anonymizer: Removes names, emails, phone numbers to eliminate bias
        - Parser: Extracts structured information
        - Semantic Matcher: Understands similar words/concepts, not just exact matches
        """
        # Step 1: Anonymize to remove bias
        anonymized_text = self.anonymizer.anonymize_text(resume_text)
        
        # Step 2: Use semantic matching to understand context and similarity
        score = self.semantic_matcher.calculate_semantic_score(job_description, anonymized_text)
        accepted = score >= self.rejection_threshold
        
        return {
            "score": score,
            "accepted": accepted,
            "method": "Semantic Matching with Anonymization"
        }
    
    def compare_systems(self, resumes: list, job_description: str) -> dict:
        """
        Compare Traditional Keyword ATS vs Our Fair Semantic ATS.
        
        Args:
            resumes: List of resume texts
            job_description: The job description to match against
            
        Returns:
            dict with comparison statistics
        """
        print("="*80)
        print("COMPARING ATS SYSTEMS")
        print("="*80)
        print(f"\nTraditional ATS: Uses simple keyword matching (looks for exact words)")
        print(f"Our Fair ATS: Uses anonymization + semantic matching (understands similar concepts)")
        print(f"Rejection Threshold: {self.rejection_threshold} (scores below this are rejected)")
        print("="*80)
        
        traditional_results = []
        fair_results = []
        
        print(f"\nProcessing {len(resumes)} resumes...\n")
        
        for i, resume in enumerate(resumes, 1):
            print(f"Resume #{i}:")
            
            # Traditional ATS (keyword matching, no bias removal)
            traditional_result = self.process_with_traditional_ats(resume, job_description)
            traditional_results.append(traditional_result)
            print(f"  Traditional ATS (Keywords): Score={traditional_result['score']:.4f} ({traditional_result['score']*100:.1f}%) - {'✓ ACCEPTED' if traditional_result['accepted'] else '✗ REJECTED'}")
            
            # Our Fair ATS (semantic matching with anonymization)
            fair_result = self.process_with_fair_ats(resume, job_description)
            fair_results.append(fair_result)
            print(f"  Our Fair ATS (Semantic):    Score={fair_result['score']:.4f} ({fair_result['score']*100:.1f}%) - {'✓ ACCEPTED' if fair_result['accepted'] else '✗ REJECTED'}")
            print()
        
        # Calculate statistics
        traditional_accepted = sum(1 for r in traditional_results if r['accepted'])
        traditional_rejected = len(resumes) - traditional_accepted
        
        fair_accepted = sum(1 for r in fair_results if r['accepted'])
        fair_rejected = len(resumes) - fair_accepted
        
        traditional_rejection_rate = (traditional_rejected / len(resumes)) * 100
        fair_rejection_rate = (fair_rejected / len(resumes)) * 100
        
        improvement = traditional_rejected - fair_rejected
        
        print("="*80)
        print("RESULTS SUMMARY")
        print("="*80)
        print(f"Total Resumes Processed: {len(resumes)}")
        print(f"Rejection Threshold: {self.rejection_threshold}")
        print()
        print(f"Traditional ATS (Keyword Matching):")
        print(f"  ✓ Accepted: {traditional_accepted}")
        print(f"  ✗ Rejected: {traditional_rejected}")
        print(f"  Rejection Rate: {traditional_rejection_rate:.1f}%")
        print()
        print(f"Our Fair ATS (Semantic + Anonymization):")
        print(f"  ✓ Accepted: {fair_accepted}")
        print(f"  ✗ Rejected: {fair_rejected}")
        print(f"  Rejection Rate: {fair_rejection_rate:.1f}%")
        print()
        if improvement > 0:
            print(f"✓ IMPROVEMENT: {improvement} fewer resume(s) rejected!")
            print(f"  ({(improvement/len(resumes))*100:.1f}% improvement in acceptance rate)")
        elif improvement < 0:
            print(f"⚠ WARNING: {abs(improvement)} more resume(s) rejected")
        else:
            print(f"Same number of rejections in both systems")
        print("="*80)
        
        return {
            "traditional_accepted": traditional_accepted,
            "traditional_rejected": traditional_rejected,
            "fair_accepted": fair_accepted,
            "fair_rejected": fair_rejected,
            "traditional_rejection_rate": traditional_rejection_rate,
            "fair_rejection_rate": fair_rejection_rate,
            "total_resumes": len(resumes),
            "improvement": improvement
        }
    
    def visualize_comparison(self, comparison_stats: dict):
        """
        Create a single bar chart comparing the number of rejections.
        """
        fig, ax = plt.subplots(figsize=(10, 7))
        
        systems = ['Traditional ATS\n(Keyword Matching)', 'Our Fair ATS\n(Semantic + Anonymization)']
        rejections = [
            comparison_stats['traditional_rejected'],
            comparison_stats['fair_rejected']
        ]
        
        # Color code: red for traditional (more rejections), green for ours (fewer rejections)
        colors = ["#07F1F92D", "#E7910F"]
        
        bars = ax.bar(systems, rejections, color=colors, edgecolor='black', linewidth=2, width=0.6)
        
        # Add labels and title
        ax.set_ylabel('Number of Resumes Rejected', fontsize=14, fontweight='bold')
        ax.set_title('ATS Comparison: Resume Rejections', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_ylim(0, max(rejections) * 1.3)  # Add space at top for labels
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on top of bars
        for bar, rejection_count in zip(bars, rejections):
            height = bar.get_height()
            percentage = (rejection_count / comparison_stats['total_resumes']) * 100
            
            # Main number
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(rejection_count)}',
                    ha='center', va='bottom', fontweight='bold', fontsize=20)
            
            # Percentage below the number
            ax.text(bar.get_x() + bar.get_width()/2., height + (max(rejections) * 0.08),
                    f'({percentage:.1f}%)',
                    ha='center', va='bottom', fontsize=12, style='italic')
        
        # Add improvement annotation if there's a difference
        if comparison_stats['improvement'] > 0:
            mid_x = (bars[0].get_x() + bars[1].get_x() + bars[1].get_width()) / 2
            mid_y = max(rejections) * 0.7
            
            ax.annotate('', xy=(bars[1].get_x() + bars[1].get_width()/2, rejections[1]),
                       xytext=(bars[0].get_x() + bars[0].get_width()/2, rejections[0]),
                       arrowprops=dict(arrowstyle='<->', color='green', lw=2.5))
            
            ax.text(mid_x, mid_y,
                   f'{comparison_stats["improvement"]} fewer\nrejections!',
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', edgecolor='green', linewidth=2),
                   fontsize=12, fontweight='bold')
        
        # Add total at bottom
        ax.text(0.5, -0.15, f'Total Resumes Processed: {comparison_stats["total_resumes"]}',
               ha='center', va='top', transform=ax.transAxes,
               fontsize=11, style='italic')
        
        plt.tight_layout()
        plt.show()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================
if __name__ == "__main__":
    # Job Description
    job_description = """
    Position: Lead Software Developer 
    Company: Open Text

    Description:As a Lead Software Developer, you will:
    Design and build web services and cloud native apps using modern JavaScript (React, node.js, jest), HTML/CSS, TypeScript, SQL, nginx stack.
    Design and implement RESTful APIs and business logic using .NET / .NET Core (C#).
    Containerize applications and manage deployments with Docker and Kubernetes (EKS).
    Implement CI/CD pipelines and ensure efficient, automated deployment processes.
    Ensure application security, performance, and reliability at scale.
    Participate in code reviews, architecture discussions, and agile ceremonies.
    Stay current with emerging AI, cloud, and web technologies.

    Requirements: What You Need To Succeed:
    Computer Science or related bachelor’s degree with 8-10 years of professional experience.
    Strong proficiency with React.js, JavaScript, and TypeScript
    Experience with AWS (EC2, S3, RDS, Lambda, EKS or similar services).
    Hands-on experience with Docker and Kubernetes for container orchestration.
    Familiarity with MySQL or other relational databases.
    Proficient with Git and modern CI/CD workflows.
    Knowledge of responsive UI design and cross-browser compatibility.

    Nice to haves:
    Cloud Certifications eg. AWS Certified Developer
    UI frameworks such as Material UI, Chakra UI, or Tailwind CSS.
    Testing experience (Jest, NUnit, xUnit, Cypress).
    Experience with Infrastructure as Code eg. Terraform, CloudFormation
    Experience building AI-powered front-end experiences, like chat interfaces or intelligent search.

    """
    
    # Sample resumes - Feed in the potential sample resumes
    sample_resumes = [

#  Resume 1 
        """
Jason Jones
E-commerce Specialist

Contact Information:

* Email: [jasonjones@email.com](mailto:jasonjones@email.com)
* Phone: 555-123-4567
* LinkedIn: linkedin.com/in/jasonjones

Summary:
Results-driven E-commerce Specialist with 5+ years of experience in inventory management, SEO, online advertising, and analytics. Proven track record of increasing online sales, improving website traffic, and optimizing inventory levels. Skilled in analyzing complex data sets, identifying trends, and making data-driven decisions. Passionate about staying up-to-date with the latest e-commerce trends and technologies.

Professional Experience:

E-commerce Specialist, XYZ Corporation (2018-Present)

* Managed inventory levels across multiple channels, resulting in a 25% reduction in stockouts and a 15% reduction in overstocking
* Developed and implemented SEO strategies that increased website traffic by 30% and improved search engine rankings by 20%
* Created and executed online advertising campaigns that generated a 50% increase in sales and a 20% increase in conversion rates
* Analyzed website analytics to identify trends, optimize user experience, and improve customer engagement
* Collaborated with cross-functional teams to launch new product lines, promotions, and marketing campaigns

E-commerce Coordinator, ABC Retail (2015-2018)

* Assisted in managing inventory levels, processing orders, and resolving customer inquiries
* Conducted keyword research and optimized product descriptions to improve search engine rankings
* Assisted in creating and executing online advertising campaigns, resulting in a 20% increase in sales
* Analyzed website analytics to identify trends and areas for improvement

Education:

* Bachelor's Degree in Business Administration, [University Name] (2015)

Skills:

* Inventory Management
* SEO for E-commerce
* Online Advertising (Google Ads, Facebook Ads)
* Analytics (Google Analytics, Excel)
* Data Analysis
* E-commerce Platforms (Shopify, WooCommerce)
* Customer Service

Achievements:

* Winner of the XYZ Corporation's "Innovator of the Year" award for developing and implementing a data-driven approach to inventory management
* Featured speaker at the "E-commerce Summit" conference, presenting on "Optimizing Inventory Levels for E-commerce Success"
* Developed and implemented a social media strategy that increased followers by 500% and engagement by 200%

Certifications:

* Google Analytics Certification
* HubSpot Inbound Marketing Certification
* Shopify Plus Certification
        """,



# Resume 2
        """

Alejandra Delgado
UI Engineer

Contact Information:

* Email: [alejandradelgado@email.com](mailto:alejandradelgado@email.com)
* Phone: 555-555-5555
* LinkedIn: linkedin.com/in/alejandradelgado
* GitHub: github.com/alejandradelgado

Professional Summary:
Highly motivated and detail-oriented UI Engineer with 5+ years of experience in designing and developing user interfaces for web applications. Skilled in HTML, React, and wireframing, with a strong understanding of user experience principles. Proven track record of delivering high-quality solutions that meet and exceed client expectations.

Technical Skills:

* Front-end development: HTML, CSS, JavaScript, React
* UI design: wireframing, prototyping, design systems
* Collaboration tools: Git, Slack, Asana
* Design software: Sketch, Figma, Adobe XD

Professional Experience:

Senior UI Engineer, ABC Company (2018-Present)

* Designed and developed high-quality user interfaces for multiple web applications, resulting in a 25% increase in user engagement
* Collaborated with cross-functional teams to define and implement UI design systems, improving consistency and efficiency across products
* Mentored junior engineers and designers, providing guidance and support to improve skills and productivity

UI Engineer, DEF Agency (2015-2018)

* Developed and maintained multiple web applications, ensuring seamless user experiences and meeting strict deadlines
* Created wireframes and prototypes to visualize and test UI designs, resulting in a 30% reduction in design revisions
* Implemented and maintained a design system, improving consistency and efficiency across projects

Education:

* Bachelor's Degree in Computer Science, XYZ University (2015)

Achievements:

* Recipient of the "Best UI Design" award at the 2019 UX Design Conference
* Published a blog post on "Designing for Accessibility" on the company blog, reaching a global audience
* Led a team to create a design system that was recognized by the industry as a best practice

Certifications:

* Certified Scrum Master (CSM)
* Certified UI Designer (CUID)


        





""",

# Resume 3

"""Carl Reyes
Full Stack Developer

Contact Information:

* Email: [carl.reyes@email.com](mailto:carl.reyes@email.com)
* Phone: 555-555-5555
* LinkedIn: linkedin.com/in/carlreyes
* GitHub: github.com/carlreyes

Professional Summary:
Highly skilled and motivated Full Stack Developer with 5+ years of experience in designing and developing scalable, efficient, and user-friendly web applications. Proficient in CSS, JavaScript, Node.js, and database management systems. Proven track record of delivering high-quality projects on time and within budget.

Technical Skills:

* Programming languages: JavaScript, Node.js
* Front-end development: CSS, HTML, React, Angular
* Back-end development: Node.js, Express.js, MongoDB
* Database management: MySQL, MongoDB, PostgreSQL
* Version control: Git
* Agile development methodologies: Scrum, Kanban

Professional Experience:

Senior Full Stack Developer, ABC Company (2020-Present)

* Designed and developed multiple web applications using Node.js, Express.js, and MongoDB
* Collaborated with cross-functional teams to deliver high-quality projects on time and within budget
* Implemented API integrations with third-party services using RESTful APIs and GraphQL
* Conducted code reviews and ensured adherence to coding standards and best practices
* Mentored junior developers and provided guidance on coding and software development principles

Full Stack Developer, DEF Startup (2018-2020)

* Built and maintained multiple web applications using React, Node.js, and MongoDB
* Developed and deployed RESTful APIs using Node.js and Express.js
* Designed and implemented database schema using MongoDB and PostgreSQL
* Collaborated with designers to develop user interfaces and user experiences
* Participated in code reviews and ensured adherence to coding standards and best practices

Achievements:

* Top Performer: Awarded as top performer in ABC Company's annual performance review (2020)
* Best Code Quality: Won the Best Code Quality award in DEF Startup's coding competition (2019)
* Open-Source Contributions: Contributed to multiple open-source projects on GitHub, including React and Node.js libraries

Education:

* Bachelor of Science in Computer Science, XYZ University (2015-2019)

Certifications:

* Certified Scrum Master (CSM), Scrum Alliance (2020)
* Certified Node.js Developer, Node.js Foundation (2019)

""",


# Resume 4

"""
Denise Guzman
Contact Information:

* Email: [denise.guzman@email.com](mailto:denise.guzman@email.com)
* Phone: (555) 123-4567
* LinkedIn: linkedin.com/in/deniseguzman
* Portfolio: deniseguzman.contently.com

Professional Summary:
Results-driven content professional with 5+ years of experience in crafting compelling, SEO-optimized content that drives engagement and conversions. Skilled in writing for various industries and formats, including blog posts, articles, product descriptions, and more. Proven track record of delivering high-quality content on time, with a strong focus on meeting client objectives and exceeding expectations.

Experience:

* Content Writer, XYZ Corporation (2018-Present)
+ Write and edit high-quality content for clients across various industries, including healthcare, finance, and technology
+ Conduct keyword research and optimize content for maximum search engine visibility
+ Collaborate with designers and developers to ensure content is visually appealing and user-friendly
+ Develop and implement content strategies to drive engagement and conversions
+ Managed a portfolio of 20+ clients, delivering an average of 20 articles per month
* Technical Writer, ABC Agency (2015-2018)
+ Created user manuals, guides, and other technical documentation for software and hardware products
+ Researched and wrote content for marketing materials, including brochures, flyers, and case studies
+ Worked with subject matter experts to ensure accuracy and clarity in technical content
+ Edited and revised content to ensure consistency and quality

Skills:

* SEO Writing and Optimization
* Copywriting and Content Strategy
* Technical Writing and Documentation
* Content Management Systems (CMS)
* Google Analytics and Tracking
* Microsoft Office and Google Suite
* Grammarly and other content editing tools

Education:

* Bachelor's Degree in English, [University Name] (2015)
* Certificate in Content Marketing, [Course Name] (2017)

Achievements:

* Awarded "Content Writer of the Year" by [Industry Publication] (2020)
* Increased client engagement by 25% through targeted content strategies and optimization (2019)
* Published 50+ articles on industry-leading publications, including [Publication Name] and [Publication Name] (2018-2020)

Certifications:

* HubSpot Inbound Marketing Certification (2019)
* Google Analytics Certification (2018)


""",

# Resume 5

"""
Alexander Nash

Contact Information:

* Phone: (123) 456-7890
* Email: [alexander.nash@email.com](mailto:alexander.nash@email.com)
* LinkedIn: linkedin.com/in/alexandernash

Professional Summary:

Results-driven business analyst with 5+ years of experience in gathering requirements, analyzing data, and presenting insights to drive business growth. Proven track record of delivering high-impact projects and improving operational efficiency. Skilled in communication, problem-solving, and stakeholder management. Seeking a challenging Business Analyst role that leverages my expertise to drive business success.

Technical Skills:

* Business Analysis methodologies (BABOK, Agile, Waterfall)
* Data analysis and visualization tools (Excel, Tableau, Power BI)
* Presentation and communication tools (Microsoft Office, PowerPoint, Prezi)
* Problem-solving and decision-making frameworks (Root Cause Analysis, Pareto Analysis)
* Collaboration and project management tools (Asana, Trello, Jira)

Professional Experience:

Business Analyst, ABC Corporation (2018-Present)

* Gathered and analyzed requirements for multiple projects, resulting in a 25% increase in project success rate
* Conducted data analysis and created visualizations to inform business decisions, leading to a 30% reduction in operational costs
* Developed and presented business cases to executive stakeholders, securing funding for 3 high-impact projects
* Collaborated with cross-functional teams to identify and prioritize business needs, ensuring alignment with corporate strategy

Business Analyst, DEF Agency (2015-2018)

* Collected and documented business requirements for software development projects, ensuring accurate implementation and timely delivery
* Analyzed business data to identify trends and opportunities, informing business decisions and driving growth
* Created and presented reports to stakeholders, providing insights and recommendations to improve business performance
* Developed and maintained relationships with key stakeholders, ensuring open communication and effective issue resolution

Education:

* Bachelor's Degree in Business Administration, XYZ University (2015)

Certifications:

* Certified Business Analyst (CBA), Business Analysis Certification Institute (2018)
* Data Analysis Certification, Data Analysis Certification Institute (2015)

Achievements:

* Recipient of the ABC Corporation's Business Analyst of the Year award (2020)
* Published article on Effective Stakeholder Management in the Business Analysis Journal (2019)
* Participated in the Business Analysis Certification Program at the Business Analysis Institute (2018)

""",

# Resume 6

"""
Tracy Martinez
Cloud Engineer

Contact Information:

* Phone: (555) 123-4567
* Email: [tracy.martinez@email.com](mailto:tracy.martinez@email.com)
* LinkedIn: linkedin.com/in/tracymartinez

Summary:
Highly motivated and experienced Cloud Engineer with a strong background in Cloud Cost Optimization and Serverless Architecture. Proven track record of delivering scalable, secure, and cost-effective cloud solutions. Skilled in designing and implementing cloud infrastructure, migrating legacy systems to the cloud, and optimizing cloud costs.

Professional Experience:

Cloud Engineer, ABC Corporation (2018-Present)

* Designed and implemented cloud infrastructure for multiple customers, resulting in a 30% reduction in overall cloud costs
* Migrated 10 legacy applications to AWS Serverless Architecture, resulting in a 50% reduction in server costs
* Collaborated with development teams to design and implement secure and scalable cloud-based solutions
* Conducted cloud cost optimization analysis and implemented cost-saving measures, resulting in a 25% reduction in cloud expenses

Cloud Architect, DEF Startups (2015-2018)

* Designed and implemented cloud infrastructure for multiple startups, resulting in a 25% reduction in overall cloud costs
* Migrated 5 legacy applications to AWS CloudFormation, resulting in a 40% reduction in server costs
* Conducted cloud security assessments and implemented security measures to ensure compliance with industry standards
* Collaborated with development teams to design and implement scalable and secure cloud-based solutions

Education:

* Bachelor's Degree in Computer Science, XYZ University (2010-2014)

Certifications:

* AWS Certified Solutions Architect - Associate
* AWS Certified Developer - Associate
* Certified Cloud Security Professional (CCSP)

Skills:

* Cloud Cost Optimization
* Serverless Architecture
* Cloud Infrastructure Design
* Cloud Security
* Cloud Migration
* AWS CloudFormation
* AWS Lambda
* AWS API Gateway
* Terraform
* Ansible
* Linux

Achievements:

* Winner of the 2020 AWS Cloud Competition for outstanding contributions to cloud innovation
* Featured speaker at the 2019 AWS Summit for expertise in cloud cost optimization
* Published article on cloud security best practices in the 2018 AWS Journal

Tools and Technologies:

* AWS CloudFormation
* AWS Lambda
* AWS API Gateway
* Terraform
* Ansible
* Linux
* Windows
* Jenkins
* Docker

""",


# Resume 7
"""
Edward Watts
Contact Information:

* Email: [ewatts@email.com](mailto:ewatts@email.com)
* Phone: (555) 123-4567
* LinkedIn: linkedin.com/in/edwardwatts

Summary:
Results-driven Product Manager with 8+ years of experience in driving business growth through effective stakeholder communication, data-driven decision making, and agile product development. Proven track record of delivering high-performing products that exceed customer expectations and drive revenue growth.

Professional Experience:

Product Manager, ABC Corporation (2018-Present)

* Led cross-functional teams to develop and launch multiple products, resulting in 25% revenue growth and 30% increase in customer satisfaction
* Collaborated with stakeholders to define product vision, strategy, and roadmap, ensuring alignment with business goals and customer needs
* Conducted market research to identify trends, opportunities, and competitive landscape, informing product development and go-to-market strategies
* Developed and tracked key performance indicators (KPIs) to measure product success, making data-driven decisions to optimize product performance

Senior Business Analyst, DEF Consulting (2015-2018)

* Analyzed complex business problems, developed solutions, and presented findings to senior stakeholders, resulting in 20% cost savings and 15% increase in productivity
* Collaborated with project teams to implement agile methodologies, ensuring timely and successful project delivery
* Conducted market research and competitive analysis to inform business strategy and product development
* Developed and maintained relationships with key stakeholders, including executive leadership, customers, and partners

Education:

* Master of Business Administration (MBA), XYZ University (2012-2014)
* Bachelor of Science in Business Administration, PQR University (2008-2012)

Skills:

* Stakeholder Communication
* Agile Methodologies
* Data Analysis and Interpretation
* Leadership and Team Management
* Market Research and Competitive Analysis
* Product Development and Launch
* Project Management
* Process Improvement

Achievements:

* Product of the Year Award (2019) - Awarded for developing and launching a product that exceeded customer expectations and drove revenue growth
* Team Leadership Award (2017) - Recognized for exceptional leadership and team management skills, resulting in successful product launches and high team morale
* Innovation Award (2015) - Awarded for developing and implementing a innovative solution that improved business processes and reduced costs

Certifications:

* Certified Scrum Master (CSM), Scrum Alliance (2016)
* Certified Business Analyst (CBA), International Institute of Business Analysis (2013)

""",

# Resume 8
"""
Joe Wells
Contact Information:

* Phone: (555) 555-5555
* Email: [joe.wells@email.com](mailto:joe.wells@email.com)
* LinkedIn: linkedin.com/in/joewellsdba
* Twitter: @joewellsdba

Professional Summary:
Highly skilled and experienced Database Administrator with 8+ years of experience in designing, implementing, and maintaining large-scale databases. Proven expertise in SQL, NoSQL, database optimization, backup and recovery, and database security. Committed to delivering high-quality solutions that meet business needs and ensure data integrity.

Technical Skills:

* Database Management Systems: Oracle, MySQL, MongoDB, Microsoft SQL Server
* Database Languages: SQL, NoSQL, PL/SQL
* Database Tools: Toad, SQL Developer, MongoDB Compass
* Operating Systems: Windows, Linux, macOS
* Backup and Recovery: Oracle Recovery Manager, MySQL Backup, MongoDB Backup
* Database Security: Access Control, Encryption, Auditing

Professional Experience:

Database Administrator, ABC Corporation (2018-Present)

* Designed and implemented a high-performance database solution for a large-scale e-commerce platform, resulting in a 30% increase in sales.
* Optimized database queries, resulting in a 25% reduction in query response time.
* Developed and maintained database security policies, ensuring data integrity and compliance with regulatory requirements.
* Collaborated with development teams to design and implement database schema changes, ensuring seamless integration with applications.

Senior Database Administrator, DEF Company (2015-2018)

* Managed a team of junior database administrators, providing guidance and mentorship to ensure high-quality database support.
* Designed and implemented a database backup and recovery solution, resulting in a 99.9% uptime and zero data loss.
* Conducted regular database performance tuning, resulting in a 20% reduction in query response time.
* Developed and maintained database security policies, ensuring compliance with regulatory requirements.

Education:

* Bachelor's Degree in Computer Science, XYZ University (2010-2014)

Certifications:

* Oracle Certified Professional (OCP) - Database Administration
* MySQL Certified Developer
* MongoDB Certified Developer

Achievements:

* Recipient of the ABC Corporation's "Employee of the Quarter" award for outstanding contributions to the company.
* Published several articles on database optimization and security in industry-leading publications.
* Presented at industry conferences on database design and implementation.

""",

# Resume 9

"""
Elizabeth Jones
Data Analyst

Contact Information:

* Phone: (555) 555-5555
* Email: [elizabeth.jones@email.com](mailto:elizabeth.jones@email.com)
* LinkedIn: linkedin.com/in/elizabethjonesdatanalyst
* Address: [Your Address]

Summary:
Highly motivated and detail-oriented Data Analyst with 3+ years of experience in data analysis, visualization, and reporting. Proficient in Excel, Tableau, Power BI, SQL, and statistical analysis. Proven track record of delivering high-quality insights and recommendations to improve business performance. Seeking a challenging role as a Data Analyst where I can utilize my skills to drive data-driven decision making.

Technical Skills:

* Microsoft Excel: Advanced formulas, pivot tables, and data visualization
* Tableau: Data visualization, dashboard creation, and data storytelling
* Power BI: Data modeling, reporting, and dashboard creation
* SQL: Data querying, indexing, and optimization
* Statistical Analysis: Regression analysis, hypothesis testing, and confidence intervals

Professional Experience:

Data Analyst, ABC Corporation (2020-Present)

* Analyzed large datasets to identify trends and insights, resulting in a 25% increase in sales revenue
* Created interactive dashboards using Tableau to visualize complex data, improving stakeholder understanding by 30%
* Developed and maintained complex SQL queries to extract data from multiple sources, improving data accuracy by 20%
* Collaborated with business stakeholders to design and implement data-driven solutions, resulting in a 15% reduction in costs

Data Analyst, DEF Startups (2018-2020)

* Analyzed customer behavior data to identify opportunities for growth, resulting in a 20% increase in customer engagement
* Created reports and visualizations using Power BI to track key performance indicators (KPIs), improving business decision-making
* Developed and maintained databases using SQL, ensuring data consistency and integrity
* Conducted statistical analysis to identify trends and patterns, informing business strategy

Education:

* Master of Science in Data Science, XYZ University (2018)
* Bachelor of Science in Mathematics, ABC University (2016)

Certifications:

* Certified Data Analyst (CDA), Data Science Council of America (2020)
* Microsoft Certified: Data Analyst Associate (2019)

Achievements:

* Winner of the ABC Corporation's Data Analytics Competition (2020)
* Featured speaker at the DEF Startups' Data Science Conference (2019)
* Published research paper on "Applying Statistical Analysis to Business Decision Making" in the Journal of Business Analytics (2018)

""",



"""
Monique Hancock
Contact Information:

* Email: [monique.hancock@email.com](mailto:monique.hancock@email.com)
* Phone: (123) 456-7890
* LinkedIn: linkedin.com/in/moniquehancock
* GitHub: github.com/moniquehancock

Summary:
Highly skilled AI Researcher with expertise in NLP, GANs, and Computer Vision. Proven track record of developing innovative solutions that drive business value. Passionate about leveraging AI to solve complex problems and drive human-machine collaboration.

Professional Experience:

Senior AI Researcher, XYZ Corporation (2018-Present)

* Led a team of researchers in developing state-of-the-art NLP models for natural language understanding and text generation
* Designed and implemented GAN-based architectures for image-to-image translation and style transfer
* Collaborated with computer vision experts to develop object detection and segmentation algorithms using convolutional neural networks
* Published research papers in top-tier conferences, including NeurIPS, IJCAI, and CVPR
* Mentored junior researchers and students in AI research and development

Research Scientist, ABC University (2015-2018)

* Developed and taught courses on AI, machine learning, and deep learning for graduate students
* Conducted research on computer vision and NLP, with a focus on image segmentation, object recognition, and text classification
* Collaborated with industry partners to develop and commercialize AI-based solutions
* Published research papers in top-tier journals, including IEEE Transactions on Pattern Analysis and Machine Intelligence and Journal of Machine Learning Research

Education:

* Ph.D. in Computer Science, ABC University (2015)
* M.Sc. in Computer Science, DEF University (2010)
* B.Sc. in Computer Science, GHI University (2008)

Skills:

* NLP: NLP libraries (NLTK, spaCy), NLP models (LSTM, GRU, attention), text classification, sentiment analysis
* GANs: PyTorch, TensorFlow, GAN architectures (DCGAN, WGAN, StyleGAN)
* Computer Vision: OpenCV, PyTorch, TensorFlow, convolutional neural networks (CNNs), object detection, segmentation
* Programming languages: Python, C++, Java
* Research software: TensorFlow, PyTorch, Keras, scikit-learn
* Operating Systems: Windows, Linux, macOS

Achievements:

* Published 10+ research papers in top-tier conferences and journals
* Awarded the Best Research Paper award at IJCAI 2019
* Developed and commercialized an AI-based solution for image classification and object detection, resulting in a 25% increase in accuracy and a 30% reduction in latency
* Collaborated with industry partners to develop and deploy AI-based solutions in computer vision, NLP, and robotics

Professional Memberships:

* Association for the Advancement of Artificial Intelligence (AAAI)
* Institute of Electrical and Electronics Engineers (IEEE)
* International Joint Conference on Artificial Intelligence (IJCAI)
* NeurIPS

""",

# Resume 11

"""
Sandra Melton
Contact Information:

* Email: [sandra.melton@email.com](mailto:sandra.melton@email.com)
* Phone: 555-555-5555
* LinkedIn: linkedin.com/in/sandramelton

Summary:
Highly skilled Data Engineer with expertise in MLOps, Airflow, Big Data, Cloud Platforms, and Spark. Proven track record of designing, building, and deploying scalable data pipelines and machine learning models that drive business value. Proficient in collaborating with cross-functional teams to drive data-driven decision-making.

Professional Experience:

Senior Data Engineer, ABC Corporation (2018-Present)

* Designed and implemented scalable data pipelines using Apache Airflow, Spark, and Python, resulting in 30% reduction in data processing time and 25% improvement in model accuracy.
* Collaborated with data scientists to develop and deploy machine learning models using TensorFlow and PyTorch, achieving 20% increase in model performance and 15% reduction in model deployment time.
* Worked with cloud teams to design and deploy cloud-agnostic data platforms on AWS and GCP, ensuring 99.99% uptime and 30% reduction in cloud costs.
* Led a team of 3 data engineers to design and implement a data lake on Apache Hadoop, resulting in 40% reduction in data storage costs and 20% improvement in data query performance.

Data Engineer, DEF Startups (2015-2018)

* Designed and implemented real-time data pipelines using Apache Kafka, Spark, and Python, resulting in 20% improvement in data freshness and 15% reduction in data processing time.
* Collaborated with data analysts to develop and deploy data visualizations using Tableau and Power BI, achieving 25% increase in data insights and 15% reduction in reporting time.
* Worked with cloud teams to design and deploy cloud-based data platforms on AWS and Azure, ensuring 99.99% uptime and 20% reduction in cloud costs.

Education:

* Master of Science in Data Science, XYZ University (2015)
* Bachelor of Science in Computer Science, ABC University (2010)

Skills:

* Programming languages: Python, Scala, Java
* Data engineering tools: Apache Airflow, Apache Spark, Apache Kafka
* Cloud platforms: AWS, GCP, Azure
* Big data platforms: Apache Hadoop, Apache HBase
* Data visualization tools: Tableau, Power BI
* Machine learning frameworks: TensorFlow, PyTorch
* Operating Systems: Linux, Windows

Certifications:

* AWS Certified Data Engineer (2019)
* Google Cloud Certified - Professional Data Engineer (2020)

Achievements:

* Winner, ABC Corporation's Data Science Competition (2019): Developed a machine learning model using TensorFlow and PyTorch that achieved 95% accuracy and 10% improvement in model performance.
* Speaker, DEF Startups' Data Engineering Conference (2018): Presented a talk on "Designing Scalable Data Pipelines using Apache Airflow and Spark".


""",

# Resume 12

"""
**Hank Brown**
**Contact Information:**

* Phone: (123) 456-7890
* Email: [hank.brown@email.com](mailto:hank.brown@email.com)
* LinkedIn: linkedin.com/in/hankbrown

**Summary:**
Highly motivated and detail-oriented software engineer with 5+ years of experience in designing, developing, and deploying scalable software solutions. Proven track record of delivering high-quality code, collaborating effectively with cross-functional teams, and driving innovation in software development.

**Technical Skills:**

* Programming languages: Java, Python, C++, JavaScript
* Development frameworks: Spring, Django, React, Angular
* Databases: MySQL, MongoDB, PostgreSQL
* Agile methodologies: Scrum, Kanban
* Version control: Git, SVN
* Cloud platforms: AWS, Azure, Google Cloud
* Operating Systems: Windows, Linux, macOS

**Experience:**

**Senior Software Engineer, ABC Corporation (2018-Present)**

* Designed and developed multiple features for a cloud-based e-commerce platform, resulting in a 30% increase in sales
* Collaborated with the DevOps team to implement CI/CD pipelines, reducing deployment time by 50%
* Mentored junior engineers, providing guidance on coding best practices and software design principles
* Participated in code reviews, ensuring high-quality code and adhering to coding standards

**Software Engineer, DEF Startups (2015-2018)**

* Developed a mobile app for a food delivery service, achieving a 4.5-star rating on the app store
* Worked on a team to design and implement a real-time analytics platform, reducing data processing time by 90%
* Contributed to the development of a machine learning model for predicting user behavior, resulting in a 25% increase in user engagement

**Achievements:**

* Recipient of the ABC Corporation's "Best Code Contribution" award (2019)
* Published a research paper on "Designing Scalable Software Systems" at the International Conference on Software Engineering (2017)
* Achieved a 95% code coverage rate on a complex software project, demonstrating exceptional testing skills

**Projects:**

* **Personal Website:** Developed a responsive, statically generated website using Hugo and GitHub Pages (https://hankbrown.com)
* **Open-Source Contributions:** Contributed to the development of several open-source projects, including the Spring Framework and the ReactJS library
* **Machine Learning Model:** Built a machine learning model using scikit-learn and TensorFlow to predict user behavior in a mobile app (https://github.com/hankbrown/user-behavior-model)

**Education:**

* **Bachelor's Degree in Computer Science, XYZ University (2015)**

**Certifications:**

* **Certified Scrum Master (CSM), Scrum Alliance (2018)**
* **Certified Java Developer, Oracle Corporation (2016)**

""",
# Resume 13
"""
**Suresh**
**Software Engineer**

**Contact Information:**

* Email: [suresh@email.com](mailto:suresh@email.com)
* Phone: 123-456-7890
* LinkedIn: linkedin.com/in/sureshsoftwareengineer

**Objective:**
To obtain a challenging and rewarding Software Engineer position that utilizes my skills in Java and API development to drive innovation and growth.

**Experience Summary:**

Highly motivated and detail-oriented Software Engineer with 1 year of experience in designing, developing, and testing software applications. Proven ability to work effectively in a team environment and deliver high-quality solutions on time. Proficient in Java and Python programming languages, with expertise in API development.

**Technical Skills:**

* Programming languages: Java, Python
* API development: Experience with designing, developing, and deploying RESTful APIs
* Software development methodologies: Agile, Scrum
* Version control systems: Git
* Operating Systems: Windows, Linux

**Professional Experience:**

**Software Engineer**, ABC Company (2022-Present)

* Designed and developed multiple software applications using Java and Python
* Developed and deployed RESTful APIs for data exchange and integration
* Collaborated with cross-functional teams to identify and prioritize project requirements
* Ensured high-quality code through thorough testing and debugging
* Participated in code reviews and provided feedback to improve code quality

**Education:**

* Bachelor's Degree in Computer Science, XYZ University (2020-2024)

**Certifications:**

* Certified Java Developer, Oracle Corporation (2022)
* Certified Python Programmer, Python Institute (2022)

"""

# Resume 14
"""
**Software Engineer Candidate**

**Contact Information:**

* Email: [lucas@email.com](mailto:lucas@email.com)
* Phone: 555-555-5555
* LinkedIn: linkedin.com/in/lucassoftwareengineer

**Summary:**
Highly accomplished Software Engineer with 8 years of Director-level experience in designing, developing, and deploying scalable, efficient, and secure software systems. Proven track record of delivering high-quality solutions with a focus on microservices architecture, cloud computing, and cutting-edge technologies. Adept at working in a fast-paced, in-office environment, with a strong passion for collaboration and innovation.

**Technical Skills:**

* Programming languages: JavaScript (ES6+), Node.js
* Frameworks: React, Express.js
* Databases: MongoDB, PostgreSQL
* Operating Systems: Windows, Linux
* Cloud platforms: AWS, Azure, Google Cloud
* Version control: Git, SVN
* Agile methodologies: Scrum, Kanban
* Microservices architecture: Design, development, and deployment
* System architecture: Design, development, and optimization
* Cloud computing: Design, development, and deployment

**Professional Experience:**

**Director of Software Engineering, ABC Corporation (2018 - Present)**

* Led a team of 10 software engineers in designing, developing, and deploying multiple software projects
* Designed and implemented microservices architecture for a large-scale e-commerce platform, resulting in a 30% increase in efficiency and a 25% reduction in costs
* Mentored junior engineers and provided technical guidance on software development best practices
* Collaborated with cross-functional teams to identify and prioritize project requirements and deliverables
* Developed and maintained technical documentation, including architecture diagrams, technical specifications, and code reviews

**Senior Software Engineer, DEF Startups (2015 - 2018)**

* Participated in the design and development of multiple software projects, including a cloud-based SaaS platform and a mobile application
* Utilized Node.js, React, and MongoDB to build scalable and efficient software systems
* Collaborated with the QA team to identify and resolve bugs, resulting in a 20% reduction in defects
* Participated in code reviews and ensured adherence to coding standards and best practices

**Education:**

* Bachelor's degree in Computer Science, XYZ University (2010 - 2014)

**Certifications:**

* Certified Scrum Master (CSM), Scrum Alliance (2016)
* Certified Cloud Practitioner, AWS (2017)

**Achievements:**

* 5.0 rating in the "Hackathon" competition, where a team of 5 engineers built a scalable, cloud-based platform in 48 hours
* Awarded "Best Engineer of the Year" by ABC Corporation for outstanding contributions to software engineering and team leadership

**Personal Projects:**

* Developed and maintained a personal blog, [lucasblog.com](http://lucasblog.com), which showcases technical expertise and thought leadership in software engineering
* Contributed to open-source projects, including [project1](https://github.com/project1) and [project2](https://github.com/project2)

""",

# Resume 14 
"""
Jean Turner
Software Engineer

Contact Information:

* Phone: (123) 456-7890
* Email: [jean.turner@email.com](mailto:jean.turner@email.com)
* LinkedIn: linkedin.com/in/jeanturner
* GitHub: github.com/jean-turner

Professional Summary:

Highly motivated and detail-oriented software engineer with 5+ years of experience in designing, developing, and deploying scalable software systems. Skilled in Java, Python, and DevOps, with a strong foundation in algorithms, data structures, and system design. Proficient in Agile methodologies and passionate about delivering high-quality software solutions.

Technical Skills:

* Programming languages: Java, Python, C++, JavaScript
* Development frameworks: Spring, Django, Flask
* Data structures and algorithms: Arrays, Linked Lists, Stacks, Queues, Trees, Graphs
* System design: Microservices, Cloud Computing, Containerization
* DevOps tools: Docker, Kubernetes, Jenkins, Git
* Agile methodologies: Scrum, Kanban

Professional Experience:

Senior Software Engineer, ABC Corporation (2018-Present)

* Designed and developed large-scale software systems using Java and Python, resulting in 30% increase in productivity and 25% reduction in bug rates
* Implemented DevOps practices, including continuous integration and continuous deployment, using Jenkins and Docker, leading to 40% reduction in deployment time
* Collaborated with cross-functional teams to identify and prioritize project requirements, resulting in 25% increase in customer satisfaction
* Mentored junior engineers on software design patterns, algorithms, and data structures, leading to 20% increase in team's overall technical expertise

Software Engineer, DEF Startup (2015-2018)

* Developed and deployed multiple web applications using Python and Django, resulting in 50% increase in user engagement and 20% increase in revenue
* Designed and implemented database schema using MySQL and Oracle, leading to 30% reduction in data retrieval time
* Collaborated with product managers to gather requirements and prioritize features, resulting in 25% increase in product adoption
* Participated in code reviews and contributed to the improvement of overall code quality

Education:

* Bachelor of Science in Computer Science, XYZ University (2015)

Achievements:

* Winner of the "Best Software Engineer" award at ABC Corporation's annual hackathon (2020)
* Published a research paper on "Efficient Algorithms for Big Data Processing" in the International Journal of Computer Science and Engineering (2019)
* Completed the "Certified Scrum Master" course and applied Agile methodologies in multiple projects (2018)

Certifications:

* Certified Scrum Master (CSM), Scrum Alliance (2018)
* Certified Java Developer (OCPJP), Oracle Corporation (2016)

""",
# Resume 15

"""Garrett Holt
Cloud Engineer

Contact Information:

* Address: 123 Main St, Anytown, USA 12345
* Phone: (555) 555-5555
* Email: [garrett.holt@email.com](mailto:garrett.holt@email.com)
* LinkedIn: linkedin.com/in/garretholt

Professional Summary:
Highly motivated and experienced Cloud Engineer with a strong background in Cloud Cost Optimization, Scripting, and Cloud Architecture. Proven track record of delivering cost-effective and scalable cloud solutions for clients across various industries. Skilled in leveraging automation tools and technologies to streamline cloud operations and improve overall efficiency.

Technical Skills:

* Cloud Platforms: AWS, Azure, Google Cloud
* Scripting Languages: Python, PowerShell, Bash
* Cloud Cost Optimization Tools: Cloudability, ParkMyCloud, AWS Cost Explorer
* Automation Tools: Ansible, Terraform, CloudFormation
* Operating Systems: Windows, Linux
* Databases: MySQL, PostgreSQL

Professional Experience:

Cloud Engineer, ABC Company (2018-Present)

* Designed and implemented cloud infrastructure for multiple clients, resulting in a 30% reduction in cloud costs
* Developed and maintained scripts for automating cloud operations, including server provisioning, deployment, and scaling
* Collaborated with cross-functional teams to identify and implement cost-optimization strategies
* Utilized Cloudability to analyze and optimize cloud spend, resulting in a 25% reduction in cloud costs
* Mentored junior engineers on cloud best practices and automation tools

Cloud Engineer, DEF Startup (2015-2018)

* Built and managed cloud infrastructure for a high-growth startup, scaling from 100 to 1,000 users
* Developed and implemented scalable architectures using AWS and Azure
* Created and maintained scripts for automating cloud operations, including deployment and scaling
* Collaborated with the DevOps team to implement continuous integration and deployment pipelines

Education:

* Bachelor's Degree in Computer Science, XYZ University (2010-2014)

Certifications:

* AWS Certified Cloud Practitioner - Cloud Architect
* Azure Certified: Azure Developer Associate
* CompTIA Cloud+ Certification

Achievements:

* Cloud Cost Optimization Award: Winner of the Cloud Cost Optimization Award at the 2020 Cloud Computing Conference
* AWS Community Builder: Recognized as an AWS Community Builder for contributions to the AWS community
* GitHub Star: Achieved over 1,000 stars on GitHub for open-source cloud automation projects
"""
    ]
    
    # Initialize the comparison system with a rejection threshold
    ats_comparison = ATSComparison(rejection_threshold=0.4)
    
    # Run comparison
    stats = ats_comparison.compare_systems(sample_resumes, job_description)
    
    # Visualize results
    ats_comparison.visualize_comparison(stats)