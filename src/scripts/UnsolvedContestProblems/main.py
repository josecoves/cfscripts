import sys
import os

from rich.pretty import pprint
from urllib.parse import quote_plus
from rich.table import Table
from rich.console import Console
from rich.prompt import IntPrompt, Prompt, Confirm
from collections import Counter

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../..")

from lib.submissions import get_submissions, get_submissions_for_contest
from lib.contests import get_contest_map, get_contest_number
from lib.problems import get_problems

# printer.PRINT=set_status

def get_table():
    table=Table(
        title="List of codeforces problems",
        title_style="on_default",
        show_lines=True,
        highlight=True,
        expand=True,
    )
    table.add_column("contest name", ratio=4)
    table.add_column("contest id", ratio=1)
    table.add_column("problem name", ratio=3)
    table.add_column("problem id", ratio=1)
    table.add_column("problem rating", ratio=1)
    table.add_column("url", ratio=7)
    return table

def add_row(table, data, contest_mp):
    cid = None
    if "contestId" in data: cid = data["contestId"]
    cname = None
    if cid is not None: cname = contest_mp[cid]["name"]
    pname = data["name"]
    pid = data["index"]
    rating = None
    if "rating" in data: rating = data["rating"]
    url = None
    if cid is not None:
        url = "https://codeforces.com/contest/{}/problem/{}".format(
            quote_plus(str(cid)),
            quote_plus(pid),
        )
    if cname is None: cname = ""
    if cid is None: cid = ""
    if pname is None: pname = ""
    if pid is None: pid = ""
    if rating is None: rating = ""
    if url is None: url = ""
    table.add_row(cname, str(cid), pname, pid, str(rating), url)

def getStats(problems):
    c = Counter()
    for problem in problems:
        for tag in problem["tags"]:
            c[tag] += 1
    # for tag, count in c.most_common():
    #     print(f"{tag}: {count}")
    return c
    
def ask_numbers(prompt, default=None):
    while True:
        user_input = Prompt.ask(prompt, default=default or "")
        try:
            numbers = [int(x) for x in user_input.replace(",", " ").split()]
            return numbers
        except ValueError:
            print("Invalid input. Please enter a list of numbers separated by spaces or commas.")


def get_unsolved_problems_from_participated_contests(handle):
    submissions = get_submissions(handle)
    used_contest_ids = set()
    contest_mp = get_contest_map()
    solved_problems = set()
    for submission in submissions:
        is_ac = submission["verdict"] == "OK"
        # handle div1 and div2 having the same problems but different ids
        if "contestId" not in submission: continue
        cid = submission["contestId"]
        if is_ac:
            full_problem_name = str(cid) + submission["problem"]["name"]
            solved_problems.add(full_problem_name)
        used_contest_ids.add(cid)
        if cid not in contest_mp: continue
        cnum = get_contest_number(contest_mp[cid]["name"])
        if cid - 1 in contest_mp:
            num = get_contest_number(contest_mp[cid - 1]["name"])
            if num is not None and cnum == num:
                used_contest_ids.add(cid - 1)
                if is_ac:
                    full_problem_name = str(cid - 1) + submission["problem"]["name"]
                    solved_problems.add(full_problem_name)
        if cid + 1 in contest_mp:
            num = get_contest_number(contest_mp[cid + 1]["name"])
            if num is not None and cnum == num:
                used_contest_ids.add(cid + 1)
                if is_ac:
                    full_problem_name = str(cid + 1) + submission["problem"]["name"]
                    solved_problems.add(full_problem_name)
    all_problems = get_problems()
    
    problems = []
    for problem in all_problems:
        is_problem_ok = False
        if "contestId" not in problem:
            is_problem_ok = True
        else:
            cid = problem["contestId"]
            full_problem_name = str(cid) + problem["name"]
            if cid in used_contest_ids and full_problem_name not in solved_problems:
                is_problem_ok = True
        if is_problem_ok:
            problems.append(problem)
    problems = problems[::-1] # reverse
    counter = getStats(problems)
    tags = []
    for i, (tag, count) in enumerate(counter.most_common()[::-1]):
        print(f"{i}. {tag}: {count}")
        tags.append(tag)
    tag_ids = ask_numbers("Enter tag ids (space or comma separated):")
    if len(tag_ids) == 0: return problems
    filtered_problems = []
    for problem in problems:
        is_problem_ok = False
        for id in tag_ids:
            assert(id >= 0 and id < len(tags))
            if tags[id] in problem["tags"]:
                is_problem_ok = True
                break
        if is_problem_ok:
            filtered_problems.append(problem)
    return filtered_problems

def filter_by_rating(problems, rmin, rmax):
    def filter_problem(problem):
        rating = None
        if "rating" in problem: rating = problem["rating"]
        return rating is not None and rmin <= rating <= rmax
    return filter(filter_problem, problems)

def main():
    handle = Prompt.ask("CodeForces handle", default='Jomax100')

    should_filter_by_rating = Confirm.ask(
        "Filter by rating",
        default=False,
    )
    rmin = None
    rmax = None
    if should_filter_by_rating:
        rmin = IntPrompt.ask(
            "Minimum rating",
            choices=list(map(str, range(0,10000))),
            show_choices=False
        ) 
        rmax = IntPrompt.ask(
            "Maximum rating",
            choices=list(map(str, range(rmin,10000))),
            show_choices=False
        ) 

    problems = get_unsolved_problems_from_participated_contests(handle)
    if should_filter_by_rating:
        problems = filter_by_rating(problems, rmin, rmax)

    contest_mp = get_contest_map()
    table = get_table()
    for problem in problems:
        add_row(table, problem, contest_mp)

    console = Console()
    console.print(table)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(1)
    sys.exit(0)
