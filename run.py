from models.package import Package
import argparse
import itertools
import json
import re
import signal

seen = []

lowest_cost = -1
best_commands = []


class OutOfTime(Exception):
    pass


def timeout(sig, frame):
    raise OutOfTime()


# all packages that match this constraint
def matches(constraint):
    r = re.compile("([>=<]+)")
    c = re.split(r, constraint)
    return [p for p in repo[c[0]] if p.satisfies(constraint)]


def final(state):
    state = [all_packages[identifier] for identifier in state]
    return all(
        # make sure all + constraints are satisfied by a package
        any(p.satisfies(a[1:]) for p in state) for a in add
    ) and not any(
        # make sure no packages exist that need to be removed
        p.satisfies(r[1:]) for p in state for r in remove
    ) and not (len(add) > 0 and len(state) == 0)


def hashed(state):
    return ''.join(sorted(state))


def valid(state):
    state = [all_packages[identifier] for identifier in state]

    # do all packages have all their dependencies
    return all(
        # are all dependencies met for this package
        all(
            # is this dependency met by any of its options
            any(
                # do any packages match this constraint
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

    # don't install a package that is already in the initial state
    if package not in initial:
        commands.append("+%s" % package)

    commands = [x for x in commands if x != "-%s" % package]
    return state, commands


def remove_package(state, commands, package):
    state = state.copy()
    commands = commands.copy()
    state = [x for x in state if x != package]

    # don't remove a package not in the initial state
    if package in initial:
        commands.append("-%s" % package)

    commands = [x for x in commands if x != "+%s" % package]
    return state, commands


def dfs(state, commands):
    h = hashed(state)
    if h in seen:
        return
    else:
        seen.append(h)

    for identifier, package in all_packages.items():
        if identifier not in state:
            state, commands = add_package(state, commands, identifier)
        else:
            state, commands = remove_package(state, commands, identifier)

        if not valid(state):
            continue

        if final(state):
            global lowest_cost
            global best_commands
            c = cost(commands)

            # if this solution is better, save it
            if lowest_cost < 0 or c < lowest_cost:
                lowest_cost = c
                best_commands = commands
            continue

        dfs(state, commands)

    return state


if __name__ == "__main__":
    # repo, initial state, constraints
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    parser.add_argument("initial_state")
    parser.add_argument("constraints")
    args = parser.parse_args()

    signal.signal(signal.SIGALRM, timeout)

    # 5 minutes minus 10 seconds just to be on the safe side
    signal.alarm((5 * 60) - 10)

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

    try:
        dfs(initial, [])
    except RecursionError:
        print(json.dumps(["recursion"]))
        exit()
    except OutOfTime:
        pass

    if lowest_cost < 0:
        print(json.dumps(["no_solution"]))
    else:
        print(json.dumps(best_commands))
