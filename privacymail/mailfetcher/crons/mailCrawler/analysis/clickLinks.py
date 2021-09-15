from mailfetcher.models import Mail
from django.conf import settings
import os
import datetime
from pathlib import Path
from OpenWPM.openwpm.command_sequence import CommandSequence
from OpenWPM.openwpm.task_manager import TaskManager
from OpenWPM.openwpm.config import BrowserParams, ManagerParams
from OpenWPM.openwpm.storage.sql_provider import SQLiteStorageProvider
from django.db import connection

from mailfetcher.crons.mailCrawler.analysis.importClickResults import (
    import_openwpmresults_click, )

import sqlite3 as lite


def call_openwpm_click_links(link_mail_map):
    # Click a specified link for a list of emails and save the results
    wpm_db = settings.OPENWPM_DATA_DIR + "crawl-data.sqlite"
    if os.path.exists(wpm_db):
        os.remove(wpm_db)

    print("Preparing data for OpenWPM.")
    sites = []
    for url in link_mail_map:
        sites.append(url)
    # The list of sites that we wish to crawl
    num_browsers = settings.NUMBER_OF_THREADS

    # Loads the manager preference and 3 copies of the default browser dictionaries
    print("Starting OpenWPM to visit links.")
    manager_params = ManagerParams(
        num_browsers=num_browsers,
        log_path=settings.OPENWPM_LOG_DIR +
        '{date:%Y-%m-%d_%H:%M:%S}.log'.format(date=datetime.datetime.now()),
        data_directory=settings.OPENWPM_DATA_DIR)
    browser_params = [
        BrowserParams(http_instrument=True,
                      display_mode="headless",
                      prefs={"browser.chrome.site_icons": False})
        for _ in range(num_browsers)
    ]

    storage = SQLiteStorageProvider(
        Path(wpm_db))
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    with TaskManager(manager_params, browser_params, storage, None) as manager:

        # Visits the sites in succession rotating the browsers
        for site in sites:
            command_sequence = CommandSequence(site, reset=True)

            # Start by visiting the page
            command_sequence.get(sleep=0, timeout=settings.OPENWPM_TIMEOUT)

            # Not dumping cookies here, as they can be extracted from the response headers
            # command_sequence.dump_profile_cookies(120)

            # index=None browsers visit sites asynchronously
            manager.execute_command_sequence(command_sequence, index=None)

    # Make sure the db connection is open
    connection.connect()

    print("Importing OpenWPM results.")
    failed_urls = {}
    wpm_db = settings.OPENWPM_DATA_DIR + "crawl-data.sqlite"

    if os.path.isfile(wpm_db):
        conn = lite.connect(wpm_db)
        db_cursor = conn.cursor()

        for url in link_mail_map:
            import_success = import_openwpmresults_click(
                url, link_mail_map[url], db_cursor)
            if not import_success:
                failed_urls[url] = link_mail_map[url]
                link_mail_map[url].processing_fails = (
                    link_mail_map[url].processing_fails + 1)
                link_mail_map[url].save()
            else:
                link_mail_map[
                    url].processing_state = Mail.PROCESSING_STATES.LINK_CLICKED
                link_mail_map[url].processing_fails = 0
                link_mail_map[url].save()
        db_cursor.close()

        # remove openwpm sqlite db to avoid waste of disk space
        # if not settings.DEVELOP_ENVIRONMENT:
        #     os.remove(wpm_db)
    print("Done.")
    return failed_urls
