from app.main import app
from flask import Flask
import datetime
if __name__ == '__main__':
    with open('readme.md','a') as f:
        f.write(f'Last update : {datetime.datetime.now()}\n')
    app.run(debug=True)