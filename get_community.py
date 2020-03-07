import time
import sys
import os
import random
from twitter import *
from tweepy.error import TweepError


class Graph:
    def __init__(self, output_file):
        self.nodes = set()
        self.edges = set()
        if os.path.isfile(output_file):
            self.init_from_file(output_file)
            self.file = open(output_file, 'a')
        else:
            self.file = open(output_file, 'w')
            self.file.write('follower,followed\n')
        self.initial_nodes = set(self.nodes)
        self.output_file = output_file

    def init_from_file(self, filename):
        with open(filename, 'r') as f:
            for i, line in enumerate(f):
                if i == 0:
                    assert line == 'follower,followed\n'
                    continue
                usr, other = line.split(',')
                usr = int(usr)
                other = int(other)
                self.nodes.add(usr)
                self.nodes.add(other)
                self.edges.add((usr, other))
        print(f'Initialized from file, got {len(self.nodes)} nodes and {len(self.edges)} edges')

    def add_edge(self, usr, other, only_if_exists):
        if (usr, other) in self.edges:
            return
        if only_if_exists and (usr not in self.nodes or other not in self.nodes):
            return
        self.nodes.add(usr)
        self.nodes.add(other)
        self.edges.add((usr, other))
        self.file.write(f'{usr},{other}\n')


def explore_users(user_list, graph, only_if_exists):
    for i, usr in enumerate(user_list):
        print(f'{i:5d}/{len(user_list):5d}')
        try:
            for other in get_follower_ids(usr):
                graph.add_edge(other, usr, only_if_exists)
            for other in get_friend_ids(usr):
                graph.add_edge(usr, other, only_if_exists)
        except TweepError:
            continue


def get_community(base_users, output_file, filter_location=None):
    t1 = time.time()
    base_users = [api.get_user(screen_name=usr).id for usr in base_users]
    graph = Graph(output_file)
    try:
        explore_users(base_users, graph, only_if_exists=False)
    except KeyboardInterrupt:
        print('Download of the nodes interrupted by user')
    community = graph.nodes - set(base_users)
    t2 = time.time()
    print(f'Downloaded the {len(community)} nodes of the graph in {t2-t1:.2f} seconds')
    community = list(community - graph.initial_nodes)
    print(f'Removed all users already in the file, there remains {len(community)}')
    if filter_location:
        loc = filter_location.lower()
        users = ids_to_users(community)
        community = [usr.id for usr in users if loc in usr.location.lower()]
    print(f'Removed all users not located in {filter_location}, there remains {len(community)}')
    random.shuffle(community)
    try:
        explore_users(community, graph, only_if_exists=True)
    except KeyboardInterrupt:
        print('Download of the edges interrupted by user')
    t3 = time.time()
    print(f'Downloaded the {len(graph.edges)} edges of the graph in {t3-t2:.2f} seconds')
    print(f'Total time: {t3-t1:.2f} seconds')


def main():
    if len(sys.argv) <= 1:
        sys.exit(f'Syntax: {sys.argv[0]} <twitter_users>')
    get_community(sys.argv[1:], 'community.csv', filter_location='Grenoble')


if __name__ == '__main__':
    main()
