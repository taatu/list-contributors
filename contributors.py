import os

STATISTIC_TYPES = ["orphans", "commits", "files_changed", "additions", "deletions"]


def flatten(z):
    flat = []
    if type(z) is list:
        for i in z:
            flat += flatten(i)
        return flat
    else:
        return [z]


def print_contributors(sort: str = "commits+orphans"):
    """Get list of contributors for current git repository.\n
    valid sorts are: commits, orphans, commits+orphans, additions, deletions, files_changed, geomean\n
    Orphans are commits with no information. Geomean takes commits+orphans as one value."""

    if sort not in ["commits", "orphans", "additions", "deletions", "files_changed", "commits+orphans", "geomean"]:
        raise ValueError("Invalid argument for sort. " + str(print_contributors.__doc__).split("\n\n    ")[1])

    cmd = "git log --oneline --pretty=\"@%an\"  --stat   |grep -v \\| |  tr \"\n\" \" \"  |  tr \"@\" \"\n\" > statfile.txt"
    success_file = False
    try:
        with open("statfile.txt", "r") as fp:
            text = fp.readlines()
            if len(text) < 2:
                os.remove("statfile.txt")
                print_contributors(sort)
                return
            success_file = True
    except IOError:
        success_file = False

    if not success_file:
        try:
            if "bash" not in os.getenv("SHELL"):
                raise OSError("This script cannot generate the git output without access to the bash shell.")
            os.system(cmd)
            with open("statfile.txt", "r") as fp:
                text = fp.readlines()
        except TypeError:
            raise OSError("This script cannot generate the git output without access to the bash shell.")
        except IOError:
            raise IOError("Could not open statfile.txt")

    lst = []
    for i in text:
        x = i.split("   ")
        if len(x) > 1:
            x = [x[0], x[1].split(" ")]

        x = flatten(x)
        newx = []
        for k in x:
            k = k.replace(" \n", "").replace("\n", "")
            if len(k) > 0:
                newx.append(k)
        x = newx
        if len(x) > 0:
            x[0] = x[0].lower().replace(" ", "")
            lst.append(x)

    if len(lst) == 0:
        print("0 commits found.")
        return

    authors = dict()
    for i in lst:
        if i[0] not in authors:
            authors[i[0]] = {"orphans": 0, "commits": 0, "files_changed": 0, "additions": 0, "deletions": 0}

    for i in lst:
        if len(i) == 1:
            authors[i[0]]["orphans"] += 1
        elif len(i) == 8:
            authors[i[0]]["commits"] += 1
            authors[i[0]]["files_changed"] += int(i[1])
            authors[i[0]]["additions"] += int(i[4])
            authors[i[0]]["deletions"] += int(i[6])
        elif len(i) == 6 and any(["insertions(+)" in i, "insertion(+)" in i]):
            authors[i[0]]["commits"] += 1
            authors[i[0]]["files_changed"] += int(i[1])
            authors[i[0]]["additions"] += int(i[4])
        elif len(i) == 6 and any(["deletion(-)" in i, "deletions(-)" in i]):
            authors[i[0]]["commits"] += 1
            authors[i[0]]["files_changed"] += int(i[1])
            authors[i[0]]["deletions"] += int(i[4])
        else:
            print("ERROR: " + str(i) + " len: " + str(len(i)))
            raise ValueError

    if sort == "commits+orphans":
        sorted_authors = sorted(authors.items(), key=lambda item: item[1]["commits"] + item[1]["orphans"], reverse=True)
    elif sort == "geomean":
        def geomean(item):
            total = 1.0
            for i in STATISTIC_TYPES[2:]:
                val = item[1][i]
                if val == 0:
                    val = 1
                total *= val
            total *= (item[1]["orphans"] + item[1]["commits"])
            return total**(1/(len(STATISTIC_TYPES) - 1))
        sorted_authors = sorted(authors.items(), key=geomean, reverse=True)
    else:
        sorted_authors = sorted(authors.items(), key=lambda item: item[1][sort], reverse=True)

    maxes = dict()
    maxes["name_len"] = len(max(sorted_authors, key=lambda item: len(item[0]))[0])
    for i in STATISTIC_TYPES:
        maxes[i] = len(str(max(sorted_authors, key=lambda item: len(str(item[1][i])))[1][i]))

    for i in sorted_authors:
        print("{}: commits: {} orphans: {} additions: {} deletions: {} files changed: {}".format(
            i[0].rjust(maxes["name_len"]),
            str(i[1]["commits"]).ljust(maxes["commits"]),
            str(i[1]["orphans"]).ljust(maxes["orphans"]),
            str(i[1]["additions"]).ljust(maxes["additions"]),
            str(i[1]["deletions"]).ljust(maxes["deletions"]),
            str(i[1]["files_changed"]).ljust(maxes["files_changed"])))


if __name__ == "__main__":
    print_contributors(sort="commits+orphans")
