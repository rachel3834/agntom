from django.test import TestCase
from unittest.mock import patch
from datetime import datetime, timedelta
from dateutil.parser import parse

from tom_observations.tests.factories import ObservingRecordFactory, SiderealTargetFactory
from tom_observations.models import ObservationGroup, DynamicCadence
from tom_observations.facility import get_service_class
from agntom.cadence_strategies import LongBaselineMonitoring

mock_filters = {'1M0-SCICAM-SINISTRO': {
                    'type': 'IMAGE',
                    'class': '1m0',
                    'name': '1.0 meter Sinistro',
                    'optical_elements': {
                        'filters': [{'name': 'Bessell-I', 'code': 'I'}]}
                    }
                }

obs_params = {
        'facility': 'LCO',
        'observation_type': 'IMAGING',
        'name': 'Test',
        'ipp_value': 1.05,
        'start': '2020-01-01T00:00:00',
        'end': '2020-01-02T00:00:00',
        'exposure_count': 1,
        'exposure_time': 60.0,
        'max_airmass': 2.0,
        'observation_mode': 'NORMAL',
        'proposal': 'LCOSchedulerTest',
        'filter': 'I',
        'instrument_type': '1M0-SCICAM-SINISTRO'
    }

@patch('tom_observations.facilities.lco.LCOBaseForm._get_instruments', return_value=mock_filters)
@patch('tom_observations.facilities.lco.LCOBaseForm.proposal_choices',
       return_value=[('LCOSchedulerTest', 'LCOSchedulerTest')])
@patch('tom_observations.facilities.lco.LCOFacility.submit_observation', return_value=[198132])
@patch('tom_observations.facilities.lco.LCOFacility.validate_observation')
class TestCadenceStrategies(TestCase):
    def setUp(self):
        target = SiderealTargetFactory.create()
        obs_params['target_id'] = target.id
        obs_params['start'] = (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S')
        obs_params['end'] = (datetime.now() + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S')
        observing_records = ObservingRecordFactory.create_batch(5,
                                                                target_id=target.id,
                                                                parameters=obs_params)
        self.group = ObservationGroup.objects.create()
        self.group.observation_records.add(*observing_records)
        self.group.save()
        self.dynamic_cadence = DynamicCadence.objects.create(
            cadence_strategy='Test Strategy',
            cadence_parameters={'cadence_frequency': 72},
            active=True,
            observation_group=self.group)

    def test_long_baseline_monitoring(self, patch1, patch2, patch3, patch4):

        # This cadence only triggers when all existing observations have
        # expired
        original_obs = self.group.observation_records.all()
        for observing_record in original_obs:
            observing_record.status = 'WINDOW_EXPIRED'
            observing_record.save()

        # Store the last observation in the original group to test with,
        # since this will be used as the template
        obs_template = self.group.observation_records.order_by('-created').first()
        observation_payload = obs_template.parameters
        facility = get_service_class(obs_template.facility)()
        start_keyword, end_keyword = facility.get_start_end_keywords()
        original_start = parse(observation_payload[start_keyword])
        original_end = parse(observation_payload[end_keyword])

        # Run the cadence strategy.  This should replace all of the original
        # expired records with new ones that have observation windows advanced
        # by the cadence frequency
        strategy = LongBaselineMonitoring(self.dynamic_cadence)
        new_records = strategy.run()
        self.group.refresh_from_db()
        new_obs = self.group.observation_records.all()

        # Cannot check whether the new observations are all now PENDING, because
        # the test DB doesn't update this parameter

        # Check that the first ObservationRecord in the new list has a window
        # starting at the incremented interval
        first_new_obs = self.group.observation_records.order_by('-created').last()
        cadence_frequency = self.dynamic_cadence.cadence_parameters.get('cadence_frequency')
        new_start = parse(obs_template.parameters[start_keyword]) + timedelta(hours=cadence_frequency)

        self.assertEqual(
            parse(first_new_obs.parameters['start']),
            new_start
        )
