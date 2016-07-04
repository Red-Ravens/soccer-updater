# /r/ussoccer Updater

This script runs daily and does three things:

1. Parses the [US soccer website](https://www.ussoccer.com/schedule-tickets) for match info

2. Compiles it into reddit- and /r/ussoccer-friendly text

3. Runs daily to updates the sidebar with match info via [pythonanywhere.com](https://wwpythonanywhere.com)


#### Parsing US Soccer

Because I had always intended to use [pythonanywhere](https://wwpythonanywhere.com) to run this script daily, I had to develop a way to use their website which has strict whitelists and blacklists. Since US Soccer doesn't currently have an API that provides match info, I used [importio](https://www.import.io/) to build a custom JSON API that also complies with pythonanywhere's whitelist. The two links in `SoccerUpdaterImportio.py` return full upcoming match info and full past match info, respectively. 

#### Making Markdown

The next section parses the importio JSON and creates tables. The tables are divided into MNT, WNT, U-23 MNT, U-23 WNT, U-20 MNT, U-20 WNT, and Other. Currently, the Other table does not get posted in favor of posting the recent MNT and WNT results. I have set the row limit to 4 for all tables to reduce clutter. The first row of the MNT and WNT tables is sent to ussoccer_bot for match thread creation purposes.

#### Updating the sidebar

I currently use HTMLParser and some code thrown together by someone else to update the sidebar. It works, so I haven't bothered to change it.

### Known Issues

On occasion, there is an error due to the JSON. I suspect that the error is on importio's end. Here is the traceback:

    Traceback (most recent call last):
    File "/home/redravens/updater/SoccerUpdaterImportio.py", line 482, in new_main  
    make_schedule(schedule_data, current_year, mnt_times, wnt_times, limit, now) 
    File "/home/redravens/updater/SoccerUpdaterImportio.py",  
    line 202, in make_schedule for match in schedule_data['results']: 
    KeyError: 'results'
