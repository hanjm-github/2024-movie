import os
from dotenv import load_dotenv

from sqlalchemy import Column, Integer, String, Date

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy


# 데이터베이스 연결 정보
load_dotenv()
server_host = os.getenv('server_host')
user = os.getenv('user')
password = os.getenv('password')
db = os.getenv('db')

# Flask 앱 설정
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{user}:{password}@{server_host}/{db}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.ensure_ascii = False

db = SQLAlchemy(app)

# 영화 테이블 정의
class Movie(db.Model):
    __tablename__ = 'dailyboxoffice'
    rank = Column(Integer, primary_key=True)
    movieNm = Column(String(255))
    openDt = Column(Date)
    audiAcc = Column(Integer)
    movieCd = Column(Integer)
    imgURL = Column(String(255))

# 데이터를 chunk로 나누는 함수
def chunk_list(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

# 영화 데이터를 HTML 템플릿으로 반환하는 엔드포인트 추가
@app.route('/', methods=['GET','POST'])
def show_movies():
    movies = Movie.query.filter(Movie.rank <= 9)
    movies_list = []
    for movie in movies:
        movie_data = {
            'rank': movie.rank,
            'movieNm': movie.movieNm,
            'openDt': movie.openDt,
            'audiAcc': movie.audiAcc,
            'movieCd': movie.movieCd,
            'imgURL': movie.imgURL
        }
        movies_list.append(movie_data)
    chunked_movies = list(chunk_list(movies_list, 3))
    return render_template('index.html', chunked_movies=chunked_movies)


if __name__ == '__main__':
    app.run(debug=True)