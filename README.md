# Subtitle Translator

![python version](https://img.shields.io/badge/Python-3.12-blue)

A program that uses deepl or google to translate multiple subtitle files. Both services offer free api access.

## Instructions

### Install Packages

```commandline
pip install -r requirements.txt
```

- Run the program once to create the credential files.
- At least one api key must be provided for the program to run.

### Deepl API

[Deepl Supported Languages](https://developers.deepl.com/docs/resources/supported-languages)

- Setup free access to the Deepl Translate api. [Link](https://www.deepl.com/en/pro#developer)
- Get the api key from [here](https://www.deepl.com/en/your-account/keys) and paste it in the `deepl api key.txt` file.

### Google API

[Google Supported Languages](https://cloud.google.com/translate/docs/languages)

- Setup free access to the Google Translate api. [Link](https://cloud.google.com/translate/docs/setup)
- Get the api key from [here](https://console.cloud.google.com/apis/credentials) and paste it in the
  `google api key.txt` file.

## Usage

- A folder containing the subtitles to be translated and the source and target language should be provided.
- The subtitles should all have `.srt` extensions.

``` python
translation_dir = Path(r"C:\Users\user1\Downloads\Chinese Videos")
source_lang, target_lang = "ch", "en"
```
