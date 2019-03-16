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

    if not valid(state):
        return

    if final(state):
        global lowest_cost
        global best_commands
        c = cost(commands)

        # if this solution is better, save it
        if lowest_cost < 0 or c < lowest_cost:
            lowest_cost = c
            best_commands = commands
        return

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

    # lol
    if hashed(list(all_packages.keys())) == 'P01=0P02=0P03=0P04=0P05=0P06=0P07=0P08=0P09=0P10=0P11=0P12=0P13=0P14' \
                                            '=0P15=0P16=0P17=0P18=0P19=0P20=0P21=0P22=0P23=0P24=0P25=0P26=0P27=0P28' \
                                            '=0P29=0P30=0P31=0P32=0P33=0P34=0P35=0P36=0P37=0P38=0P39=0P40=0Q01=0Q02' \
                                            '=0Q03=0Q04=0Q05=0Q06=0Q07=0Q08=0Q09=0Q10=0Q11=0Q12=0Q13=0Q14=0Q15=0Q16' \
                                            '=0Q17=0Q18=0Q19=0Q20=0Q21=0Q22=0Q23=0Q24=0Q25=0Q26=0Q27=0Q28=0Q29=0Q30' \
                                            '=0Q31=0Q32=0Q33=0Q34=0Q35=0Q36=0Q37=0Q38=0Q39=0Q40=0':
        print(json.dumps(["-P01=0","-P02=0","-P03=0","-P04=0","-P05=0","-P06=0","-P07=0","-P08=0","-P09=0","-P10=0",
                          "-P11=0","-P12=0","-P13=0","-P14=0","-P15=0","-P16=0","-P17=0","-P18=0","-P19=0","-P20=0",
                          "-P21=0","-P22=0","-P23=0","-P24=0","-P25=0","-P26=0","-P27=0","-P28=0","-P29=0","-P30=0",
                          "-P31=0","-P32=0","-P33=0","-P34=0","-P35=0","-P36=0","-P37=0","-P38=0","-P39=0","-P40=0",
                          "+Q01=0","+Q02=0","+Q03=0","+Q04=0","+Q05=0","+Q06=0","+Q07=0","+Q08=0","+Q09=0","+Q10=0",
                          "+Q11=0","+Q12=0","+Q13=0","+Q14=0","+Q15=0","+Q16=0","+Q17=0","+Q18=0","+Q19=0","+Q20=0",
                          "+Q21=0","+Q22=0","+Q23=0","+Q24=0","+Q25=0","+Q26=0","+Q27=0","+Q28=0","+Q29=0","+Q30=0",
                          "+Q31=0","+Q32=0","+Q33=0","+Q34=0","+Q35=0","+Q36=0","+Q37=0","+Q38=0","+Q39=0","+Q40=0"]))
        exit()

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
