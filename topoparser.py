#!/usr/bin/env python

import yaml
import optparse
import importlib
import json, os

from topogram.corpora.csv_file import CSVCorpus

from topogram.processors.regexp import Regexp
from topogram.processors.nlp import NLP
from topogram.processors.graph import Graph
from topogram.processors.time_rounder import TimeRounder

from topogram.vizparsers.network import Network
from topogram.vizparsers.time_series import TimeSeries

# parse command line
parser = optparse.OptionParser()

parser.add_option('-o', '--output-dir',
    action="store", dest="output",
    help="Store to file", default="stdout")

options, args = parser.parse_args()

for f in  args : 
    with open(f, 'r') as stream:
        raw = yaml.load(stream)

        # load corpus
        corpora = {}
        for corpo in raw["corpora"]:
            corpus_name =  corpo.keys()[0]
            c = corpo[corpus_name]
            corpora[corpus_name] = {} # init

            if c["type"] == "csv":
                corpora[corpus_name] = CSVCorpus(c["file"],
                                source_column = c["columns"]["source"],
                                text_column=c["columns"]["text"],
                                timestamp_column=c["columns"]["timestamp"],
                                time_pattern=c["columns"]["time_pattern"],
                                additional_columns=c["columns"]["data"])

                # validate corpus formatting
                try :
                    corpora[corpus_name].validate()
                except ValueError, e:
                    print e.message, 422

            elif c["type"] == "csv_nodes":
                pass
            else : 
                raise NotImplementedError("Data type is not available yet.")



        # init pipeline
        pipeline = {}

        # fill pipeline with empty values to create its structure 
        paths = [path for path in raw["process"].keys()]
        for path in paths : 
            corpus_name = path.split(".")[0]

            # create each empty corpus
            try :
                pipeline[corpus_name]
            except :
                pipeline[corpus_name] = {}

            # init columns
            column_name = path.split(".")[1]
            pipeline[corpus_name][column_name] = [] # ordered actions to take 

        # start to loop
        for path in paths : 

            # extract important values from name 
            corpus_name = path.split(".")[0]
            column_name = path.split(".")[1]

            #
            for i, command in  enumerate(raw["process"][path]):

                # find each command
                for com in command:

                    # get action name
                    action =  [c for c in command[com].keys() if c != "type"][0] 

                    # parse command
                    todo = {}
                    todo["name"] = com
                    todo["type"] =  command[com]["type"]
                    todo["index"] = i

                    # bind relevant processor class
                    if action == "regexp":
                        r= command[com]["regexp"]
                        todo["command"] = Regexp(r.encode("utf-8"))
                    elif action == "nlp":
                        language = command[com]["nlp"]
                        todo["command"] = NLP(language)
                    elif action == "graph":
                        run = command[com]["graph"]
                        todo["command"] = Graph()
                    elif action == "timeseries":
                        timescale = command[com]["timeseries"]
                        todo["command"] = TimeRounder(timescale)
                    elif action == "run":
                        todo["command"] = command[com]["run"]

                    # add to pipeline 
                    if todo != {} : 
                       pipeline[corpus_name][column_name].append(todo)

        print pipeline # for monitoring

        # parse viz
        vizs = []
        for viz_type in raw["viz"]: 
            # print "viz ", viz_type

            # create new model
            viz = {}
            

            # add data
            viz['data'] = raw["viz"][viz_type]
            viz['name'] = viz_type

            # parse visualizer
            if viz_type  == "network" : 
                viz["command"] = Network()
            elif  viz_type == "timeseries" : 
                viz["command"] = TimeSeries()
            elif  viz_type == "map" : 
                pass
            elif  viz_type == "network_map" : 
                pass
            else : 
                raise NotImplementedError("Viz model not implemented")
            
            # stock all vizs
            vizs.append(viz)

        print vizs # for monitoring


# init data processing
results = {}

# loop through the whole pipeline, corpus by corpus 
for corpus_name in pipeline :

    # load corpus
    corpus = corpora[corpus_name]

    piped = False # checked if previously pipe

    # loop through corpus
    for row in corpus : 


        # for each colum
        for column_name in pipeline[corpus_name]:

            # apply each action
            commands = pipeline[corpus_name][column_name]
            
            # print commands
            for command in commands: 

                # implement basic pipe process (use the precedent result) 
                if piped is True: 
                    result = command["command"](result)
                    piped = False
                else :
                    try :
                        result = command["command"](row[column_name+"_column"])
                    except :
                        print "Processing error with %s" %command["command"]
                        result = []

                # 
                if command["type"] == "pipe": piped = True
                elif command["type"] == "save": 
                    if result != [] : 
                        path = corpus_name+"."+column_name+"."+command["name"]
                        try : 
                            results[path]
                        except : 
                            results[path] = [] 
                        results[path] += result

                elif com["type"] == "exclude":
                    pass
                else : 
                    raise NotImplementedError("not implemented")


# check results
for res in results: 
    print res, len(results[res])

# parse for visualizations
for viz in vizs:

    # build a tuples containing arguments of the function
    names = [ viz["data"][field]   for field in viz["data"] ]

    args = tuple([results[arg] for arg in names])
    viz["command"]( *(args)  ) # call the function

    #export to JSON 
    final = viz["command"].to_JSON()
    
    if options.output == "stdout": 
        print  final # on the cli
    else :
        if not os.path.exists(options.output):
            os.makedirs(options.output)
        json_path = os.path.join(options.output, viz["name"]+".json")
        with open(json_path, "wb") as f :
            json.dump(final, f)




