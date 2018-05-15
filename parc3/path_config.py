import os
import sys
import json


def get_path_config():


    PATH_CONFIG = {
        'PARC': os.path.expanduser('~/parc3/parc3'),
        'BNP': os.path.expanduser('~/parc3/bnp-pcet'),
        'PROPBANK': os.path.expanduser('~/parc3/propbank_1')
    }

    # Read the corenlp path from the corenlpyrc config file
    try:
        RC_PATH_CONFIG = json.loads(
            open(os.path.expanduser('~/.parc3rc')).read()
        )
        expected_keys = set(PATH_CONFIG.keys())
        found_keys = set(RC_PATH_CONFIG.keys())
        unexpected_keys = found_keys - expected_keys
        if len(unexpected_keys) > 0:
            raise ValueError(
                'Got unexpected key(s) in .parcrc configuration file: '
                + ', '.join(unexpected_keys)
            )

        print "Using paths set in '~/.parc3rc':"
        PATH_CONFIG.update(RC_PATH_CONFIG)


    # Fail if the corenlpyrc file has invalid json
    except ValueError:
            print "invalid json in '~/.parc3rc'"
            sys.exit(1)

    # Tolerate missing file or unspecified corenlp_path silently
    except IOError:
            print 'Using default paths:'
            pass

    print json.dumps(PATH_CONFIG, indent=2)

    return PATH_CONFIG
