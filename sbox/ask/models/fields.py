from datetime import datetime, time
import ast
from string import capwords
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
import markdown
from django.conf import settings
import custom_widgets
import floppyforms
from twiliobox import question_methods as twiliofunctions
import ask.validators as validators
from ask.models import stata_functions as stata
import base64
import magic
from django.core.files.base import ContentFile


FIELD_NAMES = [
    'checkboxes',
    'date',
    'date-time',
    'time',
    'decimal',
    'hangup',
    'instruction',
    'uninterruptible-instruction',
    'integer',
    'likert',
    'likert-list',
    'long-text',
    'pulldown',
    'required-checkbox',
    'short-text',
    'show-score',
    'upload',
    'webcam',
]


def class_name(q_type_string):
    return "".join([capwords(i) for i in q_type_string.split("-")])

__all__ = [class_name(i) for i in FIELD_NAMES]


def _merge_field_or_widget_kwargs(old, extra):
    if extra:
        for k, v in extra.items():
            if isinstance(v, dict) and old.get(k, None):
                old[k].update(v)
            else:
                old[k] = v
    return old


class SignalboxField(object):
    """
    Adds things to Floppyforms fields.

    A mixin to be used in conjunction with floppyforms fields to display
    a :class:`Question`."""

    voice_function = None
    has_choices = True
    required = False
    required_possible = True
    response_possible = True
    prepend_null_choice = False
    export_processor = None
    widget_kwargs = {}
    error_messages = {'required': _("An answer to this question is needed.")}
    choices = None
    input_formats = None
    validators = []

    @staticmethod
    def save_answer(response, answer):
        """
        Save user data for this field type.

        Accepts a user response and and answer object and insert the
        response into the answer. Allows custom fields to have
        type-specific processing (e.g. files or webcam images)."""

        answer.answer = response
        return answer

    @staticmethod
    def label_variable(question):
        """Returns (stata) syntax to label this variable in exported data."""

        return stata.label_variable(question)

    @staticmethod
    def label_choices(question):
        """Returns (stata) syntax to label the choices in exported data."""

        return stata.label_choices(question)

    @staticmethod
    def set_format(question):
        """Returns (stata) syntax to format/recast the exported data."""

        return ""

    @staticmethod
    def redisplay_processor(value):
        """Returns object to use when redisplaying a saved value.

        Default is just to pass back the string saved in the database,
        but needed for some of the more complex fields below.
        """
        return value

    @staticmethod
    def voice_function(*args, **kwargs):
        """The function to call the Twilio api for this question type."""

        raise Exception(_("Not implemented yet"))

    def __init__(self, questioninaskpage, reply, request, *args, **kwargs):

        super(
            SignalboxField, self).__init__(error_messages=self.error_messages,
                                           validators=self.validators,
                                           *args, **kwargs)

        self.label = mark_safe(markdown.markdown(
            questioninaskpage.question.display_text(
                reply=reply, request=request, page=getattr(
                    questioninaskpage, 'page', None))))
        self.help_text = questioninaskpage.question.help_text

        # Is the field required?
        self.required = False
        if self.required_possible:
            self.required = self.required or questioninaskpage.required\
                or questioninaskpage.question.always_required
        else:
            self.required = False

        # update the widget too because floppy forms triggers html5
        # client side validation in Chrome
        self.widget.is_required = self.required

        # Extra information on the widget stored on the ...
        # ...Field class
        self.widget.attrs.update(self.widget_kwargs.get('attrs', {}))
        # ...Question instance
        if questioninaskpage.question.widget_kwargs:
            self.widget.attrs.update(
                questioninaskpage.question.widget_kwargs.get('attrs', {}))

        # Extra information about the field stored on the Question
        if questioninaskpage.question.field_kwargs:
            for k, v in questioninaskpage.question.field_kwargs.items():
                setattr(self, k, v)

        # Setup choices
        self.widget.choices = self.choices = questioninaskpage.question.choices()
        if self.widget.choices:
            if questioninaskpage.allow_not_applicable:
                self.widget.choices.insert(0, ["NA", "NA"])
            self.initial = questioninaskpage.question.choiceset.default_value()

            if self.prepend_null_choice:
                self.widget.choices.insert(0, ["", "---"])

        previous_answer = questioninaskpage.question.previous_answer(reply)
        if previous_answer:
            self.initial = self.redisplay_processor(previous_answer)


class Instruction(SignalboxField, floppyforms.CharField):
    """Display question text only."""

    widget = custom_widgets.InstructionWidget
    widget_kwargs = {'a': 1}

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.instruction(*args, **kwargs)

    has_choices = False
    response_possible = False
    required_possible = False


class ShortText(SignalboxField, floppyforms.CharField):
    """Enter a single line of text."""

    has_choices = False

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.listen(*args, **kwargs)


class LongText(SignalboxField, floppyforms.CharField):
    """Enter a single line of text."""

    widget = floppyforms.widgets.Textarea
    has_choices = False

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.listen(*args, **kwargs)


class Likert(SignalboxField, floppyforms.ChoiceField):
    """Choose a single option from Radio buttons presented horizontally."""

    widget = custom_widgets.InlineRadioSelect
    validators = [validators.is_int, ]

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.multiple(*args, **kwargs)


class LikertList(Likert):
    """Choose a single option from Radio buttons presented vertically."""

    widget = floppyforms.RadioSelect


class Checkboxes(SignalboxField, floppyforms.TypedMultipleChoiceField):
    """Choose multiple options from a vertical list of checkboxes."""

    widget = floppyforms.widgets.CheckboxSelectMultiple
    label_choices = stata.label_choices_checkboxes

    @staticmethod
    def label_choices(question):
        return  stata.label_choices_checkboxes(question)

    @staticmethod
    def redisplay_processor(value):
        """Returns a python list to redisplay checkbox selections."""

        return ast.literal_eval(value)

    @staticmethod
    def export_processor(value):
        """Preprocess list __repr__ for export to txt.

        Preprocessor function to process the list repr stored in the
        DB for use in export txt files."""
        try:
            return ",".join(ast.literal_eval(value))
        except Exception:
            return value


class RequiredCheckbox(SignalboxField, floppyforms.BooleanField):
    """A single checkbox which must be selected by the user to continue."""

    widget = floppyforms.widgets.CheckboxInput
    required = True


class Pulldown(SignalboxField, floppyforms.ChoiceField):
    """Choose a single option from a pulldown list."""

    widget = floppyforms.Select
    prepend_null_choice = True

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.multiple(*args, **kwargs)


class ShowScore(SignalboxField, floppyforms.CharField):
    """Display summary score from previous responses within Questionnaire."""

    widget = custom_widgets.ShowScoreSheetWidget
    has_choices = False
    response_possible = False
    required_possible = False

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.instruction(*args, **kwargs)


class Date(SignalboxField, floppyforms.DateField):
    """Presents an html date-picker object. Degrades to text input."""

    widget = floppyforms.widgets.TextInput
    input_formats = settings.DATE_INPUT_FORMATS
    has_choices = False
    widget_kwargs = {'attrs': {'class': 'datepicker'}}

    @staticmethod
    def set_format(question):
        """Returns (stata) syntax to label the choices in exported data."""
        return stata.set_format_date(question)


class DateTime(SignalboxField, floppyforms.DateTimeField):
    """Presents an html datetime-picker object. Degrades to text input."""

    widget = floppyforms.widgets.TextInput
    has_choices = False
    widget_kwargs = {'attrs': {'class': 'datetimepicker'}}

    @staticmethod
    def set_format(question):
        """Returns (stata) syntax to correctly format exported data."""
        return stata.set_format_datetime(question)


class Time(SignalboxField, floppyforms.TimeField):
    """Presents an html datetime-picker object. Degrades to text input."""

    has_choices = False
    widget_kwargs = {'attrs': {'class': 'timepicker'}}

    @staticmethod
    def set_format(question):
        """Returns (stata) syntax to correctly format exported data."""
        return stata.set_format_time(question)

    @staticmethod
    def export_processor(value):
        """Add number of milliseconds from 00:00 -> (str, str)"""

        timeparts = [int(i) for i in value.split(":")]
        thetime = time(*timeparts)
        baseline = datetime.today()
        difference = datetime.combine(
            baseline, thetime) - datetime.combine(baseline, time())
        return ",".join((value, unicode(difference.total_seconds())))


class Integer(SignalboxField, floppyforms.IntegerField):
    """Text box to enter any integer."""

    has_choices = False
    error_messages = {'invalid': _(
        "This question needs an answer in whole numbers."), }

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.integer(*args, **kwargs)


class Decimal(SignalboxField, floppyforms.DecimalField):
    """Textbox to enter a number to two decimal places."""

    has_choices = False
    decimal_places = 2
    max_digits = 10


class RangeSlider(SignalboxField, floppyforms.IntegerField):
    """Displays an html range slider. Default is 0 to 100."""

    widget = floppyforms.widgets.RangeInput  # renders as an html range input
    has_choices = False


# some twilio specific types (we can use the fields above too if they
# have a voice_function)
class Hangup(Instruction):

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.hangup(*args, **kwargs)


class UninterruptibleInstruction(Instruction):
    """Twilio plays the question text without allowing barge-in."""

    @staticmethod
    def voice_function(*args, **kwargs):
        return twiliofunctions.uninterruptible_instruction(*args, **kwargs)


class Upload(SignalboxField, floppyforms.FileField):
    """."""

    widget = floppyforms.widgets.FileInput  # renders as an html range input
    has_choices = False
    validators = [validators.is_allowed_upload_file_type]

    @staticmethod
    def save_answer(response, answer):
        answer.upload = response
        answer.answer = ""
        return answer


class Webcam(LongText):
    """."""

    widget = custom_widgets.WebcamWidget

    @staticmethod
    def save_answer(response, answer):
        """Decode base64 encoded pngs and save as a file object."""
        try:
            myFile = ContentFile(base64.b64decode(response))
            answer.upload.save(
                "{0}.png".format(answer.question.variable_name), myFile, save=False)
            answer.answer = ""
        except:
            answer.meta = "ERROR SAVING WEBCAM IMAGE"

        return answer
