#!/usr/bin/env python

import yaml
import optparse
import importlib
from topogram.corpora.csv_file import CSVCorpus
from topogram.processors.regexp import Regexp
from topogram.processors.nlp import NLP
from topogram.processors.graph import Graph
from topogram.vizparsers.network import Network

parser = optparse.OptionParser()

parser.add_option('-q', '--query',
    action="store", dest="query",
    help="query string", default="spam")

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


        # parse pipeline
        pipeline = {}

        for path in raw["process"].keys() : 
            
            pipeline[path] = [] # ordered actions to take 

            for i, command in  enumerate(raw["process"][path]):
                for com in command:
                    action =  command[com].keys()[0]

                    todo = {}
                    if action == "regexp":
                        r= command[com]["regexp"]
                        todo["name"] = com
                        todo["command"] = Regexp(r.encode("utf-8"))
                        todo["type"] =  command[com]["type"]
                        todo["index"] = i
                    elif action == "nlp":
                        language = command[com]["nlp"]
                        todo["name"] = com
                        todo["command"] = NLP(language)
                        todo["type"] =  command[com]["type"]
                        todo["index"] = i
                    elif action == "graph":
                        todo["name"] = com
                        run = command[com]["graph"]
                        todo["command"] = Graph()
                        todo["type"] =  command[com]["type"]
                        todo["index"] = i
                    elif action == "run":
                        todo["name"] = com
                        todo["command"] = command[com]["run"]
                        todo["type"] =  command[com]["type"]
                        todo["index"] = i
                    
                    pipeline[path]. append(todo)

        # parse viz
        viz = {}

        for viz_type in raw["viz"].keys() : 
            if viz_type  == "network" : 
                Network()
            elif  viz_type == "map" : 
                pass
            elif  viz_type == "network_map" : 
                pass
            else : 
                raise NotImplementedError("Viz model not implemented")


print corpora
print pipeline

for path in pipeline: 
    corpus_name = path.split(".")[0]
    column_name = path.split(".")[1]

    corpus = corpora[corpus_name]
    commands = pipeline[path]
    for row in corpus :
        data = row[column_name+"_column"]
        for com in commands: 
            print com["command"](data)

    
