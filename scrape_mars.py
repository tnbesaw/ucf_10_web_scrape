from splinter import Browser
from bs4 import BeautifulSoup
import pandas as pd
from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo



executable_path = {'executable_path': 'chromedriver.exe'}
browser = Browser('chrome', **executable_path, headless=True)

results = {}

def scrapeNews():
    #Scrape the NASA Mars News Site and 
    #collect the latest News Title and Paragraph Text. 
    news_dic_list = []
    news_keys = ['news_title', 'news_desc']
    #news_vals = []

    # define url and goto page
    url = 'https://mars.nasa.gov/news'
    browser.visit(url)

    # HTML object
    html = browser.html

    # Parse HTML with Beautiful Soup
    soup = BeautifulSoup(html, 'html.parser')

    # Retrieve news titles
    v_items = soup.find_all('li', class_='slide')
    print(v_items)
    
    for rec in v_items:    
        news_vals = []

        v_title = rec.find('div', class_='content_title').text
        news_vals.append(v_title)

        v_desc = rec.find('div', class_='article_teaser_body').text
        news_vals.append(v_desc)

        # add scrape results to dictionary list
        news_dic_list.append(dict(zip(news_keys, news_vals)))

    print(news_dic_list)   
    # assign to results object
    results["news"] = news_dic_list


def scrapeFeaturedImage():
    # find the image url for the current Featured Mars Image 
    # and assign the url string to a variable called featured_image_url.
    #   Make sure to find the image url to the full size .jpg image.
    #   Make sure to save a complete url string for this image.

    # define url and goto page
    base_url = 'https://www.jpl.nasa.gov/'
    url = base_url + 'spaceimages/?search=&category=Mars'
    browser.visit(url)

    # HTML object
    html = browser.html

    # Parse HTML with Beautiful Soup
    soup = BeautifulSoup(html, 'html.parser')

    # Retrieve first slide image
    v_item = soup.find('li', class_='slide')
    v_link = v_item.find('a')
    featured_image_url = base_url + v_link['data-fancybox-href']
    print(featured_image_url)

    # assign to results object
    results["featured"] = featured_image_url


def scrapeWeather():
    # find the image url for the current Featured Mars Image 
    # and assign the url string to a variable called featured_image_url.
    #   Make sure to find the image url to the full size .jpg image.
    #   Make sure to save a complete url string for this image.

    # define url and goto page
    url = 'https://twitter.com/marswxreport?lang=en'
    browser.visit(url)

    # HTML object
    html = browser.html

    # Parse HTML with Beautiful Soup
    soup = BeautifulSoup(html, 'html.parser')

    # Retrieve first weather tweet
    v_tweets = soup.find('div', class_='ProfileTimeline')
    v_tweet = v_tweets.find('div', class_='tweet')
    mars_weather = v_tweet.find('p', class_='TweetTextSize').text
    print(mars_weather)

    # assign to results object
    results["weather"] = mars_weather


def scrapeFacts():
    # define url and goto page
    url = 'https://space-facts.com/mars/'
    tables = pd.read_html(url)

    # get first table and set header columns
    df = tables[0]
    df.columns = ['Name', 'Value']
    df.rename(columns={'Name':'Description'}, inplace=True)
    #df.set_index('Name')

    # Use Pandas to convert the data to a HTML table string.
    html_table = df.to_html()
    html_table = html_table.replace('\n', '')
    print(html_table)

    # assign to results object
    results["facts"] = html_table


def scrapeHemispheres():
    # define empty list
    hemisphere_dic_list = []
    hemisphere_keys = ['img_title', 'img_url']
    #hemisphere_vals = []

    # define url and goto page
    base_url = 'https://astrogeology.usgs.gov'
    url = base_url + '/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'
    browser.visit(url)

    # HTML object
    html = browser.html

    # Parse HTML with Beautiful Soup
    soup = BeautifulSoup(html, 'html.parser')

    # Retrieve image results
    v_results = soup.find_all('div', class_='item')

    for rec in v_results:
        hemisphere_vals = []

        # get title
        v_title = rec.find('div', class_='description').find('a').find('h3').text
        hemisphere_vals.append(v_title)

        # click / goto image page
        browser.click_link_by_partial_text(v_title)
        
        # setup new html soup scrapper
        html2 = browser.html
        soup2 = BeautifulSoup(html2, 'html.parser')   
        
        # get full image link
        v_link = soup2.find('div', class_='downloads').find('ul').find('li').find('a')['href']
        hemisphere_vals.append(v_link)
        
        # click / go back to main result list
        browser.click_link_by_partial_text('Back')

        # add scrape results to dictionary list
        hemisphere_dic_list.append(dict(zip(hemisphere_keys, hemisphere_vals)))

    print(hemisphere_dic_list)   
    # assign to results object
    results["hemisphere"] = hemisphere_dic_list


def init_browser():
    # @NOTE: Replace the path with your actual path to the chromedriver
    executable_path = {'executable_path': 'chromedriver.exe'}
    return Browser("chrome", **executable_path, headless=True)


def scrape():
    #browser = init_browser()
    scrapeNews()
    scrapeFeaturedImage()
    scrapeWeather()
    scrapeFacts()
    scrapeHemispheres()
    return results


app = Flask(__name__)

# Use flask_pymongo to set up mongo connection
#app.config["MONGO_URI"] = "mongodb://localhost:27017/craigslist_app"
#mongo = PyMongo(app)

# Or set inline
mongo = PyMongo(app, uri="mongodb://localhost:27017/mars_app")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/show")
def show():
    blah = mongo.db.mars.find_one()
    return render_template("show.html", results=blah)

@app.route("/scrape")
def scraper():
    mars = mongo.db.mars
    mars_data = scrape()
    mars.update({}, mars_data, upsert=True)
    return redirect("/show", code=302)


if __name__ == "__main__":
    app.run(debug=True)