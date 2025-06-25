# MTGMelee Tournament Scraper

Scrapes the tournament page on mtgmelee for a magic the gathering tournament. Gathers standings and decklists and runs some basic winrate analysis for archetypes (both globally and by matchup).

# The Code

Run globals.py and then main.py. You'll be asked to input the mtgmelee web ID (the numbers at the end of the tournament URL on melee's website: e.g. https://melee.gg/Tournament/View/303784) and the tournament name. The code creates a data folder and a subfolder for the tournament in which it will deposit all the output files (and which is named whatever you named the tournament, e.g. Pro Tour Final Fantasy).

Code that uses the webdriver:
- run_standings_scraper()
- run_pairings_scraper()
- run_decklists_scraper()

A browser (with a head) will open and scrape the standings and the pairings and then decklists. The decklists take quite a while becaues it has to load each decklist page for each player.

Code that doesn't use the browser:
- create_archetype_results()
- create_archetypes_matchups()
- create_archetype_winrates()

These three functions create a csv for each decklist in the tournament and then create another csv with their wins and losses vs each other archetype in the event and deposits them in new folders called Matchups and Results in the tournament subfolder. The last function creates a large matrix of every archetype matchup in the dataset which can be easily fed into some sort of data vizualization setup for a heatmap (useful to first filter for archetypes with a lot of matches). This final csv is put into the main tournament subfolder.

# Possible Problems / Frustrations
I started tinkering with this a couple years ago and in that time Melee has changed the interface a few times causing massive headaches for the webdriver (elements moved, etc.). Hasn't happened in 8 months and it sort of feels like they've hit their stride so perhaps it won't change again. If it does I'll update the driver.

On the webdriver specifically, it auto downloads the latest chromedriver and then launches a new guest browser. If your Chrome is out of date (e.g. you've left that little reminder at the top right stick around a while) the chromedriver will fail because it's trying to drive the latest version of Chrome. Just update your Chrome and run the script again.

Occasionally (it's pretty rare) a Melee event won't close out properly for a couple of days. The Standings Scraper scrapes whatever standings are visible on the page and so if the TO / Melee doesn't finish the event the standings table that populates when you normally load a page will be blank (often they forget to close out the finals and so the standings table will be on FINALS but there's nothing listed because the pairing hasn't been completed). There are two solutions for this: wait for the TO / Melee to close it out or write a quick little addition to the webdriver code in run_standings_scraper() that will load the previous Round in the standings table.

Some events have horrible decklists names. If it's an RC or a PT, Frank Karsten / Somebody will usually update the names as the event goes on or shortly thereafter. If they don't update them the winrates will be useless and you'll have to do some manual editing yourself with the csvs (like you'll need to merge the csv files for an archetype - Dimir Midrange, Dimir Aggro, Dimir Tempo). Then run the results / matchups / winrates functions again and they'll work their magic.

# Roadmap
I'm still new to Python and coding so some of the above can be done easier / more efficiently / in cooler ways. There's an mtgmelee API but I couldn't figure out how to get access to it (and I discovered it near the end of this project and didn't want to fight too hard to figure it out). If you acccess the API, the above is much easier and will not require any webdriving.

For example, scraping decklists takes a while because it has to load each decklist page and scrape the decklist table. On the main tournament page the decklist appears in a hover card for each player in the standings table but I couldn't figure out how to scrape that from the html. Perhaps it's in there somewhere and that part can be more efficient.

If the pull is strong enough I will at some point economize some of the functions. For example there's no reason to output multiple csv files for the matchups and results. It does so because while I was learning and testing it was useful to have something concrete I could open and look at and return to while testing and experimenting to get it to do what I wanted (this was also in the early stages when I didn't understand how I could inspect data inside the IDE I was using). But at this point some of this is redundant and I would like to clean it up.

There's not much more I want to do with this project generally. I started it entirely as a way to get into Python and while it proved to be obnoxious and frustrating and horrifying for a variety of reasons it was very fun. It's exceptionally satisfying to run it on an event right as Final Standings go up and have all the data a day before Frank Karsten.

I wrote a couple of scripts that query the decklist data and I will add those to this repository when they're clean and useful. You can, for example, pull winrates for a deck given different copies of different cards, among other useful questions.

Finally, some other folks pull this same data and show it around Twitter and wherever but I have no idea how they do it (API, manual scraping like me, something else entirely). At some point I'd like to reach out to see what methods they use. It would be educational (I being a newbie and they presumably being a sophisticated programmer with many awards and statues) but it would also be cool to pool this knowledge and share it around. As LLMs proliferate in both skill and use it will be easy for non-programmers to do this work themselves and giving them a leg up could make all the difference.

# License
This project is licensed under the MIT License. Have fun, lemme know where it sucks / breaks / fails and I for sure am open to all suggestions for improvements. The main reason I'm hosting it on GitHub at all is to solicit feedback and learn how to make better stuff.

Cheers
