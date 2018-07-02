# FastWordQuery Addon For Anki

## Features

This addon looks up words in local dictionary or web dictionary and pasting the explanations to anki.
It forks from WordQuery, **multi-thread feature**, and some other features.

  > - See [WordQuery](https://github.com/finalion/WordQuery) Addon Project.
  > - Querying Words and Making Cards, IMMEDIATELY!
  > - Support querying in mdx and stardict dictionaries.
  > - Support querying in web dictionaries.
  > - Support Multi-thread to query faster.

## Install

1. Place src folder of this repository to anki addon folder.
**OR**
2. Use the installation code: 1807206748


## Setting

### Shortcut

> 1. Click Menu **"Tools -> Add-ons -> FastWQ -> Edit..."**

![](screenshots/setting_menu.png)

> 2. Edit the code and click **Save**

```python
# shortcut
shortcut = 'Ctrl+Q'
```

![](screenshots/setting_shortcut.png)


### Config

> 1. In Browser window click menu **"FastWQ -> Options"**

![](screenshots/setting_config_01.png)

> 2. Click **Settings** button in the Options window

![](screenshots/setting_config_02.png)

  > - **Force Update : Update all fields even if it's None**
  > - **Thread : The number of threads running at the same time**
  
  
## Use

### Set the query fields

> 1. Click menu **"Tools ->  FastWQ"**, or in Browser window click menu **"FastWQ -> Options"**

> 2. Select note type

![](screenshots/options_01.png)

> 3. Select Dictionary

![](screenshots/options_02.png)

> 4. Select Fields

![](screenshots/options_03.png)

> 5. Click **OK** button


### 'Browser' Window

> Select single word or multiple words, click menu **"FastWQ -> Query Selected"**.

![](screenshots/options_04.png)


## Other Projects Used
  - [mdict-query](https://github.com/mmjang/mdict-query)
  - [pystardict](https://github.com/lig/pystardict)
  - [WordQuery](https://github.com/finalion/WordQuery)
