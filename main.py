import random
import yaml
from tempfile import TemporaryDirectory
import os
from src.captcha import solve_persian_math_captcha
from seleniumbase import SB
from telethon import TelegramClient, events
import pdb
import asyncio
import traceback

config = {}
with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.loader.SafeLoader)

proxy = None
second_page = False
sms_code = None
success = False
exception_occured = False
if config['proxy']:
    proxy = config['proxy']

client = TelegramClient(config['session'], config['api_id'], config['api_hash'], proxy=proxy).start(bot_token=config['bot_token'])

@client.on(events.NewMessage(func=lambda e: e.sender_id == config['telegram_admin_id'] , incoming=True))
async def handler_admin(event):
    global exception_occured
    if exception_occured == True:
        if event.message.text == '/yes':
            exception_occured = False
            await event.respond("Resuming...")
            return
        elif event.message.text == '/no':
            await event.respond("Stopping the program.")
            exit(0)
        else:
            await event.respond("Invalid answer.")
            return

@client.on(events.NewMessage(func=lambda e: e.sender_id == config['telegram_user_id'] , incoming=True))
async def handler_user(event):
    global second_page, sms_code
    if second_page == True and sms_code is None:
        sms_code = event.message.text
        await event.respond("Thank you!")
    else:
        await event.respond("Not in second page yet.")

async def initialize_first_page(sb):
    sb.open("https://ve.cbi.ir/TasRequest.aspx")
    sb.type("#ctl00_ContentPlaceHolder1_tbIDNo", config['code_melli'])
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlBrDay", config['birth_day'])
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlBrMonth", config['birth_month'])
    sb.type("#ctl00_ContentPlaceHolder1_tbBrYear", config['birth_year'])
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlMarryDay", config['marry_day'])
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlMarryMonth", config['marry_month'])
    sb.type("#ctl00_ContentPlaceHolder1_tbMarrYear", config['marry_year'])
    sb.type("#ctl00_ContentPlaceHolder1_tbMobileNo", config['mobile_no'])
    if config['phone_owner_code_melli_if_under_18'] is not None:
        sb.type("#ctl00_ContentPlaceHolder1_tbIDNoOwnerMobile", config['phone_owner_code_melli_if_under_18'])
    if config['foreigner_or_married_in_foreign_country'] == True:
        sb.click("#ctl00_ContentPlaceHolder1_rbtnMarrKind2")
    elif config['religious_minority'] == True:
        sb.click("#ctl00_ContentPlaceHolder1_rbtnMarrKind3")
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlState", config['state'])

async def initialize_second_page(sb):
    global sms_code
    if config['isar'] == False:
        sb.click("#ctl00_ContentPlaceHolder1_rbtnIsar0")
    else:
        sb.click("#ctl00_ContentPlaceHolder1_rbtnIsar1")
    if config['sarbasi_status'] is not None:
        sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlSarbasiST", config['sarbasi_status'])
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlCity", config['city'])
    if config['code_melli_hamsar'] is not None:
        sb.type("#ctl00_ContentPlaceHolder1_tbIDNo2", config['code_melli_hamsar'])
    sb.type("#ctl00_ContentPlaceHolder1_tbTel", config['home_no'])
    if config['email'] is not None:
        sb.type("#ctl00_ContentPlaceHolder1_tbEMail", config['email'])
    sb.type("#ctl00_ContentPlaceHolder1_tbZipCD", config['postal_code'])
    sb.click("#ctl00_ContentPlaceHolder1_btnEstelamAddr")
    if sms_code is None:
        await client.send_message(config['telegram_user'], "Please provide the SMS code.")
        await client.send_message(config['telegram_admin'], "SMS sent to user.")
        while sms_code is None:
            await asyncio.sleep(1)
    sb.type("#ctl00_ContentPlaceHolder1_tbMobConfCode", sms_code)

def print_user_config():
    msg = ""
    msg += f"Code Melli: {config['code_melli']}\n"
    msg += f"Birth Day: {config['birth_day']}\n"
    msg += f"Birth Month: {config['birth_month']}\n"
    msg += f"Birth Year: {config['birth_year']}\n"
    msg += f"Marry Day: {config['marry_day']}\n"
    msg += f"Marry Month: {config['marry_month']}\n"
    msg += f"Marry Year: {config['marry_year']}\n"
    msg += f"Mobile No.: {config['mobile_no']}\n"
    msg += f"Phone owner if under 18 : {config['phone_owner_code_melli_if_under_18']}\n"
    msg += f"Foreigner or married in foreign country: {config['foreigner_or_married_in_foreign_country']}\n"
    msg += f"religious minority: {config['religious_minority']}\n"
    msg += f"State: {config['state']}\n"
    msg += f"Isar: {config['isar']}\n"
    msg += f"Sarbazi: {config['sarbasi_status']}\n"
    msg += f"City: {config['city']}\n"
    msg += f"Code Melli Hamsar: {config['code_melli_hamsar']}\n"
    msg += f"Home No.: {config['home_no']}\n"
    msg += f"Email: {config['email']}\n"
    msg += f"Postal Code: {config['postal_code']}\n"
    return msg

async def main():
    global sms_code, second_page, success, exception_occured
    with SB(headed=True) as sb:
        msg = "Bot started working with this information:\n"
        msg += print_user_config()
        await client.send_message(config['telegram_admin'], msg)
        while True:
            try:
                reinitialize = True
                while second_page == False:
                    if reinitialize:
                        await initialize_first_page(sb)
                        reinitialize = False
                    captcha = None
                    while captcha is None:
                        sb.click("#ctl00_ContentPlaceHolder1_imgBtnCreateNewCaptcha")
                        with TemporaryDirectory() as tempdir:
                            sb.save_element_as_image_file("#ctl00_ContentPlaceHolder1_ImgCaptcha", "captcha.png", folder=tempdir)
                            captcha = solve_persian_math_captcha(os.path.join(tempdir, "captcha.png"))
                    
                    sb.type("#ctl00_ContentPlaceHolder1_tbCaptcha", str(captcha))
                    sb.find_element("#ctl00_ContentPlaceHolder1_btnContinue1").click()
                    try:
                        alert = sb.switch_to_alert()
                        if alert.text == "تاریخ ازدواج وارد شده با اطلاعات ثبت شده در سامانه سازمان ثبت اسناد یا ثبت احوال کشور تطابق ندارد، لطفا به اداره ثبت اسناد یا ثبت احوال شهرستان خود مراجعه نمایید":
                            print("Invalid info given.")
                        elif alert.text == "در حال حاضر هیچ بانکی در استان انتخابی شما دارای اعتبار نمی باشد، دوباره تلاش نمایید":
                            print("No banks available.")
                        elif alert.text == "پس از چند ثانیه، دوباره تلاش نمایید":
                            print("Try again later.")
                        elif alert.text == "کد امنیتی وارد شده نامعتبر است !":
                            print("Captcha failed.")
                        elif alert.text == "شماره تلفن همراه و شماره ملی با هم تطابق ندارند":
                            print("Phone number and ID do not match.")
                        elif alert.text == "یک کد تایید 6 رقمی بر روی تلفن همراه شما ارسال گردید که در ادامه باید این کد را در کادر مربوطه وارد نمایید":
                            second_page = True
                            print("Reached second page.")
                        else:
                            msg = "Page 1 new alert:\n"
                            msg += alert.text
                            await client.send_message(config['telegram_admin'], msg)
                            print(msg)
                            print("Unknown state. Reinitializing...")
                            reinitialize = True
                            second_page = False
                        sb.wait_for_and_accept_alert()
                    except Exception:
                        print("Unknown state. Reinitializing...")
                        reinitialize = True
                        second_page = False
            except Exception:
                success = False
                exception_occured = True
                second_page = False
                sms_code = None
                traceback.print_exc()
                formatted_lines = traceback.format_exc().splitlines()
                msg = ""
                for line in formatted_lines:
                    msg += line + '\n'
                await client.send_message(config['telegram_admin'], msg)
                print(msg)
                msg = "Exception on page 1. Should I continue?\n"
                msg += "/yes or /no"
                await client.send_message(config['telegram_admin'], msg)
                while exception_occured == True:
                    await asyncio.sleep(1)
            try:
                branch_idx = 1
                sb.sleep(5)
                reinitialize = True
                while success == False and second_page == True:
                    if reinitialize == True:
                        await initialize_second_page(sb)
                        reinitialize = False
                    captcha = None
                    while captcha is None:
                        sb.click("#ctl00_ContentPlaceHolder1_imgBtnCreateNewCaptcha2")
                        with TemporaryDirectory() as tempdir:
                            sb.save_element_as_image_file("#ctl00_ContentPlaceHolder1_ImgCaptcha1", "captcha.png", folder=tempdir)
                            captcha = solve_persian_math_captcha(os.path.join(tempdir, "captcha.png"))
                    sb.type("#ctl00_ContentPlaceHolder1_tbCaptcha2", str(captcha))
                    sb.find_element("#ctl00_ContentPlaceHolder1_btnBankListRefresh").click()
                    try:
                        alert = sb.switch_to_alert()
                        if alert.text == "در حال حاضر هیچ بانکی در استان انتخابی شما دارای اعتبار نمی باشد، دوباره تلاش نمایید":
                            print("No banks available.")
                        elif alert.text == "پس از چند ثانیه، دوباره تلاش نمایید":
                            print("Try again later.")
                        elif alert.text == "کد امنیتی وارد شده نامعتبر است !":
                            print("Captcha failed.")
                            captcha = None
                        else:
                            msg = "Page 2 step 1 new alert:\n"
                            msg += alert.text
                            await client.send_message(config['telegram_admin'], msg)
                            print(msg)
                            print("Unknown state. Still staying in the second page.")
                        sb.wait_for_and_accept_alert()
                    except Exception:
                        print("Unknown state. Still staying in the second page.")

                    banks = sb.get_select_options("#ctl00_ContentPlaceHolder1_ddlBankName")
                    if captcha is not None and len(banks) > 1:
                        # Temrorary code for not selecting Post bank
                        if len(banks) == 2:
                            if 'پست' in banks[1]:
                                continue
                            selected_bank = banks[1]
                        else:
                            selected_bank = random.choice(banks[1:])
                            while 'پست' in selected_bank:
                                selected_bank = random.choice(banks[1:])
                        sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlBankName", selected_bank)
                        sb.sleep(1)
                        try:
                            branches = sb.get_select_options("#ctl00_ContentPlaceHolder1_lstBoxSuggShb")
                        except Exception:
                            sb.sleep(2)
                            branches = sb.get_select_options("#ctl00_ContentPlaceHolder1_lstBoxSuggShb")
                        if branch_idx >= len(branches):
                            branch_idx = 1
                        sb.select_option_by_text("#ctl00_ContentPlaceHolder1_lstBoxSuggShb", branches[branch_idx])
                        branch_idx = branch_idx + 1
                        sb.type("#ctl00_ContentPlaceHolder1_tbCaptcha1", str(captcha))
                        sb.find_element("#ctl00_ContentPlaceHolder1_btnSave").click()
                        try:
                            alert = sb.switch_to_alert()
                            if alert.text == "در حال حاضر هیچ بانکی در استان انتخابی شما دارای اعتبار نمی باشد، دوباره تلاش نمایید":
                                print("No banks available.")
                            elif alert.text == "پس از چند ثانیه، دوباره تلاش نمایید":
                                print("Try again later.")
                            elif alert.text == "کد امنیتی وارد شده نامعتبر است !":
                                print("Captcha failed.")
                            elif alert.text == "لطفا نام بانک عامل را از ليست مربوطه انتخاب نماييد":
                                print("Bank not selected.")
                            else:
                                msg = "Page 2 step 2 new alert:\n"
                                msg += alert.text
                                await client.send_message(config['telegram_admin'], msg)
                                print(msg)
                                print("Unknown state. Still staying in the second page.")
                                pdb.set_trace()
                            sb.wait_for_and_accept_alert()
                        except Exception:
                            print("Unknown state. Still staying in the second page.")
                            pdb.set_trace()
            except Exception:
                success = False
                exception_occured = True
                traceback.print_exc()
                formatted_lines = traceback.format_exc().splitlines()
                msg = ""
                for line in formatted_lines:
                    msg += line + '\n'
                await client.send_message(config['telegram_admin'], msg)
                print(msg)
                msg = "Exception on page 1. Should I continue?\n"
                msg += "/yes or /no"
                await client.send_message(config['telegram_admin'], msg)
                while exception_occured == True:
                    await asyncio.sleep(1)

with client:
    client.loop.run_until_complete(main())
