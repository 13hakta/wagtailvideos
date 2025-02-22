# Generated by Django 3.1.2 on 2022-10-03 22:43

from django.db import migrations


def add_choose_permission_to_admin_groups(apps, _schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    Group = apps.get_model("auth.Group")

    # Get video content type
    video_content_type, _created = ContentType.objects.get_or_create(
        model="video", app_label="wagtailvideos"
    )

    # Create the Choose permission (if it doesn't already exist)
    choose_video_permission, _created = Permission.objects.get_or_create(
        content_type=video_content_type,
        codename="choose_video",
        defaults={"name": "Can choose video"},
    )

    # Assign it to all groups which have "Access the Wagtail admin" permission.
    # This emulates the previous behaviour, where everyone could choose any video in any Collection
    # because choosing wasn't permissioned.
    for group in Group.objects.filter(permissions__codename="access_admin"):
        group.permissions.add(choose_video_permission)


def remove_choose_permission(apps, _schema_editor):
    """Reverse the above additions of permissions."""
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    video_content_type = ContentType.objects.get(
        model="video",
        app_label="wagtailvideos",
    )
    # This cascades to Group
    Permission.objects.filter(
        content_type=video_content_type, codename="choose_video"
    ).delete()


def get_choose_permission(apps):
    Permission = apps.get_model("auth.Permission")
    ContentType = apps.get_model("contenttypes.ContentType")

    video_content_type, _created = ContentType.objects.get_or_create(
        model="video",
        app_label="wagtailvideos",
    )
    return Permission.objects.filter(
        content_type=video_content_type, codename__in=["choose_video"]
    ).first()


def copy_choose_permission_to_collections(apps, _schema_editor):
    Collection = apps.get_model("wagtailcore.Collection")
    Group = apps.get_model("auth.Group")
    GroupCollectionPermission = apps.get_model("wagtailcore.GroupCollectionPermission")

    root_collection = Collection.objects.get(depth=1)

    permission = get_choose_permission(apps)
    if permission:
        for group in Group.objects.filter(permissions=permission):
            GroupCollectionPermission.objects.create(
                group=group, collection=root_collection, permission=permission
            )


def remove_choose_permission_from_collections(apps, _schema_editor):
    GroupCollectionPermission = apps.get_model("wagtailcore.GroupCollectionPermission")
    choose_permission = get_choose_permission(apps)
    if choose_permission:
        GroupCollectionPermission.objects.filter(permission=choose_permission).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailvideos", "0012_remove_unique_constraint"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="video",
            options={
                "permissions": [("choose_video", "Can choose video")],
                "verbose_name": "video",
                "verbose_name_plural": "videos",
            },
        ),
        migrations.RunPython(
            add_choose_permission_to_admin_groups, remove_choose_permission
        ),
        migrations.RunPython(
            copy_choose_permission_to_collections,
            remove_choose_permission_from_collections,
        ),
    ]
