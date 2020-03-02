import time
import sys
import random
from twitter import *
from tweepy.error import TweepError


class Graph:
    def __init__(self, output_file):
        self.output_file = output_file
        self.file = open(output_file, 'w')
        self.file.write('follower,followed\n')
        self.nodes = set()
        self.edges = set()

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


def get_community(base_users, output_file):
    t1 = time.time()
    base_users = [api.get_user(screen_name=usr).id for usr in base_users]
    graph = Graph(output_file)
    try:
        explore_users(base_users, graph, only_if_exists=False)
    except KeyboardInterrupt:
        print('Download of the nodes interrupted by user')
    community = list(graph.nodes - set(base_users))
    t2 = time.time()
    print(f'Downloaded the {len(community)} nodes of the graph in {t2-t1:.2f} seconds')
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
    get_community(sys.argv[1:], 'community.csv')


if __name__ == '__main__':
    main()