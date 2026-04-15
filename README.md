# 🌴 neLenkin_bot
A telegram bot supporting [NeLenkin Club](https://t.me/lenka_ne_club) — a book club where we discuss [Designing Data-Intensive Applications](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/), [SRE book](https://sre.google/sre-book/table-of-contents/) &amp; more!

### 🍄 Current functionality:
 - User can enroll to an activity stream
 - Bot sends a Zoom link 5 min before meeting
 - Stream curator can broadcast a message to everyone enrolled to a stream
 - Users can sign up to Leetcode mocks
 - Bot creates pairs for Leetcode mocks and send a message to a group chat
 - Bot manages subscriptions and Pro courses

### 🍄 Tech Stack
Python, Docker, Postgres, Redis, Patreon API

## 🍀 Installing and running locally

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
    ```
   This will start the local Postgres on [http://127.0.0.1:8080/](http://127.0.0.1:8080/) and local Redis on [http://127.0.0.1:8081/](http://127.0.0.1:8081/).

6. Install [alembic](https://pypi.org/project/alembic/) and run

    ```sh
    $ alembic upgrade head
    ```
   This will create empty tables in your Postgres.

7. Run

    ```sh
    $ uv run main.py
    ```
   This will start your test bot. Try `/start` command in your bot!

## 🎁 Contributing

Donate monthly on [Patreon](https://www.patreon.com/c/LenaAnyusha) or [Boosty](boosty.to/lenaan).

If you are not yet a member, join the club via [Telegram Bot](https://t.me/neLenkin_bot), use command `/join`.

### Participate in club discussions

The best way to contribute to the club is to present the topic of the week in courses you participate in. (Command 
`/courses` in [Telegram Bot](https://t.me/neLenkin_bot)). If you have learned something exciting that is not covered in 
any book we are reading and you what to share it, reach out to Lena to set up an ad-hoc presentation.

### Tell your friends about the Club

Please do! Bring more passionate smart humble nice people to the club.

### If you really what to write some code

Choose any of the [Issues](https://github.com/LenaAn/neLenkin_bot/issues)

Discuss what you want implement with Lena before opening a Pull Request. Any PR without prior discussion most likely 
will not get reviewed.

If you have a bug report, security issue or feature request, please also discuss it with Lena.
