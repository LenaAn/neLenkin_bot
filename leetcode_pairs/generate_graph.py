import os

# todo: get them programmatically
users = [0, 3, 4, 6, 7, 10, 11, 16, 18, 21]
number_of_users = 22

graph = set()
for i in range(len(users)):
    for j in range(i+1, len(users)):
        graph.add((users[i], users[j]))
print(f"len(graph) = {len(graph)}")

with open('edges_to_delete.txt', 'r') as f:
    for line in f.readlines():
        (a, b) = [int(item) for item in line.split()]
        print(f"a = {a}, b = {b}")
        if (a, b) in graph:
            graph.remove((a, b))

print(f"after deletion len(graph) = {len(graph)}")

with open('graph_for_week_n', 'w') as f:
    f.write(f"{number_of_users} {len(graph)}\n")
    for (a, b) in graph:
        f.write(f"{a} {b}\n")

ans = os.popen("./a.out < graph_for_week_n").read()
print(f"==========\n{ans}")
