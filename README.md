# neLenkin_bot
A telegram bot supporting [NeLenkin Club](https://t.me/lenka_ne_club) — a book club where we discuss [Designing Data-Intensive Applications](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/), [SRE book](https://sre.google/sre-book/table-of-contents/) &amp; more!

### Current functionality:
 - User can enroll to an activity stream
 - Bot sends a Zoom link 5 min before meeting
 - Stream curator can broadcast a message to everyone enrolled to a stream
 - Users can sign up to Leetcode mocks
 - Bot creates pairs for Leetcode mocks and send a message to a group chat
 - Bot manages subscriptions and Pro courses

## Installing and running locally

1. Install [Docker](https://www.docker.com/get-started)

2. Clone the repo

    ```sh
    $ git clone https://github.com/LenaAn/neLenkin_bot.git
    $ cd neLenkin_bot
    ```
3. Create a test telegram bot and get a token, here's [an instruction](https://core.telegram.org/bots/tutorial#obtain-your-bot-token).
4. Create a `.env` file, look at `.env.example` for the example. Put your bot token into `.env` file.
5. Run

    ```sh
    $ docker compose up -d
    $ python3 main.py
    ```

This will start the local Postgres on [http://127.0.0.1:8080/](http://127.0.0.1:8080/) and local Redis on [http://127.0.0.1:8081/](http://127.0.0.1:8081/). It will also start your test bot. Try `/start` command in your bot!