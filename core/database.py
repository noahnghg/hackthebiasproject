from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional, List
import uuid

# --- Database Models ---

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str 
    password: str
    skills: str  # JSON string or comma-separated
    experience: str
    education: str

class Job(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    title: str
    description: str
    company: str
    requirements: str


class Application(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="job.id")
    user_id: str = Field(foreign_key="user.id")
    score: float

# --- Database Setup ---

DATABASE_URL = "sqlite:///./hackthebias.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# --- User Operations ---

def add_user(user: User) -> User:
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

def get_user(user_id: str) -> Optional[User]:
    with Session(engine) as session:
        return session.get(User, user_id)
def get_user_by_email(email: str) -> Optional[User]:
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()

def get_all_users() -> List[User]:
    with Session(engine) as session:
        return session.exec(select(User)).all()

# --- Job Operations ---

def add_job(job: Job) -> Job:
    with Session(engine) as session:
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

def get_job(job_id: str) -> Optional[Job]:
    with Session(engine) as session:
        return session.get(Job, job_id)

def get_all_jobs() -> List[Job]:
    with Session(engine) as session:
        return session.exec(select(Job)).all()

def search_jobs(query: str) -> List[Job]:
    with Session(engine) as session:
        statement = select(Job).where(
            (Job.title.contains(query)) | 
            (Job.company.contains(query)) |
            (Job.description.contains(query))
        )
        return session.exec(statement).all()

# --- Application Operations ---

def add_application(application: Application) -> Application:
    with Session(engine) as session:
        session.add(application)
        session.commit()
        session.refresh(application)
        return application

def get_application(application_id: str) -> Optional[Application]:
    with Session(engine) as session:
        return session.get(Application, application_id)

def get_applications_for_job(job_id: str) -> List[Application]:
    with Session(engine) as session:
        statement = select(Application).where(Application.job_id == job_id)
        return session.exec(statement).all()

def get_applications_for_user(user_id: str) -> List[Application]:
    with Session(engine) as session:
        statement = select(Application).where(Application.user_id == user_id)
        return session.exec(statement).all()

# --- Seed Sample Data ---

def seed_sample_jobs():
    """Insert sample job data into the database."""
    sample_jobs = [
        Job(
            user_id="test-user-001",
            title="Software Developer Intern",
            company="Nokia",
            description="""Duration: 4 Months+ (May 4 - August 28, 2026). Location: Hybrid in Ottawa Office. Number of Position(s): 1.

As a part of our team, you will collaborate with software designers and testers to refine requirements, develop, and test product features. You will investigate and fix product defects while enhancing automated test suites. You'll gain hands-on experience working in an agile environment, participating in sprint planning, daily standups, and retrospectives. 

You will have the opportunity to work on real production systems that serve millions of users globally. Our mentorship program pairs you with senior engineers who will guide your professional development throughout the internship.""",
            requirements="2nd year+ Master's or Bachelor's in Engineering/CS with an accredited school in Canada. Strong foundation in data structures, algorithms, and SQL. Proficiency in Java, JavaScript, React, or Go. Effective problem-solving skills. Strong communication and teamwork abilities. Nice to have: Experience with Git, IDEs, Jira, Kubernetes, container orchestration, networking and telecommunications knowledge."
        ),
        Job(
            user_id="test-user-001",
            title="Backend Engineering Intern",
            company="Shopify",
            description="""Duration: 4 Months (May - August 2026). Location: Remote (Canada). Number of Position(s): 2.

Join Shopify's Core Platform team to design and implement RESTful APIs powering the world's largest commerce platform. You will work on high-traffic distributed systems that handle millions of requests per second during peak shopping events like Black Friday.

Your responsibilities include building new API endpoints, optimizing database queries for performance, implementing caching strategies, and participating in code reviews with senior engineers. You'll learn about system design, scalability patterns, and best practices for building resilient microservices. 

We offer a comprehensive onboarding program, weekly learning sessions, and access to all of Shopify's internal tools and resources. You'll also participate in hackathons and demo days to showcase your work.""",
            requirements="Currently pursuing Bachelor's or Master's in Computer Science. Strong knowledge of Python or Ruby. Experience with PostgreSQL and Redis. Understanding of microservices architecture. Good communication skills and ability to work independently in a remote environment."
        ),
        Job(
            user_id="test-user-002",
            title="Machine Learning Co-op",
            company="Google DeepMind",
            description="""Duration: 8 Months (January - August 2026). Location: Hybrid in Toronto Office. Number of Position(s): 1.

Join DeepMind's research team to work on cutting-edge artificial intelligence projects. You will research and implement deep learning models for various applications including natural language processing, computer vision, and reinforcement learning.

As a member of our team, you will collaborate with world-class researchers on projects with potential for academic publication. You'll have access to state-of-the-art computing infrastructure including TPU clusters and cutting-edge GPU systems.

Your work may involve designing novel neural network architectures, running large-scale experiments, analyzing results, and contributing to research papers. You'll participate in weekly paper reading groups, attend internal seminars from leading AI researchers, and receive mentorship from PhD-level scientists.""",
            requirements="Master's or PhD candidate in CS, Math, Physics, or related field. Strong foundation in machine learning and deep learning fundamentals. Proficiency in Python and frameworks like PyTorch or TensorFlow. Prior research experience with publications preferred. Strong mathematical background in linear algebra and probability."
        ),
        Job(
            user_id="test-user-002",
            title="Cloud Infrastructure Intern",
            company="Amazon Web Services",
            description="""Duration: 4 Months (May - August 2026). Location: Hybrid in Vancouver Office. Number of Position(s): 3.

As part of AWS's Infrastructure team, you will build and maintain cloud services used by millions of developers worldwide. Your work will directly impact the reliability and performance of AWS services that power the internet's most critical applications.

You will automate deployment pipelines using Infrastructure as Code tools, work on container orchestration platforms, and implement monitoring and alerting systems. You'll gain experience with internal AWS tools and services before they're released publicly.

The internship includes a structured project with clear deliverables, regular 1:1s with your manager, and opportunities to present your work to senior leadership. You'll also participate in AWS's intern programming including tech talks, networking events, and community service activities.""",
            requirements="3rd year+ Bachelor's in Computer Science or Engineering. Experience with AWS services (EC2, S3, Lambda). Proficiency in Docker and Kubernetes. Strong Linux/Unix command line skills. Programming experience in Python, Go, or Java. Understanding of networking concepts and TCP/IP."
        ),
        Job(
            user_id="test-user-002",
            title="Frontend Developer Intern",
            company="Wealthsimple",
            description="""Duration: 4 Months (May - August 2026). Location: Remote (Canada). Number of Position(s): 2.

Join Wealthsimple's Product Engineering team to build beautiful, responsive web applications that help Canadians achieve financial freedom. You will work closely with product designers to implement pixel-perfect user interfaces using modern React patterns.

Your responsibilities include developing new features for our investment platform, optimizing web performance for mobile devices, implementing accessibility standards, and writing comprehensive unit and integration tests.

You'll participate in design reviews, contribute to our component library, and learn about financial technology regulations and compliance. Our remote-first culture includes virtual team events, learning stipends, and flexible working hours. You'll receive mentorship from senior engineers and have access to professional development resources.""",
            requirements="2nd year+ Bachelor's in Computer Science. Proficiency in JavaScript, React, and TypeScript. Strong understanding of HTML5 and CSS3 best practices. Experience with responsive design and cross-browser compatibility. Familiarity with Git version control. Strong attention to detail and passion for user experience."
        ),
        Job(
            user_id="test-user-002",
            title="Data Engineering Co-op",
            company="Databricks",
            description="""Duration: 8 Months (January - August 2026). Location: Hybrid in San Francisco or Remote. Number of Position(s): 1.

Join Databricks to work on the platform that powers data and AI for the world's most innovative companies. You will build and optimize data pipelines that process petabytes of data daily, implement data quality monitoring systems, and work with large-scale distributed computing frameworks.

As a Data Engineering Co-op, you'll contribute to our internal data infrastructure, helping teams across the company make data-driven decisions. You'll work with Apache Spark, Delta Lake, and other cutting-edge data technologies that we've pioneered.

The internship includes exposure to multiple teams, opportunities to work on open-source projects, and a structured program designed to maximize your learning. You'll participate in technical talks, code reviews, and have the opportunity to present your projects to the broader engineering organization.""",
            requirements="Master's or Bachelor's candidate in CS, Data Science, or related field. Experience with Python and SQL. Familiarity with Apache Spark or similar distributed computing frameworks. Understanding of data warehousing concepts and ETL pipelines. Knowledge of cloud platforms (AWS, Azure, or GCP). Strong analytical and troubleshooting skills."
        ),
        Job(
            user_id="test-user-002",
            title="DevOps Engineering Intern",
            company="Microsoft",
            description="""Duration: 4 Months (May - August 2026). Location: Hybrid in Vancouver Office. Number of Position(s): 2.

Join Microsoft's Azure DevOps team to work on the tools and infrastructure that power software development for millions of developers. You will automate CI/CD pipelines, implement infrastructure as code solutions, and monitor and improve system reliability.

Your responsibilities include developing automation scripts, configuring cloud resources using Terraform and ARM templates, implementing monitoring and alerting using Azure Monitor, and participating in on-call rotations to learn incident response.

You'll work alongside senior engineers on real production systems, attend design reviews, and contribute to internal documentation. Microsoft offers a comprehensive intern program including networking events, executive speaker series, and hackathons. You'll also have access to Microsoft's learning resources and certification programs.""",
            requirements="3rd year+ Bachelor's in Computer Science or related field. Experience with Azure or AWS cloud platforms. Knowledge of Terraform, Docker, and container orchestration. Proficiency in scripting languages like Python or Bash. Understanding of networking, security, and Linux system administration."
        ),
        Job(
            user_id="test-user-002",
            title="Full Stack Developer Intern",
            company="Stripe",
            description="""Duration: 4 Months (May - August 2026). Location: Remote (North America). Number of Position(s): 3.

Join Stripe to build the economic infrastructure of the internet. As a Full Stack Developer Intern, you will work on end-to-end features for our payment platform, from frontend user interfaces to backend APIs and database systems.

You'll contribute to products used by millions of businesses worldwide, including the Stripe Dashboard, API documentation, and developer tools. Your work will directly impact how businesses accept payments and manage their finances.

Stripe's intern program is designed to give you ownership of meaningful projects from day one. You'll participate in agile development processes, code reviews, and have a dedicated mentor. We offer remote-first flexibility, comprehensive benefits, and a supportive learning environment. Past interns have shipped features to production and contributed to open-source projects that are used by developers globally.""",
            requirements="2nd year+ Bachelor's or Master's in Computer Science. Proficiency in React, Node.js, or Ruby. Experience with relational databases like PostgreSQL. Understanding of RESTful API design principles. Strong problem-solving skills and ability to work effectively in distributed teams. Interest in fintech and payments industry."
        )
    ]
    
    with Session(engine) as session:
        # Check if jobs already exist
        existing_jobs = session.exec(select(Job)).first()
        if existing_jobs:
            print("Sample jobs already exist, skipping seed.")
            return
        
        for job in sample_jobs:
            session.add(job)
        session.commit()
    
    print(f"Inserted {len(sample_jobs)} sample jobs.")

def seed_test_user():
    """Insert a test user into the database."""
    test_user_1 = User(
        id="test-user-001",
        email="test@example.com",
        password="password123",
        skills="Python, FastAPI, PyTorch, TensorFlow, AWS, Docker, React, Node.js, PostgreSQL, Machine Learning",
        experience="Engineered a context-aware pipeline using LangChain and Gemini reducing maintenance time by 25%. Developed PyTorch inference microservices using FastAPI achieving latency under 100ms. Architected full-stack platform with React and Python microservices reducing latency by 40%.",
        education="University of Calgary, Bachelor of Science in Computer Science"
    )
    test_user_2 = User(
        id="test-user-002",
        email="test2@example.com",
        password="password123",
        skills="Java, Spring Boot, AWS, Docker, React, Node.js, PostgreSQL, Distributed Systems, 3+ years experience",
        experience="Engineered a context-aware pipeline using LangChain and Gemini reducing maintenance time by 25%. Developed PyTorch inference microservices using FastAPI achieving latency under 100ms. Architected full-stack platform with React and Python microservices reducing latency by 40%.",
        education="University of Calgary, Bachelor of Science in Computer Science"
    )
    
    # Job poster users
    job_posters = [test_user_1, test_user_2]
    
    # Create applicant users (12 applicants with varying skills and detailed tech experience)
    applicant_profiles = [
        ("applicant-001", "alice@email.com", 
         "Python, JavaScript, React, Node.js, MongoDB, AWS, Docker, Git, REST APIs",
         "Built scalable e-commerce platforms using React and Node.js handling 10k daily users. Developed RESTful APIs with Express.js and MongoDB. Deployed applications on AWS EC2 with Docker containers. Implemented CI/CD pipelines using GitHub Actions.",
         "MIT, Bachelor of Science in Computer Science, 2024"),
        
        ("applicant-002", "bob@email.com", 
         "Java, Spring Boot, PostgreSQL, Kubernetes, AWS, Microservices, Redis, Kafka",
         "Led backend team at fintech startup building microservices with Spring Boot and Java. Designed distributed systems processing 50k transactions per second. Implemented event-driven architecture using Apache Kafka. Managed Kubernetes clusters on AWS EKS.",
         "Stanford University, Master of Science in Software Engineering, 2023"),
        
        ("applicant-003", "carol@email.com", 
         "Python, TensorFlow, PyTorch, Machine Learning, Deep Learning, NLP, Computer Vision, Pandas, NumPy",
         "Conducted deep learning research on transformer models and NLP at university lab. Published 3 papers on neural network optimization. Implemented computer vision models achieving 95% accuracy on image classification. Experience with PyTorch, TensorFlow, and JAX frameworks.",
         "UC Berkeley, PhD Candidate in Computer Science (Machine Learning), Expected 2025"),
        
        ("applicant-004", "david@email.com", 
         "Go, Rust, C++, Distributed Systems, Linux, Networking, gRPC, Protocol Buffers",
         "Built high-performance distributed systems in Go and Rust serving 1M requests per second. Developed low-latency networking components using C++ and Linux kernel modules. Implemented gRPC services with Protocol Buffers. Experience with consensus algorithms and distributed databases.",
         "Carnegie Mellon University, Bachelor of Science in Computer Science, 2023"),
        
        ("applicant-005", "emma@email.com", 
         "TypeScript, React, Vue, CSS, Tailwind, Figma, UI/UX Design, Storybook, Jest",
         "Created enterprise design systems in React and TypeScript used by 50+ developers. Built pixel-perfect UIs with Tailwind CSS and responsive design patterns. Developed component libraries with Storybook documentation. Implemented comprehensive testing with Jest and React Testing Library.",
         "Georgia Tech, Bachelor of Science in Computer Science, 2024"),
        
        ("applicant-006", "frank@email.com", 
         "Python, SQL, Spark, Airflow, Data Engineering, ETL Pipelines, Databricks, Snowflake, AWS Glue",
         "Built data pipelines processing 10TB daily using Apache Spark and Airflow. Designed ETL workflows on Databricks Delta Lake. Implemented data quality monitoring with Great Expectations. Experience with Snowflake data warehouse and AWS Glue for serverless ETL.",
         "University of Washington, Master of Science in Data Science, 2023"),
        
        ("applicant-007", "grace@email.com", 
         "JavaScript, React Native, iOS, Swift, Android, Kotlin, Firebase, GraphQL",
         "Developed cross-platform mobile apps with React Native reaching 100k downloads. Built native iOS features using Swift and SwiftUI. Implemented real-time features with Firebase and GraphQL subscriptions. Experience with mobile CI/CD using Fastlane and Bitrise.",
         "UCLA, Bachelor of Science in Computer Science, 2024"),
        
        ("applicant-008", "henry@email.com", 
         "AWS, Azure, Terraform, Docker, Kubernetes, CI/CD, DevOps, Ansible, Prometheus, Grafana",
         "Reduced deployment time by 80% implementing CI/CD pipelines with GitHub Actions and ArgoCD. Managed infrastructure as code using Terraform across AWS and Azure. Set up Kubernetes clusters with Helm charts and service mesh. Built monitoring dashboards with Prometheus and Grafana.",
         "University of Toronto, Bachelor of Science in Computer Engineering, 2023"),
        
        ("applicant-009", "iris@email.com", 
         "Python, R, Statistics, Machine Learning, Data Analysis, Scikit-learn, Pandas, SQL, Tableau",
         "Built recommendation systems using collaborative filtering and matrix factorization increasing sales by 15%. Conducted A/B testing and statistical analysis for product decisions. Developed ML models with Scikit-learn for customer churn prediction. Created executive dashboards in Tableau.",
         "Harvard University, Master of Science in Statistics, 2023"),
        
        ("applicant-010", "jack@email.com", 
         "Java, Kotlin, Android, Firebase, REST APIs, Room Database, Jetpack Compose, MVVM",
         "Developed Android apps with Kotlin using Jetpack Compose and MVVM architecture. Implemented offline-first features with Room database and WorkManager. Built real-time chat features with Firebase Realtime Database. Published 3 apps on Google Play Store with 50k+ downloads.",
         "University of Waterloo, Bachelor of Software Engineering, 2024"),
        
        ("applicant-011", "kate@email.com", 
         "Ruby, Rails, PostgreSQL, Redis, Sidekiq, GraphQL, Docker, Heroku",
         "Built SaaS platform with Ruby on Rails serving 5k paying customers. Implemented background job processing with Sidekiq and Redis. Designed GraphQL APIs for flexible data fetching. Deployed and scaled applications on Heroku with PostgreSQL.",
         "Brown University, Bachelor of Science in Computer Science, 2023"),
        
        ("applicant-012", "leo@email.com", 
         "Python, Django, FastAPI, PostgreSQL, Docker, Celery, RabbitMQ, Elasticsearch",
         "Developed high-traffic APIs with FastAPI handling 10k requests per minute. Built full-stack applications with Django and Django REST Framework. Implemented search functionality with Elasticsearch. Used Celery and RabbitMQ for distributed task processing.",
         "University of Michigan, Bachelor of Science in Computer Science, 2024"),
    ]
    
    applicants = [
        User(id=uid, email=email, password="password123", skills=skills, experience=exp, education=edu)
        for uid, email, skills, exp, edu in applicant_profiles
    ]
    
    with Session(engine) as session:
        # Check if user already exists
        existing = session.get(User, "test-user-001")
        if not existing:
            for user in job_posters + applicants:
                session.add(user)
            session.commit()
            print(f"Inserted {len(job_posters)} job posters and {len(applicants)} applicants.")
        else:
            print("Test users already exist, skipping seed.")

def seed_sample_applications():
    """Insert sample applications for each job (about 10 per job)."""
    import random
    from utils.semantics import semantics_instance
    
    with Session(engine) as session:
        # Check if applications already exist
        existing_apps = session.exec(select(Application)).first()
        if existing_apps:
            print("Sample applications already exist, skipping seed.")
            return
        
        # Get all jobs
        jobs = session.exec(select(Job)).all()
        
        # Get all applicant users (not job posters)
        all_users = session.exec(select(User)).all()
        applicants = [u for u in all_users if u.id.startswith("applicant-")]
        
        if not jobs or not applicants:
            print("No jobs or applicants found, skipping application seed.")
            return
        
        print("Seeding applications with NLP scoring (this may take a moment)...")
        applications_created = 0
        for job in jobs:
            # Get applicants who are not the job poster
            eligible_applicants = [a for a in applicants if a.id != job.user_id]
            
            # Randomly select 8-12 applicants for this job
            num_applicants = min(len(eligible_applicants), random.randint(8, 12))
            selected = random.sample(eligible_applicants, num_applicants)
            
            # Build job string for scoring
            job_string = f"{job.title} {job.description} {job.requirements}"
            
            for applicant in selected:
                # Build user data string for scoring
                user_data = f"{applicant.skills} {applicant.experience} {applicant.education}"
                
                # Calculate real score using NLP pipeline
                score = semantics_instance.get_final_score(job_string, user_data)
                
                app = Application(
                    job_id=job.id,
                    user_id=applicant.id,
                    score=round(score, 3)
                )
                session.add(app)
                applications_created += 1
        
        session.commit()
        print(f"Inserted {applications_created} sample applications with NLP scores.")