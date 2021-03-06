#!/usr/bin/env python3
from selenium import webdriver
import time, json, requests, sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
#-------------------------------------------------------------------------#
def waitForItem(driver, css, timeout=10):
    WebDriverWait(driver, timeout).until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, css)))
def find_answers(quizID):
    quizInfo = requests.get("https://quizizz.com/quiz/" + quizID + "/").json()
    answers = {}
    if "error" in quizInfo:
        print("[error] I couldn't find that quiz")
        exit()

    for question in quizInfo["data"]["quiz"]["info"]["questions"]:
        if question["type"] == "MCQ":
            if question["structure"]["options"][int(question["structure"]["answer"])]["text"] == "":
                # image answer
                answer = question["structure"]["options"][int(question["structure"]["answer"])]["media"][0]["url"]
            else:
                answer = question["structure"]["options"][int(question["structure"]["answer"])]["text"]
        elif question["type"] == "MSQ":
            # multiple answers
            answer = []
            for answerC in question["structure"]["answer"]:
                if question["structure"]["options"][int(answerC)]["text"] == "":
                    answer.append(question["structure"]["options"][int(answerC)]["media"][0]["url"])
                else:
                    answer.append(question["structure"]["options"][int(answerC)]["text"])
        questionID = question["structure"]["query"]["text"]
        answers[questionID.replace("&nbsp;"," ").replace(u'\xa0',u' ').rstrip("\n\r").lower()[:75]] = answer.replace("&nbsp;"," ").rstrip("\n\r").lower()
    return answers
def play(gamecode, name, gameID, short_delay=0.2, delay=0.5, long_delay=5):
    driver = webdriver.Chrome("C:/chromedriver.exe")
    driver.get("https://quizizz.com/join/")
    print("[info] starting game")
    waitForItem(driver,'.check-room-input')
    driver.find_element_by_css_selector('.check-room-input').send_keys(gamecode)
    driver.find_element_by_css_selector('.proceed-button').click()
    waitForItem(driver,'.check-player-input')
    driver.find_element_by_css_selector('.check-player-input').send_keys(name)
    driver.find_element_by_css_selector('.proceed-button').click()
    time.sleep(long_delay)
    driver.find_element_by_css_selector('.skip-btn').click()
    time.sleep(long_delay)
    driver.find_element_by_css_selector('.game-start-btn').click()
    time.sleep(delay)
    answers = find_answers(gameID)
    print("[info] answers found")
    notFirstQuestion = False
    while True:
        time.sleep(delay)
        if notFirstQuestion:
            time.sleep(long_delay)
        notFirstQuestion = True
        try:
            question = None
            while question is None:
                try:
                    question = driver.find_element_by_css_selector('.question-text-color').get_attribute('innerHTML').replace("&nbsp;"," ").replace(u'\xa0',u' ').rstrip("\n\r").lower()
                    if question:
                        break
                except Exception:
                    time.sleep(0.001)
            questionAnswer = answers[question[:75]]
            choices = driver.find_element_by_css_selector('.options-container').find_elements_by_css_selector('.option')
            for answer in choices:
                try:
                    if isinstance(questionAnswer, list):
                        # multiple select
                        if answer.find_element_by_css_selector(".resizeable").get_attribute('innerHTML').lower() in questionAnswer:
                            answer.click()
                            break
                    elif answer.find_element_by_css_selector(".resizeable").get_attribute('innerHTML').lower() == questionAnswer:
                        while True:
                            try:
                                answer.click()
                                break
                            except Exception:
                                time.sleep(0.001)
                        break      
                except NoSuchElementException:
                    # Is an image
                    style = answer.find_element_by_css_selector(".option-image").get_attribute("style").lower()
                    if isinstance(questionAnswer, list):
                        # multiple select
                        for correctAnswer in questionAnswer:
                            if style in correctAnswer:
                                answer.click()
                                break
                    elif questionAnswer in style:
                        answer.click()
                        break
            if isinstance(questionAnswer, list):
                driver.find_element_by_css_selector(".multiselect-submit-btn").click()
        except KeyError:
            print(question)
            for answer in driver.find_element_by_css_selector('.options-container').find_elements_by_css_selector('.option'):
                print(answer.find_element_by_css_selector(".resizeable").get_attribute('innerHTML').lower())
            try:
                print(answers[input("Manual search for answer - question >>> ").lower()])
                input("Click the answer please then hit [enter]")
            except KeyError:
                input("Manual search failed. Try clicking the correct answer then hit [enter]")
    driver.quit()

if __name__ == '__main__':
    USAGE = "quizizz-bot (INFO|PLAY)"
    if len(sys.argv) == 1:
       print(USAGE) 
    elif sys.argv[1] == "INFO":
        answers = find_answers(input("gameID >>> "))
        for key in answers:
            print("{}\n>>> {}\n{}".format(key, answers[key], "="*20))
    elif sys.argv[1] == "PLAY":
        play(input("PIN >>> "), input("username >>> "), input("gameID >>> "))
    else:
        print(USAGE)
