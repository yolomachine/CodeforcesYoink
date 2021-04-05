import os
import json
from yoink.utils import Config

if __name__ == '__main__':
    config = Config()
    if not os.path.exists(config.working_dir_path):
        exit()

    sources = {}
    contests = [info[0] for info in os.walk(config.working_dir_path)]
    for contest in contests:
        path = config.combine_path(contest)
        meta_path = os.path.join(path, 'meta.json')
        submissions_path = os.path.join(path, 'submissions')

        if not os.path.exists(submissions_path):
            continue

        names = os.listdir(submissions_path)
        for submission_name in names:
            submission_path = os.path.join(submissions_path, submission_name)
            with open(submission_path, 'r') as fp:
                data = json.load(fp)
                tags = data['Tags']
                code = data['Source-Code']
                if len(tags) == 0:
                    continue

            tag = tags[0]
            tag_priority_list = [
                'combinatorics',
                'data structures',
                'constructive algorithms',
                'dp',
                'greedy',
                'graphs',
                'games',
                'interactive',
                'math',
                'sortings',
                'binary search'
            ]
            for t in tag_priority_list:
                if t in tags:
                    tag = t
                    break
            if tag not in sources:
                sources[tag] = []
            sources[tag].append({'name': submission_name.replace('.json', ''), 'code': code})

    index = 0
    prefix = f'dataset_{index}'
    while os.path.exists(prefix):
        index += 1
        prefix = f'dataset_{index}'

    os.mkdir(prefix)
    for tag in sources:
        tag_path = os.path.join(prefix, tag)
        if not os.path.exists(tag_path):
            os.mkdir(tag_path)
        for entry in sources[tag]:
            with open(os.path.join(tag_path, f'{entry["name"]}.txt'), 'w', encoding='utf-8') as fp:
                fp.write(entry['code'])
