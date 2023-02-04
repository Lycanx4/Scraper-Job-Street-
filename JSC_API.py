import pandas as pd 
from bs4 import BeautifulSoup 
from selenium.webdriver import Chrome
import pandas as pd
import re 
import time
import json
import math
from waitress import serve
from flask import jsonify
from flask import Flask,render_template, url_for,request,redirect

#Chrome Imposter
headers = {'User-Agent':'Chrome/44.0.2403.157'}
# path to the chromedriver
path = "CD/chromedriver"

base_url = "https://www.jobstreet.com.my/en/job-search/{}-jobs/{}/"
driver = Chrome(executable_path=path)
time.sleep(2)

def get_page_number(keyword):
    #input: keyword for job_postings
    #output: number of pages
    print(keyword)
    url = base_url.format(keyword, 1)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    result_text = soup.find("span",{"class": "sx2jih0 zcydq84u es8sxo0 es8sxo1 es8sxo21 _1d0g9qk4 es8sxo7"})
    print("result_text", result_text)
    results = result_text.text.split()
    print("results", results)
    result = result_text.text.split()[-2]
    print("result", result)
    resultInt = int(result.replace(',',''))
    print(resultInt)
    page_number = math.ceil(resultInt/30)
    print(page_number)
    
    return page_number

def job_page_scraper(link):

    url = "https://www.jobstreet.com.my"+link
    print("scraping...", url)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    scripts = soup.find_all("script")
    postedDate=""
    jobTitle=""
    jobDescription=""

    for script in scripts:
        if script.contents:
            txt = script.contents[0].strip()
            if 'window.REDUX_STATE = ' in txt:
                jsonStr = script.contents[0].strip()
                jsonStr = jsonStr.split('window.REDUX_STATE = ')[1].strip()
                jsonStr = jsonStr.split('}}}};')[0].strip()
                jsonStr = jsonStr+"}}}}"
                jsonObj = json.loads(jsonStr)
    try:
        jobTitle = jsonObj["details"]["header"]["jobTitle"]
        job=jsonObj["details"]["jobDetail"]
        jobDescription = job["jobDescription"]["html"]
        jobRequirement = job["jobRequirement"]
        postedDate = jobRequirement["postedDate"]
    except:
        print("Invalid Link, skip!!!")

    return [jobTitle, postedDate, jobDescription, url]

def page_crawler(keyword):
    # input: keyword for job postings
    # output: dataframe of links scraped from each page

    # to get all page number change my hard coding and open this
    # page_number = get_page_number(keyword)

    #But for now only use 2 pages, otherwise we need to wait like forever
    page_number = 2
    job_links = []

    for n in range(page_number):
        print('Loading page {} ...'.format(n+1))
        url = base_url.format(keyword, n+1)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    
        #extract all job links
        links = soup.find_all('a',{'class':'_1hr6tkx5 _1hr6tkx7 _1hr6tkxa sx2jih0 sx2jihf zcydq8h'})
        
        job_links += links
 
    jobs = []

    for link in job_links:
        job_link = link['href'].strip().split('?', 1)[0]
        if "job-search" not in job_link:
            print(job_link)
            jobs.append(job_page_scraper(job_link))

    print(jobs)
    result_df = pd.DataFrame(jobs, columns = ["jobTitle","postedDate","jobDescription","jobUrl"])
    return result_df

def getData(keyword):
    file = keyword.lower() + "_results.csv"
    df = pd.read_csv(file)
    df2Json = df.to_json(orient="records")
    data = json.loads(df2Json)
    return data

def crawlData(key_word):
    key = key_word.replace("_", " ")
    df = page_crawler(key)
    name = key_word.lower() + "_results.csv"
    # save scraped information as csv
    df.to_csv(name, index=False)
    return getData(key_word)

app = Flask(__name__)

# http://localhost:8080/
@app.route("/")
def hello():
    return "Hello, this is Kaung Myat & this is job scraper!"

# !!!Don't call this method for frontend it take 5-10min!!!
# http://localhost:8081//crawl_jobdata/?keyword=
@app.route('/crawl_jobdata/', methods=['GET','POST'])
def request_crawl():
    keyword = request.args.get('keyword') or request.form.get('keyword') 
    return crawlData(keyword)

# http://localhost:8081//request_data/?keyword=software_developer
@app.route('/request_jobdata/', methods=['GET','POST'])
def request_data():
    keyword = request.args.get('keyword') or request.form.get('keyword') 
    try:
        data = getData(keyword)
        return data
    except:
        print("No Available data")
    return "No data found"

# run the server #the imposter browser will pop up >>> DO NOT CLOSE IT <<<
if __name__ == '__main__':
    print("Starting the server.....")
    serve(app, host="0.0.0.0", port=8081)