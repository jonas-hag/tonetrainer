import sys
import sqlite3
import requests
import vlc
import time


class TonePair:

    def __init__(self):
        # set up the DB connection
        self.connection = sqlite3.connect("../data/tone_and_user_info.db")
        self.cursor = self.connection.cursor()
        self.all_data = None
        self.audio_path = None
        # get the API key
        with open("../apikey.txt") as file:
            self.api_key = file.readline().strip()

    def new(self):
        # get a random tone pair (word + audio)
        # as I can't be sure that all words have entries in forvo, repeat the
        # following until a valid entry was found (but as I've filtered for
        # frequency, most words should be known)
        searching_word = True
        while searching_word:
            # get a random entry from the DB
            # but it shouldn't be already shown that it is not in the forvo DB
            sql_query = "SELECT * FROM toneinfo WHERE forvo_available <> 'no' " \
                        "ORDER BY Random() LIMIT 1;"
            self.all_data = self.cursor.execute(sql_query).fetchone()
            # query the word in forvo to get the link for the audio
            # 1. define the parameters
            payload = {"key": self.api_key,
                       "format": "json",
                       "action": "standard-pronunciation",
                       "word": self.all_data[1],
                       "language": "zh"}
            # bring the payload into the correct format
            payload_string = "/".join(key + "/" + value for key, value
                                      in payload.items())
            api_endpoint = "https://apifree.forvo.com/"
            # 2. make the query
            api_result = requests.get(api_endpoint + payload_string)
            # 3. check the result
            if api_result.status_code != 200:
                print("The forvo API can't be reached, "
                      "terminating the program.")
                sys.exit(1)
            # check that the word actually exists
            if len(api_result.json()["items"]) == 1:
                # 4. save the mp3 path
                # the returned json object has the following structure:
                # dictionary with only entry "items": api_result.json()["items]
                # the value of "items" is a list: .[0]
                # this list contains a dictionary which also includes the
                # desired path: .["pathmp3]
                self.audio_path = api_result.json()["items"][0]["pathmp3"]
                # if not already noted in the DB, mark the availability with yes
                if self.all_data[6] != "yes":
                    self.cursor.execute(
                        "UPDATE toneinfo SET forvo_available = ? "
                        "WHERE simplified = ?",
                        ("yes", self.all_data[1])
                    )
                    self.connection.commit()
                searching_word = False
            else:
                # note in the DB that this word is not contained in forvo
                self.cursor.execute(
                    "UPDATE toneinfo SET forvo_available = ? "
                    "WHERE simplified = ?",
                    ("no", self.all_data[1])
                )
                self.connection.commit()

    def play_audio(self):
        # play the audio
        audio_file = vlc.MediaPlayer(self.audio_path)
        audio_file.play()
        time.sleep(5)

    def show_pinyin(self):
        output_string = self.all_data[2] + " " + self.all_data[3]
        print(output_string)

    def get_audio_path(self):
        return self.audio_path


def run_app():
    while True:
        print("p")
        current_pair = TonePair()
        # 1. get a new tonepair
        current_pair.new()
        # 2. play the audio/show pinyin
        current_pair.show_pinyin()
        current_pair.play_audio()
        # 3. get user input
        # 4. play again or evaluate
        # 5. save changes

if __name__ == "__main__":
    test = TonePair()
    test.new()
    test.show_pinyin()
    test.play_audio()
    # # show startup message
    # print("Welcome to the (mandarin) tonetrainer (c) 2020 Jonas Hagenberg")
    # print("Characters and pinyin by CEDICT, pronounciation by forvo.com")
    # print("For help press 'h + Enter', to start press 's + Enter'")
    # # start program or show help
    # input_string = str(input())
    # while input_string != "h" and input_string != "s" and input_string != "q":
    #     print("Please enter a character out of the choices")
    #     input_string = str(input())
    #
    # if input_string == "h":
    #     print("help here")
    #     # TODO: show help
    # elif input_string == "s":
    #     print("start program here")
    #     run_app()
    # else:
    #     sys.exit(0)
