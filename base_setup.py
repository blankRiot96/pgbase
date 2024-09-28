import os

os.rmdir(".git")
os.system("pre-commit install")

os.system("git init")
os.system("git add .gitignore")
os.system("git commit -m 'added .gitignore'")
os.system("git add .")
os.system("git commit -m 'initial commit'")

os.system("py -m venv venv")
os.system("source venv/bin/activate.fish")
os.system("pip install -r requirements.txt")
