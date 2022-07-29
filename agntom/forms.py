from tom_observations.observation_template import GenericTemplateForm
from tom_observations.facilities.lco import LCOBaseForm, LCOBaseObservationForm
from django import forms
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Div, Submit

class LCOImagingTemplateForm(GenericTemplateForm, LCOBaseForm):
    """
    The template form modifies the LCOBaseForm in order to only provide fields
    that make sense to stay the same for the template. For example, there is no
    point to making start_time an available field, as it will change between
    observations.
    """
    min_lunar_distance = forms.FloatField()
    max_lunar_phase = forms.FloatField()
    cadence = forms.FloatField()
    jitter = forms.FloatField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in ['groups', 'target_id']:
            self.fields.pop(field_name, None)
        for field in self.fields:
            if field != 'template_name':
                self.fields[field].required = False
        self.helper.layout = Layout(
            self.common_layout,
            Row(
                Column('proposal'),
                ),
            Row(
                Column('ipp_value'),
                Column('filter'),
                Column('instrument_type'),
                ),
            Row(
                Column('exposure_time'),
                Column('exposure_count'),
                ),
            Row(
                Column('max_airmass'),
                Column('min_lunar_distance'),
                Column('max_lunar_phase'),
                ),
            Row(
                Column('cadence'),
                Column('jitter'),
                )
            )

class LCOCustomPhotometricSequenceForm(LCOBaseObservationForm):
    """
    The LCOCustomPhotometricSequenceForm provides a form that allows the user
    to request imaging exposure sequences in multiple filters within the
    same observation request.
    The form is adapted from the TOM's internal LCOPhotometricSequenceForm.
    """
    valid_instruments = ['1M0-SCICAM-SINISTRO', '0M4-SCICAM-SBIG', '2M0-SPECTRAL-AG']
    valid_filters = ['U', 'B', 'V', 'R', 'I', 'up', 'gp', 'rp', 'ip', 'zs', 'w']
    cadence_frequency = forms.IntegerField(required=True, help_text='in hours')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add fields for each available filter as specified in the filters property
        for filter_code, filter_name in LCOCustomPhotometricSequenceForm.filter_choices():
            self.fields[filter_code] = FilterField(label=filter_name, required=False)

        # Massage cadence form to be SNEx-styled
        self.fields['cadence_strategy'] = forms.ChoiceField(
            choices=[('', 'Once in the next'), ('ResumeCadenceAfterFailureStrategy', 'Repeating every')],
            required=False,
        )
        for field_name in ['exposure_time', 'exposure_count', 'filter']:
            self.fields.pop(field_name)
        if self.fields.get('groups'):
            self.fields['groups'].label = 'Data granted to'
        for field_name in ['start', 'end']:
            self.fields[field_name].widget = forms.HiddenInput()
            self.fields[field_name].required = False

        self.helper.layout = Layout(
            Row(
                Column('name'),
                Column('cadence_strategy'),
                Column('cadence_frequency'),
            ),
            Layout('facility', 'target_id', 'observation_type'),
            self.layout(),
            self.button_layout()
        )

    def _build_instrument_config(self):
        """
        Because the photometric sequence form provides form inputs for 10 different filters, they must be
        constructed into a list of instrument configurations as per the LCO API. This method constructs the
        instrument configurations in the appropriate manner.
        """
        instrument_config = []
        for filter_name in self.valid_filters:
            if len(self.cleaned_data[filter_name]) > 0:
                instrument_config.append({
                    'exposure_count': self.cleaned_data[filter_name][1],
                    'exposure_time': self.cleaned_data[filter_name][0],
                    'optical_elements': {
                        'filter': filter_name
                    }
                })

        return instrument_config

    def clean_start(self):
        """
        Unless included in the submission, set the start time to now.
        """
        start = self.cleaned_data.get('start')
        if not start:  # Start is in cleaned_data as an empty string if it was not submitted, so check falsiness
            start = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S')
        return start

    def clean_end(self):
        """
        Override clean_end in order to avoid the superclass attempting to date-parse an empty string.
        """
        return self.cleaned_data.get('end')

    def clean(self):
        """
        This clean method does the following:
            - Adds an end time that corresponds with the cadence frequency
        """
        cleaned_data = super().clean()
        start = cleaned_data.get('start')
        cleaned_data['end'] = datetime.strftime(parse(start) + timedelta(hours=cleaned_data['cadence_frequency']),
                                                '%Y-%m-%dT%H:%M:%S')

        return cleaned_data

    @staticmethod
    def instrument_choices():
        """
        This method returns only the instrument choices available in the current SNEx photometric sequence form.
        """
        return sorted([(k, v['name'])
                       for k, v in LCOCustomPhotometricSequenceForm._get_instruments().items()
                       if k in LCOCustomPhotometricSequenceForm.valid_instruments],
                      key=lambda inst: inst[1])

    @staticmethod
    def filter_choices():
        return sorted(set([
            (f['code'], f['name']) for ins in LCOCustomPhotometricSequenceForm._get_instruments().values() for f in
            ins['optical_elements'].get('filters', [])
            if f['code'] in LCOCustomPhotometricSequenceForm.valid_filters]),
            key=lambda filter_tuple: filter_tuple[1])

    def cadence_layout(self):
        return Layout(
            Row(
                Column('cadence_type'), Column('cadence_frequency')
            )
        )

    def layout(self):
        if settings.TARGET_PERMISSIONS_ONLY:
            groups = Div()
        else:
            groups = Row('groups')

        # Add filters to layout
        filter_layout = Layout(
            Row(
                Column(HTML('Exposure Time')),
                Column(HTML('No. of Exposures')),
                Column(HTML('Block No.')),
            )
        )
        for filter_name in self.valid_filters:
            filter_layout.append(Row(MultiWidgetField(filter_name, attrs={'min': 0})))

        return Row(
            Column(
                filter_layout,
                css_class='col-md-6'
            ),
            Column(
                Row('max_airmass'),
                Row(
                    PrependedText('min_lunar_distance', '>')
                ),
                Row('instrument_type'),
                Row('proposal'),
                Row('observation_mode'),
                Row('ipp_value'),
                groups,
                css_class='col-md-6'
            ),
        )
