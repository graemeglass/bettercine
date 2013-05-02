from bs4 import BeautifulSoup
from datetime import datetime
import requests
import re
from imdb import IMDb
import os
ia = IMDb()

base_url = "http://www.sterkinekor.mobi"

class Movie:
    movie_id = ""
    title = ""
    genres = []
    age = []
    comingsoon = ""
    image = ""

    def __init__(self, movie_id, title):
        self.movie_id = movie_id
        self.title = title.lstrip('(3D)').strip()

def getHtml(url):
    r = requests.get(base_url + url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.25 (KHTML, like Gecko) Chrome/12.0.706.0 Safari/534.25'})
    return r

def getIMDbRating(title):
    r = requests.get("http://www.imdb.com/xml/find?xml=1&nr=1&q=%s" % title).text.strip()
    imdb_id = BeautifulSoup(r).find("resultset").imdbentity['id']

    r = requests.get("http://www.imdb.com/title/%s/" % imdb_id).text.strip()
    rating = BeautifulSoup(r).find("div", class_="star-box-giga-star").text.strip()

    return rating

def getRegions():
    pass

def getCinemas(region_id):
    pass

def getMovieList(region_id=4, cinema_id=164, verbose=False):

    if (verbose):
        print "Getting list for Region %s, Cinema %s" % (region_id, cinema_id)

    movies = []
    start_page = 1
    end_page = 1
    region = region_id
    cinema = cinema_id

    thecount = 0

    page = start_page

    r = getHtml("/movies/page:%s/region:%s|%s" % (page, region, cinema))
    html = r.text

    soup = BeautifulSoup(html).find('div', class_="page-counter")
    end_page = int(soup.string.split()[-1])

    for page in xrange(start_page, end_page+1):
        r = getHtml("/movies/page:%s/region:%s|%s" % (page, region, cinema))
        html = r.text

        soup = BeautifulSoup(html).find_all('tr', class_="list-item")
        for items in soup:
            thecount += 1
            movie = items.find_all("td")
            image = movie[0].img['src']
            movie_id = re.findall(r"^/movie/(.*)/(?:.)", movie[1].a["href"], re.I)[0]
            title = movie[1].a.find('span', class_="movie-title").string
            genres = [genre.strip() for genre in movie[1].find_all('span')[1].string.split(",")]
            age = [a.strip() for a in movie[1].find_all('span')[2].string.split(" ")]

            comingsoon = ""
            if len(movie[1].find_all('span')) >= 4:
                comingsoon = movie[1].find_all('span')[3].string

            m = Movie(movie_id, title)
            m.image = image
            m.genres = genres
            m.age = age
            m.comingsoon = comingsoon

            if (verbose):
                print "%s of %s: %s" % (thecount, len(soup), title)

            m.imdb = getIMDbRating(m.title)

            m.showtimes = getShowtimes(movie_id, cinema)

            movies.append(m)

    return movies

def getShowtimes(movie_id, cinema_id):

    showtimes = []
    search_url = "/book/select/performance/%s/%s" % (movie_id, cinema_id)

    html = getHtml(search_url).text
    soup = BeautifulSoup(html).find("div", class_="performance-selection").find_all("p")
    for day in soup:
        dayshowtimes = []
        date = day.strong.string
        times = day.find_all("a")
        for showtime in times:
            date_object = datetime.strptime("%s %s %s" % (date, str(datetime.now().year), showtime.string), '%a %d %b %Y %H:%M')
            dayshowtimes.append((date_object,showtime['href'].split("?")[0]))
        showtimes.append({'day':date, 'showtimes':dayshowtimes})

    return showtimes

def main():
    region_id=4
    cinema_id=164
    movies = getMovieList(region_id, cinema_id, False)

    fdir = os.path.dirname(os.path.realpath(__file__))
    stream = file(fdir+'/movies.html', 'w')

    stream.write("<html><body>")

    stream.write("<h1>Now Showing at %s %s</h1>" % (region_id, cinema_id))
    stream.write("<ul>")
    for m in movies:
        stream.write("<li><a href='#%s'>%s</a></li>" % (m.title, m.title))
    stream.write("</ul><hr>")

    for movie in movies:
        stream.write( "<h1><a name='%s'></a>%s</h1>" % (movie.title, movie.title))
        stream.write( "<h2>%s/10</h2>" % (movie.imdb))
        stream.write( "<ul>")
        for theday in movie.showtimes:
            stream.write("<li>%s<ul>" % (theday['day']))
            for showtime in theday['showtimes']:
                stream.write( "<li><a href='%s'>%s</a></li>" % ((base_url + showtime[1]), showtime[0].strftime("%A, %d %B %I:%M%p")))
            stream.write("</ul></li>")
        stream.write( "</ul>" )
        stream.write( "<hr>" )

    stream.write("<small>Rendered by BetterCine</small>")
    stream.write("</body></html>")
    stream.close()

if __name__ == "__main__":
    main()
