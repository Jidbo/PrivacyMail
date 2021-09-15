from django.conf import settings
import os
import tempfile
import datetime
from mailfetcher.models import Mail
from pathlib import Path
from OpenWPM.openwpm.command_sequence import CommandSequence
from OpenWPM.openwpm.task_manager import TaskManager
from OpenWPM.openwpm.storage.sql_provider import SQLiteStorageProvider
from OpenWPM.openwpm.config import BrowserParams, ManagerParams
import sqlite3 as lite

from django.db import connection
from mailfetcher.crons.mailCrawler.analysis.importViewResults import (
    import_openwpmresults,
    import_openwpmresults_single_mail,
)


def call_openwpm_view_single_mail(mail):
    wpm_db = settings.OPENWPM_DATA_DIR + "crawl-data.sqlite"
    if os.path.exists(wpm_db):
        os.remove(wpm_db)
    filename = write_mail_to_file(mail)
    manager = open_browsers(1)
    visit_site(filename, manager)
    manager.close()
    if os.path.isfile(wpm_db):
        conn = lite.connect(wpm_db)
        db_cursor = conn.cursor()
        eresources = import_openwpmresults_single_mail(filename, db_cursor)

        os.unlink("/tmp/" + filename.split("/")[3])
        # remove file to avoid zombie data
        db_cursor.close()

        # remove openwpm sqlite db to avoid waste of disk space
        if not settings.DEVELOP_ENVIRONMENT:
            os.remove(wpm_db)
    return eresources


def call_openwpm_view_mail(mailQueue):
    # View a queue of emails with OpenWPM and save the observed connections
    print("Preparing data for OpenWPM.")
    db_name = "crawl-data.sqlite"
    wpm_db = settings.OPENWPM_DATA_DIR + db_name
    if os.path.exists(wpm_db):
        os.remove(wpm_db)

    file_to_mail_map = {}
    mailFiles = []
    # Go through all emails to create temporary files with their contents
    # These can then be analyzed with OpenWPM later
    for mail in mailQueue:
        if mail.body_html:
            # create unique filename
            filename = write_mail_to_file(mail.body_html)
            mailFiles.append(filename)
            file_to_mail_map[filename] = mail
        else:
            mail.processing_state = Mail.PROCESSING_STATES.DONE
            mail.save()
            continue

    num_browsers = settings.NUMBER_OF_THREADS
    with open_browsers(num_browsers) as manager:
        # The list of sites that we wish to crawl
        sites = mailFiles

        # Visits the sites in succession rotating the browsers
        for site in sites:
            visit_site(site, manager)

    # Make sure the db connection is open
    connection.connect()

    print("Importing OpenWPM results.")
    failed_mails = []
    if os.path.isfile(wpm_db):
        conn = lite.connect(wpm_db)
        db_cursor = conn.cursor()
        for fileName in mailFiles:
            successful_import = import_openwpmresults(
                fileName, file_to_mail_map[fileName], db_cursor)
            if not successful_import:
                failed_mails.append(file_to_mail_map[fileName])
                file_to_mail_map[fileName].processing_fails = (
                    file_to_mail_map[fileName].processing_fails + 1)
                file_to_mail_map[fileName].save()
            else:
                file_to_mail_map[
                    fileName].processing_state = Mail.PROCESSING_STATES.VIEWED
                file_to_mail_map[fileName].processing_fails = 0
                file_to_mail_map[fileName].save()
            os.unlink(
                "/tmp/" +
                fileName.split("/")[3])  # remove file to avoid zombie data
        db_cursor.close()

        # remove openwpm sqlite db to avoid waste of disk space
        if not settings.DEVELOP_ENVIRONMENT:
            os.remove(wpm_db)
    print("Done.")
    return failed_mails


def write_mail_to_file(body_html):
    file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html")
    file.write(body_html)
    file_basename = os.path.basename(file.name)
    filename = "http://" + settings.LOCALHOST_URL + "/" + file_basename
    file.close()
    return filename


def open_browsers(num_browsers):

    # sites = ["file:///tmp/tmpvvfmzvpo"]
    # Loads the manager preference and 3 copies of the default browser dictionaries
    print("Starting OpenWPM to view mails.")
    manager_params = ManagerParams(
        num_browsers=num_browsers,
        log_path=Path(settings.OPENWPM_LOG_DIR +
                      '{date:%Y-%m-%d_%H:%M:%S}.log'.format(
                          date=datetime.datetime.now())),
        data_directory=Path(settings.OPENWPM_DATA_DIR))
    browser_params = [
        BrowserParams(http_instrument=True,
                      display_mode="headless",
                      prefs={"browser.chrome.site_icons": False})
        for _ in range(num_browsers)
    ]

    storage = SQLiteStorageProvider(
        Path(settings.OPENWPM_DATA_DIR + "crawl-data.sqlite"))
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    return TaskManager(manager_params, browser_params, storage, None)


def visit_site(site, manager):
    command_sequence = CommandSequence(site, reset=True)
    # Start by visiting the page
    command_sequence.get(sleep=0, timeout=settings.OPENWPM_TIMEOUT)

    # dump_profile_cookies/dump_flash_cookies closes the current tab.
    # Not dumping cookies here, as they should be extractable from the response headers.
    # command_sequence.dump_profile_cookies(120)

    # index=None browsers visit sites asynchronously
    manager.execute_command_sequence(command_sequence, index=None)
