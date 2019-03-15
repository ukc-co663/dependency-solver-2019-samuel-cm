from models.package import Package
import argparse
import itertools
import json
import re

seen = []


def matches(constraint):
    r = re.compile("([>=<]+)")
    c = re.split(r, constraint)
    return [p for p in repo[c[0]] if p.satisfies(constraint)]


def final(state):
    state = [all_packages[identifier] for identifier in state]
    return all(
        p.satisfies(a[1:]) for p in state for a in add
    ) and not any(
        p.satisfies(r[1:]) for p in state for r in remove
    ) and not (len(add) > 0 and len(state) == 0)


def hashed(state):
    return ''.join(sorted(state))


def valid(state):
    state = [all_packages[identifier] for identifier in state]
    return all(
        all(
            all(
                any(x.satisfies(option) for x in state)
                for option in d)
            for d in p.depends)
        for p in state
    ) and not any(
        (a.conflicts_with(b) or b.conflicts_with(a))
        for a, b in itertools.combinations(state, 2)
    )


def cost(transformations):
    return sum([all_packages[t[1:]].size if t.startswith("+") else 10 ** 6 for t in transformations])


def add_package(state, commands, package):
    state = state.copy()
    commands = commands.copy()
    state.append(package)
    commands.append("+%s" % package)
    commands = [x for x in commands if x != "-%s" % package]
    return state, commands


def remove_package(state, commands, package):
    state = state.copy()
    commands = commands.copy()
    state = [x for x in state if x != package]
    commands.append("-%s" % package)
    commands = [x for x in commands if x != "+%s" % package]
    return state, commands


def dfs(state, commands):
    print(state, commands)
    if not valid(state):
        return

    if final(state):
        print(commands)
        exit()

    for identifier, package in all_packages.items():
        if identifier not in state:
            state, commands = add_package(state, commands, identifier)
            dfs(state, commands)
            state, commands = remove_package(state, commands, identifier)

    for identifier, package in all_packages.items():
        if identifier in state:
            state, commands = remove_package(state, commands, identifier)
            dfs(state, commands)
            state, commands = add_package(state, commands, identifier)

    return state


if __name__ == "__main__":
    # repo, initial state, constraints
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    parser.add_argument("initial_state")
    parser.add_argument("constraints")
    args = parser.parse_args()

    with open(args.repo, "r") as f:
        repo = {}
        for x in json.load(f):
            p = Package(x)
            try:
                repo[p.name].append(p)
            except KeyError:
                repo[p.name] = [p]
        all_packages = {v.identifier: v for l in repo.values() for v in l}

    with open(args.initial_state, "r") as f:
        initial = json.load(f)

    with open(args.constraints, "r") as f:
        constraints = json.load(f)

    add = [x for x in constraints if x.startswith("+")]
    remove = [x for x in constraints if x.startswith("-")]

    dfs(initial, [])
