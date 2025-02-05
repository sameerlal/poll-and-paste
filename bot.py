from setup import setup, login
from twscrape import AccountsPool, API, gather
from dotenv import dotenv_values
from utils import find_code, paste_code, check_tweets, get_time, turn_green, handle_img
import argparse
import logging
import sys
import signal
import pick
import json
import asyncio
import os
import time

logging.basicConfig(
    level=logging.INFO,
    format="\x1b[32m%(asctime)s\x1b[0m | \x1b[37m%(levelname)s\x1b[0m | \x1b[36m%(module)s:%(funcName)s:%(lineno)d\x1b[0m - %(message)s",
)

# ------------ handling exit ------------
def handle_exit(sig, frame):
    logging.info("Exiting.....")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)
# ----------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument(
    "--nopaste", action="store_true", help="Disable pasting code into messages"
)
parser.add_argument("--image", action="store_true", help="Enable image scanning")
args = parser.parse_args()

paste = args.nopaste
scan_image = args.image

USER_ID = 133448051
# USER_ID = "1682586506345447426" # Test account

acc_path = "./.env"
config_path = "./config.json"
codes_path = "./codes.txt"


if not os.path.exists(codes_path):
    with open(codes_path, "w") as f:
        f.write("")

codes = set(line.strip() for line in open("codes.txt"))


def handle_code(code, paste):
    if code in codes:
        logging.info(f"Code already used: {code}")
        return

    paste_code(code, paste, load_config())

    logging.info("###########################################")
    for _ in range(8):
        logging.info(f"CODE FOUND: {code}")
    logging.info("###########################################")
    codes.add(code)

    with open("codes.txt", "a") as f:
        f.write(code + "\n")


def load_config():
    with open(config_path) as file:
        data = json.load(file)

    X = data["position"][0]
    Y = data["position"][1]

    return X, Y


def load_acc():

    with open(".env", "r") as f:
        info = f.read().split("\n")
    print("found info = ")
    for line in info:
        print(line)
    return [item.split(",") for item in info if item is not ""]
    # env_vars = dotenv_values()
    # USERNAME = env_vars["USERNAME"]
    # EMAIL = env_vars["EMAIL"]
    # PASSWORD = env_vars["PASSWORD"]

    # return USERNAME, EMAIL, PASSWORD


def choose_option():
    options = [
        "1) Run bot",
        "2) Reconfigure cursor",
        "3) Add an additional account (new)",
        "4) Exit",
    ]
    option, index = pick.pick(
        options,
        "Chipotle Bot\n"
        + ("Pasting disabled" if paste else "Pasting enabled")
        + "\n"
        + ("Image scanning enabled" if scan_image else "Image scanning disabled"),
        indicator="=>",
        default_index=0,
    )

    if index == 1:
        setup()
        choose_option()
    elif index == 2:
        login()
        choose_option()
    elif index == 3:
        sys.exit(0)


async def main():
    logging.info(turn_green("Bot starting..."))

    if not os.path.exists(acc_path):
        logging.warning("Account not yet signed in")
        login()

    if not os.path.exists(config_path) and paste:
        logging.warning("Config not yet generated")
        setup()

    if os.path.exists("./accounts.db"):
        os.remove("./accounts.db")

    if not scan_image:
        pool = AccountsPool()
        accounts = load_acc()
        
        print("----------")
        print(accounts)

        for usnm,pw,email in accounts:
            await pool.add_account(usnm,pw,email,pw)
        await pool.login_all()

        api = API(pool)

    cnt = 0
    while cnt < 600:
        print("Query = ", cnt)
        cnt += 1
        if not scan_image:
            print("q.")
            tweets = await gather(api.user_tweets(USER_ID, limit=1))
            print("..")

            if check_tweets(tweets) is False:
                continue

            tweet = tweets[0]
            tweet_content = tweet.rawContent
        else:
            tweet_content = handle_img()
            logging.info(tweet_content)

        code = find_code(tweet_content)
        if code != "":
            handle_code(code, paste)
        elif not scan_image:
            tweet_time, current_time = get_time(tweet)
            logging.info(
                turn_green(f"Posted at: {tweet_time}. Current time: {current_time}")
            )

        time.sleep(
            0.2 #1.85
        )  # twitter allows 500ish requests every 15 minuts ~= 1 request every 1.8 seconds
    logging.log("END RUN..")


if __name__ == "__main__":
    choose_option()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Exiting.....")
        sys.exit(0)
