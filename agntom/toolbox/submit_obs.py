import argparse
from os import path
import json
from datetime import datetime, timedelta
import copy
import lco

def run():

    args = get_args()

    obs_template = load_obs_template(args)

    # Load the user's LCO credentials:
    lco_info = lco.load_lco_info(args.lco_info)

    configure_daily_obs(args, obs_template, lco_info)

def configure_daily_obs(args, obs_template, lco_info):

    start_date = datetime.strptime(args.start_date + 'T00:00:00', "%Y-%m-%dT%H:%M:%S")
    end_date = datetime.strptime(args.end_date + 'T23:59:59', "%Y-%m-%dT%H:%M:%S")

    dates = [start_date + timedelta(days=x) for x in range((end_date-start_date).days + 1)]

    for tstart in dates:
        tend = tstart + timedelta(seconds=(60*60*24.0 - 1))

        obs_config = copy.copy(obs_template)

        new_requests = []
        for req in obs_config['requests']:
            req['windows'] = [{
                'start': tstart.strftime("%Y-%m-%dT%H:%M:%S"),
                'end': tend.strftime("%Y-%m-%dT%H:%M:%S")
            }]
            new_requests.append(req)
        obs_config['requests'] = new_requests

        obs_config['name'] = obs_config['name'] + '_' + tstart.strftime("%Y%m%d")
        obs_config['proposal'] = lco_info['proposal_id']

        if 'submit' in args.submit:
            response = lco.lco_api(obs_config, lco_info, 'requestgroups')

            if 'id' in response.keys():
                print('Submitted observation ' + obs_config['name'] + ' with ID='+str(response['id']))
            else:
                print(response)

def load_obs_template(args):

    if path.isfile(args.obs_template):
        obs_template = json.loads(open(args.obs_template).read())

    else:
        raise IOError('Cannot find observation template file ' + args.obs_template)

    return obs_template

def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('obs_template', help='Path to file with the observation template')
    parser.add_argument('start_date', help='Start date in UTC, YYYY-MM-DD')
    parser.add_argument('end_date', help='End date in UTC, YYYY-MM-DD')
    parser.add_argument("lco_info", type=str,
                    help='lco_info: Path to file containing the users LCO token and proposal ID')
    parser.add_argument("submit", type=str,
                    help='submit: Trigger to submit observations to LCO, either "nogo" or "submit"')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    run()