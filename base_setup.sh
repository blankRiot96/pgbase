rm -rf .git/

pre-commit install

git init
git add .gitignore
git commit -m "added .gitignore"
git add .
git commit -m "initial commit"
