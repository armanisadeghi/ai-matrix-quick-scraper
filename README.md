
## Project Summary

It is about quick scraper


[![screenshot](image.png)](https://www.loom.com/share/3648ee5b292c46aea82383ad72254f7c)

---

## Running this project

**python == 3.12.0**
python = "^3.12,<3.13"

To get this project up and running you should start by having Python installed on your computer. It's advised you create a virtual environment to store your projects dependencies separately. You can install virtualenv with

```
python -m venv venv
```

Clone or download this repository and open it in your editor of choice. In a terminal (mac/linux) or windows terminal, run the following command in the base directory of this project

```
python -m venv venv
```

That will create a new folder `venv` in your project directory. Next activate it with this command on mac/linux:

```
source venv/bin/active
```

Then install the project dependencies with

```
pip install -r requirements.txt
```

Now you can run the project with this command

```
python manage.py quick_scraper.py
```

**Note** Repalcae `.env.example` file to `.env`.
And then change base directory to current project working directory

---

You can poetry either. Be sure to include added package to poetry 