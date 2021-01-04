import sys
import os
import sqlite3
import requests
import vlc

current_dir = os.path.dirname(__file__)


class TonePair:

    def __init__(self):
        # set up the DB connection
        db_path = os.path.join(current_dir, "../data/tone_and_user_info.db")
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.all_data = None
        self.audio_paths = None
        self.last_played_audio = 0
        # get the API key
        api_path = os.path.join(current_dir, "../apikey.txt")
        with open(api_path) as file:
            self.api_key = file.readline().strip()
        # get users to exclude from pronunciation
        exclude_path = os.path.join(current_dir,
                                    "../data/pron_exclusion_list.txt")
        with open(exclude_path) as file:
            self.excluded_users = file.read().splitlines()
        # read in the settings
        # so far only if simplified or traditional characters are shown
        setting_path = os.path.join(current_dir, "../data/settings.txt")
        with open(setting_path) as file:
            settings = file.read().splitlines()
        if settings[0] == "simplified":
            # because simplified is the second column in the DB
            self.character_style = 1
        elif settings[0] == "traditional":
            # because traditional is the first column in the DB
            self.character_style = 0
        else:
            print("The settings file doesn't contain 'simplified' or "
                  "'traditional' in the first line, stopping.")
            self.connection.close()
            sys.exit(1)

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
                       "action": "word-pronunciations",
                       "word": self.all_data[1],
                       "language": "zh",
                       "order": "rate-desc"}
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
            checked_results = self.check_forvo_results(
                api_result.json()["items"])
            if checked_results[0]:
                # 4. save the mp3 paths
                # the returned json object has the following structure:
                # dictionary with 'attributes'  and 'items' api_result.json()["items]
                # the value of "items" is a list of dictionaries, from each item
                # with a rating from at least 0 that are not from excluded
                # # users extract the mp3path
                # this is done by the check_forvo_results function (above)
                self.audio_paths = checked_results[1]
                # reset the number of current played audio
                self.last_played_audio = 0

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

    def check_forvo_results(self, api_result):
        # check that the forvo API returned entries at all
        if len(api_result) == 0:
            return False, None
        else:
            # if yes, check that there remain entries when the entries from
            # the users in the exclusion list are removed
            # the returned json object has the following structure:
            # the value of api_result is a list of dictionaries, from each item
            # with a rating from at least 0 that are not from the excluded
            # users extract the mp3path
            possible_audio_paths = [entry["pathmp3"] for entry
                                    in api_result
                                    if entry["rate"] >= 0 and
                                    entry[
                                        "username"] not in self.excluded_users]

            # check if there is an audio link left
            if len(possible_audio_paths) > 0:
                return True, possible_audio_paths
            else:
                return False, None

    def play_audio(self, playback_type="current"):
        # play the current or next audio file
        file_number = None
        if playback_type == "current":
            # keep the current audio file
            file_number = self.last_played_audio
        elif playback_type == "next":
            # use the next audio file, if the end of the audio paths are
            # reached, use the first again
            if self.last_played_audio == len(self.audio_paths) - 1:
                file_number = 0
            else:
                file_number = self.last_played_audio + 1
            self.last_played_audio = file_number

        # play the audio
        audio_file = vlc.MediaPlayer(self.audio_paths[file_number])
        audio_file.play()

    def show_pinyin(self):
        # output the pinyin and the number of available pronunciations
        avail_pron = str(len(self.audio_paths))
        string_pron = " [" + avail_pron + " pron.]"
        output_string = self.all_data[2] + " " + self.all_data[3] + string_pron
        print(output_string)

    def evaluate_userinput(self):
        current_input = str(input())

        # parse the input and extract the possible tones
        if len(current_input) == 2:
            first_tone = current_input[0]
            second_tone = current_input[1]
            try:
                first_tone_int = int(first_tone)
            except (ValueError, IndexError):
                first_tone_int = -1

            try:
                second_tone_int = int(second_tone)
            except (ValueError, IndexError):
                second_tone_int = -1
        else:
            first_tone_int = -1
            second_tone_int = -1

        if current_input == "q":
            self.connection.close()
            sys.exit(0)
        elif current_input == "r":
            self.play_audio()
            return True
        elif current_input == "n":
            self.play_audio(playback_type="next")
            return True
        elif (0 < first_tone_int < 6 and
              0 < second_tone_int < 6):
            self.check_tones(first_tone_int, second_tone_int)
            return False
        else:
            print("please either enter 'q', 'r' or a tone combination, "
                  "e.g. 14")
            return True

    def check_tones(self, first_tone, second_tone):
        correct_first_tone = int(self.all_data[4])
        correct_second_tone = int(self.all_data[5])

        # correct for the 33 -> 23 tone conversion
        if correct_first_tone == 3 and correct_second_tone == 3:
            correct_first_tone_adapted = 2
        else:
            correct_first_tone_adapted = correct_first_tone

        if (first_tone == correct_first_tone_adapted and
                second_tone == correct_second_tone):
            print("your guess was correct")
        else:
            if correct_first_tone == 3 and correct_second_tone == 3:
                print("your guess was not correct; the correct tones are "
                      "2 3 (3 3)")
            else:
                print("your guess was not correct; the correct tones are " +
                      self.all_data[4] + " " + self.all_data[5])
        print("the queried word was " + self.all_data[self.character_style])

    def update_db(self):
        new_number_tested = int(self.all_data[7]) + 1
        new_number_tested_str = str(new_number_tested)
        self.cursor.execute(
            "UPDATE toneinfo SET number_tested = ? "
            "WHERE simplified = ?",
            (new_number_tested_str, self.all_data[1])
        )
        self.connection.commit()

    def wait_for_next_pair(self):
        current_input = str(input())
        if current_input == "r":
            self.play_audio()
            return True
        if current_input == "n":
            self.play_audio(playback_type="next")
            return True
        if current_input == "q":
            self.connection.close()
            sys.exit(0)
        else:
            return False


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
        # 5. wait for next commands (replay/quit/continue with next pair)
        wait_for_commands = True
        while wait_for_commands:
            wait_for_commands = current_pair.wait_for_next_pair()


def show_help():
    print("This program helps you to train recognising mandarin tones.")
    print("The program shows you the pinyin of a two character word and "
          "plays the corresponding audio")
    print("To replay the audio, press 'r + Enter', to play the next "
          "pronunciation from a different person,")
    print("press 'n + Enter', to quit the program press 'q + Enter'")
    print("When you want to make a guess, type the two tones and press enter, "
          "e.g. '24'")
    print("After your guess, it is shown if you were correct and which word "
          "was queried")
    print("Then you can replay the audio ('r + Enter'), replay the next audio "
          "('n' + Enter), quit ('q + Enter') "
          "or continue with the next tone pair (press 'Enter')")


if __name__ == "__main__":
    # show startup message
    print(
        "Welcome to the (mandarin) tonetrainer (c) 2020 - 2021 Jonas Hagenberg")
    print(
        "Characters and pinyin by CC-CEDICT, https://cc-cedict.org/wiki/start,")
    print("pronunciations by Forvo, https://forvo.com")
    print("For help press 'h + Enter', to start press 's + Enter',")
    print("to quit press 'q + Enter', to set the simplified/traditional setting, ")
    print("press 't + Enter'")
    # start program or show help
    input_string = str(input())
    while input_string != "h" and input_string != "s"\
            and input_string != "q" and input_string != "t":
        print("Please enter a character out of the choices")
        input_string = str(input())

    if input_string == "h":
        show_help()
        input()
        run_app()
    elif input_string == "t":
        wait_for_input = True
        while wait_for_input:
            print("type 's + Enter' for simplified or 't + Enter' for 'traditional':")
            input_setting = str(input())
            if input_setting == "s":
                setting_path = os.path.join(current_dir, "../data/settings.txt")
                with open(setting_path, "w") as file:
                    file.write("simplified")
                wait_for_input = False
            elif input_setting == "t":
                setting_path = os.path.join(current_dir, "../data/settings.txt")
                with open(setting_path, "w") as file:
                    file.write("traditional")
                wait_for_input = False
            else:
                print("please type one of the above mentioned characters")
                wait_for_input = True

        run_app()
    elif input_string == "s":
        run_app()
    else:
        sys.exit(0)
