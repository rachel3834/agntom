from tom_observations.observation_template import GenericTemplateForm
from tom_observations.facilities.lco import LCOBaseForm, LCOBaseObservationForm, observation_mode_help
from tom_observations.widgets import FilterField
from django import forms
from django.urls import reverse
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import AppendedText, PrependedText
from crispy_forms.layout import ButtonHolder, Column, Layout, HTML, Row, Div
from crispy_forms.layout import Submit, MultiWidgetField

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
    template_type = forms.CharField(initial='lco_imaging_request',
                                widget=forms.HiddenInput())

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
                Column('template_type'),
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


class LCOImagingSequenceTemplateForm(GenericTemplateForm, LCOBaseForm):
    """
    The LCOImagingSequenceTemplateForm provides a form offering a subset of the parameters in the LCOImagingObservationForm.
    The form is modeled after the Supernova Exchange application's Photometric Sequence Request Form, and allows the
    configuration of multiple filters, as well as a more intuitive proactive cadence form.

    Note that in contrast with the LCOPhotometricSequenceForm, this class cannot
    inherit from the LCOBaseObservationForm, since that class has methods
    which refer to specific targets.
    """
    valid_instruments = ['1M0-SCICAM-SINISTRO', '0M4-SCICAM-SBIG', '2M0-SPECTRAL-AG']
    valid_filters = ['U', 'B', 'V', 'R', 'I', 'up', 'gp', 'rp', 'ip', 'zs', 'w']
    max_lunar_phase = forms.FloatField()
    min_lunar_distance = forms.FloatField()
    cadence = forms.FloatField(help_text='in hours')
    jitter = forms.FloatField(help_text='in hours')
    observation_mode = forms.ChoiceField(
        choices=(('NORMAL', 'Normal'), ('RAPID_RESPONSE', 'Rapid-Response'), ('TIME_CRITICAL', 'Time-Critical')),
        help_text=observation_mode_help
    )
    template_type = forms.CharField(initial='lco_imaging_sequence',
                                    widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add fields for each available filter as specified in the filters property
        for filter_code, filter_name in LCOImagingSequenceTemplateForm.filter_choices():
            self.fields[filter_code] = FilterField(label=filter_name, required=False)

        # The FilterField objects inserted for each filter replace the
        # separate fields for exposure and exposure count etc in the parameters.
        for field_name in ['exposure_time', 'exposure_count', 'filter']:
            self.fields.pop(field_name)

        for field in self.fields:
            if field != 'template_name' and field != 'template_type':
                self.fields[field].required = False

        self.helper.layout = Layout(
            Row(
                Column('template_name'),
                Column('template_type'),
            ),
            Layout('facility'),
            self.layout(),
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

    @staticmethod
    def instrument_choices():
        """
        This method returns only the instrument choices available in the current SNEx photometric sequence form.
        """
        return sorted([(k, v['name'])
                       for k, v in LCOImagingSequenceTemplateForm._get_instruments().items()
                       if k in LCOImagingSequenceTemplateForm.valid_instruments],
                      key=lambda inst: inst[1])

    @staticmethod
    def filter_choices():
        return sorted(set([
            (f['code'], f['name']) for ins in LCOImagingSequenceTemplateForm._get_instruments().values() for f in
            ins['optical_elements'].get('filters', [])
            if f['code'] in LCOImagingSequenceTemplateForm.valid_filters]),
            key=lambda filter_tuple: filter_tuple[1])

    def layout(self):

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
                Row('max_lunar_phase'),
                Row(
                    PrependedText('min_lunar_distance', '>')
                ),
                Row('instrument_type'),
                Row('proposal'),
                Row('observation_mode'),
                Row('ipp_value'),
                Row('cadence'),
                Row('jitter'),
                css_class='col-md-6'
            ),
        )
