from tom_observations.cadence import CadenceStrategy, BaseCadenceForm
from tom_observations.models import ObservationRecord
from tom_observations.facility import get_service_class
from datetime import timedelta
from dateutil.parser import parse


class LongBaselineMonitoringForm(BaseCadenceForm):
    pass

class LongBaselineMonitoring(CadenceStrategy):
    """
    The LongBaselineMonitoring strategy is designed to continue to maintain
    regular photometric observations with consistent parameters
    for targets on a selected target list.

    The user should set up the initial observation request(s) and add them to
    an ObservationGroup, which is then associated with a DynamicCadence.  Each
    DynamicCadence has its own cadence parameter set, used to specify the repeat
    intervals.
    """
    name = 'Long Baseline Monitoring'
    description = """This strategy automatically repeats a set of observation
                    requests with the same parameters to extend the baseline"""
    form = LongBaselineMonitoringForm

    def run(self):

        # Review current set of ObservationRecords in this ObservationGroup,
        # and check to see if they are all expired
        current_obs = self.dynamic_cadence.observation_group.observation_records.all()
        obs_expired = True
        for obs in current_obs:
            if not obs.terminal:
                obs_expired = False

        if not obs_expired:
            return

        # If all current observations in this group have expired, extract the
        # last ObservationRecord to use as a template but then clear the
        # list of ObservationRecords associated with this Group.  This
        # avoids exponentially repeating all subrequests in a cadence group.
        # Note that this does not remove the ObservationRecord from the TOM DB.
        obs_template = self.dynamic_cadence.observation_group.observation_records.order_by('-created').first()

        for record in current_obs:
            if obs.terminal:
                self.dynamic_cadence.observation_group.observation_records.remove(record)

        # Generate a replacement request with the same parameters as
        # the template, but advance the window
        observation_payload = obs_template.parameters
        facility = get_service_class(obs_template.facility)()
        start_keyword, end_keyword = facility.get_start_end_keywords()
        observation_payload = self.advance_window(
            observation_payload, start_keyword=start_keyword, end_keyword=end_keyword
        )
        obs_type = obs_template.parameters.get('observation_type', None)
        form = facility.get_form(obs_type)(observation_payload)
        form.is_valid()
        observation_ids = facility.submit_observation(form.observation_payload())

        # Record the new observations:
        new_observations = []
        for observation_id in observation_ids:
            record = ObservationRecord.objects.create(
                target=obs_template.target,
                facility=facility.name,
                parameters=observation_payload,
                observation_id=observation_id
            )
            self.dynamic_cadence.observation_group.observation_records.add(record)
            self.dynamic_cadence.observation_group.save()
            new_observations.append(record.status)

        return new_observations

    def advance_window(self, observation_payload, start_keyword='start', end_keyword='end'):
        cadence_frequency = self.dynamic_cadence.cadence_parameters.get('cadence_frequency')
        if not cadence_frequency:
            raise Exception(f'The {self.name} strategy requires a cadence_frequency cadence_parameter.')
        advance_window_hours = cadence_frequency
        new_start = parse(observation_payload[start_keyword]) + timedelta(hours=advance_window_hours)
        new_end = parse(observation_payload[end_keyword]) + timedelta(hours=advance_window_hours)
        observation_payload[start_keyword] = new_start.isoformat()
        observation_payload[end_keyword] = new_end.isoformat()

        return observation_payload
