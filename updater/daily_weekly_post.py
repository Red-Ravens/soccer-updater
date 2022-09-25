#!/usr/bin/env python3
#####################################
#    LAST UPDATED     23 SEP 2022   #
#####################################
"""
Generates/updates a weekly post with schedule information
"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sys
import praw
import logging
import updater
import datetime
import praw_oauth2
from random import randint

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y',
                        filename='log.log', level=logging.WARNING)
logging.disable(logging.INFO)


def make_final_text(text: str) -> str:
    """
    Use the baseline text
    :param text: str schedule markdown
    :return: str of the two combined
    """
    baseline_text_template = """Use this thread to discuss anything (within the rules of the subreddit):

* What you didn't think was worthy of its own post
* What club game you're most excited for
* Where you're staying to watch a friendly
* Which players should be called in
{}
* What the mods told you to re-post here
* Etc

### Schedules
{}
"""

    with open('random_dumb_questions.txt', 'r') as files:
        list_of_questions = files.readlines()

    question = list_of_questions[randint(0, len(list_of_questions))].replace('\n', '')

    return baseline_text_template.format(question, text)


def create_new_thread(r: praw.Reddit, text: str) -> str:
    """
    Create a new thread
    :param r: authenticated praw instance
    :param text: text to submit
    :return: str new thread id
    """
    r.validate_on_submit = True
    discussion_thread = r.subreddit('ussoccer').submit('Weekly Discussion Thread', selftext=text, send_replies=False)
    discussion_thread.mod.suggested_sort('new')
    discussion_thread.mod.sticky()
    logging.info('Created weekly discussion thread')
    return discussion_thread.id


def edit_existing_thread(r: praw.Reddit, thread_id: str, text: str) -> None:
    """
    Edit an existing thread
    :param r: authenticated praw instance
    :param thread_id: str of weekly discussion post thread id
    :param text: str of text to submit
    :return: str new thread id
    """
    r.validate_on_submit = True
    r.submission(thread_id).edit(text)
    logging.info('Updated weekly discussion thread')


def save_thread_id(thread_id: str) -> None:
    """
    Save the thread id for easy access
    :param thread_id: str
    :return: None
    """
    with open('post_id.txt', 'w') as files:
        files.write(thread_id)


def load_thread_id() -> str:
    """
    Load and return the thread id
    :return: str of the thread id
    """
    with open('post_id.txt', 'r') as files:
        thread_id = files.read()

    return thread_id


def unsticky_thread(r: praw.Reddit, thread_id: str) -> None:
    """
    Unsticky the previous week's discussion thread
    :param r: authenticated praw instance
    :param thread_id: str of thread id
    :return: None
    """
    r.submission(thread_id).mod.unsticky()


def main(debug: bool = True):
    """
    Main function.
    :param debug: bool to debug and print to console or run for real and update post
    :return: None
    """
    schedule = updater.new_main(debug=False, get_text=True)
    final_text = make_final_text(schedule).rstrip()

    if debug:
        print(final_text)
    else:
        user_agent = "/r/ussoccer sidebar match updater v3.0 by /u/RedRavens /u/ussoccer_b0t"
        reddit = praw_oauth2.ussoccer_bot(user_agent)

        if datetime.datetime.today().weekday() == 0:
            # Monday, time for a new thread
            old_thread_id = load_thread_id()
            unsticky_thread(r=reddit, thread_id=old_thread_id)
            new_thread_id = create_new_thread(r=reddit, text=final_text)
            save_thread_id(thread_id=new_thread_id)
        else:
            # not Monday, just update the schedule
            thread_id = load_thread_id()
            edit_existing_thread(r=reddit, thread_id=thread_id, text=final_text)


def start_bot() -> None:
    """
    Function to manage debugging
    :return: None
    """
    if sys.platform == 'darwin':
        force = False

        if force:
            deb = False
        else:
            deb = True

        main(debug=deb)
    else:
        force = True
        if force:
            main(debug=False)
        else:
            main(debug=True)


if __name__ == '__main__':
    start_bot()
