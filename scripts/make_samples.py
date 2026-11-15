
import os
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = os.path.join(os.path.dirname(__file__), "..", "samples"); os.makedirs(OUT, exist_ok=True)
P = [  # name, title, years, degree, skills sentence, project line
 ("Aarav Mehta","Senior Backend Engineer",6,"B.Tech Computer Science","Python, FastAPI, PostgreSQL, Docker, AWS, REST APIs, Git, CI/CD","Built microservices serving 2M requests/day and a spaCy-based document classifier."),
 ("Diya Sharma","ML Engineer",4,"M.Tech Artificial Intelligence","Python, PyTorch, Transformers, NLP, spaCy, scikit-learn, Docker","Fine-tuned BERT models for resume and ticket classification; deployed with FastAPI."),
 ("Rohan Iyer","Full Stack Developer",3,"B.E. Information Technology","JavaScript, React, Node.js, MongoDB, HTML, CSS, Git","Developed React dashboards and REST APIs with Express and MongoDB."),
 ("Sneha Kulkarni","Java Developer",5,"B.Tech Computer Science","Java, Spring Boot, SQL, MySQL, Microservices, Jenkins, Docker","Designed Spring Boot microservices for a banking platform."),
 ("Kabir Singh","Data Analyst",2,"B.Sc Statistics","Python, Pandas, NumPy, SQL, Tableau, Power BI, data analysis","Created Tableau dashboards and automated reporting using Pandas."),
 ("Meera Nair","AI Engineer",3,"B.Tech AI and Data Science","Python, FastAPI, React, Transformers, NLP, PostgreSQL, Docker, Git","Built an NLP-powered semantic search engine with sentence embeddings and a React frontend."),
 ("Vikram Rao","DevOps Engineer",7,"B.E. Computer Engineering","Linux, Docker, Kubernetes, AWS, Jenkins, CI/CD, Python, Git","Managed Kubernetes clusters and automated deployments on AWS."),
 ("Ananya Gupta","Python Developer",2,"BCA","Python, Flask, SQL, HTML, CSS, REST APIs, Git","Developed Flask REST APIs and automated data pipelines."),
 ("Ishaan Verma","Frontend Developer",4,"B.Tech Computer Science","JavaScript, TypeScript, React, HTML, CSS, Git, REST APIs","Built responsive React and TypeScript interfaces for an e-commerce site."),
 ("Pooja Desai","NLP Research Engineer",5,"M.Sc Computer Science","Python, NLP, spaCy, Transformers, PyTorch, Deep Learning, MongoDB","Published research on named-entity recognition; built information extraction pipelines."),
 ("Arjun Patel","Junior Developer",1,"B.Tech Computer Science","Python, Django, SQL, Git, HTML","Built a Django blog and a small inventory app."),
 ("Tanvi Joshi","Machine Learning Engineer",6,"M.Tech Computer Science","Python, Machine Learning, scikit-learn, TensorFlow, FastAPI, PostgreSQL, AWS, Docker","Productionised ML ranking models behind FastAPI services on AWS."),
]
def lines(i):
    n,t,y,d,s,pr = P[i]; e=f"{n.split()[0].lower()}.{n.split()[1].lower()}@example.com"
    return [n, f"{t} | {e} | +91 98765 4{i:04d}", "", "SUMMARY", f"{t} with {y} years of experience building software products.",
            "", "SKILLS", s, "", "EXPERIENCE", f"{t}, Sample Tech Pvt Ltd, {2025-y} - Present", pr,
            "", "EDUCATION", d]
JD = """Senior AI / Backend Engineer
We are looking for an engineer with 4+ years of experience building AI-powered web services.
Strong Python and FastAPI skills are required, along with PostgreSQL and REST API design.
Hands-on experience with NLP, Transformers or spaCy for text processing is required.
Experience with Docker and Git is required.
Experience with React is a plus. AWS is nice to have.
Bachelor's degree in Computer Science or related field.
You will build semantic search and ranking systems that process large volumes of documents."""
open(os.path.join(OUT,"sample_jd.txt"),"w").write(JD)
for i in range(len(P)):
    base=os.path.join(OUT,f"resume_{i+1:02d}_{P[i][0].replace(' ','_')}")
    if i%2==0:
        d=Document()
        for l in lines(i): d.add_paragraph(l)
        d.save(base+".docx")
    else:
        c=canvas.Canvas(base+".pdf",pagesize=A4); y=800
        for l in lines(i): c.drawString(50,y,l); y-=18
        c.save()
print("Wrote", len(P), "resumes + sample_jd.txt to", os.path.abspath(OUT))
