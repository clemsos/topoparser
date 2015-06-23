# Topoparser

Command-line parser for [Topogram](http://github.com/topogram/topogram). 

Use a YAML file to describe data source and workflow

## Install 

    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt

## Usage

Use the command line to call a YAML file containing the parsing instructions  

    python topoparser.py weibo.yaml

You can save the output to json file by specficing and ```--output-dir``` params

    python topoparser.py --output-dir test weibo.yaml


## YAML command file structure

The overall workflow is separated in 3 main steps :

1. **corpora** : load and describe the corpus
2. **process** : extract information from the data
3. **viz** : parse the data properly  (JSON output)


#### Corpora

The corpora description follow a standard model  

    corpora : 
        - content:
            type : csv # could be a mongo or dict adapter
            file : 'examples/sampleweibo.csv' # path of the file
            columns:  # name of the relevant columns or fields
                source : uid
                text : text
                timestamp : created_at
                time_pattern : '%Y-%m-%d %H:%M:%S'
                data : [ permission_denied, deleted_last_seen ]

Multiple corpora can be used together (not implemented yet)

#### Process


You first select the column you want to process from the data set -- ex . ```content.text```

The process remains on several data processors :

* **regexp** : compile a regexp  -- ex. ```regexp : '@([^:：,，\)\(（）|\\\s]+)' ``` extract @ mentions from Twitter-like corpus
* **nlp** : extract keywords from a specific languages  -- ex. ``` nlp : zh ``` extract words from Chinese language
* **graph** :  will add a list of elements into a graph -- ex. ``` graph : add_edges_from_nodes_list ```
* **timeseries** : will format time information following specific time scales (second, minute, hour, day, month, year) -- ex. ``` timeseries : minute ```


You can use  2 different operators to link them together :

**save** : will store the results of the operation 
    -- ex. extract all mentions and keep the results 

    - mentions : 
            regexp : '@([^:：,，\)\(（）|\\\s]+)'
            type : save 


**pipe** : will pass the data to the next operations ( like unix ```|``` symbol )
    -- ex. extract all keywords from a Chinese sentence and add words  into a network

    - words :
        nlp : "zh"
        type : pipe
    - words_relationships :
        graph: add_edges_from_nodes_list
        type : save


**Complete example**

This will extract hashtags, mentions and urls + create a network of words + compute a daily timeseries from the quantity of messages 

    process: 
        content.text :
            - hashtags :
                regexp: '#([^#\s]+)#'
                type : save
            - mentions : 
                regexp : '@([^:：,，\)\(（）|\\\s]+)'
                type : save 
            - urls: 
                regexp : '\b(([\w-]+://?|www[.])[^\s()<>]+(?:\([\w\d]+\)|([^\p{P}\s]|/)))'
                type : save
            - words :
                nlp : "zh"
                type : save
            - words :
                nlp : "zh"
                type : pipe
            - words_relationships :
                graph: add_edges_from_nodes_list
                type : save
        content.time :
            - timecount: 
                timeseries: day
                type : save


## Visualization parsers

The final step is to parse into JSON formatted properly for visualization library (like d3js)

Currently available : timeseries and network. 

    viz :
        timeseries:
            data : content.time.timecount
    network : 
        nodes : content.text.words
        edges : content.text.words_relationships 


## TODO

* Use multiple datasets
* Additional visualization models (map & network+map)
* New data operators like ```fork``` for parrallel processing 
* Support for custom scripts and  operations 


Project inspired by [Datscript](https://github.com/datproject/datscript/) 
