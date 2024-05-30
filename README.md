# marriage-loan-bot (ربات وام ازدواج)
A bot for getting marriage loan in Iran.

# How to use:
1. Install docker and docker-compose. (Look up tutorial elsewhere)
2. Create a telegram bot. (Look up tutorial elsewhere)

**Note:** The user has to send the sms code to the telegram bot when asked.

3. Clone the repo: `git clone https://github.com/Ali-Flt/marriage-loan-bot.git && cd marriage-loan-bot`
4. Create `config.yaml` based on `config.yaml.example` (skip telegram_user_id and telegram_admin_id) for now.
5. Run `docker compose build`.
6. Run `./create_telegram_session.sh`.
7. Run `./get_user_ids.sh` and use the result as telegram_user_id and telegram_admin_id in `config.yaml`.
8. Set a VNC password (SE_VNC_PASSWORD) in `docker-compose.yml`.
9. Run `docker compose up -d`.
10. Install a VNC viewer
11. Use the VNC viewer to connect to `127.0.0.1:5900` (change IP if the bot is installed on a remote machine).
12. Open shell in VNC and run `python3 main.py`

When the bot reaches the second page it will send a message to the telegram user asking for the SMS code. The user should send the code immediately.

**Note: An available bank and bank branch is selected randomly and there are no custom bank selection supported as of right now.**

Enjoy :) **Don't forget to leave a star on the top right corner.**

# Donations
Consider buying me a coffee if this helped you.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/aflt)


## Stargazers over Time

[![Stargazers over time](https://starchart.cc/Ali-Flt/XXX.svg?variant=adaptive)](https://starchart.cc/Ali-Flt/XXX)
