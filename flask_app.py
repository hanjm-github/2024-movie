import os
from dotenv import load_dotenv

from sqlalchemy import Column, Integer, String, Date

from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from bs4 import BeautifulSoup
import requests

# 데이터베이스 연결 정보
load_dotenv()
server_host = os.getenv('server_host')
user = os.getenv('user')
password = os.getenv('password')
db = os.getenv('db')

api_image = os.getenv('api_image')

key = os.getenv('api_key')

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

# 광고 링크 테이블 정의
class adlinks(db.Model):
    __tablename__ = 'adlinks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    imgURL = Column(String(255))

# 투표 테이블 정의
class Poll(db.Model):
    __tablename__ = 'poll'
    id = Column(Integer, primary_key=True, autoincrement=True)
    votes_1 = Column(Integer, default=0)
    votes_2 = Column(Integer, default=0)

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

    url = adlinks.query.all()
    adlink_list = []
    for adlink in url:
        adlink_data = {
            'imgURL': adlink.imgURL
        }
        adlink_list.append(adlink_data)

    poll = db.session.query(Poll).first()
    ironman = poll.votes_1
    cap = poll.votes_2

    return render_template('index.html', chunked_movies=chunked_movies, adlink_list=adlink_list, ironman=ironman, cap=cap)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    poll = db.session.query(Poll).first()

    if request.is_json:
        data = request.get_json()
        choice = data.get('value')
        if choice == 'choice_1':
            poll.votes_1 += 1
        elif choice == 'choice_2':
            poll.votes_2 += 1
        db.session.commit()

    return ('', 201)

@app.route('/search', methods=["GET", "POST"])
def search():
    data = request.get_json()
    search = data['action']['params']['파라미터']

    url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.xml?key={key}&movieNm={search}"

    response = requests.get(url)
    xml_data = response.content
    soup = BeautifulSoup(xml_data, 'xml')

    movieas = soup.find_all('movie')
    moviea_list = []


    for moviea in movieas:
        movieNm = moviea.find('movieNm').text
        openDt = moviea.find('openDt').text
        movieCd = moviea.find('movieCd').text
        movieLink = f"https://kobis.or.kr/kobis/business/mast/mvie/searchMovieList.do?dtTp=movie&dtCd={movieCd}"


        # 영화 정보를 리스트에 추가
        moviea_list.append({'movieNm': movieNm, 'openDt': openDt, 'movieCd': movieCd, 'movieLink': movieLink})

    if len(moviea_list) == 0:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "검색 결과가 없습니다."
                        }
                    }
                ]
            }
        }
        return jsonify(response)
    else:
        response = {
  "version": "2.0",
  "template": {
    "outputs": [
      {
        "textCard": {
          "title": moviea_list[0]['movieNm'],
          "description": "개봉일 : " + moviea_list[0]['openDt'],
          "buttons": [
            {
              "action": "webLink",
              "label": "소개 보러가기",
              "webLinkUrl": moviea_list[0]['movieLink']
            }
          ]
        }
      }
    ]
  }
}
    return jsonify(response)

@app.route('/api', methods=['GET', 'POST'])
def carousel():

    movies = Movie.query.filter(Movie.rank <= 10)
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

    
    response = {
    "version": "2.0",
    "template": {
        "outputs": [
            {
                "carousel": {
                    "type": "itemCard",
                "items": [
                {
                    "imageTitle": {
                        "title": movies_list[0]['movieNm'],
                        "description": movies_list[0]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[0]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[0]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[0]['audiAcc']) + '명'
                    },
                },
                {
                    "imageTitle": {
                        "title": movies_list[1]['movieNm'],
                        "description": movies_list[1]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[1]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[1]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[1]['audiAcc']) + '명'
                    },
                },
                {
                    "imageTitle": {
                        "title": movies_list[2]['movieNm'],
                        "description": movies_list[2]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[2]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[2]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[2]['audiAcc']) + '명'
                    },
                },
                {
                    "imageTitle": {
                        "title": movies_list[3]['movieNm'],
                        "description": movies_list[3]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[3]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[3]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[3]['audiAcc']) + '명'
                    },
                },
                {
                    "imageTitle": {
                        "title": movies_list[4]['movieNm'],
                        "description": movies_list[4]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[4]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[4]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[4]['audiAcc']) + '명'
                    },
                },
                {
                    "imageTitle": {
                        "title": movies_list[5]['movieNm'],
                        "description": movies_list[5]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[5]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[5]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[5]['audiAcc']) + '명'
                    },
                },
                {
                    "imageTitle": {
                        "title": movies_list[6]['movieNm'],
                        "description": movies_list[6]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[6]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[6]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[6]['audiAcc']) + '명'
                    },
                },
                {
                    "imageTitle": {
                        "title": movies_list[7]['movieNm'],
                        "description": movies_list[7]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[7]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[7]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[7]['audiAcc']) + '명'
                    },
                },
                {
                    "imageTitle": {
                        "title": movies_list[8]['movieNm'],
                        "description": movies_list[8]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[8]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[8]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[8]['audiAcc']) + '명'
                    },
                },
                                {
                    "imageTitle": {
                        "title": movies_list[9]['movieNm'],
                        "description": movies_list[9]['movieNm']
                    },
                    "title": "",
                    "description": "",
                    "thumbnail": {
                        "imageUrl": movies_list[9]['imgURL'],
                    },
                    "profile": {
                        "title": "일일 박스오피스",
                        "imageUrl": api_image
                    },
                    "itemList": [
                        {
                            "title": "개봉일",
                            "description": str(movies_list[9]['openDt'])
                        }
                    ],
                    "itemListAlignment" : "right",
                    "itemListSummary": {
                        "title": "총 관객 수",
                        "description": str(movies_list[9]['audiAcc']) + '명'
                    },
                }
                ]
                }
            }
        ]
    }
}
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)