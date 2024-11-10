# 기본 라이브러리
from datetime import *
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# 데이터베이스 관련 라이브러리
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker, declarative_base

# Selenium 관련 라이브러리
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
key = os.getenv('api_key')

# 데이터베이스 연결 정보
server_host = os.getenv('server_host')
user = os.getenv('user')
password = os.getenv('password')
db = os.getenv('db')

# 어제 날짜 구하기
today = datetime.today()
yesterday = today - timedelta(days=1)
target_date = yesterday.strftime("%Y%m%d")
yesterday_str = yesterday.strftime("%Y-%m-%d")

# API URL 생성
url = f"https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.xml?key={key}&targetDt={target_date}"

# XML 데이터를 가져옴
response = requests.get(url)
xml_data = response.content
soup = BeautifulSoup(xml_data, 'xml')

# 영화 정보 추출
movies = soup.find_all('dailyBoxOffice')
movie_list = []

# 데이터베이스 연결 설정
DATABASE_URL = f"mysql+pymysql://{user}:{password}@{server_host}/{db}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# 영화 테이블 정의
class Movie(Base):
    __tablename__ = 'dailyboxoffice'
    #id = Column(Integer, primary_key=True, autoincrement=True)
    rank = Column(Integer, primary_key=True)
    movieNm = Column(String(255))
    openDt = Column(Date)
    audiAcc = Column(Integer)
    movieCd = Column(Integer)
    imgURL = Column(String(255))

# 기존 테이블 삭제 및 새로 생성
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# 세션 생성
Session = sessionmaker(bind=engine)
session = Session()

# Chrome Driver 설정
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 브라우저 창을 띄우지 않음
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 영화 정보 추출
for movie in movies:
    rank = movie.find('rank').text
    movieNm = movie.find('movieNm').text
    openDt = movie.find('openDt').text
    audiAcc = movie.find('audiAcc').text
    movieCd = movie.find('movieCd').text

    # 영화 포스터 이미지 URL 추출
    url = f"https://kobis.or.kr/kobis/business/mast/mvie/searchMovieList.do?dtTp=movie&dtCd={movieCd}"
    driver.get(url)

    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'fl'))
    )
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    soup = soup.find('a', class_='fl')['href']
    imgURL ='https://kobis.or.kr'+soup

    # 영화 정보를 리스트에 추가
    movie_list.append({'rank': rank, 'movieNm': movieNm, 'openDt': openDt, 'audiAcc': audiAcc, 'movieCd': movieCd, 'imgURL': imgURL})

# 데이터베이스에 추가
for movie in movie_list:
    new_movie = Movie(rank=movie['rank'], movieNm=movie['movieNm'], openDt=movie['openDt'], audiAcc=movie['audiAcc'], movieCd=movie['movieCd'], imgURL=movie['imgURL'])
    session.add(new_movie)

# 변경사항 커밋
session.commit()