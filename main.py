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
if config['proxy']:
    proxy = config['proxy']

client = TelegramClient(config['session'], config['api_id'], config['api_hash'], proxy=proxy).start(bot_token=config['bot_token'])

@client.on(events.NewMessage(func=lambda e: e.sender_id == config['telegram_user_id'], incoming=True))
async def handler_sms_code(event):
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
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlState", config['state'])

async def initialize_second_page(sb):
    global sms_code
    if config['isar'] == False:
        sb.click("#ctl00_ContentPlaceHolder1_rbtnIsar0")
    else:
        sb.click("#ctl00_ContentPlaceHolder1_rbtnIsar1")
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlSarbasiST", config['sarbasi_status'])
    sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlCity", config['city'])
    if config['code_melli_hamsar'] is not None:
        sb.type("#ctl00_ContentPlaceHolder1_tbIDNo2", config['code_melli_hamsar'])
    sb.type("#ctl00_ContentPlaceHolder1_tbTel", config['home_no'])
    if config['email'] is not None:
        sb.type("#ctl00_ContentPlaceHolder1_tbEMail", config['email'])
    sb.type("#ctl00_ContentPlaceHolder1_tbZipCD", config['postal_code'])
    sb.click("#ctl00_ContentPlaceHolder1_btnEstelamAddr")
    await client.send_message(config['telegram_username'], "Please provide the SMS code.")
    while sms_code is None:
        await asyncio.sleep(1)
    sb.type("#ctl00_ContentPlaceHolder1_tbMobConfCode", sms_code)

async def main():
    global sms_code, second_page, success
    with SB(headed=True) as sb:
        while True:
            try:
                reinitialize = True
                while second_page == False:
                    if reinitialize:
                        await asyncio.sleep(1)
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
                        elif alert.text == "یک کد تایید 6 رقمی بر روی تلفن همراه شما ارسال گردید که در ادامه باید این کد را در کادر مربوطه وارد نمایید":
                            second_page = True
                            print("Reached second page.")
                        else:
                            msg = "Page 1 new alert:\n"
                            msg += alert.text
                            await client.send_message(config['telegram_username'], msg)
                            print(msg)
                            print("Unknown state. Reinitializing...")
                            reinitialize = True
                            second_page = False
                        sb.wait_for_and_accept_alert()
                    except Exception:
                        print("Unknown state. Reinitializing...")
                        reinitialize = True
                        second_page = False
                
                sb.sleep(5)
                await initialize_second_page(sb)
                while success == False and second_page == True:
                    captcha = None
                    while captcha is None:
                        sb.click("#ctl00_ContentPlaceHolder1_imgBtnCreateNewCaptcha2")
                        with TemporaryDirectory() as tempdir:
                            sb.save_element_as_image_file("#ctl00_ContentPlaceHolder1_ImgCaptcha2", "captcha.png", folder=tempdir)
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
                            await client.send_message(config['telegram_username'], msg)
                            print(msg)
                            print("Unknown state. Still staying in the second page.")
                        sb.wait_for_and_accept_alert()
                    except Exception:
                        print("Unknown state. Still staying in the second page.")

                    banks = sb.get_select_options("#ctl00_ContentPlaceHolder1_ddlBankName")
                    if captcha is not None and len(banks) > 1:
                        sb.select_option_by_text("#ctl00_ContentPlaceHolder1_ddlBankName", random.choice(banks[1:]))
                        branches = sb.get_select_options("#ctl00_ContentPlaceHolder1_lstBoxSuggShb")
                        sb.select_option_by_text("#ctl00_ContentPlaceHolder1_lstBoxSuggShb", random.choice(branches[1:]))
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
                                await client.send_message(config['telegram_username'], msg)
                                print(msg)
                                print("Unknown state. Still staying in the second page.")
                                pdb.set_trace()
                            sb.wait_for_and_accept_alert()
                        except Exception:
                            print("Unknown state. Still staying in the second page.")
                            pdb.set_trace()
            except Exception:
                second_page = False
                reinitialize = True
                sms_code = None
                success = False
                traceback.print_exc()
                formatted_lines = traceback.format_exc().splitlines()
                msg = formatted_lines[0] + '\n' + formatted_lines[-1]
                print(msg)


with client:
    client.loop.run_until_complete(main())

