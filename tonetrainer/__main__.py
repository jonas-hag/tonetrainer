import sys
import sqlite3
import requests
import vlc


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
            # all_data contains a tuple with the following fields:
            # traditional, simplified, pinyin_1, pinyin_2, tone_1, tone_2,
            # forvo_available, number_tested

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
                self.connection.close()
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

    def show_pinyin(self):
        output_string = self.all_data[2] + " " + self.all_data[3]
        print(output_string)

    def evaluate_userinput(self):
        input_string = str(input())

        # parse the input and extract the possible tones
        if (len(input_string) == 2):
            first_tone = input_string[0]
            second_tone = input_string[1]
            try:
                first_tone_int = int(first_tone)
            except:
                first_tone_int = -1

            try:
                second_tone_int = int(second_tone)
            except:
                second_tone_int = -1
        else:
            first_tone_int = -1
            second_tone_int = -1

        if input_string == "q":
            self.connection.close()
            sys.exit(0)
        elif input_string == "r":
            self.play_audio()
            return True
        elif (first_tone_int > 0 and first_tone_int < 6 and
              second_tone_int > 0 and second_tone_int < 6):
            self.check_tones(first_tone_int, second_tone_int)
            return False
        else:
            print("please either enter 'q', 'r' or a tone combination, "
                  "e.g. 14")
            return True

    def check_tones(self, first_tone, second_tone):
        correct_first_tone = int(self.all_data[4])
        correct_second_tone = int(self.all_data[5])
        if (first_tone == correct_first_tone and
                second_tone == correct_second_tone):
            print("your guess was correct")
        else:
            print("your guess was not correct; the correct tones are " +
                  self.all_data[4] + " " + self.all_data[5])
        print("the queried word was " + self.all_data[1])

    def update_db(self):
        new_number_tested = int(self.all_data[7]) + 1
        new_number_tested_str = str(new_number_tested)
        self.cursor.execute(
            "UPDATE toneinfo SET number_tested = ? "
            "WHERE simplified = ?",
            (new_number_tested_str, self.all_data[1])
        )
        self.connection.commit()


def run_app():
    while True:
        current_pair = TonePair()
        # 1. get a new tonepair
        current_pair.new()
        # 2. play the audio/show pinyin
        current_pair.show_pinyin()
        current_pair.play_audio()
        # 3. evaluate user input
        current_pair_active = True
        while current_pair_active:
            current_pair_active = current_pair.evaluate_userinput()
        # 4. save changes
        current_pair.update_db()
        # 5. wait until enter
        input()

if __name__ == "__main__":
    # test = TonePair()
    # test.new()
    # test.show_pinyin()
    # test.play_audio()
    # test.evaluate_userinput()
    # test.update_db()
    # show startup message
    print("Welcome to the (mandarin) tonetrainer (c) 2020 - 2021 Jonas Hagenberg")
    print("Characters and pinyin by CEDICT, pronounciation by forvo.com")
    print("For help press 'h + Enter', to start press 's + Enter'")
    # start program or show help
    input_string = str(input())
    while input_string != "h" and input_string != "s" and input_string != "q":
        print("Please enter a character out of the choices")
        input_string = str(input())

    if input_string == "h":
        print("help here")
        # TODO: show help
    elif input_string == "s":
        print("start program here")
        run_app()
    else:
        sys.exit(0)
