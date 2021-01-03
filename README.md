# tonetrainer
This command line program helps you to train the listening comprehension for tones in mandarin.
While the software itself is free, you need to buy API access from [forvo](https://forvo.com).
For private use this costs $2/month and you have to buy at least 6 months access.

## Installation
1. You need `python 3.x` and `virtualenv` 
2. Download/clone the repository
3. Go to the location of the repository, create a virtual environment and install
the modules mentioned in [`requirements.txt`](requirements.txt)
4. Install the [`VLC media player`](https://www.videolan.org/vlc/index.html) 
(if you use 64bit `python`, you need to install the 64bit version)
5. Add the location of `libvlc.dll` to the `path` variable
6. Go to [forvo](https://api.forvo.com/) and buy an API access key. Store this
key in a file called `apikey.txt` (just one line) in the same directory where
`requirements.txt` is stored
7. Use a font that supports Chinese characters, e.g. `SimHei`
7. Activate the virtual environment and start *tonetrainer* with `python -m tonetrainer`

## Get started
The purpose of this program is to make you better at recognising tones in two
syllable words. You'll see the pinyin (without the tones) and hear the respective
pronunciation. Then you can either replay the audio, play the next pronunciation
from a different person, quit or enter your guess.

On startup, you have the following choices:
- `h + Enter` for help
- `s + Enter` to start the program
- `q + Enter` to exit the program

Once you see the pinyin, you have the following choices:
- `r + Enter` to replay the audio
- `n + Enter` to play the pronunciation from a different person (if available)
- enter your guess, e.g. `14 + Enter`
- `q + Enter` to exit the program

After you've entered your guess, you have the following choices:
- `Enter` to go to the next tone pair
- `r + Enter` to replay the audio from current tone pair
- `n + Enter` to play the pronunciation from a different person (if available) 
from the current tone pair
- `q + Enter` to exit the program

## Tone conversions
If a word consists of two third tone characters, the correct solution is `23`.
To avoid hassles with tone conversions of 不 or 一, words containing these
characters are not used.

## Data
The pronunciations are provided by [forvo](https://forvo.com), the dictionary
information by [CC-CEDICT](https://cc-cedict.org/wiki/start). I use only the 
roughly 2000 most frequent words, word frequency provided by [SUBTLEX-CH](http://crr.ugent.be/programs-data/subtitle-frequencies/subtlex-ch).

## License
TODO, especially for the data used.