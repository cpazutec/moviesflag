from flask import Flask, render_template, request, jsonify
import requests
import json
import functools
import timeit
from concurrent.futures import ThreadPoolExecutor
import asyncio
from timeit import default_timer


app = Flask(__name__)
apikey = "a2c21c91"

def searchfilms(search_text, page):
    url = f"https://www.omdbapi.com/?type=movie&page={page}&s={search_text}&apikey={apikey}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve search results.")
        return None

@functools.cache
def getmoviedetails(movieid):
    url = "https://www.omdbapi.com/?i=" + movieid + "&apikey=" + apikey
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve search results.")
        return None

@functools.cache
def get_country_flag(fullname):

    url = f"https://restcountries.com/v3.1/name/{fullname}?fullText=true"
    print(f"call {url}")
    response = requests.get(url)
    if response.status_code == 200:
        country_data = response.json()
        if country_data:
            return {
                "name": fullname,
                "flag": country_data[0].get("flags", {}).get("svg", None)
            }
    print(f"Failed to retrieve flag for country code: {fullname}")
    return {
                "name": fullname,
                "flag": None
            }

def merge_data_with_flags(filter, parallel):
    filmssearch = searchfilms(filter, 1)
    filmssearchres = filmssearch["Search"]
    if len(filmssearchres) == 10:
        secondpage = searchfilms(filter, 2)["Search"]
        #for movie2 in secondpage:
            #filmssearchres.append(movie2)
    moviesdetailswithflags = []
    for movie in filmssearchres:
         moviedetails = getmoviedetails(movie["imdbID"])
         countriesNames = moviedetails["Country"].split(",")
         countries = []
         if parallel=="1":
            t = []
            for country in countriesNames:
                t.append(country.strip())
            with ThreadPoolExecutor(max_workers=10) as executor:
                countries = list(executor.map(get_country_flag, t))
         if parallel == "0":
            for country in countriesNames:
                countries.append(get_country_flag(country.strip()))
         moviewithflags = {
            "title": moviedetails["Title"],
            "year": moviedetails["Year"],
            "countries": countries
         }
         moviesdetailswithflags.append(moviewithflags)

    return moviesdetailswithflags

@app.route("/")
def index():
    filter = request.args.get("filter", "")
    parallel = request.args.get("parallel","1")
    start = default_timer()
    movies = merge_data_with_flags(filter, parallel)
    end = default_timer()
    print(end - start)
    return render_template("index.html", movies = movies)
    

@app.route("/api/movies")
def api_movies():
    filter = request.args.get("filter", "")
    parallel = request.args.get("parallel", "0")
    return jsonify(merge_data_with_flags(filter, parallel))    

if __name__ == "__main__":
    app.run(debug=True  , port=3000)

