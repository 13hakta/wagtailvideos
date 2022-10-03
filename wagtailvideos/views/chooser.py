from distutils.version import LooseVersion

import wagtail
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.core.models import Collection
from wagtail.search import index as search_index

from wagtailvideos import get_video_model
from wagtailvideos.forms import get_video_form
from wagtailvideos.permissions import permission_policy

if LooseVersion(wagtail.__version__) >= LooseVersion('2.7'):
    from wagtail.admin.auth import PermissionPolicyChecker
    from wagtail.admin.models import popular_tags_for_model
else:
    from wagtail.admin.utils import (
        PermissionPolicyChecker, popular_tags_for_model)

permission_checker = PermissionPolicyChecker(permission_policy)


def get_chooser_js_data():
    """construct context variables needed by the chooser JS"""
    return {
        'step': 'chooser',
        'error_label': _("Server Error"),
        'error_message': _("Report this error to your webmaster with the following information:"),
        'tag_autocomplete_url': reverse('wagtailadmin_tag_autocomplete'),
    }


def get_video_json(video):
    """
    helper function: given a video, return the json to pass back to the
    video chooser panel
    """

    return {
        'id': video.id,
        'edit_link': reverse('wagtailvideos:edit', args=(video.id,)),
        'title': video.title,
        'preview': {
            'url': video.thumbnail.url if video.thumbnail else '',
        }
    }


def chooser(request):
    Video = get_video_model()
    VideoForm = get_video_form(Video)
    uploadform = VideoForm()

    videos = Video.objects.order_by('-created_at')

    q = None
    if (
        'q' in request.GET or 'p' in request.GET or 'tag' in request.GET
        or 'collection_id' in request.GET
    ):
        # this request is triggered from search, pagination or 'popular tags';
        # we will just render the results.html fragment
        collection_id = request.GET.get('collection_id')
        if collection_id:
            videos = videos.filter(collection=collection_id)

        collections = permission_policy.collections_user_has_any_permission_for(
            request.user, ['choose'])

        if len(collections) > 0:
            videos = videos.filter(collection__in=collections)

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            videos = videos.search(q)
            is_searching = True
        else:
            is_searching = False

            tag_name = request.GET.get('tag')
            if tag_name:
                videos = videos.filter(tags__name=tag_name)

        # Pagination
        paginator = Paginator(videos, per_page=12)
        page = paginator.get_page(request.GET.get('p'))

        return render(request, "wagtailvideos/chooser/results.html", {
            'videos': page,
            'is_searching': is_searching,
            'query_string': q,
        })
    else:
        searchform = SearchForm()

        collections = permission_policy.collections_user_has_permission_for(
            request.user, 'choose'
        )

        if len(collections) < 2:
            collections = None

        paginator = Paginator(videos, per_page=12)
        page = paginator.get_page(request.GET.get('p'))

    return render_modal_workflow(request, 'wagtailvideos/chooser/chooser.html', None, {
        'videos': page,
        'uploadform': uploadform,
        'searchform': searchform,
        'is_searching': False,
        'query_string': q,
        'popular_tags': popular_tags_for_model(Video),
        'collections': collections,
    }, json_data=get_chooser_js_data())


def video_chosen(request, video_id):
    video = get_object_or_404(get_video_model(), id=video_id)

    return render_modal_workflow(
        request, None, json_data={
            'step': 'video_chosen',
            'result': get_video_json(video)
        })


@permission_checker.require('add')
def chooser_upload(request):
    Video = get_video_model()
    VideoForm = get_video_form(Video)

    searchform = SearchForm()

    if request.POST:
        video = Video(uploaded_by_user=request.user)
        form = VideoForm(request.POST, request.FILES, instance=video)

        if form.is_valid():
            video.uploaded_by_user = request.user
            video.save()

            # Reindex the video to make sure all tags are indexed
            search_index.insert_or_update_object(video)

            return render_modal_workflow(
                request, None, json_data={
                    'step': 'video_chosen',
                    'result': get_video_json(video)
                }
            )
    else:
        form = VideoForm()

    videos = Video.objects.order_by('title')
    paginator = Paginator(videos, per_page=12)
    page = paginator.get_page(request.GET.get('p'))

    return render_modal_workflow(
        request, 'wagtailvideos/chooser/chooser.html', None,
        template_vars={'videos': page, 'uploadform': form, 'searchform': searchform},
        json_data=get_chooser_js_data()
    )
