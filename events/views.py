from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.db.models import Q

from django.http import Http404

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST



from .calendar_utils import (

    MONTH_NAMES_RU,

    WEEKDAY_NAMES_RU,

    build_month_data,

    get_three_months,

    group_events_by_date,

    parse_month_param,

    shift_month,

)

from .forms import CustomFieldFormSet, EventApplicationForm, EventForm

from .models import Event, EventApplication

from .utils import build_form_fields_config





def _get_filtered_events(request):

    """Возвращает queryset опубликованных мероприятий с учётом фильтров."""

    queryset = Event.objects.filter(is_published=True).select_related('organizer')



    event_types = request.GET.getlist('event_type')

    if event_types:

        queryset = queryset.filter(event_type__in=event_types)



    city = request.GET.get('city', '').strip()

    if city:

        queryset = queryset.filter(

            Q(location__icontains=city) | Q(organizer__city__icontains=city)

        )



    return queryset.order_by('event_date')





def _get_city_choices():

    """Возвращает список городов для фильтра календаря."""

    locations = (

        Event.objects.filter(is_published=True)

        .exclude(location='')

        .values_list('location', flat=True)

        .distinct()

    )

    cities = (

        Event.objects.filter(is_published=True)

        .exclude(organizer__city='')

        .values_list('organizer__city', flat=True)

        .distinct()

    )

    return sorted(set(locations) | set(cities))





@login_required

def calendar_view(request):

    """Monthly-view календарь: три месяца подряд с маркерами-логотипами."""

    center_year, center_month = parse_month_param(request.GET.get('month'))

    months_data = get_three_months(center_year, center_month)



    events = _get_filtered_events(request)

    range_start = months_data[0]

    range_end = months_data[2]



    from datetime import date

    from dateutil.relativedelta import relativedelta



    start_date = date(range_start[0], range_start[1], 1)

    end_date = date(range_end[0], range_end[1], 1) + relativedelta(months=1)



    events = events.filter(

        event_date__date__gte=start_date,

        event_date__date__lt=end_date,

    )

    events_by_date = group_events_by_date(events)



    calendar_months = [

        build_month_data(year, month, events_by_date)

        for year, month in months_data

    ]



    prev_year, prev_month = shift_month(center_year, center_month, -1)

    next_year, next_month = shift_month(center_year, center_month, 1)



    filter_query = request.GET.urlencode()

    if 'month' in filter_query:

        filter_parts = [

            part for part in filter_query.split('&')

            if not part.startswith('month=')

        ]

        filter_suffix = '&'.join(filter_parts)

    else:

        filter_suffix = filter_query



    context = {

        'calendar_months': calendar_months,

        'center_year': center_year,

        'center_month': center_month,

        'center_month_param': f'{center_year}-{center_month:02d}',

        'center_month_label': f'{MONTH_NAMES_RU[center_month]} {center_year}',

        'prev_month_param': f'{prev_year}-{prev_month:02d}',

        'next_month_param': f'{next_year}-{next_month:02d}',

        'weekday_names': WEEKDAY_NAMES_RU,

        'event_type_choices': Event.EVENT_TYPE_CHOICES,

        'selected_event_types': request.GET.getlist('event_type'),

        'selected_city': request.GET.get('city', ''),

        'city_choices': _get_city_choices(),

        'filter_suffix': filter_suffix,

        'can_create_event': request.user.user_type == 'organizer',

    }

    return render(request, 'events/calendar.html', context)





@login_required

def event_detail(request, pk):

    """Страница мероприятия."""

    event = get_object_or_404(

        Event.objects.select_related('organizer', 'organizer__organizer_profile'),

        pk=pk,

    )

    if not event.is_published and event.organizer != request.user:

        messages.error(request, 'Мероприятие недоступно.')

        return redirect('events:calendar')



    user_application = None

    can_apply = False



    if request.user.is_authenticated and request.user != event.organizer:

        user_application = EventApplication.objects.filter(

            event=event,

            applicant=request.user,

        ).first()

        can_apply = (

            event.is_registration_open

            and user_application is None

        )



    context = {

        'event': event,

        'is_organizer': request.user == event.organizer,

        'user_application': user_application,

        'can_apply': can_apply,

        'registration_open': event.is_registration_open,

        'applications_count': event.applications.count() if request.user == event.organizer else None,

    }

    return render(request, 'events/detail.html', context)





@login_required

@require_http_methods(['GET', 'POST'])

def event_create(request):

    """Создание мероприятия — только для организаторов."""

    if request.user.user_type != 'organizer':

        messages.error(request, 'Создавать мероприятия могут только организаторы.')

        return redirect('events:calendar')



    if request.method == 'POST':

        form = EventForm(request.POST, request.FILES)

        field_formset = CustomFieldFormSet(request.POST, prefix='fields')



        if form.is_valid() and field_formset.is_valid():

            event = form.save(commit=False)

            event.organizer = request.user

            event.form_fields = build_form_fields_config(

                field_formset,

                form.cleaned_data.get('require_audio', True),

            )

            event.save()

            messages.success(request, f'Мероприятие «{event.title}» создано!')

            return redirect('events:detail', pk=event.pk)

    else:

        form = EventForm()

        field_formset = CustomFieldFormSet(prefix='fields')



    return render(request, 'events/create.html', {

        'form': form,

        'field_formset': field_formset,

    })





@login_required

@require_http_methods(['GET', 'POST'])

def event_apply(request, pk):

    """Подача заявки участником на мероприятие."""

    event = get_object_or_404(Event.objects.select_related('organizer'), pk=pk)



    if not event.is_published:

        messages.error(request, 'Мероприятие недоступно для заявок.')

        return redirect('events:detail', pk=event.pk)



    if request.user == event.organizer:

        messages.error(request, 'Организатор не может подать заявку на своё мероприятие.')

        return redirect('events:detail', pk=event.pk)



    if not event.is_registration_open:

        messages.error(request, 'Регистрация на это мероприятие закрыта.')

        return redirect('events:detail', pk=event.pk)



    existing = EventApplication.objects.filter(event=event, applicant=request.user).first()

    if existing:

        messages.info(request, 'Вы уже подали заявку на это мероприятие.')

        return redirect('events:detail', pk=event.pk)



    if request.method == 'POST':

        form = EventApplicationForm(event, request.POST, request.FILES)

        if form.is_valid():

            application = EventApplication(

                event=event,

                applicant=request.user,

                form_data=form.get_form_data(),

                status='pending',

            )

            if form.cleaned_data.get('audio_file'):

                application.audio_file = form.cleaned_data['audio_file']

            application.save()

            messages.success(request, 'Заявка успешно отправлена!')

            return redirect('events:detail', pk=event.pk)

    else:

        form = EventApplicationForm(event)



    return render(request, 'events/apply.html', {

        'event': event,

        'form': form,

    })





@login_required

def event_applications(request, pk):

    """Список заявок на мероприятие — только для организатора."""

    event = get_object_or_404(Event.objects.select_related('organizer'), pk=pk)



    if request.user != event.organizer:

        raise Http404



    status_filter = request.GET.get('status', '')

    applications = EventApplication.objects.filter(

        event=event,

    ).select_related('applicant').order_by('-created_at')



    if status_filter in dict(EventApplication.STATUS_CHOICES):

        applications = applications.filter(status=status_filter)



    return render(request, 'events/applications.html', {

        'event': event,

        'applications': applications,

        'status_filter': status_filter,

        'status_choices': EventApplication.STATUS_CHOICES,

    })





@login_required

@require_POST

def application_update_status(request, pk):

    """Изменение статуса заявки организатором."""

    application = get_object_or_404(

        EventApplication.objects.select_related('event', 'event__organizer'),

        pk=pk,

    )



    if request.user != application.event.organizer:

        raise Http404



    new_status = request.POST.get('status', '')

    valid_statuses = dict(EventApplication.STATUS_CHOICES)



    if new_status not in valid_statuses:

        messages.error(request, 'Некорректный статус заявки.')

    else:

        application.status = new_status

        application.save(update_fields=['status', 'updated_at'])

        messages.success(

            request,

            f'Статус заявки от {application.applicant.username} изменён на «{valid_statuses[new_status]}».',

        )



    next_url = request.POST.get('next')

    if next_url:

        return redirect(next_url)

    return redirect('events:applications', pk=application.event.pk)


